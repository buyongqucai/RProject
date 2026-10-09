"""pcNet as in scTenifoldNet 1.4.3: one Gram eigenproblem, then the secular equation.

The algebra is the vendored `R_仓库公式/pcNet_1.4.3.R`. This file does not
use a per-gene SVD. Torch runs the same steps in float64 on CPU or CUDA.
"""

from __future__ import annotations

import numpy as np
import torch

from knk_accel.pcnet import r_quantile


def _as_torch(values: np.ndarray, device: torch.device) -> torch.Tensor:
    array = np.ascontiguousarray(values)
    if not array.flags.writeable:
        array = array.copy()
    return torch.as_tensor(array, device=device, dtype=torch.float64)


def _standardize(counts_genes_by_cells: np.ndarray, device: torch.device):
    """Match .pcNetStandardize. Returns samples-by-used-genes and the keep mask."""
    raw = _as_torch(np.asarray(counts_genes_by_cells, dtype=np.float64).T, device)
    n_samples, n_genes = raw.shape
    first = raw[0]
    non_constant = torch.sum(raw != first.unsqueeze(0), dim=0) > 0
    used = raw[:, non_constant]
    means = used.mean(dim=0)
    centered = used - means
    denom = max(n_samples - 1, 1)
    sds = torch.sqrt(torch.sum(centered * centered, dim=0) / denom)
    return centered / sds, non_constant.detach().cpu().numpy()


def _eigen_basis(x_std: torch.Tensor):
    """Match .pcNetEigenBasis. Eigenvalues come back in decreasing order."""
    n_samples, n_genes = x_std.shape
    if n_samples <= n_genes:
        gram = x_std @ x_std.T
        evals, evecs = torch.linalg.eigh(gram)
        evals = torch.flip(evals, dims=(0,))
        evecs = torch.flip(evecs, dims=(1,))
        d = torch.clamp(evals, min=0)
        z = evecs.T @ x_std
    else:
        gram = x_std.T @ x_std
        evals, evecs = torch.linalg.eigh(gram)
        evals = torch.flip(evals, dims=(0,))
        evecs = torch.flip(evecs, dims=(1,))
        d = torch.clamp(evals, min=0)
        z = torch.sqrt(d).unsqueeze(1) * evecs.T
    return z, d


def _secular_weights(z: torch.Tensor, d: torch.Tensor, n_comp: int, strategy: str = "loop") -> torch.Tensor:
    """Match .pcNetSecularWeights. Column k is the weight vector of gene k."""
    eps = torch.finfo(torch.float64).eps
    n_eig_input = z.shape[0]
    n_genes = z.shape[1]
    n_eig = n_eig_input
    if n_eig < n_comp + 1:
        n_pad = n_comp + 1 - n_eig
        z = torch.cat([z, torch.zeros((n_pad, n_genes), dtype=torch.float64, device=z.device)], dim=0)
        d = torch.cat([d, torch.zeros(n_pad, dtype=torch.float64, device=d.device)], dim=0)
        n_eig = n_comp + 1

    xmin = torch.tensor(torch.finfo(torch.float64).tiny, dtype=torch.float64, device=z.device)
    tiny = torch.sqrt(torch.maximum(d[0], xmin)) * 1e-60
    near_zero = torch.abs(z) < tiny
    if bool(torch.any(near_zero)):
        z = torch.where(near_zero, torch.where(z < 0, -tiny, tiny), z)
    if strategy == "fused":
        from knk_accel.secular_merge import fused_secular_weights

        return fused_secular_weights(z, d, n_comp)[:n_eig_input]
    z2 = z * z
    weights = torch.zeros((n_eig, n_genes), dtype=torch.float64, device=z.device)

    for index in range(n_comp):
        d_upper = d[index]
        d_lower = d[index + 1]
        gap = d_upper - d_lower
        if not bool(gap > 0):
            continue
        rows_above = slice(0, index + 1)
        rows_below = slice(index + 1, n_eig)
        midpoint = d_lower + gap / 2
        near_upper = (1 - torch.sum(z2 / (d - midpoint).unsqueeze(1), dim=0)) >= 0
        origin = torch.where(near_upper, d_upper, d_lower)
        zeros = torch.zeros(n_genes, dtype=torch.float64, device=z.device)
        pole_lower = torch.where(near_upper, -gap.expand(n_genes), zeros)
        pole_upper = torch.where(near_upper, zeros, gap.expand(n_genes))
        bracket_lo = torch.where(near_upper, (-gap / 2).expand(n_genes), zeros)
        bracket_hi = torch.where(near_upper, zeros, (gap / 2).expand(n_genes))
        tau = (bracket_lo + bracket_hi) / 2
        d_minus_origin = d.unsqueeze(1) - origin.unsqueeze(0)
        active = torch.arange(n_genes, device=z.device)

        for _iteration in range(300):
            if active.numel() == 0:
                break
            tau_a = tau[active]
            gaps = d_minus_origin[:, active] - tau_a.unsqueeze(0)
            terms = z2[:, active] / gaps
            slopes = terms / gaps
            sum_above = torch.sum(terms[rows_above], dim=0)
            slope_above = torch.sum(slopes[rows_above], dim=0)
            sum_below = torch.sum(terms[rows_below], dim=0)
            slope_below = torch.sum(slopes[rows_below], dim=0)
            residual = 1 - sum_above - sum_below

            lo = bracket_lo[active].clone()
            hi = bracket_hi[active].clone()
            lo = torch.where(residual > 0, tau_a, lo)
            hi = torch.where(residual < 0, tau_a, hi)
            bracket_lo[active] = lo
            bracket_hi[active] = hi

            to_lower = pole_lower[active] - tau_a
            to_upper = pole_upper[active] - tau_a
            quad_a = residual + slope_below * to_lower + slope_above * to_upper
            quad_b = (
                quad_a * (to_lower + to_upper)
                - slope_below * to_lower * to_lower
                - slope_above * to_upper * to_upper
            )
            quad_c = residual * to_lower * to_upper
            sqrt_disc = torch.sqrt(torch.clamp(quad_b * quad_b - 4 * quad_a * quad_c, min=0))
            half = (quad_b + torch.where(quad_b >= 0, sqrt_disc, -sqrt_disc)) / 2
            root_1 = half / quad_a
            root_2 = quad_c / half
            use_first = (~torch.isnan(root_1)) & (root_1 > to_lower) & (root_1 < to_upper)
            step = torch.where(use_first, root_1, root_2)
            tau_new = tau_a + step
            outside = torch.isnan(tau_new) | (tau_new <= lo) | (tau_new >= hi)
            tau_new = torch.where(outside, (lo + hi) / 2, tau_new)
            exact = residual == 0
            tau_new = torch.where(exact, tau_a, tau_new)
            converged = exact | (torch.abs(tau_new - tau_a) <= 4 * eps * torch.abs(tau_new)) | (
                (hi - lo) <= 4 * eps * torch.maximum(torch.abs(lo), torch.abs(hi))
            )
            tau[active] = tau_new
            active = active[~converged]

        mu = origin + tau
        direction = z / (d_minus_origin - tau.unsqueeze(0))
        scale = 1 / (mu * torch.sum(direction * direction, dim=0))
        weights = weights + direction * scale.unsqueeze(0)

    return weights[:n_eig_input]


def _type7_threshold(values: torch.Tensor, probability: float) -> torch.Tensor:
    """stats::quantile type 7 on a tensor. kthvalue is 1-based, same rank as R."""
    flat = values.reshape(-1)
    n = int(flat.numel())
    if n == 0:
        raise ValueError("empty quantile")
    if n == 1:
        return flat[0]
    index = 1.0 + (n - 1) * probability
    lo = min(max(int(np.floor(index)), 1), n)
    hi = min(max(int(np.ceil(index)), 1), n)
    if lo == hi:
        return torch.kthvalue(flat, lo).values
    left = torch.kthvalue(flat, lo).values
    right = torch.kthvalue(flat, hi).values
    weight = index - lo
    return left + weight * (right - left)


def _finish_network_torch(network: torch.Tensor, scale_scores: bool, symmetric: bool, q: float) -> torch.Tensor:
    """Scale and type-7 cutoff while the matrix is still on its own device."""
    if symmetric:
        network = (network + network.T) / 2
    if scale_scores:
        max_abs = torch.max(torch.abs(network))
        if bool(torch.isfinite(max_abs)) and float(max_abs) > 0:
            network = network / max_abs
    if 0 < q < 1:
        threshold = _type7_threshold(torch.abs(network), q)
        network = torch.where(torch.abs(network) < threshold, torch.zeros((), dtype=network.dtype, device=network.device), network)
    return network


def _finish_network(network: np.ndarray, scale_scores: bool, symmetric: bool, q: float) -> np.ndarray:
    if symmetric:
        network = (network + network.T) / 2.0
    if scale_scores:
        max_abs = float(np.max(np.abs(network)))
        if np.isfinite(max_abs) and max_abs > 0:
            network = network / max_abs
    if 0 < q < 1:
        threshold = r_quantile(np.abs(network), q)
        network[np.abs(network) < threshold] = 0.0
    return network


def _embed_constants(product: torch.Tensor, non_constant: np.ndarray, n_genes: int) -> torch.Tensor:
    """Put dropped constant genes back as empty rows and columns, on the same device."""
    if int(np.sum(non_constant)) == n_genes:
        return product
    full = torch.zeros((n_genes, n_genes), dtype=product.dtype, device=product.device)
    index = torch.as_tensor(np.flatnonzero(non_constant), device=product.device)
    full[index[:, None], index[None, :]] = product
    return full


def pcnet_secular(
    counts_genes_by_cells: np.ndarray,
    n_comp: int = 3,
    scale_scores: bool = True,
    symmetric: bool = False,
    q: float = 0.0,
    device: str = "cpu",
    merge: str = "auto",
    async_copy: bool = False,
):
    """Genes-by-cells counts to the dense network from scTenifoldNet 1.4.3 pcNet.

    device is cpu or gpu. Both use float64. gpu raises when CUDA is absent.
    merge auto estimates the secular work and, on GPU, may run that loop as
    one CUDA kernel. It does not switch a gpu request back to CPU.
    q follows pcNet's own default of 0. Callers that go through makeNetworks
    or scTenifoldKnk pass 0.95 or 0.9 themselves.
    async_copy on GPU returns a HostBuffer. numpy() waits for the copy.
    """
    if device not in ("cpu", "gpu"):
        raise ValueError("device must be cpu or gpu")
    if device == "gpu" and not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available")
    counts = np.asarray(counts_genes_by_cells, dtype=np.float64)
    if counts.ndim != 2:
        raise ValueError("counts must be a genes-by-cells matrix")
    n_genes = counts.shape[0]
    if n_comp < 2:
        raise ValueError("n_comp must be >= 2")
    torch.set_num_threads(1)
    torch_device = torch.device("cuda" if device == "gpu" else "cpu")
    x_std, non_constant = _standardize(counts, torch_device)
    n_used = int(np.sum(non_constant))
    if n_comp >= n_used:
        raise ValueError(f"n_comp must be < number of non-constant genes ({n_used})")
    from knk_accel.secular_merge import plan_secular_merge

    n_eig_est = min(int(x_std.shape[0]), n_used)
    plan = plan_secular_merge(n_eig_est, n_used, n_comp, device, merge)
    z_basis, eigenvalues = _eigen_basis(x_std)
    weights = _secular_weights(z_basis, eigenvalues, n_comp, strategy=plan["strategy"])
    product = weights.T @ z_basis
    product.fill_diagonal_(0.0)
    if product.is_cuda:
        product = _embed_constants(_finish_network_torch(product, scale_scores, symmetric, q), non_constant, n_genes)
        if async_copy:
            from knk_accel.pcnet import enqueue_host

            return enqueue_host(product)
        return product.detach().cpu().numpy()
    used_network = _finish_network(product.detach().cpu().numpy(), scale_scores, symmetric, q)
    if n_used == n_genes:
        return used_network
    full = np.zeros((n_genes, n_genes), dtype=np.float64)
    full[np.ix_(non_constant, non_constant)] = used_network
    return full
