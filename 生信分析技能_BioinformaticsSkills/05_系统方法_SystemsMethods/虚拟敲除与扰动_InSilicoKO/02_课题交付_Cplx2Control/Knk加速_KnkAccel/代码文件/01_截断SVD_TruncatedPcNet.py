"""Leave-one-out PC regression matching scTenifoldNet 1.4 pcNetCoreRcpp.

The installed C++ loop calls arma::svd_econ on every leave-one-out
design matrix, then keeps only nComp right singular vectors. This module
computes the same coefficients with a rank-nComp SVD. It does not replace
the running Formal job. Matrices with more than MAX_GENES columns are refused
unless allow_large=True, so a full 8000-gene network is not started by accident.
"""

from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np
from scipy.linalg import svd
from scipy.sparse.linalg import svds

MAX_GENES = 200


def _coefficients_from_components(design: np.ndarray, target: np.ndarray, components: np.ndarray) -> np.ndarray:
    """Same algebra as pcNetCore.cpp after the SVD is truncated to nComp."""
    pc_scores = design @ components
    score_sq_norms = np.sum(pc_scores * pc_scores, axis=0)
    pc_scores_normalized = pc_scores / score_sq_norms
    pc_coefficients = pc_scores_normalized.T @ target
    return components @ pc_coefficients


def pc_net_core(x_std: np.ndarray, n_comp: int = 3, method: str = "truncated") -> np.ndarray:
    """Return the (n_genes, n_genes-1) coefficient matrix.

    x_std is samples by genes, already centered and scaled by column.
    method='full' uses a complete economy SVD and then keeps n_comp.
    method='truncated' computes only those n_comp components.
    """
    if x_std.ndim != 2:
        raise ValueError("x_std must be a 2-d samples-by-genes matrix")
    n_samples, n_genes = x_std.shape
    if n_comp < 2 or n_comp >= n_genes:
        raise ValueError("n_comp must be >= 2 and < n_genes")
    if n_genes > MAX_GENES:
        raise ValueError(
            f"refusing {n_genes} genes (limit {MAX_GENES}); "
            "this helper is for alignment, not the live Formal network"
        )
    if method not in {"full", "truncated"}:
        raise ValueError("method must be 'full' or 'truncated'")

    coefficients = np.empty((n_genes, n_genes - 1), dtype=np.float64)
    for gene_index in range(n_genes):
        target = x_std[:, gene_index]
        design = np.delete(x_std, gene_index, axis=1)
        if method == "full":
            _u, _s, vt = svd(design, full_matrices=False, lapack_driver="gesdd")
            components = vt[:n_comp].T
        else:
            # svds returns smallest-to-largest; reverse to match svd_econ order.
            _u, _s, vt = svds(design, k=n_comp, which="LM", return_singular_vectors="vh")
            components = vt[::-1].T
        coefficients[gene_index] = _coefficients_from_components(design, target, components)
    return coefficients


def max_abs_diff(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.max(np.abs(left - right)))
