"""Checkpoint around the 1.4.3 secular pcNet. Storage is local; the formula is not.

Fresh cell indices are drawn by R sample.int after set.seed, through
`建网_SecularStore.R`. An existing index file is kept. SVD checkpoints are
not reused: the npz must record method secular143.
"""

from __future__ import annotations

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy import sparse

from knk_accel.checkpoint import _atomic_replace
from knk_accel.pcnet import HostBuffer, limit_threads
from knk_accel.secular import pcnet_secular

METHOD = "secular143"
RSCRIPT = Path(r"E:\R-4.6.0\bin\Rscript.exe")
R_STORE = Path(__file__).resolve().parents[1] / "R_仓库公式" / "建网_SecularStore.R"


def _paths(out_dir: Path, net_id: int) -> dict[str, Path]:
    stem = f"net_{net_id:02d}"
    return {
        "indices": out_dir / f"{stem}_indices.npy",
        "network": out_dir / f"{stem}.npz",
        "done": out_dir / f"{stem}.done",
    }


def _save_network(path: Path, matrix: sparse.csr_matrix, indices: np.ndarray, gene_names: np.ndarray, n_comp: int, q: float) -> None:
    tmp = path.with_name(path.name + ".partial")
    csr = matrix.tocsr()
    with open(tmp, "wb") as handle:
        np.savez_compressed(
            handle,
            data=csr.data,
            indices=csr.indices,
            indptr=csr.indptr,
            shape=np.asarray(csr.shape, dtype=np.int32),
            cell_indices=np.asarray(indices, dtype=np.int32),
            genes=np.asarray(gene_names),
            n_comp=np.int32(n_comp),
            q=np.float64(q),
            method=np.asarray(METHOD),
        )
    _atomic_replace(tmp, path)


def _matches(path: Path, gene_names: np.ndarray, n_comp: int, q: float) -> bool:
    try:
        with np.load(path, allow_pickle=False) as blob:
            method = str(np.asarray(blob["method"]).reshape(-1)[0])
            saved_genes = np.asarray(blob["genes"]).astype(str)
            saved_comp = int(blob["n_comp"])
            saved_q = float(blob["q"])
    except (OSError, ValueError, KeyError, IndexError):
        return False
    return (
        method == METHOD
        and saved_comp == int(n_comp)
        and saved_q == float(q)
        and np.array_equal(saved_genes, np.asarray(gene_names).astype(str))
    )


def build_secular_checkpoint(
    counts_genes_by_cells: np.ndarray,
    gene_names,
    out_dir: Path,
    n_net: int = 10,
    n_draw: int = 500,
    n_comp: int = 3,
    q: float = 0.9,
    seed: int = 1,
    device: str = "cpu",
) -> list[Path]:
    limit_threads()
    counts = np.asarray(counts_genes_by_cells, dtype=np.float64)
    genes = np.asarray(gene_names)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_r_indices(counts.shape[1], n_draw, n_net, seed, out_dir)
    writer = ThreadPoolExecutor(max_workers=1, thread_name_prefix="knk_save")
    pending = []

    def _save(net_id: int, result, indices, sub_genes, names) -> None:
        dense = result.numpy() if isinstance(result, HostBuffer) else result
        placed = _place(dense, sub_genes, names)
        paths = _paths(out_dir, net_id)
        _save_network(paths["network"], sparse.csr_matrix(placed), indices, names, n_comp, q)
        _atomic_replace_bytes(paths["done"])
        print(f"网 {net_id}/{n_net} 已写入", flush=True)

    try:
        for net_id in range(1, n_net + 1):
            paths = _paths(out_dir, net_id)
            if paths["done"].exists() and _matches(paths["network"], genes, n_comp, q):
                print(f"网 {net_id}/{n_net} 跳过", flush=True)
                continue
            if paths["done"].exists():
                paths["done"].unlink()
            indices = np.load(paths["indices"]).astype(np.int32)
            sub = counts[:, indices]
            keep = sub.sum(axis=1) > 0
            print(f"网 {net_id}/{n_net} 计算 基因 {int(keep.sum())}", flush=True)
            result = pcnet_secular(
                sub[keep], n_comp=n_comp, q=q, device=device, async_copy=device == "gpu"
            )
            pending.append(writer.submit(_save, net_id, result, indices, genes[keep], genes))
        for job in pending:
            job.result()
    finally:
        writer.shutdown(wait=True)
    return [_paths(out_dir, net_id)["network"] for net_id in range(1, n_net + 1)]


def _atomic_replace_bytes(path: Path) -> None:
    tmp = path.with_name(path.name + ".partial")
    tmp.write_bytes(b"ok\n")
    os.replace(tmp, path)


def _place(sub_matrix: np.ndarray, sub_genes: np.ndarray, full_genes: np.ndarray) -> np.ndarray:
    name_to_col = {str(name): index for index, name in enumerate(full_genes)}
    full = np.zeros((len(full_genes), len(full_genes)), dtype=np.float64)
    columns = [name_to_col[str(name)] for name in sub_genes]
    full[np.ix_(columns, columns)] = sub_matrix
    return full


def _write_r_indices(n_cells: int, n_draw: int, n_net: int, seed: int, out_dir: Path) -> None:
    r_dir = out_dir / "_r_indices"
    r_dir.mkdir(parents=True, exist_ok=True)
    command = (
        f"source('{R_STORE.as_posix()}', keep.source=TRUE); "
        f"paths <- draw_indices({int(n_cells)}, {int(n_draw)}, {int(n_net)}, {int(seed)}, '{r_dir.as_posix()}'); "
        "for (path in paths) { "
        "idx <- readRDS(path); "
        "write(idx, file=sub('\\\\.rds$', '.txt', path), ncolumns=1); "
        "}"
    )
    subprocess.run([str(RSCRIPT), "-e", command], check=True)
    for net_id in range(1, n_net + 1):
        dest = _paths(out_dir, net_id)["indices"]
        if dest.exists() and dest.stat().st_size > 0:
            continue
        values = np.loadtxt(r_dir / f"net_{net_id:02d}_indices.txt", dtype=np.int32)
        values = np.atleast_1d(values).astype(np.int32) - 1
        tmp = dest.with_name(dest.name + ".partial")
        with open(tmp, "wb") as handle:
            np.save(handle, np.atleast_1d(values))
        _atomic_replace(tmp, dest)
