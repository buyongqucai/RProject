"""Build truncated-SVD networks with resume detection and a progress file.

    python 04_截断建网可续跑_BuildCheckpoint.py --self-test

Does not read Formal counts and does not start an 8000-gene run.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import numpy as np

from knk_accel.checkpoint import build_checkpoint_networks, net_paths, scan_networks
from knk_accel.pcnet import pcnet_truncated, standardize_cells_by_genes, truncated_coefficients


def _write_counts(path: Path, counts: np.ndarray, genes: np.ndarray) -> None:
    header = "gene," + ",".join(f"c{i}" for i in range(counts.shape[1]))
    lines = [header]
    for name, row in zip(genes, counts):
        lines.append(str(name) + "," + ",".join(str(int(v)) for v in row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _r_reference(counts: np.ndarray, genes: np.ndarray, work: Path) -> tuple[np.ndarray, np.ndarray]:
    src = work / "counts.csv"
    net_path = work / "net.csv"
    core_path = work / "core.csv"
    _write_counts(src, counts, genes)
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    completed = subprocess.run(
        [
            os.environ.get("RSCRIPT", "Rscript"),
            "--vanilla",
            str(CODE_DIR / "06_对照pcNet_ExportRef.R"),
            str(src),
            str(net_path),
            str(core_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
    )
    if completed.returncode != 0:
        tail = (completed.stderr or completed.stdout or "").strip().splitlines()
        raise RuntimeError(tail[-1] if tail else f"R exit {completed.returncode}")
    net = np.loadtxt(net_path, delimiter=",", skiprows=1, usecols=range(1, counts.shape[0] + 1))
    core = np.loadtxt(core_path, delimiter=",")
    return net, core


def self_test() -> None:
    rng = np.random.default_rng(1)
    n_genes, n_cells = 25, 40
    counts = rng.poisson(3, size=(n_genes, n_cells)).astype(np.float64)
    counts += 1
    genes = np.array([f"g{i}" for i in range(n_genes)])
    with tempfile.TemporaryDirectory(prefix="knk_accel_") as tmp:
        work = Path(tmp)
        ref_net, ref_core = _r_reference(counts, genes, work)
        got = pcnet_truncated(counts, n_comp=3, q=0.95).toarray()
        x_std = standardize_cells_by_genes(counts)
        # R scaled inside ExportRef; compare cores on the same Python standardization via a second path:
        # ref_core came from R scale(t(x)), so recompute python from counts the same way.
        py_core = truncated_coefficients(x_std, n_comp=3)
        diff_net = float(np.max(np.abs(ref_net - got)))
        diff_core = float(np.max(np.abs(ref_core - py_core)))

        med_genes, med_cells = 80, 60
        med = rng.normal(size=(med_genes, med_cells))
        med_std = standardize_cells_by_genes(med)
        t0 = time.perf_counter()
        truncated_coefficients(med_std, n_comp=3)
        t_trunc = time.perf_counter() - t0

        out_dir = work / "ckpt"
        tiny = counts[:, :15]
        build_checkpoint_networks(
            tiny, genes, out_dir, n_net=3, n_cells=8, seed=7,
            subtype="cLTMR", subtype_index=1, n_subtypes=5, progress_every=5,
        )
        saved_idx = np.load(net_paths(out_dir, 2)["indices"])
        net_paths(out_dir, 2)["done"].unlink()
        net_paths(out_dir, 2)["network"].unlink()
        build_checkpoint_networks(
            tiny, genes, out_dir, n_net=3, n_cells=8, seed=7,
            subtype="cLTMR", subtype_index=1, n_subtypes=5, progress_every=5,
        )
        resume_idx = np.load(net_paths(out_dir, 2)["indices"])
        actions = [row["action"] for row in scan_networks(out_dir, 3)]
        progress_text = (out_dir / "进度_Progress.log").read_text(encoding="utf-8")
        resume_ok = actions == ["skip", "skip", "skip"] and np.array_equal(saved_idx, resume_idx)
        progress_ok = "基因" in progress_text and "续跑检测" in progress_text and "已完成网" in progress_text

    passed = diff_core < 1e-5 and resume_ok and progress_ok
    docs = CODE_DIR.parent / "文档_docs"
    docs.mkdir(parents=True, exist_ok=True)
    report = "\n".join(
        [
            "# 截断建网自测",
            "",
            f"- 25 基因网络对 pcNet(useRcpp=TRUE) 的最大绝对差：{diff_net:.3e}",
            f"- 系数矩阵对 pcNetCoreRcpp 的最大绝对差：{diff_core:.3e}",
            f"- 80 基因 × 60 细胞，Python 截断 SVD、1 线程：{t_trunc:.3f} 秒",
            f"- 删掉第 2 张网后重跑，三张都在且细胞下标不变：{'是' if resume_ok else '否'}",
            f"- 进度文件含基因计数：{'是' if progress_ok else '否'}",
            "- 未读取 Formal 数据，也没有修改 13 号正式脚本。",
            "",
        ]
    )
    (docs / "截断建网自测_CheckpointSelfTest.md").write_text(report, encoding="utf-8")
    print(report)
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    if len(sys.argv) == 1 or "--self-test" in sys.argv:
        self_test()
    else:
        raise SystemExit("只实现了 --self-test。8000 基因要等 Formal 结束并设置 KNK_ALLOW_LARGE=1。")
