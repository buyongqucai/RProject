# -*- coding: utf-8 -*-
"""13_论文图表_Fig1237.py —— §5 缺失图件：Fig1 流程图、Fig2 三源韦恩+统计、Fig3 敏感性面板、Fig7 对接热图

约定：图面英文（phaseE）、DPI=600、PNG+SVG、标签 ≤28 字符（PlotQA label_length）。
输出：结果文件/图片文件/总图/
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib_venn as mv
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DELIV = ROOT.parent / "交付文件"
FIG = ROOT / "结果文件" / "图片文件" / "总图"
FIG.mkdir(parents=True, exist_ok=True)
DPI = 600

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name: str) -> None:
    for ext in ("png", "svg"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def load_sets():
    F = set(pd.read_csv(DELIV / "数据文件/药物/药物靶点_全药.csv", encoding="utf-8-sig")["gene"])
    D = set(pd.read_csv(DELIV / "数据文件/疾病/疾病靶点合并.csv", encoding="utf-8-sig")["gene"])
    Mm = pd.read_csv(ROOT / "结果文件" / "数据文件" / "代谢物/M_主面板靶点.csv", encoding="utf-8-sig")
    M = set(Mm["gene"])
    return F, D, M, Mm


# ---------------- Fig 1: study design flow（matplotlib only；禁止 draw.io）----------------
def fig1() -> None:
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

    C_FORM, C_DIS, C_MET = "#C17B7B", "#5B8FA8", "#6B8F71"
    C_CORE, C_DOWN, C_INK = "#D4A574", "#8B7BA8", "#2F2F2F"

    fig, ax = plt.subplots(figsize=(8.2, 5.4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10.2)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    def soft(hex_color: str, a: float = 0.22) -> tuple:
        h = hex_color.lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        return (r, g, b, a)

    def box(x, y, w, h, title, sub, edge, *, title_fs=9.2, sub_fs=7.8, accent=True):
        # 轻阴影
        ax.add_patch(FancyBboxPatch(
            (x + 0.06, y - 0.06), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.22",
            facecolor=(0, 0, 0, 0.06), edgecolor="none", zorder=1,
        ))
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.22",
            facecolor=soft(edge, 0.20), edgecolor=edge, linewidth=1.35,
            zorder=2,
        ))
        if accent:
            ax.add_patch(Rectangle(
                (x + 0.08, y + 0.18), 0.10, h - 0.36,
                facecolor=edge, edgecolor="none", zorder=3, alpha=0.9,
            ))
        ax.text(x + w / 2 + 0.04, y + h * 0.62, title, ha="center", va="center",
                fontsize=title_fs, color=C_INK, fontweight="bold", zorder=4)
        ax.text(x + w / 2 + 0.04, y + h * 0.30, sub, ha="center", va="center",
                fontsize=sub_fs, color="#555555", zorder=4)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch(
            (x1, y1), (x2, y2),
            arrowstyle="-|>", mutation_scale=11, lw=1.05,
            color="#9A9A9A", shrinkA=1, shrinkB=1,
            connectionstyle="arc3,rad=0.0", zorder=1,
        ))

    box(0.35, 8.05, 3.3, 1.30, "Formula targets", "F = 636", C_FORM)
    box(4.35, 8.05, 3.3, 1.30, "UC disease targets", "D = 1517", C_DIS)
    box(8.35, 8.05, 3.3, 1.30, "Metabolite targets", "M = 466", C_MET)

    box(1.15, 5.55, 3.5, 1.20, "I1 = F ∩ D", "291 genes", C_FORM)
    box(7.35, 5.55, 3.5, 1.20, "I2 = M ∩ D", "165 genes", C_MET)

    box(3.55, 3.20, 4.9, 1.40, "C = I1 ∩ I2", "78 triple-core targets", C_CORE,
        title_fs=10.2, sub_fs=8.4)

    box(0.30, 0.55, 3.55, 1.40, "Sensitivity", "colon filter · hub · panel", C_DOWN)
    box(4.225, 0.55, 3.55, 1.40, "Mechanism", "PPI · GO · KEGG · G-M-C-T-P", C_DOWN)
    box(8.15, 0.55, 3.55, 1.40, "External support", "docking · GEO", C_DOWN)

    arrow(2.0, 8.05, 2.5, 6.75)
    arrow(5.2, 8.05, 3.4, 6.75)
    arrow(6.8, 8.05, 8.6, 6.75)
    arrow(10.0, 8.05, 9.5, 6.75)
    arrow(2.9, 5.55, 5.0, 4.60)
    arrow(9.1, 5.55, 7.0, 4.60)
    arrow(4.8, 3.20, 2.1, 1.95)
    arrow(6.0, 3.20, 6.0, 1.95)
    arrow(7.2, 3.20, 9.9, 1.95)

    ax.text(6.0, 9.85, "Triple-source intersection design",
            ha="center", fontsize=12.2, color=C_INK, fontweight="bold")
    ax.text(6.0, 9.48, "UC formula × gut metabolites",
            ha="center", fontsize=8.6, color="#666666")
    save(fig, "01_研究流程图_双交集设计_StudyDesignFlow")


# ---------------- Fig 2: Venn + statistics ----------------
def fig2(F, D, M) -> None:
    stats = pd.read_csv(ROOT / "结果文件" / "数据文件" / "双交集统计汇总.csv", encoding="utf-8-sig")
    main = stats[(stats.analysis == "main_evidence_priority") &
                 (stats.evidence == "H_plus_M")].iloc[0]
    full = stats[(stats.analysis == "full_gutmgene_human") &
                 (stats.evidence == "H_plus_M")].iloc[0]

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.9))
    # 等大圆：固定各子集面积权重，数字仍用真实子集计数
    from matplotlib_venn.layout.venn3 import DefaultLayoutAlgorithm
    v = mv.venn3(
        [F, D, M],
        set_labels=("Formula (F)", "UC disease (D)", "Metabolites (M)"),
        ax=axes[0],
        alpha=0.55,
        set_colors=("#C17B7B", "#6B8F71", "#5B8FA8"),
        layout_algorithm=DefaultLayoutAlgorithm(
            fixed_subset_sizes=(1, 1, 1, 1, 1, 1, 1)
        ),
    )
    for t in v.set_labels:
        if t:
            t.set_fontsize(8.5)
    for t in v.subset_labels:
        if t:
            t.set_fontsize(8.0)
    axes[0].set_title("Triple-source gene sets", fontsize=9.5)

    labels = ["Hypergeom\n(main)", "Perm. strat.\n(main)",
              "Hypergeom\n(full)", "Perm. strat.\n(full)"]
    vals = [-np.log10(float(main.hypergeom_fdr_bh)),
            -np.log10(max(float(main.degree_preserving_stratified_permutation_p), 1e-3)),
            -np.log10(float(full.hypergeom_fdr_bh)),
            -np.log10(max(float(full.degree_preserving_stratified_permutation_p), 1e-3))]
    cols = ["#5B8FA8", "#C17B7B", "#8B7BA8", "#D4A574"]
    bars = axes[1].bar(labels, vals, color=cols, width=0.62, edgecolor="none")
    axes[1].bar_label(bars, fmt="%.1f", padding=3, fontsize=7.5)
    axes[1].set_ylabel(r"$-\log_{10}$ p / FDR")
    axes[1].set_title("Set overlap vs degree structure", fontsize=9.5)
    axes[1].tick_params(axis="x", labelsize=7.5)
    axes[1].set_ylim(0, max(vals) * 1.18 if max(vals) > 0 else 1)
    axes[1].text(
        0.5, -0.28,
        f"|C| = {int(main.C_genes)} (main), {int(full.C_genes)} (full)",
        transform=axes[1].transAxes, ha="center", fontsize=7.2, color="#444",
    )
    fig.tight_layout()
    save(fig, "02_三源交集与置换检验_VennPermutation")


# ---------------- Fig 3: sensitivity panels ----------------
def fig3() -> None:
    stats = pd.read_csv(ROOT / "结果文件" / "数据文件" / "双交集统计汇总.csv", encoding="utf-8-sig")
    th = pd.read_csv(ROOT / "结果文件" / "数据文件" / "代谢物/M_阈值敏感性.csv", encoding="utf-8-sig")
    Mm = pd.read_csv(ROOT / "结果文件" / "数据文件" / "代谢物/M_主面板靶点.csv", encoding="utf-8-sig")
    D = set(pd.read_csv(DELIV / "数据文件/疾病/疾病靶点合并.csv", encoding="utf-8-sig")["gene"])
    I1 = set(pd.read_csv(DELIV / "数据文件/药物/药物疾病交集.csv", encoding="utf-8-sig")["gene"])
    colon = pd.read_csv(ROOT / "结果文件" / "数据文件" / "敏感性/结肠表达过滤_基因表.csv", encoding="utf-8-sig")

    main = stats[(stats.analysis == "main_evidence_priority") &
                 (stats.evidence == "H_plus_M")].iloc[0]
    mainH = stats[(stats.analysis == "main_evidence_priority") &
                  (stats.evidence == "H_only")].iloc[0]
    full = stats[(stats.analysis == "full_gutmgene_human") &
                 (stats.evidence == "H_plus_M")].iloc[0]
    fullH = stats[(stats.analysis == "full_gutmgene_human") &
                  (stats.evidence == "H_only")].iloc[0]

    h_genes = set(Mm.loc[Mm.evidence_level == "H", "gene"])
    def c_at(level: str) -> int:
        col = f"pass_{level}"
        mask = th[col].astype(str).str.lower().eq("true")
        g = set(th.loc[mask, "gene"]) | h_genes
        return len(I1 & g & D)

    Cmain = set(pd.read_csv(ROOT / "结果文件" / "数据文件" / "C_main_evidence_priority_H_plus_M.csv",
                            encoding="utf-8-sig")["gene"])
    colon_genes = set(colon.loc[colon["colon_expressed_tpm_ge_1"].astype(str)
                                .str.lower().eq("true"), "gene"])

    items = [
        ("Main\nH+M", int(main.C_genes)),
        ("Main\nH only", int(mainH.C_genes)),
        ("Full\nH+M", int(full.C_genes)),
        ("Full\nH only", int(fullH.C_genes)),
        ("Threshold\nrelaxed", c_at("relaxed")),
        ("Threshold\nmedium", c_at("medium")),
        ("Threshold\nstrict", c_at("strict")),
        ("No top10%\nhub", int(main.C_genes_no_top10pct_hub)),
        ("Colon\nexpressed", len(Cmain & colon_genes)),
    ]

    fig, ax = plt.subplots(figsize=(7.6, 3.6))
    names = [i[0] for i in items]; vals = [i[1] for i in items]
    cols = ["#2f5f9e" if i < 4 else "#4c8c3f" if i < 7 else "#b8860b" for i in range(len(items))]
    ax.bar(names, vals, color=cols, width=0.64)
    for i, v_ in enumerate(vals):
        ax.text(i, v_ + 2, str(v_), ha="center", fontsize=8)
    ax.axhline(30, ls="--", lw=1, color="#c0392b")
    ax.text(len(items) - 0.4, 32, "pathway-level fallback (<30)",
            ha="right", fontsize=7.2, color="#c0392b")
    ax.set_ylabel("|C| triple-core targets")
    ax.set_title("Sensitivity of the triple intersection", fontsize=9.5)
    ax.set_ylim(0, max(vals) * 1.16)
    ax.tick_params(axis="x", labelsize=7.2)
    fig.tight_layout()
    save(fig, "03_敏感性分析面板_SensitivityPanels")


# ---------------- Fig 7: docking heatmap ----------------
def fig7() -> None:
    df = pd.read_csv(ROOT / "结果文件" / "数据文件" / "对接/对接汇总.csv", encoding="utf-8-sig")
    # 结构政策：有优选 PDB 时只用优选行（4H3X / 7RTG），避免新旧结构叠行
    prefer = {("Tryptophan", "MMP9"): "4H3X", ("Adenosine", "ADA"): "7RTG"}
    keep = []
    for (met, gene), g in df.groupby(["metabolite", "gene"], sort=False):
        want = prefer.get((met, gene))
        if want is not None and (g["pdb"] == want).any():
            keep.append(g.loc[g["pdb"] == want].iloc[0])
        else:
            keep.append(g.loc[g["mean_kJ"].idxmin()])
    df = pd.DataFrame(keep).reset_index(drop=True)
    df["pair"] = df["metabolite"] + " × " + df["gene"]
    df = df.sort_values("mean_kJ")
    mat = df["mean_kJ"].values.reshape(-1, 1)

    fig, ax = plt.subplots(figsize=(5.4, 5.2))
    im = ax.imshow(mat, cmap="RdYlBu_r", aspect="auto", vmin=-36, vmax=-14)
    ax.set_xticks([0]); ax.set_xticklabels(["Mean affinity\n(kJ/mol)"], fontsize=8)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["pair"], fontsize=8)
    for i, v in enumerate(df["mean_kJ"]):
        # 数值纯黑；不加白底、不写 PASS/no
        ax.text(0, i, f"{v:.1f}", va="center", ha="center",
                fontsize=8.0, color="#000000")
    ax.set_title("Docking: metabolite x core target (3 runs)", fontsize=9.5)
    cb = fig.colorbar(im, ax=ax, shrink=0.6, pad=0.03)
    cb.set_label("kJ/mol", fontsize=8)
    ax.text(0.5, -0.10, "threshold -20.9 kJ/mol; Vina, 3 independent seeds",
            transform=ax.transAxes, ha="center", fontsize=7.2, color="#444")
    fig.tight_layout()
    save(fig, "04_对接亲和力热图_DockingAffinityHeatmap")


def main() -> None:
    F, D, M, _ = load_sets()
    fig1()
    fig2(F, D, M)
    fig3()
    fig7()
    print("all figures done ->", FIG)


if __name__ == "__main__":
    main()
