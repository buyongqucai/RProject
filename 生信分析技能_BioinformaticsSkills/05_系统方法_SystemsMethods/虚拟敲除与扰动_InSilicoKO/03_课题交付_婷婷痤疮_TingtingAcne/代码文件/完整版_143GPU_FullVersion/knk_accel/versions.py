"""Two pcNet formulas. CUDA is optional and does not change which formula runs.

1.4 is the installed Rcpp path: one truncated SVD per gene, float64.
1.4.3 is the GitHub path: one Gram eigenproblem, then the secular equation.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse

from knk_accel.pcnet import cuda_available, pcnet_truncated
from knk_accel.secular import pcnet_secular


def choose_device(version: str, n_genes: int, n_cells: int, device: str) -> str:
    """Resolve auto from the 2026-10-02 size ladder. cpu and gpu stay explicit.

    1.4 GPU was slower than CPU from 24 by 18 through 320 by 150, so auto
    stays on CPU. 1.4.3 GPU was faster at every one of those sizes.
    """
    if device in ("cpu", "gpu"):
        return device
    if device != "auto":
        raise ValueError("device must be cpu, gpu, or auto")
    del n_genes, n_cells
    if version == "143" and cuda_available():
        return "gpu"
    return "cpu"


def pcnet_14(
    counts_genes_by_cells: np.ndarray,
    n_comp: int = 3,
    q: float = 0.9,
    device: str = "auto",
) -> sparse.csr_matrix:
    """Version 1.4 formula. auto uses CPU. device gpu still runs CUDA."""
    counts = np.asarray(counts_genes_by_cells)
    chosen = choose_device("14", int(counts.shape[0]), int(counts.shape[1]), device)
    return pcnet_truncated(
        counts, n_comp=n_comp, q=q, n_workers=1, device=chosen
    )


def pcnet_143(
    counts_genes_by_cells: np.ndarray,
    n_comp: int = 3,
    q: float = 0.9,
    device: str = "auto",
) -> np.ndarray:
    """Version 1.4.3 formula. auto uses CUDA when it is present."""
    counts = np.asarray(counts_genes_by_cells)
    chosen = choose_device("143", int(counts.shape[0]), int(counts.shape[1]), device)
    return pcnet_secular(counts, n_comp=n_comp, q=q, device=chosen)
