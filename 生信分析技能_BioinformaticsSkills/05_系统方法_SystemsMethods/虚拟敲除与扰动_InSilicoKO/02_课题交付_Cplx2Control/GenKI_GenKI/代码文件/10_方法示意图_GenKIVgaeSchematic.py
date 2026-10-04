"""Self-drawn GenKI (VGAE) method schematic — no overlapping labels.

Reference: Yang et al., NAR 2023 (GenKI); Kipf & Welling 2016 (VGAE).
English labels. Output: 01_方法示意_GenKIVgaeWorkflow png+svg.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

OUT = Path(r"C:\Users\10540\Desktop\琪乐无穷\虚拟敲除\结果文件\_跨亚群\GenKI\图片文件")
OUT.mkdir(parents=True, exist_ok=True)

BOXES = [
    ("Input", "GSE197289 mouse TG snRNA-seq, Control only; subtypes PEP / NF1 (author cell labels)."),
    ("Genes", "Top 3000 HVGs (Seurat vst) + forced targets Mitf, Bace2, Cplx2, Ppp1r26, Slc28a3, Sh3d21 + one low-correlation control gene per subtype."),
    ("GRN", "PC-based full regression on scaled log-expression; keep top 15% |weights| as a boolean gene graph."),
    ("VGAE", "2-D Gaussian latent encoder/decoder (Kipf & Welling 2016); edges 75% train / 5% val / 20% test. Training uses CUDA when available."),
    ("Search", "100 random trials (lr, beta, weight decay; paper grids); early stop on validation AP; select val AP minus overfit gap."),
    ("KO", "Remove the target gene's outgoing edges → re-encode → per-gene KL distance (GenKI score)."),
    ("Null", "1000 permutations of cell order without replacement (numpy seed 0)."),
    ("Response", "KL in top 5% of a replicate and hit in >95% of replicates; knocked-out gene excluded."),
    ("Enrich", "GO BP / CC / MF + KEGG (mmu); BH p<0.05 and q<0.2 on response genes only; non-passing terms not plotted; control KO terms non-specific."),
]

FIG_W, FIG_H = 12.2, 11.2
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

ax.text(
    0.5, 0.975, "GenKI virtual knockout workflow (VGAE)",
    ha="center", va="top", fontsize=18, fontweight="bold", color="#1c2430",
)
ax.text(
    0.5, 0.945,
    "After Yang et al., Nucleic Acids Research 2023 (GenKI); Kipf & Welling 2016 (VGAE).\nSelf-drawn schematic for this project — not a paper figure.",
    ha="center", va="top", fontsize=10.5, color="#5a6573", linespacing=1.35,
)

n = len(BOXES)
top, bottom = 0.905, 0.08
gap = 0.012
box_h = (top - bottom - gap * (n - 1)) / n
x0, box_w = 0.04, 0.92
tag_w = 0.12
palette = ["#DCE6F0", "#E4EDE4"]
edge = "#4A5A6A"

for i, (tag, text) in enumerate(BOXES):
    y_top = top - i * (box_h + gap)
    y_bottom = y_top - box_h
    rect = mpatches.FancyBboxPatch(
        (x0, y_bottom), box_w, box_h,
        boxstyle="round,pad=0.004,rounding_size=0.012",
        linewidth=1.15, edgecolor=edge, facecolor=palette[i % 2],
    )
    ax.add_patch(rect)
    # tag column (left), body wraps in remaining width — no overlap
    ax.text(
        x0 + 0.015, y_bottom + box_h / 2, tag,
        ha="left", va="center", fontsize=11.5, fontweight="bold", color="#1c2430",
    )
    wrapped = textwrap.fill(text, width=78)
    ax.text(
        x0 + tag_w + 0.02, y_bottom + box_h / 2, wrapped,
        ha="left", va="center", fontsize=10.2, color="#222222", linespacing=1.25,
    )
    if i < n - 1:
        ax.annotate(
            "", xy=(0.5, y_bottom - 0.001), xytext=(0.5, y_bottom - gap + 0.001),
            arrowprops=dict(arrowstyle="-|>", color="#4A5A6A", linewidth=1.35),
        )

ax.text(
    0.5, 0.032,
    "Claim: computational prediction of gene-knockout response — not wet-lab KO DEG.\n"
    "GSE197289 Control is not a chronic trigeminal neuralgia model.",
    ha="center", va="center", fontsize=10, color="#8a4b3f", linespacing=1.3,
)

png = OUT / "01_方法示意_GenKIVgaeWorkflow.png"
svg = OUT / "01_方法示意_GenKIVgaeWorkflow.svg"
fig.savefig(png, dpi=600, bbox_inches="tight", facecolor="white")
fig.savefig(svg, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("wrote", png)
print("wrote", svg)
