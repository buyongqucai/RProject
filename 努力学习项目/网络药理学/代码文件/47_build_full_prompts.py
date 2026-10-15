# -*- coding: utf-8 -*-
"""Build FULL untruncated prompts for ranks >= START (style-match 001-088)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学")
CODE = ROOT / "代码文件"
MAN = ROOT / "交付文件/图片/KEGG官方通路图/00_全部通路图清单.csv"
OUT = CODE / "_gpu_prompts"
sys.path.insert(0, str(CODE))
from kegg_zh_names import ZH  # noqa: E402

FORBIDDEN = """
Highly detailed biology textbook / medical explainer animation aesthetic.
Closer to real histology / TEM-inspired organelle morphology (not cartoon).
Soft cinematic lighting, subtle 3D shading, organic shapes, lifelike membrane texture.
Visible mitochondrial cristae, nuclear pores in double envelope, ribosome-studded ER when relevant.
Tissue microenvironment when relevant (vessels, ECM, neighboring cells).
NOT flat icons, NOT rounded rectangles as proteins, NOT abstract flowchart boxes,
NOT beads-on-a-string cascade diagrams, NOT minimalist infographic geometry,
NOT simple schematic circles for ligands.
Landscape 16:9.
Include short English anatomical labels next to key structures (cell types, receptors, ligands, organelles, key proteins) — clean sans-serif, not covering core biology.
Do NOT draw pathway titles, KEGG IDs, dark header bars, numbered step strips, or UI chrome.
No white title banner or inset step panels at the top of the image.
Keep ALL biology fully inside the frame with ≥6% margin on every edge.
Never crop or cut half-structures / half-insets at the top or bottom edge.
Fill the frame with complete anatomy — nothing important clipped by the canvas border.
""".strip()

# Curated anatomy seeds for known pathways (extend freely; never shorten FORBIDDEN)
SEEDS: dict[str, str] = {
    "hsa05216": "Thyroid follicular epithelial cell / papillary thyroid cancer context: RET/PTC or BRAF-driven MAPK cascade, follicular cells with colloid lumen, nuclear grooves hint, VEGFR angiogenesis nearby. Labels: FOLLICULAR CELL, MAPK, BRAF, NUCLEUS, BLOOD VESSEL.",
    "hsa05134": "Alveolar macrophage / lung epithelium infected by Legionella pneumophila inside Legionella-containing vacuole; Dot/Icm T4SS, NF-κB, inflammasome. Labels: LEGIONELLA, LCV, MACROPHAGE, T4SS, NUCLEUS.",
    "hsa04919": "Thyroid hormone signaling: T3/T4 entering hepatocyte or cardiomyocyte, THR nuclear receptor on DNA, TRE, mitochondria biogenesis glow. Labels: T3, THR, DNA, MITOCHONDRIA, NUCLEUS.",
    "hsa04014": "Ras signaling at plasma membrane: RTK→Grb2-Sos→Ras-GTP→Raf-MEK-ERK into nucleus; detailed bilayer, organelle-rich cytoplasm. Labels: RTK, RAS, RAF, MEK, ERK, NUCLEUS.",
    "hsa04670": "Leukocyte transendothelial migration: neutrophil squeezing between endothelial cells, ICAM/PECAM, actin cytoskeleton, basement membrane. Labels: NEUTROPHIL, ENDOTHELIUM, ICAM, PECAM, BASEMENT MEMBRANE.",
    "hsa05415": "Diabetic cardiomyopathy cardiomyocyte: AGEs, ROS from mitochondria, impaired calcium handling, lipid droplets, nucleus. Labels: CARDIOMYOCYTE, ROS, MITOCHONDRIA, AGE, NUCLEUS.",
    "hsa04935": "Pituitary somatotroph secreting GH; GH binding GHR on hepatocyte, JAK2-STAT5 to nucleus; IGF-1 output. Labels: GH, GHR, JAK2, STAT5, NUCLEUS.",
    "hsa05143": "African trypanosome among blood RBCs interacting with macrophage; VSG coat, TLR signaling, inflammatory nucleus. Labels: TRYPANOSOME, RBC, MACROPHAGE, VSG, NUCLEUS.",
}


def build(pid: str, en: str, zh: str) -> str:
    seed = SEEDS.get(
        pid,
        (
            f"Human pathway anatomy for {pid} ({en} / {zh}): tissue microenvironment with realistic cells, "
            f"multi-domain membrane receptors, organelle-rich cytoplasm (mitochondria with cristae, ER, Golgi), "
            f"nuclear pores, signal flow into nucleus and target-gene glow. "
            f"Labels for key structures in clean English."
        ),
    )
    return (
        f"Medical animation cross-section illustrating {en} ({pid}, {zh}).\n"
        f"{seed}\n"
        f"{FORBIDDEN}"
    )


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 89
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 183
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(MAN, encoding="utf-8-sig")
    n = 0
    for _, r in df.iterrows():
        rank = int(r["rank"])
        if rank < start or rank > end:
            continue
        pid = str(r["pathway_id"]).strip()
        en = str(r["description"]).strip()
        zh = ZH.get(pid, en[:24])
        text = build(pid, en, zh)
        path = OUT / f"{rank:03d}_{pid}.txt"
        path.write_text(text, encoding="utf-8")
        n += 1
        print(rank, pid, "chars", len(text), "->", path.name)
    print("DONE", n)


if __name__ == "__main__":
    main()
