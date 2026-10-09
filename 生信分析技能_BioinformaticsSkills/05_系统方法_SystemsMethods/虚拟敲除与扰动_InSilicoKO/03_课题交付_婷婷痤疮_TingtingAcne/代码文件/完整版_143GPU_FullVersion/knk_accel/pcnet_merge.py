"""One double-precision CUDA kernel for a small 1.4 network.

Each thread is one gene. It runs the same one-sided Jacobi rotation as a
full gesvd of that gene's leave-one-out design, keeps n_comp right vectors,
and applies the existing coefficient formula. Larger designs stay on the
per-gene cuSOLVER gesvd path.
"""

from __future__ import annotations

import ctypes

import torch

SMALL_MAX_SAMPLES = 40
SMALL_MAX_GENES = 40

_KERNEL = r"""
__device__ void knk_standardize_gene(const double* counts, double* xstd, int n_samples, int n_genes, int gene) {
    double mean = 0.0;
    for (int i = 0; i < n_samples; ++i) mean += counts[(size_t)gene * n_samples + i];
    mean /= (double)n_samples;
    double acc = 0.0;
    int denom = n_samples > 1 ? n_samples - 1 : 1;
    for (int i = 0; i < n_samples; ++i) {
        double diff = counts[(size_t)gene * n_samples + i] - mean;
        acc += diff * diff;
    }
    double sd = sqrt(acc / (double)denom);
    if (sd == 0.0) sd = 1.0;
    for (int i = 0; i < n_samples; ++i) {
        double diff = counts[(size_t)gene * n_samples + i] - mean;
        xstd[(size_t)i * n_genes + gene] = diff / sd;
    }
}

__device__ void knk_gene_coefficients(const double* x, int m, int n_genes, int gene, int n_comp, double* coef) {
    const int n = n_genes - 1;
    double A[40 * 39];
    double V[39 * 39];
    double y[40];
    for (int row = 0; row < m; ++row) {
        y[row] = x[(size_t)row * n_genes + gene];
        for (int col = 0; col < n; ++col) {
            int src = col < gene ? col : col + 1;
            A[row + col * m] = x[(size_t)row * n_genes + src];
        }
    }
    for (int col = 0; col < n; ++col) {
        for (int row = 0; row < n; ++row) V[row + col * n] = row == col ? 1.0 : 0.0;
    }
    for (int sweep = 0; sweep < 40; ++sweep) {
        double off = 0.0;
        for (int a = 0; a < n - 1; ++a) {
            for (int b = a + 1; b < n; ++b) {
                double app = 0.0, aqq = 0.0, apq = 0.0;
                for (int i = 0; i < m; ++i) {
                    double pa = A[i + a * m];
                    double pb = A[i + b * m];
                    app += pa * pa;
                    aqq += pb * pb;
                    apq += pa * pb;
                }
                double scale = sqrt(app) * sqrt(aqq);
                if (fabs(apq) > off) off = fabs(apq);
                if (!(scale > 0.0) || fabs(apq) <= 1e-15 * scale) continue;
                double tau = (aqq - app) / (2.0 * apq);
                double t = copysign(1.0, tau) / (fabs(tau) + sqrt(1.0 + tau * tau));
                double c = 1.0 / sqrt(1.0 + t * t);
                double s = t * c;
                for (int i = 0; i < m; ++i) {
                    double pa = A[i + a * m];
                    double pb = A[i + b * m];
                    A[i + a * m] = c * pa - s * pb;
                    A[i + b * m] = s * pa + c * pb;
                }
                for (int i = 0; i < n; ++i) {
                    double va = V[i + a * n];
                    double vb = V[i + b * n];
                    V[i + a * n] = c * va - s * vb;
                    V[i + b * n] = s * va + c * vb;
                }
            }
        }
        if (off <= 1e-12) break;
    }
    double norms[39];
    for (int col = 0; col < n; ++col) {
        double acc = 0.0;
        for (int i = 0; i < m; ++i) {
            double value = A[i + col * m];
            acc += value * value;
        }
        norms[col] = acc;
    }
    int used[39];
    for (int col = 0; col < n; ++col) used[col] = 0;
    int order[8];
    for (int k = 0; k < n_comp; ++k) {
        int best = -1;
        for (int col = 0; col < n; ++col) {
            if (used[col]) continue;
            if (best < 0 || norms[col] > norms[best]) best = col;
        }
        used[best] = 1;
        order[k] = best;
    }
    double pc[8];
    for (int k = 0; k < n_comp; ++k) {
        int col = order[k];
        double norm = norms[col];
        if (norm == 0.0) norm = 1.0;
        double dot = 0.0;
        for (int i = 0; i < m; ++i) dot += A[i + col * m] * y[i];
        pc[k] = dot / norm;
    }
    for (int j = 0; j < n; ++j) {
        double acc = 0.0;
        for (int k = 0; k < n_comp; ++k) acc += V[j + order[k] * n] * pc[k];
        coef[(size_t)gene * n + j] = acc;
    }
}

__device__ void knk_shell_sort(double* values, int n) {
    for (int gap = n / 2; gap > 0; gap /= 2) {
        for (int i = gap; i < n; ++i) {
            double temp = values[i];
            int j = i;
            while (j >= gap && values[j - gap] > temp) {
                values[j] = values[j - gap];
                j -= gap;
            }
            values[j] = temp;
        }
    }
}

__device__ void knk_finish_network(const double* coef, double* network, int n_genes, double q) {
    int n = n_genes - 1;
    int cells = n_genes * n_genes;
    for (int i = 0; i < cells; ++i) network[i] = 0.0;
    for (int gene = 0; gene < n_genes; ++gene) {
        for (int col = 0; col < n; ++col) {
            int dest = col < gene ? col : col + 1;
            network[(size_t)gene * n_genes + dest] = coef[(size_t)gene * n + col];
        }
    }
    double max_abs = 0.0;
    int finite = 1;
    for (int i = 0; i < cells; ++i) {
        double value = fabs(network[i]);
        if (!(value == value) || value > 1e300) finite = 0;
        if (value > max_abs) max_abs = value;
    }
    if (finite && max_abs > 0.0) {
        for (int i = 0; i < cells; ++i) network[i] /= max_abs;
    }
    if (q > 0.0 && q < 1.0) {
        double ordered[1600];
        for (int i = 0; i < cells; ++i) ordered[i] = fabs(network[i]);
        knk_shell_sort(ordered, cells);
        double index = 1.0 + (double)(cells - 1) * q;
        int lo = (int)floor(index);
        int hi = (int)ceil(index);
        if (lo < 1) lo = 1;
        if (hi < 1) hi = 1;
        if (lo > cells) lo = cells;
        if (hi > cells) hi = cells;
        double left = ordered[lo - 1];
        double right = ordered[hi - 1];
        double threshold = left + (index - (double)lo) * (right - left);
        for (int i = 0; i < cells; ++i) {
            if (fabs(network[i]) < threshold) network[i] = 0.0;
        }
    }
    for (int gene = 0; gene < n_genes; ++gene) network[(size_t)gene * n_genes + gene] = 0.0;
}

extern "C" __global__ void pcnet_small(
    const double* __restrict__ x,
    double* __restrict__ coef,
    int n_samples,
    int n_genes,
    int n_comp)
{
    int gene = blockIdx.x * blockDim.x + threadIdx.x;
    if (gene >= n_genes) return;
    knk_gene_coefficients(x, n_samples, n_genes, gene, n_comp, coef);
}

extern "C" __global__ void pcnet_small_network(
    const double* __restrict__ counts,
    double* __restrict__ xstd,
    double* __restrict__ coef,
    double* __restrict__ network,
    int n_samples,
    int n_genes,
    int n_comp,
    double q)
{
    int gene = threadIdx.x;
    if (gene < n_genes) knk_standardize_gene(counts, xstd, n_samples, n_genes, gene);
    __syncthreads();
    if (gene < n_genes) knk_gene_coefficients(xstd, n_samples, n_genes, gene, n_comp, coef);
    __syncthreads();
    if (gene == 0) knk_finish_network(coef, network, n_genes, q);
}
"""


def plan_pcnet_merge(n_samples: int, n_genes: int, n_comp: int, device: str, merge: str = "auto") -> dict:
    """Use one kernel only when every leave-one-out design fits the small kernel.

    auto on GPU does not fall back to CPU. A large design stays on per-gene gesvd.
    """
    if merge not in ("auto", "loop", "fused"):
        raise ValueError("merge must be auto, loop, or fused")
    small = (
        int(n_samples) <= SMALL_MAX_SAMPLES
        and int(n_genes) <= SMALL_MAX_GENES
        and int(n_samples) > int(n_comp)
        and int(n_genes) > int(n_comp)
        and int(n_comp) <= 8
    )
    pairs = max(int(n_genes) - 1, 0)
    work = int(n_samples) * int(n_genes) * pairs * max(pairs - 1, 0) // 2
    if merge == "fused" and device != "gpu":
        raise RuntimeError("fused 1.4 is a CUDA kernel; device must be gpu")
    if merge == "fused" and not small:
        raise RuntimeError("fused 1.4 kernel only fits designs up to 40 by 40")
    strategy = "fused" if device == "gpu" and small and merge != "loop" else "loop"
    return {"work": work, "strategy": strategy, "device": device, "small": small}


def _load_function(entry: bytes = b"pcnet_small"):
    from knk_accel.cuda_cache import load_kernel

    return load_kernel("pcnet_small", _KERNEL, entry)


def fused_coefficients(x: torch.Tensor, n_comp: int) -> torch.Tensor:
    """Leave-one-out coefficients for a small cells-by-genes matrix. One kernel."""
    if not x.is_cuda:
        raise RuntimeError("fused 1.4 coefficients require a CUDA tensor")
    x = x.contiguous()
    n_samples, n_genes = x.shape
    plan = plan_pcnet_merge(n_samples, n_genes, n_comp, "gpu", "fused")
    if plan["strategy"] != "fused":
        raise RuntimeError("matrix is outside the small 1.4 kernel")
    coef = torch.empty((n_genes, n_genes - 1), dtype=torch.float64, device=x.device)
    nvcuda, function = _load_function()
    block = 32
    grid = (n_genes + block - 1) // block
    x_ptr = ctypes.c_void_p(x.data_ptr())
    coef_ptr = ctypes.c_void_p(coef.data_ptr())
    n_samples_c = ctypes.c_int(n_samples)
    n_genes_c = ctypes.c_int(n_genes)
    n_comp_c = ctypes.c_int(n_comp)
    args = (ctypes.c_void_p * 5)(
        ctypes.addressof(x_ptr),
        ctypes.addressof(coef_ptr),
        ctypes.addressof(n_samples_c),
        ctypes.addressof(n_genes_c),
        ctypes.addressof(n_comp_c),
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
    return coef


def fused_small_network(counts_genes_by_cells: np.ndarray, n_comp: int, q: float) -> torch.Tensor:
    """Standardize, Jacobi, scale, and type 7 in one launch. Counts are genes by cells."""
    import numpy as np

    counts = np.ascontiguousarray(np.asarray(counts_genes_by_cells, dtype=np.float64))
    n_genes, n_samples = counts.shape
    plan = plan_pcnet_merge(n_samples, n_genes, n_comp, "gpu", "fused")
    if plan["strategy"] != "fused":
        raise RuntimeError("matrix is outside the small 1.4 kernel")
    raw = torch.as_tensor(counts, device="cuda", dtype=torch.float64)
    xstd = torch.empty((n_samples, n_genes), dtype=torch.float64, device="cuda")
    coef = torch.empty((n_genes, n_genes - 1), dtype=torch.float64, device="cuda")
    network = torch.empty((n_genes, n_genes), dtype=torch.float64, device="cuda")
    nvcuda, function = _load_function(b"pcnet_small_network")
    raw_ptr = ctypes.c_void_p(raw.data_ptr())
    xstd_ptr = ctypes.c_void_p(xstd.data_ptr())
    coef_ptr = ctypes.c_void_p(coef.data_ptr())
    network_ptr = ctypes.c_void_p(network.data_ptr())
    n_samples_c = ctypes.c_int(n_samples)
    n_genes_c = ctypes.c_int(n_genes)
    n_comp_c = ctypes.c_int(n_comp)
    q_c = ctypes.c_double(q)
    args = (ctypes.c_void_p * 8)(
        ctypes.addressof(raw_ptr),
        ctypes.addressof(xstd_ptr),
        ctypes.addressof(coef_ptr),
        ctypes.addressof(network_ptr),
        ctypes.addressof(n_samples_c),
        ctypes.addressof(n_genes_c),
        ctypes.addressof(n_comp_c),
        ctypes.addressof(q_c),
    )
    stream = ctypes.c_void_p(torch.cuda.current_stream().cuda_stream)
    status = nvcuda.cuLaunchKernel(function, 1, 1, 1, 64, 1, 1, 0, stream, args, None)
    if status != 0:
        raise RuntimeError(f"cuLaunchKernel failed: {status}")
    return network
