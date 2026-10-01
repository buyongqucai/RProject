"""Truncated leave-one-out PC regression and the sparse network around it.

Matches scTenifoldNet pcNet: column-scale the cells-by-genes matrix, keep
n_comp right singular vectors, scale by the max absolute weight, then drop
edges below quantile q. Does not call the live Formal job.
"""

from __future__ import annotations

import os

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
    """stats::quantile type 7, the R default."""
    x = np.sort(np.asarray(values, dtype=np.float64).ravel())
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
        return float(x[lo - 1])
    weight = index - lo
    return float(x[lo - 1] + weight * (x[hi - 1] - x[lo - 1]))


def _components(design: np.ndarray, n_comp: int) -> np.ndarray:
    if min(design.shape) <= n_comp:
        _u, _s, vt = svd(design, full_matrices=False, lapack_driver="gesdd")
        return vt[:n_comp].T
    _u, _s, vt = svds(design, k=n_comp, which="LM", return_singular_vectors="vh")
    return vt[::-1].T


def _coefficients_from_components(design: np.ndarray, target: np.ndarray, components: np.ndarray) -> np.ndarray:
    scores = design @ components
    norms = np.sum(scores * scores, axis=0)
    norms[norms == 0] = 1.0
    scores = scores / norms
    pc_coef = scores.T @ target
    return components @ pc_coef


def truncated_coefficients(x_std: np.ndarray, n_comp: int = 3, on_gene=None) -> np.ndarray:
    """Samples-by-genes standardized matrix to a (genes, genes-1) coefficient matrix."""
    n_samples, n_genes = x_std.shape
    if n_comp < 2 or n_comp >= n_genes:
        raise ValueError("n_comp must be >= 2 and < n_genes")
    coef = np.empty((n_genes, n_genes - 1), dtype=np.float64)
    for gene_index in range(n_genes):
        target = x_std[:, gene_index]
        design = np.delete(x_std, gene_index, axis=1)
        coef[gene_index] = _coefficients_from_components(design, target, _components(design, n_comp))
        if on_gene is not None:
            on_gene(gene_index + 1, n_genes)
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


def pcnet_truncated(counts_genes_by_cells: np.ndarray, n_comp: int = 3, q: float = 0.95, on_gene=None) -> sparse.csr_matrix:
    if np.any(np.asarray(counts_genes_by_cells).sum(axis=1) <= 0):
        raise ValueError("zero gene row sums; drop those genes first")
    x_std = standardize_cells_by_genes(counts_genes_by_cells)
    coef = truncated_coefficients(x_std, n_comp=n_comp, on_gene=on_gene)
    dense = assemble_network(coef, q=q)
    return sparse.csr_matrix(dense)
