# -*- coding: utf-8 -*-
"""GenKI 原理图：数形结合（边权分布 / 邻接截断 / 二维高斯 / KL 几何 / 排列阈）。"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Rectangle
from matplotlib.collections import LineCollection
import numpy as np

OUT = Path(r"C:\Users\10540\Desktop\婷婷\虚拟敲除\结果文件\_跨亚群\GenKI\图片文件")
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(8096)


def save(fig, stem: str) -> None:
    fig.savefig(OUT / f"{stem}.png", dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / f"{stem}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def panel_edge_weights(ax) -> None:
    """边权 |w| 直方图 + 85% 分位截断线（top 15% 保留）。"""
    w = np.abs(RNG.normal(0, 0.35, size=8000))
    w = np.clip(w, 0, None)
    cut = np.quantile(w, 0.85)
    ax.hist(w, bins=48, color="#A8C0D4", edgecolor="white", linewidth=0.4)
    ax.axvline(cut, color="#C0392B", lw=2.0, label=rf"$q_{{0.85}}=${cut:.2f}")
    ax.fill_betweenx([0, ax.get_ylim()[1] or 1], cut, w.max(), color="#C0392B", alpha=0.12)
    ax.set_xlabel(r"edge weight $|w|$")
    ax.set_ylabel("count")
    ax.set_title("① Keep top 15% |w|  (cutoff at 85th percentile)", fontsize=11, fontweight="bold")
    ax.legend(frameon=False, loc="upper right", fontsize=9)
    ax.text(
        0.98,
        0.55,
        "keep →\nsolid edges",
        transform=ax.transAxes,
        ha="right",
        va="center",
        fontsize=9,
        color="#C0392B",
        fontweight="bold",
    )


def panel_adj_ko(ax) -> None:
    """5×5 邻接示意：WT 全连 vs KO 将 AHR 出边置 0。"""
    names = ["AHR", "G1", "G2", "G3", "G4"]
    n = len(names)
    # synthetic absolute weights
    W = RNG.uniform(0.05, 1.0, size=(n, n))
    np.fill_diagonal(W, 0)
    W = (W + W.T) / 2
    # zero AHR outgoing in KO view (row 0)
    W_ko = W.copy()
    W_ko[0, :] = 0.0

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
    ax.set_title("② Virtual KO: AHR → · weights set to 0", fontsize=11, fontweight="bold")
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(r"$|w|$", fontsize=9)
    ax.text(
        0.5,
        -0.22,
        r"same expression $X$; only graph $A$ changes",
        transform=ax.transAxes,
        ha="center",
        fontsize=9,
        color="#555",
    )


def panel_latent_kl(ax) -> None:
    """二维高斯：WT vs KO，箭头标 KL，椭圆=1σ。"""
    mu_w = np.array([0.2, 0.15])
    mu_k = np.array([1.65, -1.05])
    sig_w, sig_k = 0.55, 0.70
    # sample clouds
    pts_w = RNG.normal(mu_w, sig_w * 0.55, size=(55, 2))
    pts_k = RNG.normal(mu_k, sig_k * 0.55, size=(55, 2))
    ax.scatter(pts_w[:, 0], pts_w[:, 1], s=14, c="#5B8FA8", alpha=0.55, linewidths=0, zorder=2)
    ax.scatter(pts_k[:, 0], pts_k[:, 1], s=14, c="#C17B7B", alpha=0.6, linewidths=0, zorder=2)
    ax.add_patch(Ellipse(mu_w, 2.2 * sig_w, 1.7 * sig_w, facecolor="#5B8FA8", alpha=0.15, edgecolor="#5B8FA8", lw=1.6))
    ax.add_patch(Ellipse(mu_k, 2.2 * sig_k, 1.7 * sig_k, facecolor="#C17B7B", alpha=0.15, edgecolor="#C17B7B", lw=1.6))
    ax.plot(*mu_w, "o", color="#2C5F7C", ms=7, zorder=3)
    ax.plot(*mu_k, "o", color="#8B2E2E", ms=7, zorder=3)
    ax.annotate(
        "",
        xy=mu_k,
        xytext=mu_w,
        arrowprops=dict(arrowstyle="-|>", color="#C0392B", lw=2.0, mutation_scale=14),
    )
    mid = (mu_w + mu_k) / 2
    # analytic 1-D style KL for display (isotropic approx)
    kl_show = 0.5 * (
        (sig_w**2 / sig_k**2)
        + ((mu_k - mu_w) ** 2).sum() / (sig_k**2)
        - 2
        + 2 * np.log(sig_k / sig_w)
    )
    ax.text(
        mid[0] + 0.15,
        mid[1] + 0.55,
        rf"$KL\!\left(q_{{\mathrm{{KO}}}}\,\|\,q_{{\mathrm{{WT}}}}\right)\approx{kl_show:.2f}$",
        color="#C0392B",
        fontsize=11,
        fontweight="bold",
    )
    ax.text(mu_w[0] - 0.15, mu_w[1] + 0.95, r"$q_{WT}=N(\mu,\sigma^2 I)$", color="#2C5F7C", fontsize=9)
    ax.text(mu_k[0] - 0.1, mu_k[1] - 1.05, r"$q_{KO}$", color="#8B2E2E", fontsize=10, fontweight="bold")
    ax.axhline(0, color="#DEE2E6", lw=0.8)
    ax.axvline(0, color="#DEE2E6", lw=0.8)
    ax.set_xlim(-1.6, 3.2)
    ax.set_ylim(-2.4, 2.0)
    ax.set_aspect("equal")
    ax.set_xlabel(r"latent $z_1$")
    ax.set_ylabel(r"latent $z_2$")
    ax.set_title("③ VGAE: each gene → 2-D Gaussian; score = KL", fontsize=11, fontweight="bold")


def panel_null_rule(ax) -> None:
    """排列零分布 + top5% 阈值 + hit>95% 示意条。"""
    null = np.abs(RNG.normal(0, 0.08, size=1000))
    null = null + RNG.exponential(0.02, size=1000) * 0.3
    obs = np.quantile(null, 0.985) * 1.35  # observed KL above bulk
    thr = np.quantile(null, 0.95)
    ax.hist(null, bins=40, color="#D5D9DE", edgecolor="white", linewidth=0.35, label="1,000 no-replace perms")
    ax.axvline(thr, color="#E67E22", lw=1.8, linestyle="--", label="top 5% cut (this perm)")
    ax.axvline(obs, color="#C0392B", lw=2.2, label=f"observed KL = {obs:.3f}")
    ymax = ax.get_ylim()[1]
    ax.annotate(
        "pass if KL ≥ cut\nAND hit > 950/1000",
        xy=(obs, ymax * 0.55),
        xytext=(obs * 0.45, ymax * 0.85),
        fontsize=9,
        color="#C0392B",
        fontweight="bold",
        arrowprops=dict(arrowstyle="-|>", color="#C0392B", lw=1.2),
    )
    ax.set_xlabel("KL under permutation")
    ax.set_ylabel("count")
    ax.set_title("④ Null geometry: top 5% ∩ hit > 95%", fontsize=11, fontweight="bold")
    ax.legend(frameon=False, fontsize=8, loc="upper right")


def panel_network_mini(ax, zero_ahr: bool, title: str) -> None:
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
        kill = zero_ahr and a == "AHR"
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
        edge = "#C0392B" if name == "AHR" and zero_ahr else "#2C3E50"
        ax.add_patch(Circle((x, y), 0.09, facecolor=face, edgecolor=edge, lw=1.7, zorder=3))
        ax.text(x, y, name, ha="center", va="center", fontsize=8, fontweight="bold", zorder=4)


def main() -> None:
    fig = plt.figure(figsize=(14.5, 11.2))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.15, 1.15], hspace=0.38, wspace=0.28)

    fig.suptitle(
        "GenKI virtual KO — numbers live inside the geometry",
        fontsize=17,
        fontweight="bold",
        y=0.985,
    )
    fig.text(
        0.5,
        0.955,
        "GSE175817 · lesional TREM2 macrophage · target AHR  |  "
        "Yang et al. NAR 2023; Kipf & Welling 2016  |  Self-drawn schematic (not a paper figure)",
        ha="center",
        va="top",
        fontsize=9.5,
        color="#5a6573",
    )

    ax_a = fig.add_subplot(gs[0, 0])
    panel_network_mini(ax_a, False, "GRN after PCR (cartoon)")

    ax_b = fig.add_subplot(gs[0, 1])
    panel_network_mini(ax_b, True, "KO: delete AHR outgoing edges")

    ax_c = fig.add_subplot(gs[1, 0])
    panel_edge_weights(ax_c)

    ax_d = fig.add_subplot(gs[1, 1])
    panel_adj_ko(ax_d)

    ax_e = fig.add_subplot(gs[2, 0])
    panel_latent_kl(ax_e)

    ax_f = fig.add_subplot(gs[2, 1])
    panel_null_rule(ax_f)

    fig.text(
        0.5,
        0.01,
        "Lab numbers: HVG=3000 · search=100 · perms=1000 · hit>95% · enrich GO+KEGG hsa (BH p<.05 q<.2).  "
        "Response genes ≠ Seurat DEG. Computational prediction only.",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#5a6573",
    )

    save(fig, "01_方法示意_GenKI数形结合_VgaeGeometry")
    print("WROTE", OUT / "01_方法示意_GenKI数形结合_VgaeGeometry.png")


if __name__ == "__main__":
    main()
