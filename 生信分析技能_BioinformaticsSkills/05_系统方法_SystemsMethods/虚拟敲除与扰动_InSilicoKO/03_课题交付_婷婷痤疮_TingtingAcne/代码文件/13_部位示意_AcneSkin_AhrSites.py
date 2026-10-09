# -*- coding: utf-8 -*-
"""婷婷部位示意（写实解剖版）：正位面部 + 皮肤层次 + 毛囊皮脂腺单位 + 痤疮损害 + 真皮巨噬细胞。

对齐琪乐无穷 01_部位示意 的角色：说明取材与假设，不含敲除结果。
数据：GSE175817 人痤疮皮损/非皮损；虚拟敲除在皮损 TREM2 / M2 巨噬敲 AHR（M1 检出 0 不敲）。
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import (
    Arc,
    Circle,
    Ellipse,
    FancyBboxPatch,
    PathPatch,
    Polygon,
    Rectangle,
    Wedge,
)
import numpy as np

NAVY = "#1B365D"
LES = "#C17B7B"
M2C = "#6B8F71"
M1C = "#5B8FA8"
AHR = "#E8A04D"
GREY_DK = "#6B7380"
SKIN_OUT = "#B98A6A"
SKIN_FILL = "#F4E6D6"
DERM = "#F2DECA"
EPID = "#E9C9AC"
CORNEUM = "#DFB99A"
FAT = "#F7E7C8"
HAIR = "#4A4038"
SEBUM = "#F7D48A"
PLUG = "#C9BBA8"

OUTS = [
    Path(r"C:\Users\10540\Desktop\婷婷\虚拟敲除\结果文件\_跨亚群\scTenifoldKnk_1.4.3_GPU\图片文件"),
    Path(r"C:\Users\10540\Desktop\婷婷\虚拟敲除\结果文件\_跨亚群\GenKI\图片文件"),
    Path(r"E:\RProject\婷婷\痤疮_巨噬细胞极化机制\09_虚拟敲除_GSE175817\图片"),
]
STEM = "01_部位示意_HumanAcne_AhrSites"


def save(fig: plt.Figure) -> None:
    for folder in OUTS:
        folder.mkdir(parents=True, exist_ok=True)
        fig.savefig(folder / f"{STEM}.png", dpi=600, bbox_inches="tight", facecolor="white")
        fig.savefig(folder / f"{STEM}.svg", bbox_inches="tight", facecolor="white")
        fig.savefig(folder / f"{STEM}.jpg", dpi=400, bbox_inches="tight", facecolor="white")
        print("WROTE", folder / f"{STEM}.png")


def banner(ax, x, y, w, h, text, fs=12):
    ax.add_patch(
        FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                       facecolor="white", edgecolor=NAVY, lw=2.0, zorder=8)
    )
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold", color=NAVY, zorder=9)


def leader(ax, x1, y1, x2, y2, color=GREY_DK, lw=0.7):
    ax.plot([x1, x2], [y1, y2], color=color, lw=lw, zorder=6)
    ax.add_patch(Circle((x1, y1), 0.022, facecolor=color, edgecolor="none", zorder=6))


def papule(ax, x, y, r=0.06, pustule=False):
    ax.add_patch(Circle((x, y), r, facecolor=LES, edgecolor="#8B2E2E", lw=0.5, alpha=0.95, zorder=5))
    if pustule:
        ax.add_patch(Circle((x, y), r * 0.42, facecolor="#F2E2B8", edgecolor="none", zorder=6))
    ax.add_patch(Circle((x - r * 0.3, y + r * 0.3), r * 0.22, facecolor="white", alpha=0.55, edgecolor="none", zorder=6))


def draw_face(ax, cx=1.95, cy=4.75):
    # hair cap (behind face)
    ax.add_patch(Ellipse((cx, cy + 1.32), 1.78, 1.02, facecolor=HAIR, edgecolor="#2E2A26", lw=0.8, zorder=1))
    # ears
    for sx in (-1, 1):
        ax.add_patch(Ellipse((cx + sx * 0.80, cy - 0.02), 0.17, 0.34, facecolor=SKIN_FILL,
                             edgecolor=SKIN_OUT, lw=0.9, zorder=2))
    # face outline (bezier)
    verts = [
        (cx, cy + 1.15),
        (cx + 0.45, cy + 1.15), (cx + 0.75, cy + 0.88), (cx + 0.78, cy + 0.45),
        (cx + 0.82, cy + 0.10), (cx + 0.74, cy - 0.42), (cx + 0.55, cy - 0.78),
        (cx + 0.38, cy - 0.98), (cx + 0.18, cy - 1.10), (cx, cy - 1.12),
        (cx - 0.18, cy - 1.10), (cx - 0.38, cy - 0.98), (cx - 0.55, cy - 0.78),
        (cx - 0.74, cy - 0.42), (cx - 0.82, cy + 0.10), (cx - 0.78, cy + 0.45),
        (cx - 0.75, cy + 0.88), (cx - 0.45, cy + 1.15), (cx, cy + 1.15),
    ]
    codes = [MPath.MOVETO] + [MPath.CURVE4] * 18
    ax.add_patch(PathPatch(MPath(verts, codes), facecolor=SKIN_FILL, edgecolor=SKIN_OUT, lw=1.3, zorder=2))
    # eyebrows
    for sx in (-1, 1):
        ax.add_patch(Arc((cx + sx * 0.30, cy + 0.42), 0.34, 0.16, theta1=25, theta2=155,
                         lw=1.6, color="#3A2E22", zorder=4))
    # eyes
    for sx in (-1, 1):
        ax.add_patch(Ellipse((cx + sx * 0.30, cy + 0.22), 0.28, 0.115, facecolor="white",
                             edgecolor=NAVY, lw=0.9, zorder=4))
        ax.add_patch(Circle((cx + sx * 0.30, cy + 0.22), 0.052, facecolor="#3A2E22", edgecolor="none", zorder=5))
        ax.add_patch(Circle((cx + sx * 0.30, cy + 0.22), 0.020, facecolor="black", edgecolor="none", zorder=5))
    # nose
    ax.plot([cx, cx], [cy + 0.22, cy - 0.02], color=SKIN_OUT, lw=1.1, zorder=4)
    ax.add_patch(Arc((cx, cy - 0.06), 0.24, 0.12, theta1=185, theta2=355, lw=1.1, color=SKIN_OUT, zorder=4))
    for sx in (-1, 1):
        ax.add_patch(Circle((cx + sx * 0.105, cy - 0.075), 0.030, facecolor="#8B5A3C", edgecolor="none", zorder=5))
    # lips
    ax.add_patch(Ellipse((cx, cy - 0.38), 0.36, 0.135, facecolor="#C98B7B", edgecolor=SKIN_OUT, lw=0.9, zorder=4))
    ax.plot([cx - 0.17, cx + 0.17], [cy - 0.38, cy - 0.38], color=SKIN_OUT, lw=0.8, zorder=5)
    # acne: cheeks, forehead, chin
    for x, y, r, p in [
        (cx - 0.50, cy + 0.02, 0.062, False),
        (cx - 0.58, cy - 0.16, 0.050, True),
        (cx - 0.40, cy - 0.22, 0.042, False),
        (cx + 0.48, cy + 0.06, 0.055, False),
        (cx + 0.42, cy - 0.14, 0.040, False),
        (cx - 0.08, cy + 0.62, 0.050, True),
        (cx + 0.22, cy + 0.70, 0.038, False),
        (cx + 0.10, cy - 0.84, 0.055, True),
    ]:
        papule(ax, x, y, r=r, pustule=p)
    # zoom box on left cheek (viewer's left)
    ax.add_patch(FancyBboxPatch((cx - 0.76, cy - 0.34), 0.56, 0.58,
                                boxstyle="round,pad=0.01,rounding_size=0.03",
                                fill=False, edgecolor=LES, ls="--", lw=1.3, zorder=6))
    ax.annotate("", xy=(4.62, 5.05), xytext=(cx - 0.20, cy - 0.05),
                arrowprops=dict(arrowstyle="-|>", color=LES, lw=1.6), zorder=7)


def draw_skin(ax, x0=4.75, x1=11.25, y_top=6.15, y_bot=1.30):
    w = x1 - x0
    # subcutis
    ax.add_patch(Rectangle((x0, y_bot), w, 0.95, facecolor=FAT, edgecolor=NAVY, lw=1.0, zorder=1))
    rng = np.random.default_rng(7)
    for row in range(2):
        for col in range(14):
            fx = x0 + 0.35 + col * (w - 0.7) / 13 + rng.uniform(-0.05, 0.05)
            fy = y_bot + 0.28 + row * 0.42 + rng.uniform(-0.03, 0.03)
            ax.add_patch(Circle((fx, fy), 0.155, facecolor="#FBF3DF", edgecolor="#D8BE8E", lw=0.55, zorder=2))
    ax.text(x0 + 0.18, y_bot + 0.12, "subcutis", fontsize=7, color=GREY_DK, zorder=3)
    # reticular dermis
    ax.add_patch(Rectangle((x0, y_bot + 0.95), w, 2.35, facecolor=DERM, edgecolor=NAVY, lw=1.0, zorder=1))
    for i in range(11):
        yy = y_bot + 1.12 + i * 0.20
        xs = np.linspace(x0 + 0.15, x1 - 0.15, 60)
        ax.plot(xs, yy + 0.055 * np.sin(xs * 2.4 + i * 0.8), color="#D8B99C", lw=0.75, zorder=2)
    ax.text(x0 + 0.18, y_bot + 3.10, "dermis (reticular)", fontsize=7, color=GREY_DK, zorder=3)
    # papillary dermis
    ax.add_patch(Rectangle((x0, y_bot + 3.30), w, 1.05, facecolor="#F7E9DA", edgecolor=NAVY, lw=0.8, zorder=1))
    for i in range(7):
        yy = y_bot + 3.42 + i * 0.13
        xs = np.linspace(x0 + 0.15, x1 - 0.15, 60)
        ax.plot(xs, yy + 0.035 * np.sin(xs * 3.1 + i), color="#E2C7AC", lw=0.6, zorder=2)
    ax.text(x0 + 0.18, y_bot + 4.12, "papillary dermis", fontsize=7, color=GREY_DK, zorder=3)
    # basement membrane (dashed)
    ybm = y_bot + 4.35
    ax.plot([x0, x1], [ybm, ybm], color=NAVY, lw=1.0, ls=(0, (4, 2)), zorder=3)
    # epidermis with nuclei
    yep = y_top - 0.72
    ax.add_patch(Rectangle((x0, yep), w, 0.62, facecolor=EPID, edgecolor=NAVY, lw=0.9, zorder=3))
    for col in range(22):
        ex = x0 + 0.22 + col * (w - 0.44) / 21
        ax.add_patch(Ellipse((ex, yep + 0.31), 0.115, 0.175, facecolor="#B4805A", edgecolor="none", zorder=4))
    ax.text(x0 + 0.18, yep + 0.16, "epidermis", fontsize=7, color=GREY_DK, zorder=4)
    # stratum corneum
    ysc = y_top - 0.16
    ax.add_patch(Rectangle((x0, ysc), w, 0.16, facecolor=CORNEUM, edgecolor=NAVY, lw=0.8, zorder=4))
    for col in range(26):
        ax.plot([x0 + 0.12 + col * w / 25, x0 + 0.12 + (col + 1) * w / 25],
                [ysc + 0.16, ysc + 0.16], color="#B98A6A", lw=1.4, zorder=5)
    ax.text(x0 + 0.18, ysc - 0.02, "stratum corneum", fontsize=6.6, color=GREY_DK, zorder=5)

    # ---------- hair follicle ----------
    fx = 8.15
    ax.add_patch(Polygon([(fx - 0.30, y_top), (fx + 0.30, y_top), (fx + 0.24, y_bot + 1.55),
                          (fx - 0.24, y_bot + 1.55)], closed=True,
                         facecolor="#EEDCC8", edgecolor=SKIN_OUT, lw=1.0, zorder=4))
    ax.add_patch(Polygon([(fx - 0.115, y_top + 0.72), (fx + 0.115, y_top + 0.72),
                          (fx + 0.085, y_bot + 1.85), (fx - 0.085, y_bot + 1.85)],
                         closed=True, facecolor=HAIR, edgecolor="#2E2A26", lw=0.7, zorder=6))
    ax.add_patch(Ellipse((fx, y_bot + 1.55), 0.62, 0.55, facecolor="#E8C9AC",
                         edgecolor=SKIN_OUT, lw=1.0, zorder=5))
    ax.add_patch(Ellipse((fx, y_bot + 1.42), 0.26, 0.18, facecolor="#D98A72",
                         edgecolor=SKIN_OUT, lw=0.7, zorder=6))
    ax.text(fx + 0.42, y_top - 0.42, "hair follicle", fontsize=7, color=NAVY, zorder=7)
    leader(ax, fx + 0.16, y_top - 0.36, fx + 0.38, y_top - 0.44)

    # ---------- sebaceous gland ----------
    for dx, dy, r in [(0, 0, 0.30), (0.26, 0.16, 0.24), (0.22, -0.18, 0.22), (-0.05, -0.28, 0.20)]:
        ax.add_patch(Circle((fx + 0.92 + dx, y_bot + 3.05 + dy), r,
                            facecolor=SEBUM, edgecolor=SKIN_OUT, lw=0.8, zorder=5))
    ax.plot([fx + 0.62, fx + 0.30], [y_bot + 3.05, y_bot + 3.10], color=SEBUM, lw=3.2, zorder=5)
    ax.text(fx + 1.45, y_bot + 3.02, "sebaceous gland", fontsize=7, color=NAVY, zorder=7)
    leader(ax, fx + 1.18, y_bot + 3.05, fx + 1.42, y_bot + 3.02)

    # ---------- comedone / papule ----------
    cx = 6.55
    ax.add_patch(FancyBboxPatch((cx - 0.34, y_top - 1.05), 0.68, 1.35,
                                boxstyle="round,pad=0.01,rounding_size=0.10",
                                facecolor="#F0D8C2", edgecolor=SKIN_OUT, lw=1.0, zorder=5))
    ax.add_patch(Ellipse((cx, y_top + 0.22), 0.86, 0.30, facecolor=LES,
                         edgecolor="#8B2E2E", lw=1.0, zorder=6))
    ax.add_patch(Polygon([(cx - 0.24, y_top - 0.02), (cx + 0.24, y_top - 0.02),
                          (cx + 0.16, y_top - 0.72), (cx - 0.16, y_top - 0.72)],
                         closed=True, facecolor=PLUG, edgecolor="#9C8E76", lw=0.8, zorder=7))
    for i in range(14):
        px = cx + np.random.default_rng(i).uniform(-0.14, 0.14)
        py = y_top - 0.10 - (i % 7) * 0.085
        ax.add_patch(Circle((px, py), 0.028, facecolor="#AFA08A", edgecolor="none", zorder=8))
    ax.text(cx - 1.02, y_top + 0.42, "comedone / papule", fontsize=7.2, color="#8B2E2E",
            fontweight="bold", zorder=8)
    leader(ax, cx - 0.42, y_top + 0.30, cx - 1.00, y_top + 0.42, color="#8B2E2E")

    # inflammatory infiltrate around lesion base
    rng2 = np.random.default_rng(11)
    for i in range(16):
        ix = cx + rng2.uniform(-0.85, 0.35)
        iy = y_top - 1.15 - rng2.uniform(0, 0.75)
        ax.add_patch(Circle((ix, iy), 0.055, facecolor="#D98A8A", edgecolor="none", alpha=0.85, zorder=5))

    # ---------- capillary ----------
    t = np.linspace(0, 1, 40)
    xs = x0 + 2.2 + t * 1.4
    ys = y_bot + 1.55 + 0.35 * np.sin(t * 3.4)
    ax.plot(xs, ys + 0.10, color="#C07070", lw=1.0, zorder=5)
    ax.plot(xs, ys - 0.10, color="#C07070", lw=1.0, zorder=5)
    for tt in (0.2, 0.45, 0.7, 0.9):
        j = int(tt * 39)
        ax.add_patch(Circle((xs[j], ys[j]), 0.055, facecolor="#E08A8A", edgecolor="none", zorder=6))
    ax.text(x0 + 2.15, y_bot + 1.18, "capillary", fontsize=6.6, color=GREY_DK, zorder=6)

    # ---------- macrophages ----------
    def macrophage(x, y, color, label, sub, ring=False, s=1.0):
        ax.add_patch(Ellipse((x, y), 0.46 * s, 0.34 * s, facecolor=color,
                             edgecolor=NAVY, lw=0.9, zorder=7))
        for ang in (25, 115, 205, 300):
            rad = np.deg2rad(ang)
            ax.add_patch(Ellipse((x + 0.26 * s * np.cos(rad), y + 0.20 * s * np.sin(rad)),
                                 0.16 * s, 0.11 * s, angle=ang, facecolor=color,
                                 edgecolor=NAVY, lw=0.6, zorder=7))
        ax.add_patch(Circle((x, y), 0.115 * s, facecolor="#F2E2D4", edgecolor=NAVY, lw=0.7, zorder=8))
        if ring:
            ax.add_patch(Circle((x, y), 0.24 * s, fill=False, edgecolor=AHR, lw=2.0, zorder=8))
            ax.text(x, y + 0.42 * s, "AHR+", fontsize=6.8, color=AHR,
                    fontweight="bold", ha="center", zorder=9)
        ax.text(x, y - 0.42 * s, label, ha="center", va="top", fontsize=7.4,
                color=NAVY, fontweight="bold", zorder=9)
        ax.text(x, y - 0.60 * s, sub, ha="center", va="top", fontsize=6.2,
                color=GREY_DK, zorder=9)

    macrophage(x0 + 1.35, y_bot + 2.45, LES, "TREM2 mac", "lesional n=1515", ring=True)
    macrophage(x0 + 3.05, y_bot + 2.55, M2C, "M2-like", "lesional n=266", ring=True)
    macrophage(x1 - 1.55, y_bot + 2.45, M1C, "M1-like", "AHR detected = 0", ring=False)

    ax.text(x0 + w / 2, y_bot + 0.02, "GSE175817  ·  facial skin  ·  lesional vs nonlesional",
            ha="center", fontsize=7.2, color=GREY_DK, zorder=6)


def draw_hypothesis(ax, x0=11.55, x1=14.35, y_bot=1.30, y_top=6.15):
    ax.add_patch(FancyBboxPatch((x0, y_bot), x1 - x0, y_top - y_bot,
                                boxstyle="round,pad=0.02,rounding_size=0.08",
                                facecolor="#F7FBFE", edgecolor="#8FB3D1", lw=1.5, zorder=1))
    ax.text((x0 + x1) / 2, y_top - 0.32, "Virtual KO readout", ha="center",
            fontsize=10, fontweight="bold", color=NAVY, zorder=3)

    # macrophage with nuclear AHR
    mx, my = (x0 + x1) / 2, y_bot + 3.65
    ax.add_patch(Ellipse((mx, my), 1.35, 1.02, facecolor=LES, edgecolor=NAVY, lw=1.1, zorder=3))
    for ang in (25, 115, 205, 300):
        rad = np.deg2rad(ang)
        ax.add_patch(Ellipse((mx + 0.78 * np.cos(rad), my + 0.58 * np.sin(rad)),
                             0.42, 0.28, angle=ang, facecolor=LES, edgecolor=NAVY, lw=0.7, zorder=3))
    ax.add_patch(Circle((mx, my), 0.34, facecolor="#F2E2D4", edgecolor=NAVY, lw=1.0, zorder=4))
    ax.add_patch(Circle((mx, my), 0.17, facecolor=AHR, edgecolor=NAVY, lw=0.8, zorder=5))
    ax.text(mx, my - 0.02, "AHR", ha="center", va="center", fontsize=6.4,
            color=NAVY, fontweight="bold", zorder=6)
    ax.text(mx, my + 1.02, "TREM2 / M2 macrophage", ha="center", fontsize=7.6,
            color=NAVY, fontweight="bold", zorder=6)

    ax.add_patch(FancyBboxPatch((x0 + 0.18, y_bot + 1.72), (x1 - x0) - 0.36, 0.92,
                                boxstyle="round,pad=0.02,rounding_size=0.05",
                                facecolor="white", edgecolor="#2E8A9A", lw=1.0, zorder=3))
    ax.text((x0 + x1) / 2, y_bot + 2.32, "scTenifoldKnk 1.4.3 GPU", ha="center",
            fontsize=7.8, color=NAVY, zorder=4)
    ax.text((x0 + x1) / 2, y_bot + 1.98, "GenKI (VGAE)", ha="center", fontsize=7.8, color=NAVY, zorder=4)

    ax.add_patch(FancyBboxPatch((x0 + 0.18, y_bot + 0.30), (x1 - x0) - 0.36, 1.22,
                                boxstyle="round,pad=0.02,rounding_size=0.05",
                                facecolor="white", edgecolor=NAVY, lw=1.0, zorder=3))
    ax.text((x0 + x1) / 2, y_bot + 1.22, "hypothesis (framing only)", ha="center",
            fontsize=7.8, fontweight="bold", color=NAVY, zorder=4)
    ax.text((x0 + x1) / 2, y_bot + 0.72,
            "AHR in lesional TREM2-high\nmacrophages may mark the\ninflammatory / lipid axis",
            ha="center", fontsize=6.8, color=GREY_DK, linespacing=1.35, zorder=4)


def main() -> None:
    print("部位示意已由成图替换（tingting_acne_site）。本脚本不再覆盖图片文件。")
    return
    fig, ax = plt.subplots(figsize=(15.2, 7.6))
    ax.set_xlim(0, 15.2)
    ax.set_ylim(0, 7.6)
    ax.axis("off")

    banner(ax, 1.2, 6.72, 12.8, 0.52,
           "Anatomical site — acne skin biopsies (GSE175817) · virtual KO targets AHR in lesional macrophages",
           fs=12.2)
    ax.text(7.6, 6.42, "Schematic for study framing · not a localization experiment · computational prediction only",
            ha="center", fontsize=8.2, color=GREY_DK)

    draw_face(ax)
    draw_skin(ax)
    draw_hypothesis(ax)

    ax.text(2.0, 1.05, "A  Donor / acne face", ha="center", fontsize=10, fontweight="bold", color=NAVY)
    ax.text(8.0, 1.05, "B  Skin section: pilosebaceous unit + dermal macrophages",
            ha="center", fontsize=10, fontweight="bold", color=NAVY)
    ax.text(12.95, 1.05, "C  Hypothesis", ha="center", fontsize=10, fontweight="bold", color=NAVY)

    save(fig)
    plt.close(fig)


if __name__ == "__main__":
    main()
