"""Per-network checkpoints and a one-line progress file.

Startup always scans the directory before any SVD. A finished network is
net_XX.done plus a non-empty net_XX.npz. Gene progress is display-only.
"""

from __future__ import annotations

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from scipy import sparse

from knk_accel.pcnet import HostBuffer, limit_threads, pcnet_truncated, use_gpu_for
from knk_accel.resources import plan_cpu_workers, plan_gpu_network_concurrency

GENE_CAP = 500


def net_paths(out_dir: Path, net_id: int) -> dict[str, Path]:
    stem = f"net_{net_id:02d}"
    return {
        "indices": out_dir / f"{stem}_indices.npy",
        "network": out_dir / f"{stem}.npz",
        "done": out_dir / f"{stem}.done",
    }


def _atomic_replace(tmp: Path, dest: Path) -> None:
    os.replace(tmp, dest)


def _write_bytes_atomic(dest: Path, payload: bytes) -> None:
    tmp = dest.with_name(dest.name + ".partial")
    tmp.write_bytes(payload)
    _atomic_replace(tmp, dest)


def save_indices(path: Path, indices: np.ndarray) -> None:
    tmp = path.with_name(path.name + ".partial")
    with open(tmp, "wb") as handle:
        np.save(handle, np.asarray(indices, dtype=np.int32))
    _atomic_replace(tmp, path)


def save_network(path: Path, matrix: sparse.csr_matrix, indices: np.ndarray, gene_names: np.ndarray, n_comp: int, q: float) -> None:
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
        )
    _atomic_replace(tmp, path)


def _clear_partials(out_dir: Path) -> None:
    if not out_dir.exists():
        return
    for path in out_dir.glob("*.partial"):
        path.unlink()


def snapshot_for_save(matrix: sparse.csr_matrix, indices: np.ndarray, gene_names: np.ndarray):
    """Deep copy so the writer thread never shares buffers with the next SVD."""
    csr = sparse.csr_matrix(matrix).copy()
    return csr, np.asarray(indices, dtype=np.int32).copy(), np.asarray(gene_names).copy()


def _parameters_match(path: Path, gene_names, n_comp: int, q: float) -> bool:
    try:
        with np.load(path, allow_pickle=False) as blob:
            saved_genes = np.asarray(blob["genes"]).astype(str)
            saved_comp = int(blob["n_comp"])
            saved_q = float(blob["q"])
    except (OSError, ValueError, KeyError):
        return False
    if saved_comp != int(n_comp) or saved_q != float(q):
        return False
    if gene_names is None:
        return True
    return np.array_equal(saved_genes, np.asarray(gene_names).astype(str))


def scan_networks(out_dir: Path, n_net: int, gene_names=None, n_comp: int | None = None, q: float | None = None) -> list[dict]:
    """Classify each network before any SVD. Mutates the directory only to drop broken markers."""
    out_dir.mkdir(parents=True, exist_ok=True)
    _clear_partials(out_dir)
    check_parameters = gene_names is not None and n_comp is not None and q is not None
    rows = []
    for net_id in range(1, n_net + 1):
        paths = net_paths(out_dir, net_id)
        network_ok = paths["network"].exists() and paths["network"].stat().st_size > 0
        done_ok = paths["done"].exists()
        if done_ok and not network_ok:
            paths["done"].unlink()
            done_ok = False
        if done_ok and network_ok and check_parameters and not _parameters_match(paths["network"], gene_names, n_comp, q):
            paths["done"].unlink()
            done_ok = False
        if done_ok and network_ok:
            action = "skip"
        elif paths["indices"].exists() and paths["indices"].stat().st_size > 0:
            action = "resume"
        else:
            action = "new"
        rows.append({"net_id": net_id, "action": action, "paths": paths})
    return rows


def _format_eta(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    minutes, sec = divmod(seconds, 60)
    if minutes:
        return f"{minutes} 分 {sec} 秒"
    return f"{sec} 秒"


class Progress:
    def __init__(self, path: Path, subtype: str, subtype_index: int, n_subtypes: int, n_net: int):
        self.path = path
        self.subtype = subtype
        self.subtype_index = subtype_index
        self.n_subtypes = n_subtypes
        self.n_net = n_net
        self.nets_done = 0
        self._lock = threading.RLock()
        self._last_print = time.perf_counter()
        self._last_fraction = 0.0

    def write(self, line: str) -> None:
        with self._lock:
            _write_bytes_atomic(self.path, (line + "\n").encode("utf-8"))
            log = self.path.with_name("进度_Progress.log")
            with log.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        print(line, flush=True)

    def scan_summary(self, rows: list[dict]) -> None:
        skip = sum(row["action"] == "skip" for row in rows)
        resume = sum(row["action"] == "resume" for row in rows)
        fresh = sum(row["action"] == "new" for row in rows)
        self.nets_done = skip
        self.write(
            f"{self.subtype} {self.subtype_index}/{self.n_subtypes} | 续跑检测 | "
            f"跳过 {skip} 张，沿用下标重算 {resume} 张，新算 {fresh} 张 | 已完成网 {skip}/{self.n_net}"
        )

    def gene(self, net_id: int, action: str, gene_done: int, gene_total: int, started: float) -> None:
        now = time.perf_counter()
        fraction = 0.0 if gene_total <= 0 else gene_done / gene_total
        finished = gene_done >= gene_total
        with self._lock:
            due = finished or (now - self._last_print >= 2.0 and fraction - self._last_fraction >= 0.05)
            if not due:
                return
            self._last_print = now
            self._last_fraction = fraction
            nets_done = self.nets_done
        elapsed = now - started
        remain = 0.0 if gene_done <= 0 else elapsed / gene_done * (gene_total - gene_done)
        label = {"skip": "跳过", "resume": "续跑", "new": "新算"}[action]
        line = (
            f"{self.subtype} {self.subtype_index}/{self.n_subtypes} | 网 {net_id}/{self.n_net} {label} | "
            f"基因 {gene_done}/{gene_total} | 本网已 {_format_eta(elapsed)}，约剩 {_format_eta(remain)} | "
            f"已完成网 {nets_done}/{self.n_net}"
        )
        print(line, flush=True)

    def network_finished(self, net_id: int) -> None:
        with self._lock:
            self.nets_done += 1
            nets_done = self.nets_done
        self.write(
            f"{self.subtype} {self.subtype_index}/{self.n_subtypes} | 网 {net_id}/{self.n_net} 已写入 | "
            f"已完成网 {nets_done}/{self.n_net}"
        )


def _load_or_sample(path: Path, n_cells_total: int, n_draw: int, seed: int, net_id: int) -> np.ndarray:
    if path.exists() and path.stat().st_size > 0:
        return np.load(path)
    rng = np.random.default_rng(int(seed) + int(net_id))
    indices = rng.choice(n_cells_total, size=int(n_draw), replace=True).astype(np.int32)
    save_indices(path, indices)
    return indices


def _place_on_full_genes(sub_matrix, sub_genes: np.ndarray, full_genes: np.ndarray) -> sparse.csr_matrix:
    name_to_col = {str(name): i for i, name in enumerate(full_genes)}
    csr = sub_matrix.tocsr()
    coords = sparse.coo_matrix(csr)
    rows = np.array([name_to_col[str(sub_genes[i])] for i in coords.row], dtype=np.int32)
    cols = np.array([name_to_col[str(sub_genes[j])] for j in coords.col], dtype=np.int32)
    n = len(full_genes)
    return sparse.csr_matrix((coords.data, (rows, cols)), shape=(n, n))


def _save_ready(net_id: int, paths: dict, matrix, indices: np.ndarray, sub_genes: np.ndarray, genes: np.ndarray, n_comp: int, q: float, progress: Progress) -> None:
    """CSR placement and the npz write run on the save thread, after the copy finishes."""
    if isinstance(matrix, HostBuffer):
        matrix = sparse.csr_matrix(matrix.numpy())
    placed = _place_on_full_genes(matrix, sub_genes, genes)
    frozen_net, frozen_idx, frozen_genes = snapshot_for_save(placed, indices, genes)
    save_network(paths["network"], frozen_net, frozen_idx, frozen_genes, n_comp, q)
    _write_bytes_atomic(paths["done"], b"ok\n")
    progress.network_finished(net_id)


def append_timing(out_dir: Path, step: str, seconds: float, detail: str = "") -> None:
    path = Path(out_dir) / "timings.csv"
    new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        if new:
            handle.write("step,seconds,detail\n")
        handle.write(f"{step},{seconds:.3f},{detail}\n")


def build_checkpoint_networks(
    counts_genes_by_cells: np.ndarray,
    gene_names,
    out_dir: Path,
    n_net: int = 10,
    n_cells: int = 500,
    n_comp: int = 3,
    q: float = 0.95,
    seed: int = 1,
    subtype: str = "subtype",
    subtype_index: int = 1,
    n_subtypes: int = 1,
    progress_every: int = 100,
    device: str = "auto",
) -> list[Path]:
    limit_threads()
    counts = np.asarray(counts_genes_by_cells)
    genes = np.asarray(gene_names)
    if counts.ndim != 2 or counts.shape[0] != len(genes):
        raise ValueError("counts must be genes by cells, with one name per gene")
    if np.any(counts.sum(axis=1) <= 0):
        raise ValueError("zero gene row sums; drop those genes first")
    if counts.shape[0] > GENE_CAP and os.environ.get("KNK_ALLOW_LARGE") != "1":
        raise RuntimeError(
            f"refusing {counts.shape[0]} genes while KNK_ALLOW_LARGE is unset; Formal stays untouched"
        )
    out_dir = Path(out_dir)
    rows = scan_networks(out_dir, n_net, genes, n_comp, q)
    progress = Progress(out_dir / "进度_Progress.txt", subtype, subtype_index, n_subtypes, n_net)
    progress.scan_summary(rows)
    if all(row["action"] == "skip" for row in rows):
        return [row["paths"]["network"] for row in rows]

    n_draw = min(int(n_cells), max(int(counts.shape[1]), 1))
    # makeNetworks samples with replacement even when n_cells exceeds the table,
    # but a draw larger than the table is only meaningful with replacement of the same size request.
    if int(n_cells) > 0:
        n_draw = int(n_cells)

    pending_rows = [row for row in rows if row["action"] != "skip"]
    use_gpu = use_gpu_for(n_draw, int(counts.shape[0]), device)
    if use_gpu:
        plan = plan_gpu_network_concurrency(n_draw, int(counts.shape[0]), len(pending_rows))
        net_concurrency = int(plan["concurrency"])
        gene_workers = 1
    else:
        plan = plan_cpu_workers(n_draw, int(counts.shape[0]), int(counts.shape[0]))
        net_concurrency = 1
        gene_workers = int(plan["workers"])
    append_timing(
        out_dir,
        "parallel_plan",
        0.0,
        ";".join(f"{key}={value}" for key, value in plan.items()),
    )

    prepared = []
    for row in pending_rows:
        indices = _load_or_sample(row["paths"]["indices"], counts.shape[1], n_draw, seed, row["net_id"])
        prepared.append((row, indices))

    writer = ThreadPoolExecutor(max_workers=1, thread_name_prefix="knk_save")
    pending = []

    def _compute(item: tuple[dict, np.ndarray]):
        row, indices = item
        sub = counts[:, indices]
        keep = sub.sum(axis=1) > 0
        if not np.any(keep):
            raise RuntimeError(f"network {row['net_id']} subsample has no expressed genes")
        sub_genes = genes[keep]
        started = time.perf_counter()
        last_bucket = 0

        def on_gene(done: int, total: int) -> None:
            nonlocal last_bucket
            if done == total or done // progress_every > last_bucket:
                last_bucket = done // progress_every
                progress.gene(row["net_id"], row["action"], done, total, started)

        matrix = pcnet_truncated(
            sub[keep],
            n_comp=n_comp,
            q=q,
            on_gene=on_gene,
            n_workers=gene_workers,
            device=device,
            async_copy=False,
        )
        return row, indices, matrix, sub_genes, time.perf_counter() - started, int(keep.sum())

    try:
        with ThreadPoolExecutor(max_workers=net_concurrency, thread_name_prefix="knk_net") as pool:
            futures = [pool.submit(_compute, item) for item in prepared]
            for future in as_completed(futures):
                row, indices, matrix, sub_genes, net_seconds, gene_count = future.result()
                append_timing(
                    out_dir,
                    f"network_{row['net_id']:02d}",
                    net_seconds,
                    f"device={device};action={row['action']};genes={gene_count};concurrency={net_concurrency};async_copy={int(isinstance(matrix, HostBuffer))}",
                )
                pending.append(
                    writer.submit(_save_ready, row["net_id"], row["paths"], matrix, indices, sub_genes, genes, n_comp, q, progress)
                )
        for job in pending:
            job.result()
    finally:
        writer.shutdown(wait=True)

    final = scan_networks(out_dir, n_net, genes, n_comp, q)
    if any(row["action"] != "skip" for row in final):
        missing = [str(row["net_id"]) for row in final if row["action"] != "skip"]
        raise RuntimeError("networks incomplete: " + ",".join(missing))
    return [row["paths"]["network"] for row in final]
