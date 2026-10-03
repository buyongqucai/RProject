"""Truncated leave-one-out PC regression and the sparse network around it.

Matches scTenifoldNet pcNet: column-scale the cells-by-genes matrix, keep
n_comp right singular vectors, scale by the max absolute weight, then drop
edges below quantile q. Does not call the live Formal job.
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np
from scipy import sparse
from scipy.linalg import svd
from scipy.sparse.linalg import svds


def limit_threads() -> None:
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"


def standardize_cells_by_genes(counts_genes_by_cells: np.ndarray) -> np.ndarray:
    """R scale(t(X)) with divisor n-1. X is genes by cells."""
    x = np.asarray(counts_genes_by_cells, dtype=np.float64).T
    centered = x - x.mean(axis=0, keepdims=True)
    scale = centered.std(axis=0, ddof=1, keepdims=True)
    scale[scale == 0] = 1.0
    return centered / scale


def r_quantile(values: np.ndarray, probability: float) -> float:
    """stats::quantile type 7, the R default.

    Only the one or two order statistics that type 7 interpolates are
    selected. Those values are the same ones a full sort would place at
    these ranks.
    """
    x = np.asarray(values, dtype=np.float64).ravel()
    n = x.size
    if n == 0:
        raise ValueError("empty quantile")
    if n == 1:
        return float(x[0])
    index = 1.0 + (n - 1) * probability
    lo = int(np.floor(index))
    hi = int(np.ceil(index))
    lo = min(max(lo, 1), n)
    hi = min(max(hi, 1), n)
    if lo == hi:
        return float(np.partition(x, lo - 1)[lo - 1])
    part = np.partition(x, (lo - 1, hi - 1))
    weight = index - lo
    left = float(part[lo - 1])
    right = float(part[hi - 1])
    return float(left + weight * (right - left))


def _components(design: np.ndarray, n_comp: int) -> np.ndarray:
    """Keep n_comp right singular vectors.

    Short edges use the full economy SVD. On this machine that matched the
    installed Rcpp result more closely than the iterative solver, and it was
    faster through 160 genes by 100 cells. Larger designs keep the iterative
    truncation.
    """
    if min(design.shape) <= max(n_comp, 128):
        _u, _s, vt = svd(design, full_matrices=False, lapack_driver="gesdd")
        return vt[:n_comp].T
    try:
        _u, _s, vt = svds(design, k=n_comp, which="LM", return_singular_vectors="vh")
    except Exception:
        _u, _s, vt = svd(design, full_matrices=False, lapack_driver="gesdd")
        return vt[:n_comp].T
    return vt[::-1].T


def _coefficients_from_components(design: np.ndarray, target: np.ndarray, components: np.ndarray) -> np.ndarray:
    scores = design @ components
    norms = np.sum(scores * scores, axis=0)
    norms[norms == 0] = 1.0
    scores = scores / norms
    pc_coef = scores.T @ target
    return components @ pc_coef


def _coefficient_rows(x_std: np.ndarray, gene_indices: list[int], n_comp: int) -> tuple[list[int], np.ndarray]:
    rows = np.empty((len(gene_indices), x_std.shape[1] - 1), dtype=np.float64)
    for row_index, gene_index in enumerate(gene_indices):
        target = x_std[:, gene_index]
        design = np.delete(x_std, gene_index, axis=1)
        rows[row_index] = _coefficients_from_components(design, target, _components(design, n_comp))
    return gene_indices, rows


# QR iteration. On cLTMR leave-one-out designs this stays nearer LAPACK than
# the CUDA default Jacobi solver (gesvdj). There is no wider CUDA SVD dtype.
GPU_SVD_DRIVER = "gesvd"


def cuda_available() -> bool:
    try:
        import torch
    except ImportError:
        return False
    return bool(torch.cuda.is_available())


def use_gpu_for(n_samples: int, n_genes: int, device: str = "cpu") -> bool:
    """GPU only when the caller sets device='gpu'. auto stays on CPU."""
    del n_samples, n_genes
    if device in ("cpu", "auto"):
        return False
    if device == "gpu":
        if not cuda_available():
            raise RuntimeError("CUDA is not available")
        return True
    raise ValueError("device must be cpu, auto, or gpu")


def _standardize_gpu(counts_genes_by_cells: np.ndarray, device: "torch.device") -> "torch.Tensor":
    """Same column scale as standardize_cells_by_genes, kept on the given device."""
    import torch

    cells = torch.as_tensor(
        np.ascontiguousarray(np.asarray(counts_genes_by_cells, dtype=np.float64).T),
        device=device,
        dtype=torch.float64,
    )
    centered = cells - cells.mean(dim=0, keepdim=True)
    denom = max(int(cells.shape[0]) - 1, 1)
    scale = torch.sqrt(torch.sum(centered * centered, dim=0, keepdim=True) / denom)
    scale = torch.where(scale == 0, torch.ones_like(scale), scale)
    return centered / scale


def _place_coefficients(coef: "torch.Tensor") -> "torch.Tensor":
    """Each row skips its own gene. Row i of coef lands on every column except i."""
    import torch

    n_genes = int(coef.shape[0])
    network = torch.zeros((n_genes, n_genes), dtype=torch.float64, device=coef.device)
    rows = torch.arange(n_genes, device=coef.device).unsqueeze(1)
    cols = torch.arange(n_genes - 1, device=coef.device).unsqueeze(0)
    dest = cols + (cols >= rows).to(torch.long)
    network[rows.expand_as(dest).reshape(-1), dest.reshape(-1)] = coef.reshape(-1)
    return network


def _finish_network_gpu(network: "torch.Tensor", scale_scores: bool, symmetric: bool, q: float) -> "torch.Tensor":
    """Scale and type 7 on the device. Diagonal is already empty, then written again."""
    import torch

    if symmetric:
        network = (network + network.T) / 2
    if scale_scores:
        max_abs = torch.amax(torch.abs(network))
        scale = torch.where(
            torch.isfinite(max_abs) & (max_abs > 0),
            max_abs,
            torch.ones((), dtype=network.dtype, device=network.device),
        )
        network = network / scale
    if 0 < q < 1:
        from knk_accel.secular import _type7_threshold

        threshold = _type7_threshold(torch.abs(network), q)
        network = torch.where(
            torch.abs(network) < threshold,
            torch.zeros((), dtype=network.dtype, device=network.device),
            network,
        )
    network.fill_diagonal_(0.0)
    return network


class HostBuffer:
    """Pinned host memory filled by a copy stream. numpy() waits for that copy."""

    def __init__(self, host: "torch.Tensor", event: "torch.cuda.Event", source: "torch.Tensor"):
        self._host = host
        self._event = event
        self._source = source

    def numpy(self) -> np.ndarray:
        self._event.synchronize()
        array = self._host.numpy()
        self._source = None
        return array


def enqueue_host(tensor: "torch.Tensor") -> HostBuffer:
    """Queue a device-to-host copy on its own stream and return before it finishes."""
    import torch

    host = torch.empty(tensor.shape, dtype=tensor.dtype, pin_memory=True)
    copy_stream = torch.cuda.Stream()
    copy_stream.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(copy_stream):
        host.copy_(tensor, non_blocking=True)
        event = torch.cuda.Event()
        event.record(copy_stream)
    return HostBuffer(host, event, tensor)


def _coefficients_on_device(x: "torch.Tensor", n_comp: int, on_gene=None, only_genes: list[int] | None = None) -> "torch.Tensor":
    """Small designs use one Jacobi kernel. Larger designs keep per-gene gesvd."""
    import torch

    from knk_accel.pcnet_merge import fused_coefficients, plan_pcnet_merge

    n_samples, n_genes = x.shape
    plan = plan_pcnet_merge(int(n_samples), int(n_genes), n_comp, "gpu", "auto")
    if only_genes is None and plan["strategy"] == "fused":
        coef = fused_coefficients(x, n_comp)
        if on_gene is not None:
            torch.cuda.current_stream().synchronize()
            on_gene(int(n_genes), int(n_genes))
        return coef
    return _gpu_coefficient_tensor(x, n_comp, on_gene, only_genes)


def _gpu_coefficient_tensor(
    x: "torch.Tensor",
    n_comp: int,
    on_gene=None,
    only_genes: list[int] | None = None,
) -> "torch.Tensor":
    """Leave-one-out gesvd. Coefficients stay on x.device until the caller copies them."""
    import torch

    _n_cells, n_genes = x.shape
    chosen = list(range(n_genes) if only_genes is None else only_genes)
    coef = torch.empty((len(chosen), n_genes - 1), dtype=torch.float64, device=x.device)
    status_path = os.environ.get("KNK_GENE_STATUS")
    status = open(status_path, "a", encoding="utf-8", buffering=1) if status_path else None
    for row_index, gene in enumerate(chosen):
        if status is not None and (row_index % 100 == 0):
            status.write(f"{row_index}\n")
        keep = [column for column in range(n_genes) if column != gene]
        design = x[:, keep]
        target = x[:, gene]
        _u, _s, vh = torch.linalg.svd(design, full_matrices=False, driver=GPU_SVD_DRIVER)
        components = vh[:n_comp].T
        scores = design @ components
        norms = torch.sum(scores * scores, dim=0)
        norms = torch.where(norms == 0, torch.ones_like(norms), norms)
        scores = scores / norms
        pc_coef = scores.T @ target
        coef[row_index] = components @ pc_coef
        del design, _u, _s, vh, components, scores
        done = row_index + 1
        if on_gene is not None and (done == len(chosen) or done % 100 == 0):
            torch.cuda.current_stream().synchronize()
            on_gene(done, len(chosen))
    if status is not None:
        status.close()
    return coef


def _gpu_coefficients(x_std: np.ndarray, n_comp: int, on_gene=None, only_genes: list[int] | None = None) -> np.ndarray:
    """Direct truncated SVD of each leave-one-out design, in float64, one gene at a time.

    cuSOLVER driver is gesvd (QR), not the PyTorch CUDA default gesvdj (Jacobi).
    On the cLTMR leave-one-out designs, Jacobi sat about 6e-16 from the CPU
    coefficients; gesvd sat about 1e-16, the same rounding band as CPU versus R.
    The coefficient formula is unchanged. The rows are copied once, after the loop.
    """
    import torch

    torch.set_num_threads(1)
    device = torch.device("cuda")
    x = torch.as_tensor(np.ascontiguousarray(x_std), device=device, dtype=torch.float64)
    stream = torch.cuda.Stream()
    with torch.cuda.stream(stream):
        coef = _coefficients_on_device(x, n_comp, on_gene, only_genes)
    stream.synchronize()
    return coef.detach().cpu().numpy()


def _gpu_network(counts_genes_by_cells: np.ndarray, n_comp: int, q: float, on_gene=None, async_copy: bool = False):
    """1.4 formula on one GPU stream. async_copy queues the host copy and returns before it finishes."""
    import torch

    torch.set_num_threads(1)
    device = torch.device("cuda")
    from knk_accel.pcnet_merge import fused_small_network, plan_pcnet_merge

    n_genes, n_cells = np.asarray(counts_genes_by_cells).shape
    small = plan_pcnet_merge(int(n_cells), int(n_genes), n_comp, "gpu", "auto")["strategy"] == "fused"
    stream = torch.cuda.Stream()
    with torch.cuda.stream(stream):
        if small:
            network = fused_small_network(counts_genes_by_cells, n_comp, q)
            if on_gene is not None:
                stream.synchronize()
                on_gene(int(n_genes), int(n_genes))
        else:
            x = _standardize_gpu(counts_genes_by_cells, device)
            coef = _coefficients_on_device(x, n_comp, on_gene, None)
            network = _finish_network_gpu(_place_coefficients(coef), True, False, q)
        pending = enqueue_host(network) if async_copy else None
    if pending is not None:
        return pending
    stream.synchronize()
    array = network.detach().cpu().numpy()
    del network
    if not small:
        del x, coef
    torch.cuda.empty_cache()
    return array


def _gene_chunks(n_genes: int, n_workers: int) -> list[list[int]]:
    n_workers = max(1, min(n_workers, n_genes))
    bounds = [round(i * n_genes / n_workers) for i in range(n_workers + 1)]
    return [list(range(bounds[i], bounds[i + 1])) for i in range(n_workers) if bounds[i] < bounds[i + 1]]


def truncated_coefficients(
    x_std: np.ndarray,
    n_comp: int = 3,
    on_gene=None,
    n_workers: int = 1,
    device: str = "auto",
    only_genes: list[int] | None = None,
) -> np.ndarray:
    """Samples-by-genes standardized matrix to a (genes, genes-1) coefficient matrix.

    n_workers is the number of CPU processes. Each process keeps one BLAS thread.
    The default stays at 1 so a test cannot fan out onto the Formal job.
    device="gpu" runs the direct truncated SVD in this process and refuses
    extra CPU processes, so a child cannot also open CUDA. device="auto"
    stays on CPU.
    """
    n_samples, n_genes = x_std.shape
    if n_comp < 2 or n_comp >= n_genes:
        raise ValueError("n_comp must be >= 2 and < n_genes")
    if n_workers < 1:
        raise ValueError("n_workers must be >= 1")
    if n_samples <= n_comp:
        device = "cpu"
    if use_gpu_for(n_samples, n_genes, device):
        if n_workers != 1:
            raise ValueError("device gpu keeps one process; n_workers must be 1")
        return _gpu_coefficients(x_std, n_comp, on_gene, only_genes)
    chosen = list(range(n_genes) if only_genes is None else only_genes)
    if only_genes is not None or n_workers == 1 or n_genes < 8:
        coef = np.empty((len(chosen), n_genes - 1), dtype=np.float64)
        for row_index, gene_index in enumerate(chosen):
            coef[row_index] = _coefficient_rows(x_std, [gene_index], n_comp)[1][0]
            if on_gene is not None:
                on_gene(row_index + 1, len(chosen))
        return coef
    chunks = _gene_chunks(n_genes, n_workers)
    coef = np.empty((n_genes, n_genes - 1), dtype=np.float64)
    done = 0
    with ProcessPoolExecutor(max_workers=len(chunks)) as pool:
        futures = [pool.submit(_coefficient_rows, x_std, chunk, n_comp) for chunk in chunks]
        for future in futures:
            indices, rows = future.result()
            for row_index, gene_index in enumerate(indices):
                coef[gene_index] = rows[row_index]
            done += len(indices)
            if on_gene is not None:
                on_gene(done, n_genes)
    return coef


def assemble_network(coef: np.ndarray, scale_scores: bool = True, symmetric: bool = False, q: float = 0.95) -> np.ndarray:
    n_genes = coef.shape[0]
    network = np.zeros((n_genes, n_genes), dtype=np.float64)
    for gene_index in range(n_genes):
        network[gene_index, np.arange(n_genes) != gene_index] = coef[gene_index]
    if symmetric:
        network = (network + network.T) / 2.0
    if scale_scores:
        max_abs = np.max(np.abs(network))
        if np.isfinite(max_abs) and max_abs > 0:
            network = network / max_abs
    if 0 < q < 1:
        threshold = r_quantile(np.abs(network), q)
        network[np.abs(network) < threshold] = 0.0
    np.fill_diagonal(network, 0.0)
    return network


def pcnet_truncated(
    counts_genes_by_cells: np.ndarray,
    n_comp: int = 3,
    q: float = 0.95,
    on_gene=None,
    n_workers: int = 1,
    device: str = "auto",
    async_copy: bool = False,
):
    """1.4 leave-one-out network. device gpu keeps scale, SVD, and type 7 on CUDA.

    Designs up to 40 by 40 use one Jacobi kernel. Larger designs keep per-gene gesvd.
    async_copy on that GPU path returns a HostBuffer; the copy finishes in numpy().
    device auto stays on CPU. Fewer cells than n_comp stays on CPU.
    """
    counts = np.asarray(counts_genes_by_cells)
    if np.any(counts.sum(axis=1) <= 0):
        raise ValueError("zero gene row sums; drop those genes first")
    n_genes, n_cells = counts.shape
    if use_gpu_for(n_cells, n_genes, device):
        if n_workers != 1:
            raise ValueError("device gpu keeps one process; n_workers must be 1")
        if n_cells > n_comp:
            dense = _gpu_network(counts, n_comp=n_comp, q=q, on_gene=on_gene, async_copy=async_copy)
            if async_copy:
                return dense
            return sparse.csr_matrix(dense)
    x_std = standardize_cells_by_genes(counts)
    coef = truncated_coefficients(
        x_std, n_comp=n_comp, on_gene=on_gene, n_workers=n_workers, device="cpu" if n_cells <= n_comp else device
    )
    dense = assemble_network(coef, q=q)
    return sparse.csr_matrix(dense)
