"""Compare truncated PC regression with a full SVD and, if present, R's pcNetCoreRcpp.

Writes the alignment note next to this script's 文档_docs. Uses one BLAS thread.
Does not read the Formal counts and does not call scTenifoldKnk().
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from importlib.machinery import SourceFileLoader

_CORE = SourceFileLoader(
    "truncated_pcnet",
    str(Path(__file__).with_name("01_截断SVD_TruncatedPcNet.py")),
).load_module()

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "文档_docs"
R_SCRIPT = HERE / "03_导出Rcpp对照_ExportRcpp.R"


def _standardize(raw: np.ndarray) -> np.ndarray:
    centered = raw - raw.mean(axis=0, keepdims=True)
    scale = centered.std(axis=0, ddof=1, keepdims=True)
    scale[scale == 0] = 1.0
    return centered / scale


def main() -> int:
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(1)
    raw = rng.normal(size=(40, 15))
    x_std = _standardize(raw)
    full = _CORE.pc_net_core(x_std, n_comp=3, method="full")
    truncated = _CORE.pc_net_core(x_std, n_comp=3, method="truncated")
    py_diff = _CORE.max_abs_diff(full, truncated)

    matrix_path = OUT / "_align_xstd.csv"
    np.savetxt(matrix_path, x_std, delimiter=",")
    r_diff = None
    r_note = "R 对照未跑"
    rscript = os.environ.get("RSCRIPT", "Rscript")
    try:
        completed = subprocess.run(
            [rscript, "--vanilla", str(R_SCRIPT), str(matrix_path), str(OUT / "_align_rcpp.csv")],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"},
        )
        r_out = OUT / "_align_rcpp.csv"
        if completed.returncode == 0 and r_out.exists():
            r_coef = np.loadtxt(r_out, delimiter=",")
            r_diff = _CORE.max_abs_diff(full, r_coef)
            r_note = f"与 pcNetCoreRcpp 的最大绝对差 {r_diff:.3e}"
        else:
            tail = (completed.stderr or completed.stdout or "").strip().splitlines()
            r_note = "R 对照失败：" + (tail[-1] if tail else f"exit {completed.returncode}")
    except Exception as exc:
        r_note = f"R 对照失败：{exc}"

    passed = py_diff < 1e-6 and (r_diff is None or r_diff < 1e-5)
    report = OUT / "对齐记录_PcNetAlign.md"
    report.write_text(
        "\n".join(
            [
                "# pcNet 小矩阵对齐",
                "",
                "矩阵：40 个样本 × 15 个基因，列已按 R `scale` 的总体思路中心化（标准差用 N-1）。nComp=3。",
                "线程：OMP/MKL/OpenBLAS=1。没有读取 Formal 的 counts，也没有调用 `scTenifoldKnk()`。",
                "",
                f"- Python 完整 SVD 与截断 SVD 的最大绝对差：{py_diff:.3e}",
                f"- {r_note}",
                f"- 判定：{'通过' if passed else '未通过'}（截断对完整 SVD 要求 < 1e-6；若跑了 R，对 Rcpp 要求 < 1e-5）",
                "",
                "截断 SVD 只计算 C++ 里 `svd_econ` 之后保留的那 3 个右奇异向量。符号翻转在系数里会消掉。",
                "本结果不能代替 8000 基因的对齐。未对齐前不得替换 Formal 正在写的结果。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    for leftover in (matrix_path, OUT / "_align_rcpp.csv"):
        if leftover.exists():
            leftover.unlink()
    print(report.read_text(encoding="utf-8"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
