# -*- coding: utf-8 -*-
"""只画 GenKI 方法示意（Yang NAR 2023 Fig.1）。

琪乐无穷 scTenifoldKnk 示意图禁止由此脚本覆盖：沿用五亚群留档
`01_方法示意_scTenifoldKnkWorkflow.jpg`（Osorio Patterns 2022 结构，非重绘）。
婷婷 Knk 共用该 jpg。
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
import numpy as np

NAVY = "#1B365D"
TEAL = "#2E8A9A"
BLUE = "#4A90C4"
BLUE_LT = "#A8CDE0"
BLUE_PALE = "#D7E8F3"
GREY = "#C8CED4"
GREY_DK = "#6B7380"
PANEL_FACE = "#F7FBFE"
PANEL_EDGE = "#8FB3D1"
KO_RED = "#C45C5C"
RNG = np.random.default_rng(8096)


def save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".png"), dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(path.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    try:
        fig.savefig(path.with_suffix(".jpg"), dpi=400, bbox_inches="tight", facecolor="white", pil_kwargs={"quality": 92})
    except Exception:
        pass
    print("WROTE", path.with_suffix(".png"))


def rounded(ax, x, y, w, h, **kw):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.012,rounding_size=0.08",
            facecolor=kw.get("fc", PANEL_FACE),
            edgecolor=kw.get("ec", PANEL_EDGE),
            lw=kw.get("lw", 1.6),
            zorder=0,
        )
    )


def arrow(ax, x1, y1, x2, y2, color=NAVY, lw=1.8):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="-|>",
            mutation_scale=12,
            lw=lw,
            color=color,
            zorder=5,
        )
    )


def heatmap(ax, x, y, w, h, nr, nc, cmap="Blues", zero_row=None, zero_col=None, vmin=0.15, vmax=0.95):
    grid = RNG.uniform(vmin, vmax, size=(nr, nc))
    if zero_row is not None:
        grid[zero_row, :] = 0.04
    if zero_col is not None:
        grid[:, zero_col] = grid[:, zero_col] * 0.35
    for i in range(nr):
        for j in range(nc):
            if zero_row is not None and i == zero_row:
                color = GREY
            else:
                color = matplotlib.colormaps[cmap](grid[i, j])
            ax.add_patch(
                Rectangle(
                    (x + j * w / nc, y + (nr - 1 - i) * h / nr),
                    w / nc,
                    h / nr,
                    facecolor=color,
                    edgecolor="white",
                    lw=0.25,
                    zorder=2,
                )
            )
    ax.add_patch(Rectangle((x, y), w, h, fill=False, edgecolor=NAVY, lw=0.9, zorder=3))


def cube(ax, x, y, s=0.72):
    dx, dy = 0.22 * s, 0.18 * s
    front = [(x, y), (x + s, y), (x + s, y + s), (x, y + s)]
    top = [(x, y + s), (x + s, y + s), (x + s + dx, y + s + dy), (x + dx, y + s + dy)]
    side = [(x + s, y), (x + s + dx, y + dy), (x + s + dx, y + s + dy), (x + s, y + s)]
    ax.add_patch(Polygon(front, closed=True, facecolor="#7EB6D9", edgecolor=NAVY, lw=0.9, zorder=3))
    ax.add_patch(Polygon(top, closed=True, facecolor="#C5DDF0", edgecolor=NAVY, lw=0.9, zorder=3))
    ax.add_patch(Polygon(side, closed=True, facecolor="#4A90C4", edgecolor=NAVY, lw=0.9, zorder=3))
    for k in range(1, 4):
        yy = y + k * s / 4
        ax.plot([x, x + s], [yy, yy], color="white", lw=0.4, zorder=4)
        ax.plot([x + s, x + s + dx], [yy, yy + dy], color="white", lw=0.35, zorder=4)


def mini_net(ax, cx, cy, r=0.42, kill=None, teal=True):
    pts = {
        0: (cx - 0.28, cy + 0.05),
        1: (cx + 0.02, cy + 0.28),
        2: (cx + 0.32, cy + 0.02),
        3: (cx + 0.08, cy - 0.28),
        4: (cx - 0.22, cy - 0.24),
    }
    edges = [(0, 1), (0, 2), (0, 3), (1, 2), (2, 3), (3, 4), (4, 0)]
    fill = TEAL if teal else BLUE
    for a, b in edges:
        x1, y1 = pts[a]
        x2, y2 = pts[b]
        dead = kill is not None and a == kill
        ax.plot(
            [x1, x2],
            [y1, y2],
            color=KO_RED if dead else fill,
            lw=1.7 if dead else 1.15,
            ls=(0, (2.5, 1.4)) if dead else "solid",
            zorder=2,
        )
        if dead:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.04, "0", color=KO_RED, fontsize=6.5, ha="center", fontweight="bold", zorder=4)
    for i, (x, y) in pts.items():
        ax.add_patch(
            Circle((x, y), 0.055, facecolor="#F4C27A" if i == 0 else fill, edgecolor=NAVY, lw=0.8, zorder=3, alpha=0.95 if i else 0.88)
        )


def panel_label(ax, x, y, letter, title):
    ax.add_patch(Circle((x, y), 0.16, facecolor=NAVY, edgecolor=NAVY, zorder=6))
    ax.text(x, y, letter, color="white", ha="center", va="center", fontsize=11, fontweight="bold", zorder=7)
    ax.text(x + 0.24, y, title, color=NAVY, ha="left", va="center", fontsize=12.5, fontweight="bold", zorder=7)


def caption(ax, x, y, text, size=7.2, color=GREY_DK, ha="center"):
    ax.text(x, y, text, fontsize=size, color=color, ha=ha, va="top", linespacing=1.25)


def draw_knk(path: Path, gene: str, dataset: str, extra: str) -> None:
    fig, ax = plt.subplots(figsize=(14.6, 6.85))
    ax.set_xlim(0, 14.6)
    ax.set_ylim(0, 6.85)
    ax.axis("off")
    ax.text(7.3, 6.68, "scTenifoldKnk 1.4.3 GPU virtual KO (schematic)", ha="center", va="top", fontsize=16.5, fontweight="bold", color=NAVY)
    ax.text(7.3, 6.38, extra, ha="center", va="top", fontsize=8.2, color=GREY_DK)

    # A — one horizontal pipeline, matching the gold panel
    rounded(ax, 0.16, 0.38, 5.42, 5.68)
    panel_label(ax, 0.46, 5.72, "A", "Network construction")
    y0 = 2.55
    heatmap(ax, 0.32, y0, 0.92, 2.15, 7, 5, cmap="Blues")
    ax.text(0.20, y0 + 2.05, "Gene 1", fontsize=6.0, color=NAVY, ha="right")
    ax.text(0.20, y0 + 0.05, "Gene n", fontsize=6.0, color=NAVY, ha="right")
    caption(ax, 0.78, y0 - 0.08, "gene × cell", 6.8)
    arrow(ax, 1.30, y0 + 1.05, 1.52, y0 + 1.05)
    ax.add_patch(Rectangle((1.56, y0 + 0.15), 0.88, 1.95, fill=False, ls="--", edgecolor=TEAL, lw=1.05))
    heatmap(ax, 1.64, y0 + 1.15, 0.70, 0.82, 4, 4, cmap="Blues")
    heatmap(ax, 1.70, y0 + 0.28, 0.70, 0.82, 4, 4, cmap="Blues")
    caption(ax, 2.00, y0 - 0.08, "subsample ×10", 6.8)
    arrow(ax, 2.50, y0 + 1.05, 2.70, y0 + 1.05)
    for i, yy in enumerate((y0 + 1.55, y0 + 0.95, y0 + 0.35)):
        heatmap(ax, 2.78, yy, 0.48, 0.50, 3, 3, cmap="Greens")
    caption(ax, 3.02, y0 - 0.08, r"PC $n_{comp}=3$", 6.8)
    arrow(ax, 3.32, y0 + 1.05, 3.50, y0 + 1.05)
    cube(ax, 3.56, y0 + 0.55, 0.92)
    caption(ax, 4.10, y0 - 0.08, r"tensor $T$, $K=3$", 6.8)
    arrow(ax, 4.72, y0 + 1.05, 4.90, y0 + 1.05)
    heatmap(ax, 4.96, y0 + 0.45, 0.48, 1.20, 6, 6, cmap="Blues")
    caption(ax, 5.20, y0 - 0.08, r"$W_d$ WT scGRN", 6.8)

    # B
    rounded(ax, 5.72, 0.38, 3.95, 5.68)
    panel_label(ax, 6.02, 5.72, "B", "Virtual KO")
    ax.text(7.70, 5.38, r"copy of WT adjacency $W_d$", fontsize=8.0, color=NAVY, ha="center")
    ax.add_patch(Rectangle((5.92, 4.95), 0.22, 0.18, fc=BLUE, ec=NAVY, lw=0.4))
    ax.text(6.20, 5.04, "WT edge", fontsize=6.8, va="center", color=NAVY)
    ax.add_patch(Rectangle((6.95, 4.95), 0.22, 0.18, fc=GREY, ec=NAVY, lw=0.4))
    ax.text(7.23, 5.04, "zeroed outgoing", fontsize=6.8, va="center", color=NAVY)
    heatmap(ax, 6.55, 3.15, 1.70, 1.70, 8, 8, cmap="Blues")
    caption(ax, 7.40, 3.05, f"KO gene (e.g. {gene})", 7.2)
    arrow(ax, 7.40, 2.98, 7.40, 2.62)
    heatmap(ax, 6.55, 0.72, 1.70, 1.70, 8, 8, cmap="Blues", zero_row=2)
    ax.text(8.35, 1.57, "zero outward\nedges of " + gene, fontsize=7.0, color=KO_RED, fontweight="bold", va="center")
    caption(ax, 7.40, 0.62, rf"$W_d({gene})$  pseudo-KO", 7.0)

    # C
    rounded(ax, 9.82, 0.38, 4.58, 5.68)
    panel_label(ax, 10.12, 5.72, "C", "Manifold alignment")
    ax.text(10.70, 5.32, "WT scGRN", fontsize=7.8, color=TEAL, ha="center")
    ax.text(13.05, 5.32, "pseudo-KO scGRN", fontsize=7.8, color=TEAL, ha="center")
    mini_net(ax, 10.70, 4.42, kill=None)
    mini_net(ax, 13.05, 4.42, kill=0)
    ax.plot([11.45, 12.30], [4.95, 4.95], color=GREY_DK, ls="--", lw=0.8)
    arrow(ax, 11.88, 4.05, 11.88, 3.58)
    caption(ax, 11.88, 3.52, "aligned latent space (paired genes)", 7.0)
    xs = np.linspace(10.20, 13.20, 9)
    ys = 3.05 + 0.07 * np.array([0, 1, -1, 0.5, 0, -0.4, 0.7, -0.2, 0.1])
    ax.scatter(xs, ys, s=26, c=TEAL, zorder=4, edgecolors=NAVY, linewidths=0.35)
    ax.annotate("", xy=(13.42, ys.max() + 0.06), xytext=(13.42, ys.min() - 0.06),
                arrowprops=dict(arrowstyle="<->", color=NAVY, lw=1.05))
    ax.text(13.52, 3.05, r"$d_j$", fontsize=11, fontweight="bold", color=NAVY, va="center")
    arrow(ax, 11.88, 2.78, 11.88, 2.42)
    caption(ax, 11.88, 2.36, "ranked gene list (dRegulation)", 7.2)
    for i, g in enumerate(np.linspace(0, 1, 80)):
        ax.add_patch(Rectangle((10.20 + i * 3.25 / 80, 1.95), 3.25 / 80, 0.20, facecolor=matplotlib.colormaps["GnBu"](g), lw=0, zorder=3))
    ax.add_patch(Rectangle((10.20, 1.95), 3.25, 0.20, fill=False, edgecolor=NAVY, lw=0.7, zorder=4))
    ax.text(10.20, 1.82, "rank 1", fontsize=6.8, color=NAVY, ha="left")
    ax.text(13.45, 1.82, "rank p", fontsize=6.8, color=NAVY, ha="right")
    heatmap(ax, 10.25, 0.58, 0.88, 0.88, 5, 5, cmap="Blues")
    ax.text(11.28, 1.18, r"$\chi^2$ / FDR", fontsize=9, fontweight="bold", color=NAVY, va="center")
    ax.text(11.28, 0.82, "significant DR genes\nFDR < 0.05", fontsize=7.0, color=GREY_DK, va="center")
    xs2 = 13.05 + 0.16 * RNG.normal(0, 1, 10)
    ys2 = 0.95 + 0.14 * RNG.normal(0, 1, 10)
    ax.scatter(xs2, ys2, s=12, c=TEAL, zorder=4, edgecolors=NAVY, linewidths=0.3)

    ax.text(7.3, 0.16, f"{dataset}  ·  Adapted structurally from Osorio et al., Patterns 2022; not a paper figure.  Computational prediction only.", ha="center", fontsize=7.8, color=GREY_DK)
    save(fig, path)
    plt.close(fig)


def draw_genki(path: Path, gene: str, dataset: str, extra: str, enrich_sp: str) -> None:
    fig, ax = plt.subplots(figsize=(14.6, 6.85))
    ax.set_xlim(0, 14.6)
    ax.set_ylim(0, 6.85)
    ax.axis("off")
    ax.text(7.2, 6.68, "GenKI virtual KO (schematic, after Yang et al. NAR 2023 Fig. 1)", ha="center", va="top", fontsize=15.5, fontweight="bold", color=NAVY)
    ax.text(7.3, 6.38, extra, ha="center", va="top", fontsize=8.2, color=GREY_DK)

    # A GRN
    rounded(ax, 0.18, 0.42, 4.55, 5.85)
    panel_label(ax, 0.48, 5.92, "A", "GRN from PCR")
    heatmap(ax, 0.45, 3.85, 1.15, 1.75, 6, 5, cmap="Blues")
    caption(ax, 1.02, 3.72, "gene × cell  $X$\nHVG = 3,000", 7.2)
    arrow(ax, 1.72, 4.70, 2.05, 4.70)
    heatmap(ax, 2.15, 3.85, 1.55, 1.55, 7, 7, cmap="YlOrBr")
    caption(ax, 2.92, 3.72, "PC regression weights", 7.2)
    # |w| histogram geometry
    w = np.abs(RNG.normal(0, 0.35, 400))
    bins = np.linspace(0, 1.2, 18)
    hist, edges = np.histogram(w, bins=bins)
    hist = hist / hist.max() * 1.15
    bx0, by0, bw, bh = 0.55, 0.85, 3.55, 2.15
    ax.add_patch(Rectangle((bx0, by0), bw, bh, fill=False, edgecolor=NAVY, lw=0.8))
    cut_i = int(0.85 * (len(hist) - 1))
    for i, h in enumerate(hist):
        xx = bx0 + 0.12 + i * (bw - 0.24) / len(hist)
        ax.add_patch(Rectangle((xx, by0 + 0.2), (bw - 0.3) / len(hist) * 0.9, h, fc=BLUE_LT if i < cut_i else KO_RED, lw=0, zorder=3))
    cut_x = bx0 + 0.12 + cut_i * (bw - 0.24) / len(hist)
    ax.plot([cut_x, cut_x], [by0 + 0.18, by0 + bh - 0.15], color=KO_RED, lw=1.4)
    ax.text(cut_x + 0.08, by0 + bh - 0.28, r"$q_{0.85}$ keep top 15%", fontsize=7.2, color=KO_RED, fontweight="bold")
    caption(ax, bx0 + bw / 2, 0.72, r"boolean graph: keep $|w|$ above 85th percentile", 7.2)

    # B KO + latent
    rounded(ax, 4.92, 0.42, 4.55, 5.85)
    panel_label(ax, 5.22, 5.92, "B", "Virtual KO in latent space")
    heatmap(ax, 5.25, 3.85, 1.65, 1.65, 7, 7, cmap="YlOrBr", zero_row=0, zero_col=0)
    ax.text(7.05, 4.95, f"{gene} edges\nfrom & to → 0", fontsize=7.6, color=KO_RED, fontweight="bold")
    caption(ax, 6.08, 3.72, r"same $X$; only graph $A$ changes", 7.2)
    # 2D gaussians
    ax.add_patch(Rectangle((5.25, 0.72), 3.85, 2.55, fill=False, edgecolor=NAVY, lw=0.8))
    # WT ellipse
    from matplotlib.patches import Ellipse

    ax.add_patch(Ellipse((6.15, 2.05), 1.15, 0.85, facecolor=BLUE, alpha=0.18, edgecolor=BLUE, lw=1.3))
    ax.add_patch(Ellipse((7.85, 1.35), 1.25, 0.9, facecolor=KO_RED, alpha=0.16, edgecolor=KO_RED, lw=1.3))
    pts_w = RNG.normal([6.15, 2.05], 0.18, size=(28, 2))
    pts_k = RNG.normal([7.85, 1.35], 0.20, size=(28, 2))
    ax.scatter(pts_w[:, 0], pts_w[:, 1], s=8, c=BLUE, zorder=4, linewidths=0)
    ax.scatter(pts_k[:, 0], pts_k[:, 1], s=8, c=KO_RED, zorder=4, linewidths=0)
    arrow(ax, 6.55, 1.90, 7.45, 1.50, color=KO_RED, lw=1.6)
    ax.text(6.95, 1.82, r"$KL(q_{KO}\|q_{WT})$", fontsize=8.5, color=KO_RED, fontweight="bold")
    ax.text(5.55, 2.55, r"$q_{WT}=N(\mu,\sigma^2 I)$  ·  2-D VGAE", fontsize=7.2, color=NAVY)
    caption(ax, 7.18, 0.68, "each gene is a 2-D Gaussian; score = KL", 7.2)

    # C null
    rounded(ax, 9.65, 0.42, 4.55, 5.85)
    panel_label(ax, 9.95, 5.92, "C", "Null geometry and hit rule")
    null = np.abs(RNG.normal(0, 0.08, 800)) + RNG.exponential(0.03, 800) * 0.25
    bins = np.linspace(0, 0.55, 22)
    hist, edges = np.histogram(null, bins=bins)
    hist = hist / hist.max() * 2.15
    hx0, hy0 = 9.95, 3.35
    ax.add_patch(Rectangle((hx0, hy0), 3.95, 2.35, fill=False, edgecolor=NAVY, lw=0.8))
    for i, h in enumerate(hist):
        xx = hx0 + 0.15 + i * 3.65 / len(hist)
        ax.add_patch(Rectangle((xx, hy0 + 0.22), 3.5 / len(hist) * 0.9, h, fc=GREY, lw=0, zorder=3))
    q = np.quantile(null, 0.95)
    qx = hx0 + 0.15 + (q / 0.55) * 3.65
    ax.plot([qx, qx], [hy0 + 0.2, hy0 + 2.15], color="#E07A2F", lw=1.5, ls="--")
    obsx = hx0 + 0.15 + min(0.48 / 0.55, 0.92) * 3.65
    ax.plot([obsx, obsx], [hy0 + 0.2, hy0 + 2.15], color=KO_RED, lw=1.8)
    ax.text(qx + 0.06, hy0 + 2.08, "top 5%", fontsize=7, color="#E07A2F", fontweight="bold")
    ax.text(obsx, hy0 + 2.20, "observed KL", fontsize=7, color=KO_RED, fontweight="bold", ha="center")
    caption(ax, 11.92, 3.22, "1,000 no-replace permutations of cell order", 7.2)

    ax.add_patch(FancyBboxPatch((9.95, 1.55), 3.95, 1.40, boxstyle="round,pad=0.02,rounding_size=0.06", fc="#F8EEEE", ec=KO_RED, lw=1.1))
    ax.text(11.92, 2.62, "Pass if both", ha="center", fontsize=9, fontweight="bold", color=NAVY)
    ax.text(11.92, 2.22, r"KL in top 5% of a replicate", ha="center", fontsize=8.2, color=NAVY)
    ax.text(11.92, 1.88, r"AND  hit $>950/1000$  (95%)", ha="center", fontsize=8.2, color=NAVY)

    ax.add_patch(FancyBboxPatch((9.95, 0.58), 3.95, 0.82, boxstyle="round,pad=0.02,rounding_size=0.06", fc=BLUE_PALE, ec=PANEL_EDGE, lw=1.0))
    ax.text(11.92, 1.12, f"then GO BP/CC/MF + KEGG {enrich_sp}", ha="center", fontsize=8.0, color=NAVY)
    ax.text(11.92, 0.82, r"BH $p<0.05$, $q<0.2$  ·  KO gene itself excluded", ha="center", fontsize=7.2, color=GREY_DK)

    ax.text(
        7.2,
        0.18,
        f"{dataset}  ·  After Yang et al., NAR 2023; Kipf & Welling 2016. Self-drawn — not a paper figure.  Computational prediction only.",
        ha="center",
        fontsize=8.0,
        color=GREY_DK,
    )
    save(fig, path)
    plt.close(fig)


def main() -> None:
    """琪乐无穷 Knk 示意图禁止重绘：沿用五亚群留档 Osorio 结构图。

    本脚本只画 GenKI（按 Yang NAR 2023 Fig.1 七步：WT scGRN → VGAE →
    边置零 → KL → bagging），栏式对齐那张 Knk 金标。
    """
    import shutil

    gold_knk = Path(r"C:\Users\10540\Desktop\琪乐无穷\五亚群留档\结果文件\_跨亚群\scTenifoldKnk\图片文件\01_方法示意_scTenifoldKnkWorkflow.jpg")
    qile_knk_dir = Path(r"C:\Users\10540\Desktop\琪乐无穷\虚拟敲除\结果文件\_跨亚群\scTenifoldKnk_1.4.3_GPU\图片文件")
    tt_knk_dir = Path(r"C:\Users\10540\Desktop\婷婷\虚拟敲除\结果文件\_跨亚群\scTenifoldKnk_1.4.3_GPU\图片文件")
    tt09 = Path(r"E:\RProject\婷婷\痤疮_巨噬细胞极化机制\09_虚拟敲除_GSE175817\图片")
    qile_gk = Path(r"C:\Users\10540\Desktop\琪乐无穷\虚拟敲除\结果文件\_跨亚群\GenKI\图片文件\01_方法示意_GenKIVgaeWorkflow")
    tt_gk = Path(r"C:\Users\10540\Desktop\婷婷\虚拟敲除\结果文件\_跨亚群\GenKI\图片文件\01_方法示意_GenKIVgaeWorkflow")

    if gold_knk.exists():
        qile_knk_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(gold_knk, qile_knk_dir / "01_方法示意_scTenifoldKnkWorkflow.jpg")
        # 婷婷 Knk / GenKI / 部位图已换成成图，这里不再覆盖。

    draw_genki(
        qile_gk,
        gene="Cplx2",
        dataset="GSE197289  ·  mouse TG Control  ·  PEP / NF1",
        extra="Yang et al. NAR 2023 Fig.1  ·  VGAE 2-layer GCN + inner-product decoder  ·  2-D Gaussian latents",
        enrich_sp="mmu",
    )


if __name__ == "__main__":
    # Matplotlib 3.9+: get_cmap via matplotlib.colormaps
    if not hasattr(plt.cm, "get_cmap"):
        plt.cm.get_cmap = lambda name: matplotlib.colormaps[name]
    main()
