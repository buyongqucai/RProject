# -*- coding: utf-8 -*-
"""KEGG 生物结构动画 · 底图素材库

策略：同类通路复用同一张精细插画底图，仅更换顶栏（编号/中英名）与要点芯片。
不再为每条通路 GenerateImage，大幅节省 token。

素材库目录：
  D:/数据库/KEGG数据库/KEGG动画素材库/
  E:/RProject/.../动画_生物结构/_素材库/
"""
from __future__ import annotations

from pathlib import Path

# 原型标签 → 优先选用的底图文件名（按顺序找第一个存在的）
ARCHETYPES: dict[str, list[str]] = {
    "epithelium": [
        "bio_base_01_epithelium.png",
        "bio_base_02_il17.png",
        "bio_base_070_hsa05130.png",
        "bio_base_064_hsa05321.png",
    ],
    "macrophage": [
        "bio_base_04_tlr.png",
        "bio_base_025_hsa05140.png",
        "bio_base_069_hsa04621.png",
        "bio_base_058_hsa05152.png",
    ],
    "hepatocyte": [
        "bio_base_08_hepatitis_b.png",
        "bio_base_14_hepatitis_c.png",
        "bio_base_023_hsa04936.png",
        "bio_base_024_hsa05225.png",
        "bio_base_083_hsa04932.png",
    ],
    "endothelium": [
        "bio_base_11_shear_athero.png",
        "bio_base_06_lipid_athero.png",
        "bio_base_075_hsa04370.png",
        "bio_base_07_age_rage.png",
    ],
    "cancer": [
        "bio_base_12_prostate.png",
        "bio_base_17_pancreatic.png",
        "bio_base_022_hsa05210.png",
        "bio_base_033_hsa05224.png",
        "bio_base_047_hsa05223.png",
        "bio_base_13_pi3k_akt.png",
    ],
    "lymphocyte": [
        "bio_base_048_hsa04659.png",
        "bio_base_049_hsa04660.png",
        "bio_base_078_hsa04662.png",
        "bio_base_086_hsa04658.png",
        "bio_base_040_hsa05170.png",
    ],
    "virus": [
        "bio_base_20_hcmv.png",
        "bio_base_09_kshv.png",
        "bio_base_039_hsa05171.png",
        "bio_base_036_hsa05165.png",
        "bio_base_052_hsa05168.png",
    ],
    "signaling": [
        "bio_base_13_pi3k_akt.png",
        "bio_base_055_hsa04010.png",
        "bio_base_043_hsa04064.png",
        "bio_base_081_hsa04630.png",
        "bio_base_03_tnf.png",
    ],
    "apoptosis": [
        "bio_base_044_hsa04210.png",
        "bio_base_18_ros_carcino.png",
        "bio_base_071_hsa04115.png",
    ],
    "hypoxia": [
        "bio_base_05_hif1.png",
        "bio_base_042_hsa04218.png",
    ],
    "metabolism": [
        "bio_base_068_hsa05230.png",
        "bio_base_054_hsa04931.png",
        "bio_base_088_hsa04920.png",
    ],
    "neuron": [
        "bio_base_066_hsa04722.png",
    ],
    "adhesion": [
        "bio_base_072_hsa04510.png",
        "bio_base_074_hsa04518.png",
    ],
}

# 关键词（英文 Description 小写子串）→ 原型
KEYWORD_ARCHETYPE: list[tuple[str, str]] = [
    ("virus", "virus"),
    ("viral", "virus"),
    ("herpes", "virus"),
    ("hepatitis", "hepatocyte"),
    ("liver", "hepatocyte"),
    ("hepatic", "hepatocyte"),
    ("fatty liver", "hepatocyte"),
    ("macrophage", "macrophage"),
    ("tuberculosis", "macrophage"),
    ("leishman", "macrophage"),
    ("salmonella", "macrophage"),
    ("yersinia", "macrophage"),
    ("legionell", "macrophage"),
    ("toxoplasm", "macrophage"),
    ("malaria", "macrophage"),
    ("amoeb", "epithelium"),
    ("shigell", "epithelium"),
    ("escherichia", "epithelium"),
    ("helicobacter", "epithelium"),
    ("inflammatory bowel", "epithelium"),
    ("intestinal", "epithelium"),
    ("epithelial", "epithelium"),
    ("tight junction", "epithelium"),
    ("gap junction", "epithelium"),
    ("adherens", "adhesion"),
    ("focal adhesion", "adhesion"),
    ("integrin", "adhesion"),
    ("cadherin", "adhesion"),
    ("cell adhesion", "adhesion"),
    ("endotheli", "endothelium"),
    ("VEGF", "endothelium"),
    ("vascular", "endothelium"),
    ("atherosclerosis", "endothelium"),
    ("shear", "endothelium"),
    ("platelet", "endothelium"),
    ("leukocyte transendothelial", "endothelium"),
    ("T cell", "lymphocyte"),
    ("B cell", "lymphocyte"),
    ("Th1", "lymphocyte"),
    ("Th2", "lymphocyte"),
    ("Th17", "lymphocyte"),
    ("natural killer", "lymphocyte"),
    ("HIV", "lymphocyte"),
    ("HTLV", "lymphocyte"),
    ("leukemia", "cancer"),
    ("cancer", "cancer"),
    ("carcinoma", "cancer"),
    ("melanoma", "cancer"),
    ("glioma", "cancer"),
    ("tumor", "cancer"),
    ("apoptosis", "apoptosis"),
    ("necroptosis", "apoptosis"),
    ("senescence", "hypoxia"),
    ("hypoxia", "hypoxia"),
    ("HIF", "hypoxia"),
    ("autophagy", "apoptosis"),
    ("mitophagy", "apoptosis"),
    ("neuro", "neuron"),
    ("synapse", "neuron"),
    ("axon", "neuron"),
    ("Alzheimer", "neuron"),
    ("prion", "neuron"),
    ("neurodegeneration", "neuron"),
    ("insulin", "metabolism"),
    ("diabetes", "metabolism"),
    ("glucagon", "metabolism"),
    ("adipocyte", "metabolism"),
    ("lipid", "metabolism"),
    ("metabolism", "metabolism"),
    ("steroid", "metabolism"),
    ("bile", "hepatocyte"),
    ("cytochrome", "metabolism"),
    ("MAPK", "signaling"),
    ("PI3K", "signaling"),
    ("mTOR", "signaling"),
    ("Ras", "signaling"),
    ("Rap1", "signaling"),
    ("JAK-STAT", "signaling"),
    ("NF-kappa", "signaling"),
    ("FoxO", "signaling"),
    ("Wnt", "signaling"),
    ("Hippo", "signaling"),
    ("TGF", "signaling"),
    ("ErbB", "signaling"),
    ("chemokine", "signaling"),
    ("cytokine", "signaling"),
    ("AMPK", "signaling"),
    ("cAMP", "signaling"),
    ("calcium", "signaling"),
    ("p53", "apoptosis"),
    ("cell cycle", "cancer"),
    ("thyroid", "signaling"),
    ("estrogen", "signaling"),
    ("oxytocin", "signaling"),
    ("prolactin", "signaling"),
    ("growth hormone", "signaling"),
    ("relaxin", "signaling"),
    ("osteoclast", "macrophage"),
    ("rheumatoid", "macrophage"),
    ("asthma", "macrophage"),
    ("complement", "signaling"),
    ("phagocyt", "macrophage"),
    ("efferocytosis", "macrophage"),
]


def pick_archetype(description: str, pathway_id: str = "") -> str:
    d = (description or "").lower()
    pid = (pathway_id or "").lower()
    text = f"{d} {pid}"
    for key, arch in KEYWORD_ARCHETYPE:
        if key.lower() in text:
            return arch
    # KEGG id class hints
    if pid.startswith("hsa052"):
        return "cancer"
    if pid.startswith("hsa051"):
        return "virus" if "virus" in d or "infection" in d else "macrophage"
    if pid.startswith("hsa040") or pid.startswith("hsa041") or pid.startswith("hsa043"):
        return "signaling"
    if pid.startswith("hsa046"):
        return "lymphocyte"
    if pid.startswith("hsa049"):
        return "metabolism"
    if pid.startswith("hsa047") or pid.startswith("hsa050"):
        return "neuron"
    if pid.startswith("hsa045"):
        return "adhesion"
    return "signaling"


def resolve_base(
    archetype: str,
    search_dirs: list[Path],
) -> Path | None:
    names = ARCHETYPES.get(archetype, []) + ARCHETYPES["signaling"]
    for name in names:
        for d in search_dirs:
            p = d / name
            if p.exists() and p.stat().st_size > 100_000:
                return p
    # any png fallback
    for d in search_dirs:
        cands = sorted(d.glob("bio_base_*.png"))
        if cands:
            return cands[0]
    return None


LIBRARY_README = """KEGG 动画素材库（底图复用）
========================

目的：同类通路共用一张精细插画底图，合成时只改：
  - 顶栏：KEGG编号 · 中文名
  - 副标题：英文全称
  - 右侧要点芯片

原型（archetype）：
  epithelium / macrophage / hepatocyte / endothelium /
  cancer / lymphocyte / virus / signaling / apoptosis /
  hypoxia / metabolism / neuron / adhesion

更新：运行 39_build_material_library.py 同步；
      40_compose_from_library.py 用素材库合成待绘通路。
"""
