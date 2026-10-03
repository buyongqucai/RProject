"""One double-precision CUDA kernel for the secular iteration.

The host compiler is not required. NVRTC compiles the device code, and the
launch goes on the current PyTorch stream. The algebra is the same loop as
`_secular_weights`: up to 300 iterations, the same bracket, and the same
quadratic step.
"""

from __future__ import annotations

import ctypes

import torch

# Upper bound on eigenvalue updates. On this 4080 SUPER the fused kernel was
# faster at 40x30, 800x200, and 8000x425, so a GPU request with auto merges
# at every size. The estimate is still returned by plan_secular_merge.
FUSED_MIN_WORK = 0

_KERNEL = r"""
extern "C" __global__ void secular_fused(
    const double* __restrict__ z,
    const double* __restrict__ d,
    double* __restrict__ weights,
    int n_eig,
    int n_genes,
    int n_comp,
    double eps)
{
    int gene = blockIdx.x * blockDim.x + threadIdx.x;
    if (gene >= n_genes) return;
    for (int j = 0; j < n_eig; ++j) weights[(size_t)j * n_genes + gene] = 0.0;

    for (int index = 0; index < n_comp; ++index) {
        double d_upper = d[index];
        double d_lower = d[index + 1];
        double gap = d_upper - d_lower;
        if (!(gap > 0.0)) continue;

        double midpoint = d_lower + gap * 0.5;
        double sum_mid = 0.0;
        for (int j = 0; j < n_eig; ++j) {
            double zj = z[(size_t)j * n_genes + gene];
            sum_mid += (zj * zj) / (d[j] - midpoint);
        }
        bool near_upper = (1.0 - sum_mid) >= 0.0;
        double origin = near_upper ? d_upper : d_lower;
        double pole_lower = near_upper ? -gap : 0.0;
        double pole_upper = near_upper ? 0.0 : gap;
        double lo = near_upper ? -gap * 0.5 : 0.0;
        double hi = near_upper ? 0.0 : gap * 0.5;
        double tau = (lo + hi) * 0.5;

        for (int iter = 0; iter < 300; ++iter) {
            double sum_above = 0.0, slope_above = 0.0, sum_below = 0.0, slope_below = 0.0;
            for (int j = 0; j < n_eig; ++j) {
                double zj = z[(size_t)j * n_genes + gene];
                double zj2 = zj * zj;
                double gapj = (d[j] - origin) - tau;
                double term = zj2 / gapj;
                double slope = term / gapj;
                if (j <= index) {
                    sum_above += term;
                    slope_above += slope;
                } else {
                    sum_below += term;
                    slope_below += slope;
                }
            }
            double residual = 1.0 - sum_above - sum_below;
            if (residual > 0.0) lo = tau;
            if (residual < 0.0) hi = tau;
            double to_lower = pole_lower - tau;
            double to_upper = pole_upper - tau;
            double quad_a = residual + slope_below * to_lower + slope_above * to_upper;
            double quad_b = quad_a * (to_lower + to_upper)
                - slope_below * to_lower * to_lower
                - slope_above * to_upper * to_upper;
            double quad_c = residual * to_lower * to_upper;
            double disc = quad_b * quad_b - 4.0 * quad_a * quad_c;
            if (disc < 0.0) disc = 0.0;
            double sqrt_disc = sqrt(disc);
            double half = (quad_b + ((quad_b >= 0.0) ? sqrt_disc : -sqrt_disc)) * 0.5;
            double root_1 = half / quad_a;
            double root_2 = quad_c / half;
            bool use_first = (!isnan(root_1)) && (root_1 > to_lower) && (root_1 < to_upper);
            double step = use_first ? root_1 : root_2;
            double tau_new = tau + step;
            bool outside = isnan(tau_new) || (tau_new <= lo) || (tau_new >= hi);
            if (outside) tau_new = (lo + hi) * 0.5;
            bool exact = residual == 0.0;
            if (exact) tau_new = tau;
            double abs_lo = fabs(lo);
            double abs_hi = fabs(hi);
            double abs_edge = abs_lo > abs_hi ? abs_lo : abs_hi;
            bool converged = exact
                || (fabs(tau_new - tau) <= 4.0 * eps * fabs(tau_new))
                || ((hi - lo) <= 4.0 * eps * abs_edge);
            tau = tau_new;
            if (converged) break;
        }

        double mu = origin + tau;
        double sum_dir2 = 0.0;
        for (int j = 0; j < n_eig; ++j) {
            double dir = z[(size_t)j * n_genes + gene] / ((d[j] - origin) - tau);
            sum_dir2 += dir * dir;
        }
        double scale = 1.0 / (mu * sum_dir2);
        for (int j = 0; j < n_eig; ++j) {
            double dir = z[(size_t)j * n_genes + gene] / ((d[j] - origin) - tau);
            weights[(size_t)j * n_genes + gene] += dir * scale;
        }
    }
}
"""


def estimate_secular_work(n_eig: int, n_genes: int, n_comp: int) -> int:
    """Upper bound on eigenvalue updates inside the secular loop."""
    return int(n_eig) * int(n_genes) * int(n_comp) * 300


def plan_secular_merge(n_eig: int, n_genes: int, n_comp: int, device: str, merge: str = "auto") -> dict:
    """Choose loop or fused from the work estimate.

    device is the caller's device. auto never moves a gpu request onto the CPU.
    """
    work = estimate_secular_work(n_eig, n_genes, n_comp)
    if merge not in ("auto", "loop", "fused"):
        raise ValueError("merge must be auto, loop, or fused")
    if merge == "fused" and device != "gpu":
        raise RuntimeError("fused secular is a CUDA kernel; device must be gpu")
    if merge == "loop":
        strategy = "loop"
    elif merge == "fused":
        strategy = "fused"
    elif device == "gpu" and work >= FUSED_MIN_WORK:
        strategy = "fused"
    else:
        strategy = "loop"
    return {"work": work, "strategy": strategy, "device": device}


def _load_function():
    from knk_accel.cuda_cache import load_kernel

    return load_kernel("secular_fused", _KERNEL, b"secular_fused")


def fused_secular_weights(z: torch.Tensor, d: torch.Tensor, n_comp: int) -> torch.Tensor:
    """Column k is the weight vector of gene k. z is eigenvalues by genes."""
    if not z.is_cuda:
        raise RuntimeError("fused secular weights require a CUDA tensor")
    z = z.contiguous()
    d = d.contiguous()
    n_eig, n_genes = z.shape
    weights = torch.empty((n_eig, n_genes), dtype=torch.float64, device=z.device)
    nvcuda, function = _load_function()
    block = 128
    grid = (n_genes + block - 1) // block
    eps = ctypes.c_double(torch.finfo(torch.float64).eps)
    z_ptr = ctypes.c_void_p(z.data_ptr())
    d_ptr = ctypes.c_void_p(d.data_ptr())
    w_ptr = ctypes.c_void_p(weights.data_ptr())
    n_eig_c = ctypes.c_int(n_eig)
    n_genes_c = ctypes.c_int(n_genes)
    n_comp_c = ctypes.c_int(n_comp)
    args = (ctypes.c_void_p * 7)(
        ctypes.addressof(z_ptr),
        ctypes.addressof(d_ptr),
        ctypes.addressof(w_ptr),
        ctypes.addressof(n_eig_c),
        ctypes.addressof(n_genes_c),
        ctypes.addressof(n_comp_c),
        ctypes.addressof(eps),
    )
    stream = ctypes.c_void_p(torch.cuda.current_stream().cuda_stream)
    status = nvcuda.cuLaunchKernel(
        function,
        grid,
        1,
        1,
        block,
        1,
        1,
        0,
        stream,
        args,
        None,
    )
    if status != 0:
        raise RuntimeError(f"cuLaunchKernel failed: {status}")
    return weights
