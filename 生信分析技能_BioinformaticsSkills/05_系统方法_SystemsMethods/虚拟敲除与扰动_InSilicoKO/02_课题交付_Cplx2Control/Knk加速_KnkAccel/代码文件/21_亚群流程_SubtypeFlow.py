"""Finished subtypes: 1.4.3 networks, official tail, compare with Formal tables.

cLTMR reuses the QC matrix and cell indices already exported for the 1.4 run.
PEP and TRPM8 are exported read-only. NP and NF1 are still running and are skipped.
"""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy import sparse

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))
from knk_accel.versions import pcnet_143

ROOT = Path(r"C:\Users\10540\AppData\Local\knk_flow")
CL_EXISTING = Path(r"C:\Users\10540\AppData\Local\knk_accel_cLTMR")
DATA = Path(r"C:\Users\10540\Desktop\琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO\结果文件\数据文件")
DOCS = CODE.parent / "文档_docs"
RSCRIPT = os.environ.get("RSCRIPT", r"E:\R-4.6.0\bin\Rscript.exe")
SUBTYPES = ("cLTMR", "PEP", "TRPM8")


def run_r(script: Path, out: Path, subtype: str) -> None:
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    completed = subprocess.run(
        [RSCRIPT, "--vanilla", str(script), str(out), subtype],
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if completed.returncode != 0:
        tail = (completed.stderr or completed.stdout or "").strip().splitlines()
        raise RuntimeError(tail[-8:] if tail else f"R exit {completed.returncode}")
    if completed.stdout:
        print(completed.stdout, flush=True)


def load_counts(out: Path) -> tuple[np.ndarray, list[str]]:
    genes = (out / "genes.txt").read_text(encoding="utf-8").splitlines()
    raw = np.fromfile(out / "cpm.bin", dtype=np.float64)
    return raw.reshape((len(genes), raw.size // len(genes)), order="F"), genes


def write_csr(path: Path, matrix: sparse.csr_matrix) -> None:
    csr = matrix.tocsr()
    indptr = np.asarray(csr.indptr, dtype=np.int32)
    indices = np.asarray(csr.indices, dtype=np.int32)
    data = np.asarray(csr.data, dtype=np.float64)
    with path.open("wb") as handle:
        np.asarray([csr.shape[0], csr.shape[1], csr.nnz], dtype=np.int32).tofile(handle)
        indptr.tofile(handle)
        indices.tofile(handle)
        data.tofile(handle)


def build_secular(out: Path) -> None:
    counts, _genes = load_counts(out)
    for net_id in range(1, 11):
        csr_path = out / f"net_{net_id:02d}.csr"
        if csr_path.exists() and csr_path.stat().st_size > 1000:
            print(f"skip net {net_id:02d}", flush=True)
            continue
        text = (out / f"net_{net_id:02d}_indices.txt").read_text(encoding="utf-8").split()
        indices = np.asarray([int(item) for item in text], dtype=np.int64)
        sub = counts[:, indices]
        keep = sub.sum(axis=1) > 0
        dense = pcnet_143(sub[keep], n_comp=3, q=0.9, device="gpu")
        full = np.zeros((counts.shape[0], counts.shape[0]), dtype=np.float64)
        full[np.ix_(keep, keep)] = dense
        write_csr(csr_path, sparse.csr_matrix(full))
        del dense, full
        print(f"built net {net_id:02d}", flush=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def column(rows: list[dict[str, str]], *names: str) -> str:
    keys = rows[0].keys()
    for name in names:
        if name in keys:
            return name
    raise KeyError(names)


def compare(official: Path, optimized: Path) -> dict[str, float | int | str]:
    off_rows = read_csv(official)
    new_rows = read_csv(optimized)
    gene_off = column(off_rows, "gene", "Gene")
    gene_new = column(new_rows, "gene", "Gene")
    off_map = {row[gene_off]: row for row in off_rows}
    new_map = {row[gene_new]: row for row in new_rows}
    genes = [gene for gene in off_map if gene in new_map]
    distance_off = np.array([float(off_map[gene]["distance"]) for gene in genes])
    distance_new = np.array([float(new_map[gene]["distance"]) for gene in genes])
    padj_off = np.array([float(off_map[gene]["p.adj"]) for gene in genes])
    padj_new = np.array([float(new_map[gene]["p.adj"]) for gene in genes])
    abs_diff = np.abs(distance_new - distance_off)

    def hits(values: np.ndarray) -> set[str]:
        return {genes[i] for i, value in enumerate(values) if genes[i] != "Cplx2" and np.isfinite(value) and value < 0.05}

    hit_off = hits(padj_off)
    hit_new = hits(padj_new)
    return {
        "genes": len(genes),
        "distance_max": float(np.max(abs_diff)),
        "distance_median": float(np.median(abs_diff)),
        "above_1e-5": int(np.sum(abs_diff > 1e-5)),
        "padj_max": float(np.max(np.abs(padj_new - padj_off))),
        "fdr_off": len(hit_off),
        "fdr_new": len(hit_new),
        "only_off": ",".join(sorted(hit_off - hit_new)) or "无",
        "only_new": ",".join(sorted(hit_new - hit_off)) or "无",
        "cplx2_off": float(off_map["Cplx2"]["distance"]),
        "cplx2_new": float(new_map["Cplx2"]["distance"]),
    }


def ensure_inputs(subtype: str, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    if "结果文件" in str(out):
        raise RuntimeError("refusing to write inside Formal results")
    if (out / "cpm.bin").exists() and (out / "net_10_indices.txt").exists():
        return
    if subtype == "cLTMR" and (CL_EXISTING / "cpm.bin").exists():
        for name in ("cpm.bin", "genes.txt", "timings.csv"):
            target = out / name
            if not target.exists():
                target.write_bytes((CL_EXISTING / name).read_bytes())
        for net_id in range(1, 11):
            name = f"net_{net_id:02d}_indices.txt"
            target = out / name
            if not target.exists():
                target.write_bytes((CL_EXISTING / name).read_bytes())
        return
    run_r(CODE / "21_导出质控_ExportQc.R", out, subtype)


def wt_diff(out: Path) -> str:
    for row in read_csv(out / "timings_tail.csv"):
        if row["step"] == "wt_max_abs":
            return row["seconds"]
    return "missing"


def main() -> None:
    rows = []
    if (CL_EXISTING / "dr_optimized.csv").exists():
        stats = compare(DATA / "04_扰动基因_cLTMR_Cplx2Dr_Formal.csv", CL_EXISTING / "dr_optimized.csv")
        stats["subtype"] = "cLTMR"
        stats["version"] = "1.4"
        stats["wt"] = "见亚群对照_cLTMR.md"
        rows.append(stats)
        print("cLTMR 1.4 existing", stats["distance_max"], flush=True)
    for subtype in SUBTYPES:
        out = ROOT / f"{subtype}_143"
        ensure_inputs(subtype, out)
        build_secular(out)
        if not (out / "dr_optimized.csv").exists():
            run_r(CODE / "21_后半段_Tail.R", out, subtype)
        stats = compare(DATA / f"04_扰动基因_{subtype}_Cplx2Dr_Formal.csv", out / "dr_optimized.csv")
        stats["subtype"] = subtype
        stats["version"] = "1.4.3"
        stats["wt"] = wt_diff(out)
        rows.append(stats)
        print(subtype, "1.4.3", stats["distance_max"], stats["wt"], flush=True)
    write_report(rows)


def write_report(rows: list[dict]) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# 标准流程对照",
        "",
        f"记录时间：{stamp}。小矩阵先过，再跑已完成的 cLTMR、PEP、TRPM8。NP 和 NF1 还在正式任务里，没有纳入。1 个 BLAS 线程。没有写 Formal 结果目录。",
        "",
        "小矩阵 40 基因 × 30 细胞，`q=0.9`，`nComp=3`。通过线是最大绝对差 < 1e-5。",
        "",
        "| 对照 | 最大绝对差 |",
        "|---|---:|",
        "| Python 1.4 CPU 对本机 Rcpp | 8.293e-14 |",
        "| Python 1.4 GPU 对本机 Rcpp | 6.706e-14 |",
        "| Python 1.4.3 CPU 对仓库 pcNet.R | 1.921e-14 |",
        "| Python 1.4.3 GPU 对仓库 pcNet.R | 1.532e-14 |",
        "| 仓库 1.4.3 对本机 1.4，同一矩阵 | 7.300e-14 |",
        "| Python 1.4.3 对仓库，多一行全 0 基因 | 1.921e-14 |",
        "",
        "亚群流程和正式调用相同：官方 `scQC`、CPM、`set.seed(1)` 后 furrr `seed=TRUE` 抽 10 次细胞、建网、`tensorDecomposition`、`strictDirection(lambda=0)`、Cplx2 出边置零、`manifoldAlignment`、`dRegulation(empiricalNull=FALSE)`。1.4.3 这一列的建网是 `pcnet_143(..., device=\"gpu\")`。1.4 的 cLTMR 沿用已经落盘的 GPU 截断 SVD 结果，没有重算。",
        "",
        "| 亚群 | 版本 | 基因数 | distance 最大差 | p.adj 最大差 | 差 > 1e-5 的基因数 | 正式 FDR | 本次 FDR | 只在正式结果 | 只在本次 | WT 对 RDS |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|---:|",
    ]
    for row in rows:
        lines.append(
            "| {subtype} | {version} | {genes} | {distance_max:.6e} | {padj_max:.6e} | {above_1e-5} | {fdr_off} | {fdr_new} | {only_off} | {only_new} | {wt} |".format(**row)
        )
    lines.extend(["", "Cplx2 的 distance：", ""])
    for row in rows:
        lines.append(f"- {row['subtype']} {row['version']}：正式 {row['cplx2_off']:.6e}，本次 {row['cplx2_new']:.6e}。")
    lines.append("")
    text = "\n".join(lines)
    (DOCS / "亚群对照_标准流程.md").write_text(text, encoding="utf-8")
    print(text, flush=True)


if __name__ == "__main__":
    main()
