# -*- coding: utf-8 -*-
"""scTenifoldKnk 1.4.3 GPU 原理图：数形结合（PC 子空间 / 张量 / 置零邻接 / 流形位移 / FDR）。"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np

OUT = Path(r"C:\Users\10540\Desktop\婷婷\虚拟敲除\结果文件\_跨亚群\scTenifoldKnk_1.4.3_GPU\图片文件")
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(8096)


def save(fig, stem: str) -> None:
    fig.savefig(OUT / f"{stem}.png", dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / f"{stem}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def panel_pcnet(ax) -> None:
    """基因向量落在 3 维主成分平面上；边权来自 PCR，q=0.9。"""
    n = 80
    pcs = RNG.normal(0, 1.0, size=(n, 2))
    pcs[0] = np.array([-1.6, 1.35])  # AHR
    ax.scatter(pcs[1:, 0], pcs[1:, 1], s=12, c="#A8C0D4", linewidths=0, alpha=0.85, zorder=2)
    ax.scatter(pcs[0, 0], pcs[0, 1], s=70, c="#F4C27A", edgecolors="#C0392B", linewidths=1.2, zorder=4)
    ax.annotate(
        "AHR",
        xy=pcs[0],
        xytext=(pcs[0, 0] + 0.35, pcs[0, 1] + 0.35),
        color="#C0392B",
        fontsize=9,
        fontweight="bold",
        arrowprops=dict(arrowstyle="-", color="#C0392B", lw=0.8),
    )
    t = np.linspace(-2.4, 2.4, 2)
    ax.plot([-2.6, 2.6], [0, 0], color="#DEE2E6", lw=0.8)
    ax.plot([0, 0], [-2.0, 2.0], color="#DEE2E6", lw=0.8)
    ax.annotate(
        "",
        xy=pcs[12],
        xytext=pcs[0],
        arrowprops=dict(arrowstyle="-|>", color="#4A5A6A", lw=1.2),
    )
    ax.text(
        0.98,
        0.97,
        r"$n_{\mathrm{comp}}=3$" "\n" r"$q=0.9$" "\n" r"GPU pcNet",
        transform=ax.transAxes,
        va="top",
        ha="right",
        fontsize=9,
        color="#2C3E50",
        fontweight="bold",
    )
    ax.set_xlim(-2.8, 2.8)
    ax.set_ylim(-2.2, 2.2)
    ax.set_aspect("equal")
    ax.set_xlabel(r"PC$_1$ of gene vectors")
    ax.set_ylabel(r"PC$_2$")
    ax.set_title("② pcNet 1.4.3: edges from a 3-PC subspace", fontsize=11, fontweight="bold")


def panel_tensor(ax) -> None:
    """10 张网叠成三阶张量，CP 秩 3。"""
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ax.set_title(r"③ Tensor: 10 nets $\times$ CP rank $K=3$", fontsize=11, fontweight="bold")
    # stacked slices
    cmap = plt.cm.YlOrBr
    for i, (dx, dy) in enumerate([(0.0, 0.0), (0.55, 0.45), (1.1, 0.9)]):
        x0, y0 = 1.3 + dx, 1.4 + dy
        w, h = 3.2, 3.2
        grid = RNG.random((6, 6)) * 0.7 + 0.15
        for r in range(6):
            for c in range(6):
                ax.add_patch(
                    Rectangle(
                        (x0 + c * w / 6, y0 + (5 - r) * h / 6),
                        w / 6,
                        h / 6,
                        facecolor=cmap(grid[r, c]),
                        edgecolor="white",
                        lw=0.3,
                        zorder=1 + i,
                    )
                )
        ax.add_patch(Rectangle((x0, y0), w, h, fill=False, edgecolor="#2C3E50", lw=1.1, zorder=5))
    ax.text(5.1, 5.7, r"$\mathcal{T}\in\mathbb{R}^{g\times g\times 10}$", fontsize=11, fontweight="bold")
    ax.text(5.6, 3.6, "10 cell\nsubsamples\n$n_c=500$", fontsize=9, color="#444")
    # CP bars
    ax.text(7.35, 6.2, "CP factors", fontsize=9, fontweight="bold")
    for j, (lab, hgt) in enumerate([("λ1", 2.4), ("λ2", 1.6), ("λ3", 1.05)]):
        ax.add_patch(Rectangle((7.5 + j * 0.7, 1.5), 0.5, hgt, facecolor="#6B8F71", edgecolor="#2C3E50", lw=0.8))
        ax.text(7.75 + j * 0.7, 1.25, lab, ha="center", fontsize=8)
    ax.text(7.35, 0.45, r"$K=3$  (td_K)", fontsize=9, color="#555")


def panel_ko_matrix(ax) -> None:
    names = ["AHR", "G1", "G2", "G3", "G4"]
    n = len(names)
    W = RNG.uniform(0.08, 1.0, size=(n, n))
    np.fill_diagonal(W, 0)
    W = (W + W.T) / 2
    W_ko = W.copy()
    W_ko[0, :] = 0.0  # outgoing from AHR
    im = ax.imshow(W_ko, cmap="YlOrBr", vmin=0, vmax=1)
    for i in range(n):
        for j in range(n):
            if i == 0 and j != 0:
                ax.text(j, i, "0", ha="center", va="center", color="#C0392B", fontsize=10, fontweight="bold")
            elif i != j:
                ax.text(j, i, f"{W_ko[i, j]:.1f}", ha="center", va="center", fontsize=8, color="#333")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(names, fontsize=9)
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel("to")
    ax.set_ylabel("from")
    ax.set_title("① Virtual KO: AHR outgoing weights → 0", fontsize=11, fontweight="bold")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04).set_label(r"$|w|$", fontsize=9)
    ax.text(0.5, -0.22, r"WT tensor vs KO tensor; $X$ unchanged", transform=ax.transAxes, ha="center", fontsize=9, color="#555")


def panel_manifold(ax) -> None:
    """流形对齐后每个基因一个点；位移向量即 dRegulation 的几何。"""
    n = 40
    wt = RNG.normal(0, 0.55, size=(n, 2))
    # Procrustes-like rotation of KO cloud + gene-specific shift
    theta = np.deg2rad(18)
    R = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    ko = (wt @ R.T) + RNG.normal(0, 0.08, size=wt.shape)
    ko[0] = wt[0] + np.array([1.35, -0.95])  # AHR large jump
    ko[3] = wt[3] + np.array([0.85, 0.15])
    ax.scatter(wt[:, 0], wt[:, 1], s=16, c="#5B8FA8", alpha=0.55, linewidths=0, label="WT embedding")
    ax.scatter(ko[:, 0], ko[:, 1], s=16, c="#C17B7B", alpha=0.6, linewidths=0, label="KO after align")
    for i in (0,):
        ax.annotate("", xy=ko[i], xytext=wt[i], arrowprops=dict(arrowstyle="-|>", color="#C0392B", lw=1.6))
    d_ahr = float(np.linalg.norm(ko[0] - wt[0]))
    ax.text(
        (wt[0, 0] + ko[0, 0]) / 2 + 0.15,
        (wt[0, 1] + ko[0, 1]) / 2,
        rf"$\|d_{{\mathrm{{AHR}}}}\|={d_ahr:.2f}$",
        color="#C0392B",
        fontsize=10,
        fontweight="bold",
    )
    ax.axhline(0, color="#DEE2E6", lw=0.8)
    ax.axvline(0, color="#DEE2E6", lw=0.8)
    ax.set_aspect("equal")
    ax.set_xlabel(r"aligned manifold $u_1$")
    ax.set_ylabel(r"$u_2$")
    ax.set_title("④ Manifold align: gene shift = DR distance", fontsize=11, fontweight="bold")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_xlim(-2.2, 2.6)
    ax.set_ylim(-2.4, 2.2)


def panel_fdr(ax) -> None:
    null = np.abs(RNG.normal(0, 0.12, size=2500))
    null = null + RNG.exponential(0.04, size=2500) * 0.2
    obs_hit = 1.15
    ax.hist(null, bins=42, color="#D5D9DE", edgecolor="white", linewidth=0.3, label="DR distances (all genes)")
    ax.axvline(obs_hit, color="#C0392B", lw=2.0, label=r"example passer  FDR $<0.05$")
    # chi-square-ish tail mark
    q = np.quantile(null, 0.995)
    ax.axvline(q, color="#E67E22", lw=1.6, linestyle="--", label="FDR 0.05 tail (schematic)")
    ax.set_xlabel("dRegulation distance")
    ax.set_ylabel("count")
    ax.set_title("⑤ Number on the line: FDR, not a flowchart box", fontsize=11, fontweight="bold")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.text(
        0.55,
        0.62,
        r"$p_{\mathrm{adj}}<0.05$" "\nthen GO/KEGG hsa",
        transform=ax.transAxes,
        fontsize=9,
        color="#C0392B",
        fontweight="bold",
    )


def panel_nets(ax, zero: bool, title: str) -> None:
    nodes = {
        "AHR": (0.28, 0.55),
        "G1": (0.62, 0.82),
        "G2": (0.82, 0.55),
        "G3": (0.68, 0.22),
        "G4": (0.35, 0.18),
    }
    edges = [("AHR", "G1"), ("AHR", "G2"), ("AHR", "G3"), ("G1", "G2"), ("G2", "G3"), ("G3", "G4"), ("G4", "AHR")]
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=11, fontweight="bold", pad=4)
    for a, b in edges:
        x1, y1 = nodes[a]
        x2, y2 = nodes[b]
        kill = zero and a == "AHR"
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(
                arrowstyle="-|>",
                color="#C0392B" if kill else "#4A5A6A",
                lw=2.0 if kill else 1.1,
                linestyle=(0, (3, 2)) if kill else "solid",
                mutation_scale=11,
            ),
        )
        if kill:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mx, my + 0.04, "0", color="#C0392B", fontsize=9, ha="center", fontweight="bold")
    for name, (x, y) in nodes.items():
        face = "#F4C27A" if name == "AHR" else "#DCE6F0"
        edge = "#C0392B" if name == "AHR" and zero else "#2C3E50"
        ax.add_patch(Circle((x, y), 0.09, facecolor=face, edgecolor=edge, lw=1.7, zorder=3))
        ax.text(x, y, name, ha="center", va="center", fontsize=8, fontweight="bold", zorder=4)


def main() -> None:
    fig = plt.figure(figsize=(14.6, 12.4))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.15, 1.15], hspace=0.38, wspace=0.28)
    fig.suptitle(
        "scTenifoldKnk 1.4.3 GPU — numbers live inside the geometry",
        fontsize=17,
        fontweight="bold",
        y=0.985,
    )
    fig.text(
        0.5,
        0.955,
        "GSE175817 · lesional macrophages · target AHR  |  "
        "Osorio et al. Patterns 2022; pcNet 1.4.3 on GPU  |  Self-drawn schematic (not a paper figure)",
        ha="center",
        va="top",
        fontsize=9.5,
        color="#5a6573",
    )

    ax1 = fig.add_subplot(gs[0, 0])
    panel_nets(ax1, False, "WT GRN (one of 10 nets)")
    ax2 = fig.add_subplot(gs[0, 1])
    panel_ko_matrix(ax2)
    ax3 = fig.add_subplot(gs[1, 0])
    panel_pcnet(ax3)
    ax4 = fig.add_subplot(gs[1, 1])
    panel_tensor(ax4)
    ax5 = fig.add_subplot(gs[2, 0])
    panel_manifold(ax5)
    ax6 = fig.add_subplot(gs[2, 1])
    panel_fdr(ax6)

    fig.text(
        0.5,
        0.012,
        "Lab numbers: 10 nets · n_cells=min(500,n−1) · n_comp=3 · q=0.9 · td_K=3 · FDR<0.05 → GO/KEGG hsa (BH p<.05 q<.2).  "
        "Response genes ≠ Seurat DEG. Computational prediction only.",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#5a6573",
    )
    save(fig, "01_方法示意_scTenifoldKnk_143GPU")
    print("WROTE", OUT / "01_方法示意_scTenifoldKnk_143GPU.png")


if __name__ == "__main__":
    main()
