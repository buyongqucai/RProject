# -*- coding: utf-8 -*-
"""矩形结合能热图（SOP §6 + VizStandards + DockingFrozen）。

- 输入：项目根 summary_adgpu.csv / summary_vina.csv 或 矩阵_结合能_DockingAffinityMatrix.csv
- 输出：矩阵_结合能热图_DockingAffinityHeatmap.png/.svg（DPI≥600）
- 图面 English；行/列/格内数值标签一律黑色 #000000
- 色标：仅非正值（亲和力应为负）；vmin=数据最负侧（稳健裁剪），vmax=0；图例不出现正值
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from dock_summary_schema import load_summary_rows

BLACK = "#000000"
CMAP = "RdBu_r"  # more negative (favorable) → blue; 0 → white/light


def matrix_from_summary(root: Path) -> pd.DataFrame:
    mat = root / "矩阵_结合能_DockingAffinityMatrix.csv"
    if mat.is_file():
        df = pd.read_csv(mat, index_col=0)
        return df.apply(pd.to_numeric, errors="coerce")
    summary = None
    for name in ("summary_adgpu.csv", "summary_vina.csv"):
        p = root / name
        if p.is_file():
            summary = p
            break
    if summary is None:
        raise SystemExit(f"missing summary/matrix under {root}")
    rows = load_summary_rows(summary)
    proteins: list[str] = []
    ligands: list[str] = []
    seen_p, seen_l = set(), set()
    for r in rows:
        if r["protein"] not in seen_p:
            proteins.append(r["protein"])
            seen_p.add(r["protein"])
        name = r.get("ligand_name") or r.get("ligand") or ""
        if name and name not in seen_l:
            ligands.append(name)
            seen_l.add(name)
    grid = pd.DataFrame(np.nan, index=proteins, columns=ligands, dtype=float)
    for r in rows:
        name = r.get("ligand_name") or r.get("ligand") or ""
        grid.loc[r["protein"], name] = float(r["affinity_kcal_mol"])
    return grid


def affinity_scale_limits(finite: np.ndarray) -> tuple[float, float]:
    """Colorbar: vmax fixed at 0 (no positive legend); vmin covers all ≤0 data."""
    vmax = 0.0
    if finite.size == 0:
        return -10.0, vmax
    neg = finite[finite <= 0]
    if neg.size == 0:
        return -10.0, vmax
    # full span of non-positive values so no colorbar extend arrow is needed
    vmin = float(np.nanmin(neg))
    if vmin >= -1e-6:
        vmin = -10.0
    return vmin, vmax


def plot_heatmap(df: pd.DataFrame, out_stem: Path, dpi: int = 600) -> None:
    n_row, n_col = df.shape
    w = max(8.0, 0.95 * n_col + 3.2)
    h = max(5.5, 0.55 * n_row + 2.2)
    fig, ax = plt.subplots(figsize=(w, h))
    vals = df.to_numpy(dtype=float)
    finite = vals[np.isfinite(vals)]
    vmin, vmax = affinity_scale_limits(finite)
    hm = sns.heatmap(
        df,
        ax=ax,
        annot=True,
        fmt=".1f",
        cmap=CMAP,
        vmin=vmin,
        vmax=vmax,
        linewidths=0.4,
        linecolor="#E8E8E8",
        square=False,
        cbar_kws={
            "shrink": 0.8,
            # no title/label; no extend triangles (FROZEN)
        },
        annot_kws={"size": 9, "color": BLACK, "weight": "normal"},
    )
    # FROZEN: no main title / axis titles / colorbar title / footnote
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title("")
    ax.tick_params(colors=BLACK, labelsize=9)
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right", rotation_mode="anchor", color=BLACK)
    plt.setp(ax.get_yticklabels(), rotation=0, color=BLACK)
    cbar = hm.collections[0].colorbar
    cbar.set_label("")
    cbar.ax.tick_params(colors=BLACK, labelsize=9)
    cbar.outline.set_edgecolor("#CCCCCC")
    fig.tight_layout()
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(f"{out_stem}.png", dpi=dpi, bbox_inches="tight", facecolor="white")
    fig.savefig(f"{out_stem}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def write_xlsx(df: pd.DataFrame, path: Path) -> None:
    try:
        df.to_excel(path)
    except Exception:
        pass


def main() -> None:
    ap = argparse.ArgumentParser(description="Docking affinity rectangular heatmap")
    ap.add_argument("--root", required=True, help="docking project root")
    ap.add_argument(
        "--out",
        default=None,
        help="output stem (default: <root>/矩阵_结合能热图_DockingAffinityHeatmap)",
    )
    ap.add_argument("--dpi", type=int, default=600)
    args = ap.parse_args()
    root = Path(args.root)
    df = matrix_from_summary(root)
    out = Path(args.out) if args.out else root / "矩阵_结合能热图_DockingAffinityHeatmap"
    plot_heatmap(df, out, dpi=args.dpi)
    write_xlsx(df, root / "分子对接结合能信息.xlsx")
    mat_path = root / "矩阵_结合能_DockingAffinityMatrix.csv"
    df.to_csv(mat_path, encoding="utf-8-sig")
    print(f"OK heatmap -> {out}.png / .svg  shape={df.shape}")


if __name__ == "__main__":
    main()
