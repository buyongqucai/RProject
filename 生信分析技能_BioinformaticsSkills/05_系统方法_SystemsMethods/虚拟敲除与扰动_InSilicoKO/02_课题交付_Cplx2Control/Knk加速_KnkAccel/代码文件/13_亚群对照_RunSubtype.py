"""cLTMR with the GPU gesvd networks, then the official R tail.

Compares distance and adjusted p to the finished Formal cLTMR table.
One BLAS thread. Writes outside the Formal result directory.
Does not stop the live PEP job.
"""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["KNK_ALLOW_LARGE"] = "1"

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import numpy as np
from scipy import sparse

from knk_accel.checkpoint import append_timing, build_checkpoint_networks, net_paths, save_indices
from knk_accel.pcnet import GPU_SVD_DRIVER

OUT = Path(r"C:\Users\10540\AppData\Local\knk_accel_cLTMR")
DOCS = CODE_DIR.parent / "文档_docs"
OFFICIAL_CSV = Path(
    r"C:\Users\10540\Desktop\琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO\结果文件\数据文件\04_扰动基因_cLTMR_Cplx2Dr_Formal.csv"
)
FORMAL_MARKER = "结果文件"


def _run_r(script: Path) -> None:
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    completed = subprocess.run(
        [os.environ.get("RSCRIPT", "Rscript"), "--vanilla", str(script), str(OUT)],
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if completed.returncode != 0:
        tail = (completed.stderr or completed.stdout or "").strip().splitlines()
        raise RuntimeError(tail[-1] if tail else f"R exit {completed.returncode}")
    if completed.stdout:
        print(completed.stdout, flush=True)


def _load_counts() -> tuple[np.ndarray, list[str]]:
    genes = (OUT / "genes.txt").read_text(encoding="utf-8").splitlines()
    raw = np.fromfile(OUT / "cpm.bin", dtype=np.float64)
    counts = raw.reshape((len(genes), raw.size // len(genes)), order="F")
    return counts, genes


def _write_indices(n_net: int) -> int:
    n_draw = None
    for net_id in range(1, n_net + 1):
        text = (OUT / f"net_{net_id:02d}_indices.txt").read_text(encoding="utf-8").split()
        indices = np.asarray([int(item) for item in text], dtype=np.int32)
        save_indices(net_paths(OUT, net_id)["indices"], indices)
        n_draw = int(indices.size)
    return int(n_draw)


def _write_csr(path: Path, matrix: sparse.csr_matrix) -> None:
    csr = matrix.tocsr()
    if csr.nnz >= 2**31:
        raise RuntimeError("CSR nnz does not fit in int32")
    indptr = np.asarray(csr.indptr, dtype=np.int32)
    indices = np.asarray(csr.indices, dtype=np.int32)
    data = np.asarray(csr.data, dtype=np.float64)
    header = np.asarray([csr.shape[0], csr.shape[1], csr.nnz], dtype=np.int32)
    with path.open("wb") as handle:
        header.tofile(handle)
        indptr.tofile(handle)
        indices.tofile(handle)
        data.tofile(handle)


def _export_csr(n_net: int) -> None:
    for net_id in range(1, n_net + 1):
        blob_path = net_paths(OUT, net_id)["network"]
        with np.load(blob_path, allow_pickle=False) as blob:
            matrix = sparse.csr_matrix(
                (blob["data"], blob["indices"], blob["indptr"]),
                shape=tuple(int(v) for v in blob["shape"]),
            )
        _write_csr(OUT / f"net_{net_id:02d}.csr", matrix)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _column(rows: list[dict[str, str]], *names: str) -> str:
    keys = rows[0].keys()
    for name in names:
        if name in keys:
            return name
    raise KeyError(names)


def _write_report(timings: list[tuple[str, float, str]], wt_diff: float) -> None:
    official = _read_csv(OFFICIAL_CSV)
    optimized = _read_csv(OUT / "dr_optimized.csv")
    gene_key_off = _column(official, "gene", "Gene")
    gene_key_new = _column(optimized, "gene", "Gene")
    off_map = {row[gene_key_off]: row for row in official}
    new_map = {row[gene_key_new]: row for row in optimized}
    genes = [gene for gene in off_map if gene in new_map]
    missing = sorted(set(off_map) - set(new_map))
    distance_off = np.array([float(off_map[gene]["distance"]) for gene in genes])
    distance_new = np.array([float(new_map[gene]["distance"]) for gene in genes])
    abs_diff = np.abs(distance_new - distance_off)
    padj_off = np.array([float(off_map[gene]["p.adj"]) for gene in genes])
    padj_new = np.array([float(new_map[gene]["p.adj"]) for gene in genes])

    def hits(values: np.ndarray, names: list[str]) -> set[str]:
        return {names[i] for i, value in enumerate(values) if names[i] != "Cplx2" and np.isfinite(value) and value < 0.05}

    hit_off = hits(padj_off, genes)
    hit_new = hits(padj_new, genes)
    only_off = sorted(hit_off - hit_new)
    only_new = sorted(hit_new - hit_off)
    corr = float(np.corrcoef(distance_off, distance_new)[0, 1]) if len(genes) > 1 else float("nan")
    elapsed_off = float(official[0]["elapsed_sec"])

    diff_path = DOCS / "亚群对照_cLTMR_逐基因.csv"
    with diff_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["gene", "distance_official", "distance_optimized", "abs_diff", "p.adj_official", "p.adj_optimized"])
        for i, gene in enumerate(genes):
            writer.writerow([gene, distance_off[i], distance_new[i], abs_diff[i], padj_off[i], padj_new[i]])

    timing_lines = [
        f"| {step} | {seconds:.3f} | {detail} |"
        for step, seconds, detail in timings
        if step != "wt_max_abs"
    ]
    net_seconds = sum(seconds for step, seconds, _detail in timings if step.startswith("network_"))
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = "\n".join(
        [
            "# cLTMR 亚群对照",
            "",
            f"记录时间：{stamp}。优化后建网用 GPU `{GPU_SVD_DRIVER}`，1 个 BLAS 线程，10 张网串行。后半段是官方 `tensorDecomposition`、`strictDirection`、`manifoldAlignment`、`dRegulation`，不是加速库里的 CP。优化前是已经跑完的正式参数 cLTMR（Rcpp 完整 SVD，10 张网并行，每网 BLAS 2）。",
            "",
            "细胞下标：质控和 CPM 之后，`set.seed(1)`，再按正式脚本里的 furrr `seed=TRUE` 抽样。同一调用连抽两次，下标一致。`q=0.9`，`nComp=3`，`nc_nCells=425`。没有写 Formal 结果目录。PEP 对照期间仍在跑，所以没有再开一套 Rcpp 建网。",
            "",
            "## 用时（秒）",
            "",
            "| 步骤 | 秒 | 说明 |",
            "|---|---:|---|",
            *timing_lines,
            "",
            f"优化后 10 张网合计 {net_seconds:.1f} 秒。优化前整次正式调用 {elapsed_off:.1f} 秒（{elapsed_off / 60:.1f} 分钟），里面是并行建网加后半段，不能把这一格直接除以 10 当成单网。",
            "",
            "## 和优化前结果的差异",
            "",
            f"- 基因数：优化前 {len(off_map)}，两边都有的 {len(genes)}，只在优化前出现的 {len(missing)}。",
            f"- `distance` 最大绝对差：{float(np.max(abs_diff)):.6e}。中位数 {float(np.median(abs_diff)):.6e}。",
            f"- 绝对差 > 1e-8 的基因：{int(np.sum(abs_diff > 1e-8))}。> 1e-6：{int(np.sum(abs_diff > 1e-6))}。> 1e-5：{int(np.sum(abs_diff > 1e-5))}。",
            f"- `distance` 的 Pearson 相关：{corr:.8f}。",
            f"- 张量并定向之后的 WT，对官方 RDS 的最大绝对差：{wt_diff:.6e}。",
            f"- 去掉 Cplx2 后 FDR<0.05：优化前 {len(hit_off)} 个，优化后 {len(hit_new)} 个。只在优化前：{only_off or '无'}。只在优化后：{only_new or '无'}。",
            f"- Cplx2 distance：优化前 {float(off_map['Cplx2']['distance']):.6e}，优化后 {float(new_map['Cplx2']['distance']):.6e}。",
            "",
            "逐基因表在 `亚群对照_cLTMR_逐基因.csv`。网络和检查点在 `C:\\Users\\10540\\AppData\\Local\\knk_accel_cLTMR`。",
            "",
            "这次差异同时包含求解器舍入和「完整 SVD 对截断 SVD」。下标和后半段公式按正式调用对齐。不能把这张表说成全部 5 个亚群，也不能说成已经替换 Formal。",
            "",
        ]
    )
    (DOCS / "亚群对照_cLTMR.md").write_text(text, encoding="utf-8")
    print(text, flush=True)


def _timings() -> list[tuple[str, float, str]]:
    rows = []
    for name in ("timings.csv", "timings_tail.csv"):
        path = OUT / name
        if not path.exists():
            continue
        for row in _read_csv(path):
            rows.append((row["step"], float(row["seconds"]), row.get("detail", "")))
    last: dict[str, tuple[str, float, str]] = {}
    for item in rows:
        last[item[0]] = item
    return list(last.values())


def _wt_diff(timings: list[tuple[str, float, str]]) -> float:
    for step, seconds, _detail in timings:
        if step == "wt_max_abs":
            return seconds
    raise RuntimeError("WT diff missing")


def main() -> None:
    if FORMAL_MARKER in str(OUT):
        raise RuntimeError("refusing to write inside Formal results")
    OUT.mkdir(parents=True, exist_ok=True)
    if not (OUT / "cpm.bin").exists():
        _run_r(CODE_DIR / "13_导出cLTMR质控与下标_ExportQc.R")
    counts, genes = _load_counts()
    n_draw = _write_indices(10)
    build_checkpoint_networks(
        counts,
        genes,
        OUT,
        n_net=10,
        n_cells=n_draw,
        n_comp=3,
        q=0.9,
        seed=1,
        subtype="cLTMR",
        device="gpu",
    )
    _export_csr(10)
    if not (OUT / "dr_optimized.csv").exists():
        _run_r(CODE_DIR / "13_官方后半段_OfficialTail.R")
    timings = _timings()
    _write_report(timings, _wt_diff(timings))


if __name__ == "__main__":
    main()
