"""Three-mode CP-ALS with a checkpoint after each finished iteration.

The updates follow scTenifoldNet:::cpDecomposition for num_modes == 3:
each iteration refreshes all three factor matrices, then the residual.
A checkpoint is written only after that iteration finishes, on the calling
thread. The next iteration does not share those arrays with the file writer.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")


def _digest(tensor: np.ndarray) -> str:
    raw = np.ascontiguousarray(tensor, dtype=np.float64).tobytes()
    return hashlib.sha256(raw).hexdigest()


def _atomic_npz(path: Path, **arrays) -> None:
    tmp = path.with_name(path.name + ".partial")
    with open(tmp, "wb") as handle:
        np.savez(handle, **arrays)
    os.replace(tmp, path)


def _update_numpy(slices: list[np.ndarray], u1: np.ndarray, u2: np.ndarray, u3: np.ndarray):
    n_i, n_j = slices[0].shape
    n_k = len(slices)
    n_rank = u1.shape[1]
    gram2 = u2.T @ u2
    gram3 = u3.T @ u3
    metric = gram2 * gram3
    unfolded = np.zeros((n_i, n_rank), dtype=np.float64)
    for index in range(n_k):
        unfolded += (slices[index] @ u2) * u3[index]
    solved = np.linalg.solve(metric.T, unfolded.T).T
    lambdas = np.sum(np.abs(solved), axis=0)
    u1 = solved / lambdas

    metric = (u1.T @ u1) * gram3
    unfolded = np.zeros((n_j, n_rank), dtype=np.float64)
    for index in range(n_k):
        unfolded += (slices[index].T @ u1) * u3[index]
    solved = np.linalg.solve(metric.T, unfolded.T).T
    lambdas = np.sum(np.abs(solved), axis=0)
    u2 = solved / lambdas

    metric = (u1.T @ u1) * (u2.T @ u2)
    unfolded = np.zeros((n_k, n_rank), dtype=np.float64)
    for index in range(n_k):
        unfolded[index] = np.sum(u1 * (slices[index] @ u2), axis=0)
    solved = np.linalg.solve(metric.T, unfolded.T).T
    lambdas = np.sum(np.abs(solved), axis=0)
    u3 = solved / lambdas
    return u1, u2, u3, lambdas, unfolded


def _update_torch(slices, u1, u2, u3):
    import torch

    n_k, n_i, n_j = slices.shape
    n_rank = u1.shape[1]
    gram3 = u3.T @ u3
    metric = (u2.T @ u2) * gram3
    unfolded = torch.zeros((n_i, n_rank), dtype=torch.float64, device=slices.device)
    for index in range(n_k):
        unfolded = unfolded + (slices[index] @ u2) * u3[index]
    solved = torch.linalg.solve(metric.T, unfolded.T).T
    lambdas = torch.sum(torch.abs(solved), dim=0)
    u1 = solved / lambdas

    metric = (u1.T @ u1) * gram3
    unfolded = torch.zeros((n_j, n_rank), dtype=torch.float64, device=slices.device)
    for index in range(n_k):
        unfolded = unfolded + (slices[index].T @ u1) * u3[index]
    solved = torch.linalg.solve(metric.T, unfolded.T).T
    lambdas = torch.sum(torch.abs(solved), dim=0)
    u2 = solved / lambdas

    metric = (u1.T @ u1) * (u2.T @ u2)
    unfolded = torch.zeros((n_k, n_rank), dtype=torch.float64, device=slices.device)
    for index in range(n_k):
        unfolded[index] = torch.sum(u1 * (slices[index] @ u2), dim=0)
    solved = torch.linalg.solve(metric.T, unfolded.T).T
    lambdas = torch.sum(torch.abs(solved), dim=0)
    u3 = solved / lambdas
    return u1, u2, u3, lambdas, unfolded


def _residual(u1, u2, u3, lambdas, unfolded, tensor_norm_sq: float) -> float:
    inner = float(np.sum(np.asarray(lambdas) * np.sum(np.asarray(u3) * np.asarray(unfolded), axis=0)))
    gram = (np.asarray(u1).T @ np.asarray(u1)) * (np.asarray(u2).T @ np.asarray(u2)) * (np.asarray(u3).T @ np.asarray(u3))
    estimate = float(np.sum(np.outer(np.asarray(lambdas), np.asarray(lambdas)) * gram))
    return float(np.sqrt(max(tensor_norm_sq - 2.0 * inner + estimate, 0.0)))


def _reconstruct(u1: np.ndarray, u2: np.ndarray, u3: np.ndarray, lambdas: np.ndarray) -> np.ndarray:
    n_i, _rank = u1.shape
    n_j = u2.shape[0]
    n_k = u3.shape[0]
    estimate = np.zeros((n_i, n_j, n_k), dtype=np.float64)
    for index in range(n_k):
        scaled = u1 * (lambdas * u3[index])
        estimate[:, :, index] = scaled @ u2.T
    return estimate


def _load_checkpoint(path: Path, digest: str, shape: tuple[int, int, int], n_comp: int, tol: float):
    with np.load(path, allow_pickle=False) as blob:
        if str(blob["digest"]) != digest:
            raise RuntimeError("CP checkpoint does not match this tensor")
        if tuple(int(v) for v in blob["shape"]) != shape:
            raise RuntimeError("CP checkpoint shape does not match")
        if int(blob["n_comp"]) != int(n_comp) or float(blob["tol"]) != float(tol):
            raise RuntimeError("CP checkpoint settings do not match")
        return {
            "u1": np.array(blob["u1"], dtype=np.float64, copy=True),
            "u2": np.array(blob["u2"], dtype=np.float64, copy=True),
            "u3": np.array(blob["u3"], dtype=np.float64, copy=True),
            "lambdas": np.array(blob["lambdas"], dtype=np.float64, copy=True),
            "prev_resid": float(blob["prev_resid"]),
            "curr_iter": int(blob["curr_iter"]),
            "converged": bool(int(blob["converged"])),
        }


def cp_als(
    tensor: np.ndarray,
    n_comp: int = 3,
    max_iter: int = 25,
    tol: float = 1e-5,
    seed: int = 1,
    device: str = "cpu",
    checkpoint_path: Path | None = None,
    init: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None,
) -> dict:
    """Run CP-ALS. Resume only when checkpoint_path is a finished iteration of this tensor."""
    values = np.asarray(tensor, dtype=np.float64)
    if values.ndim != 3:
        raise ValueError("tensor must have three modes")
    if device not in ("cpu", "gpu"):
        raise ValueError("device must be cpu or gpu")
    n_i, n_j, n_k = values.shape
    if n_comp < 1 or n_comp >= min(n_i, n_j, n_k):
        raise ValueError("n_comp must be >= 1 and smaller than every mode")
    digest = _digest(values)
    shape = (n_i, n_j, n_k)
    path = None if checkpoint_path is None else Path(checkpoint_path)
    loaded = None
    if path is not None and path.exists() and path.stat().st_size > 0:
        loaded = _load_checkpoint(path, digest, shape, n_comp, tol)

    if loaded is None:
        if init is None:
            generator = np.random.default_rng(int(seed))
            u1 = generator.standard_normal((n_i, n_comp))
            u2 = generator.standard_normal((n_j, n_comp))
            u3 = generator.standard_normal((n_k, n_comp))
        else:
            u1, u2, u3 = (np.array(factor, dtype=np.float64, copy=True) for factor in init)
        lambdas = np.ones(n_comp, dtype=np.float64)
        prev_resid = float("inf")
        curr_iter = 1
        converged = False
    else:
        u1, u2, u3 = loaded["u1"], loaded["u2"], loaded["u3"]
        lambdas = loaded["lambdas"]
        prev_resid = loaded["prev_resid"]
        curr_iter = loaded["curr_iter"]
        converged = loaded["converged"]

    tensor_norm_sq = float(np.sum(values * values))
    tensor_norm = float(np.sqrt(tensor_norm_sq))
    slices = [np.ascontiguousarray(values[:, :, index]) for index in range(n_k)]
    use_gpu = device == "gpu"
    torch_slices = None
    if use_gpu and not converged:
        import torch

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available")
        torch.set_num_threads(1)
        torch_slices = torch.as_tensor(np.stack(slices, axis=0), device="cuda", dtype=torch.float64)
        u1_t = torch.as_tensor(u1, device="cuda", dtype=torch.float64)
        u2_t = torch.as_tensor(u2, device="cuda", dtype=torch.float64)
        u3_t = torch.as_tensor(u3, device="cuda", dtype=torch.float64)

    while curr_iter < max_iter and not converged:
        if use_gpu:
            u1_t, u2_t, u3_t, lambdas_t, unfolded_t = _update_torch(torch_slices, u1_t, u2_t, u3_t)
            u1 = u1_t.detach().cpu().numpy().copy()
            u2 = u2_t.detach().cpu().numpy().copy()
            u3 = u3_t.detach().cpu().numpy().copy()
            lambdas = lambdas_t.detach().cpu().numpy().copy()
            unfolded = unfolded_t.detach().cpu().numpy().copy()
        else:
            u1, u2, u3, lambdas, unfolded = _update_numpy(slices, u1, u2, u3)
            u1, u2, u3 = u1.copy(), u2.copy(), u3.copy()
            lambdas = np.array(lambdas, dtype=np.float64, copy=True)
            unfolded = np.array(unfolded, dtype=np.float64, copy=True)
        current = _residual(u1, u2, u3, lambdas, unfolded, tensor_norm_sq)
        if curr_iter > 1 and tensor_norm > 0 and abs(current - prev_resid) / tensor_norm < tol:
            converged = True
        else:
            prev_resid = current
            curr_iter += 1
        if path is not None:
            _atomic_npz(
                path,
                u1=u1,
                u2=u2,
                u3=u3,
                lambdas=lambdas,
                prev_resid=np.float64(prev_resid),
                curr_iter=np.int32(curr_iter),
                converged=np.int32(1 if converged else 0),
                tol=np.float64(tol),
                max_iter=np.int32(max_iter),
                n_comp=np.int32(n_comp),
                shape=np.asarray(shape, dtype=np.int32),
                digest=np.asarray(digest),
            )

    return {
        "u1": u1,
        "u2": u2,
        "u3": u3,
        "lambdas": lambdas,
        "converged": converged,
        "curr_iter": curr_iter,
        "estimate": _reconstruct(u1, u2, u3, lambdas),
    }


def _as_csr_cuda(matrix):
    """One square CSR slice on the current CUDA device, float64."""
    import torch
    from scipy import sparse

    csr = sparse.csr_matrix(matrix, dtype=np.float64)
    if csr.shape[0] != csr.shape[1]:
        raise ValueError("each network must be square")
    size = int(csr.shape[0])
    crow = torch.as_tensor(np.asarray(csr.indptr, dtype=np.int64), device="cuda")
    cols = torch.as_tensor(np.asarray(csr.indices, dtype=np.int64), device="cuda")
    vals = torch.as_tensor(np.asarray(csr.data, dtype=np.float64), device="cuda")
    tensor = torch.sparse_csr_tensor(crow, cols, vals, size=(size, size), dtype=torch.float64, device="cuda")
    return tensor, float(np.dot(csr.data, csr.data))


def _mode_update(slices, left: "torch.Tensor", right: "torch.Tensor", weights: "torch.Tensor"):
    """One ALS mode. slices @ right, columns scaled by weights, then the  R-by-R solve."""
    import torch

    rank = right.shape[1]
    unfolded = torch.zeros((left.shape[0], rank), dtype=torch.float64, device=left.device)
    for index, slab in enumerate(slices):
        unfolded = unfolded + torch.sparse.mm(slab, right) * weights[index]
    metric = (left.T @ left) * (weights.T @ weights)
    solved = torch.linalg.solve(metric.T, unfolded.T).T
    lambdas = torch.sum(torch.abs(solved), dim=0)
    updated = solved / lambdas
    return updated, lambdas, unfolded


def tensor_from_networks_gpu(
    networks: list,
    init: tuple[np.ndarray, np.ndarray, np.ndarray],
    n_comp: int = 3,
    max_iter: int = 1000,
    tol: float = 1e-5,
    n_decimal: int = 3,
) -> dict:
    """Official 3-mode CP on CUDA, then the mean, max-abs scale, and decimal rounding.

    ``init`` is the three ``rnorm`` factors from ``set.seed(1)``, column-major,
    with shapes (genes, K), (genes, K), (networks, K). The networks stay sparse.
    The returned matrix is the rounded average, before the diagonal is cleared
    and before the transpose stored in the official WT.
    """
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available")
    torch.set_num_threads(1)
    if len(networks) < 2:
        raise ValueError("at least two networks are required")
    slices = []
    tensor_norm_sq = 0.0
    size = None
    for network in networks:
        slab, gram = _as_csr_cuda(network)
        if size is None:
            size = int(slab.shape[0])
        elif int(slab.shape[0]) != size:
            raise ValueError("networks must share one gene dimension")
        slices.append(slab)
        tensor_norm_sq += gram
    u1, u2, u3 = (np.array(factor, dtype=np.float64, copy=True) for factor in init)
    if u1.shape != (size, n_comp) or u2.shape != (size, n_comp) or u3.shape != (len(slices), n_comp):
        raise ValueError("init factors do not match the networks and n_comp")
    u1_t = torch.as_tensor(u1, device="cuda", dtype=torch.float64)
    u2_t = torch.as_tensor(u2, device="cuda", dtype=torch.float64)
    u3_t = torch.as_tensor(u3, device="cuda", dtype=torch.float64)
    tensor_norm = float(np.sqrt(tensor_norm_sq))
    transposed = [slab.transpose(0, 1).to_sparse_csr() for slab in slices]
    prev_resid = float("inf")
    curr_iter = 1
    converged = False
    lambdas_t = torch.ones(n_comp, dtype=torch.float64, device="cuda")
    while curr_iter < max_iter and not converged:
        u1_t, _lam, _fold = _mode_update(slices, u2_t, u2_t, u3_t)
        u2_t, _lam, _fold = _mode_update(transposed, u1_t, u1_t, u3_t)
        metric = (u1_t.T @ u1_t) * (u2_t.T @ u2_t)
        unfolded = torch.zeros((len(slices), n_comp), dtype=torch.float64, device="cuda")
        for index, slab in enumerate(slices):
            unfolded[index] = torch.sum(u1_t * torch.sparse.mm(slab, u2_t), dim=0)
        solved = torch.linalg.solve(metric.T, unfolded.T).T
        lambdas_t = torch.sum(torch.abs(solved), dim=0)
        u3_t = solved / lambdas_t
        gram = (u1_t.T @ u1_t) * (u2_t.T @ u2_t) * (u3_t.T @ u3_t)
        inner = torch.sum(lambdas_t * torch.sum(u3_t * unfolded, dim=0))
        estimate = torch.sum(torch.outer(lambdas_t, lambdas_t) * gram)
        current = torch.sqrt(torch.clamp(tensor_norm_sq - 2.0 * inner + estimate, min=0.0))
        current_value = float(current.item())
        if curr_iter > 1 and tensor_norm > 0 and abs(current_value - prev_resid) / tensor_norm < tol:
            converged = True
        else:
            prev_resid = current_value
            curr_iter += 1
    weights = lambdas_t * torch.sum(u3_t, dim=0)
    average = ((u1_t * weights) @ u2_t.T / float(len(slices))).detach().cpu().numpy()
    scale = float(np.max(np.abs(average)))
    if np.isfinite(scale) and scale > 0.0:
        average = average / scale
    return {
        "matrix": np.round(average, int(n_decimal)),
        "iterations": int(curr_iter),
        "converged": converged,
    }
