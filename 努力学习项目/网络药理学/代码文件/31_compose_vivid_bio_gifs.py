# -*- coding: utf-8 -*-
"""Compose vivid bio GIFs from detailed illustration bases + animated overlays."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学/交付文件/图片/动画_生物结构")
BASES = ROOT / "_bases"
ASSETS = Path(r"C:/Users/10540/.cursor/projects/e-RProject/assets")
CODE = Path(r"E:/RProject/努力学习项目/网络药理学/代码文件")
sys.path.insert(0, str(CODE))
from bio_compose_utils import DUR, animate_frames, prepare_base  # noqa: E402

SPECS = [
    {
        "src": "bio_base_01_epithelium.png",
        "out": "00_UC-EPITHELIUM_肠黏膜柱状上皮受体入口_Intestinal_columnar_epithelium_receptor_entry_动画.gif",
        "kegg": "",
        "title": "UC-EPITHELIUM · 肠黏膜柱状上皮受体入口",
        "sub": "Intestinal columnar epithelium · receptor entry (UC context)",
        "path": [(780, 220), (800, 340), (790, 480), (800, 620)],
        "notes": ["刷状缘 + 受体", "胞质细胞器", "基底核 / 固有层"],
    },
    {
        "src": "bio_base_02_il17.png",
        "out": "05_hsa04657_IL-17信号通路_IL-17_signaling_pathway_动画.gif",
        "kegg": "hsa04657",
        "title": "hsa04657 · IL-17信号通路",
        "sub": "IL-17 signaling pathway",
        "path": [(520, 360), (700, 380), (880, 420), (1050, 500)],
        "notes": ["配体-受体", "信号小体", "核孔入核"],
    },
    {
        "src": "bio_base_03_tnf.png",
        "out": "06_hsa04668_TNF信号通路_TNF_signaling_pathway_动画.gif",
        "kegg": "hsa04668",
        "title": "hsa04668 · TNF信号通路",
        "sub": "TNF signaling pathway",
        "path": [(480, 420), (700, 450), (900, 480), (1100, 500)],
        "notes": ["抗 TNF 轴", "跨膜复合体", "核应答"],
    },
    {
        "src": "bio_base_04_tlr.png",
        "out": "19_hsa04620_Toll样受体信号通路_Toll-like_receptor_signaling_pathway_动画.gif",
        "kegg": "hsa04620",
        "title": "hsa04620 · Toll样受体信号通路",
        "sub": "Toll-like receptor signaling pathway",
        "path": [(520, 400), (720, 430), (920, 470), (1120, 520)],
        "notes": ["病原识别", "Myddosome", "炎症转录"],
    },
    {
        "src": "bio_base_05_hif1.png",
        "out": "20_hsa04066_HIF-1信号通路_HIF-1_signaling_pathway_动画.gif",
        "kegg": "hsa04066",
        "title": "hsa04066 · HIF-1信号通路",
        "sub": "HIF-1 signaling pathway",
        "path": [(620, 380), (780, 450), (900, 520), (980, 560)],
        "notes": ["氧梯度", "HIF-1α 入核", "UC 黏膜缺氧"],
    },
    # --- Top20 补绘（原待绘制 16 条）---
    {
        "src": "bio_base_06_lipid_athero.png",
        "out": "01_hsa05417_脂质与动脉粥样硬化_Lipid_and_atherosclerosis_动画.gif",
        "kegg": "hsa05417",
        "title": "hsa05417 · 脂质与动脉粥样硬化",
        "sub": "Lipid and atherosclerosis",
        "path": [(420, 380), (620, 420), (820, 470), (1050, 520)],
        "notes": ["oxLDL 摄取", "泡沫细胞", "炎症入核"],
    },
    {
        "src": "bio_base_07_age_rage.png",
        "out": "02_hsa04933_AGE-RAGE信号通路_AGE-RAGE_signaling_pathway_in_diabetic_complications_动画.gif",
        "kegg": "hsa04933",
        "title": "hsa04933 · AGE-RAGE信号通路",
        "sub": "AGE-RAGE signaling pathway in diabetic complications",
        "path": [(450, 360), (680, 400), (900, 460), (1100, 520)],
        "notes": ["AGE-RAGE", "ROS 爆发", "NF-κB 入核"],
    },
    {
        "src": "bio_base_08_hepatitis_b.png",
        "out": "03_hsa05161_乙型肝炎_Hepatitis_B_动画.gif",
        "kegg": "hsa05161",
        "title": "hsa05161 · 乙型肝炎",
        "sub": "Hepatitis B",
        "path": [(400, 350), (650, 400), (900, 470), (1120, 540)],
        "notes": ["病毒入胞", "信号复合体", "核应答"],
    },
    {
        "src": "bio_base_09_kshv.png",
        "out": "04_hsa05167_卡波西肉瘤疱疹病毒感染_Kaposi_sarcoma-associated_herpesvirus_infection_动画.gif",
        "kegg": "hsa05167",
        "title": "hsa05167 · 卡波西肉瘤疱疹病毒感染",
        "sub": "Kaposi sarcoma-associated herpesvirus infection",
        "path": [(430, 340), (680, 400), (920, 470), (1150, 530)],
        "notes": ["病毒识别", "PI3K/NF-κB", "VEGF 分泌"],
    },
    {
        "src": "bio_base_10_proteoglycans.png",
        "out": "07_hsa05205_肿瘤中的蛋白聚糖_Proteoglycans_in_cancer_动画.gif",
        "kegg": "hsa05205",
        "title": "hsa05205 · 肿瘤中的蛋白聚糖",
        "sub": "Proteoglycans in cancer",
        "path": [(380, 320), (620, 400), (880, 480), (1120, 540)],
        "notes": ["ECM 捕获", "RTK 激活", "增殖入核"],
    },
    {
        "src": "bio_base_11_shear_athero.png",
        "out": "08_hsa05418_血流剪切应力与动脉粥样硬化_Fluid_shear_stress_and_atherosclerosis_动画.gif",
        "kegg": "hsa05418",
        "title": "hsa05418 · 血流剪切应力与动脉粥样硬化",
        "sub": "Fluid shear stress and atherosclerosis",
        "path": [(500, 280), (700, 380), (900, 480), (1100, 560)],
        "notes": ["剪切力", "机械感受", "Nrf2 入核"],
    },
    {
        "src": "bio_base_12_prostate.png",
        "out": "09_hsa05215_前列腺癌_Prostate_cancer_动画.gif",
        "kegg": "hsa05215",
        "title": "hsa05215 · 前列腺癌",
        "sub": "Prostate cancer",
        "path": [(450, 360), (700, 420), (920, 490), (1120, 550)],
        "notes": ["受体激活", "PI3K-Akt", "核内应答"],
    },
    {
        "src": "bio_base_13_pi3k_akt.png",
        "out": "10_hsa04151_PI3K-Akt信号通路_PI3K-Akt_signaling_pathway_动画.gif",
        "kegg": "hsa04151",
        "title": "hsa04151 · PI3K-Akt信号通路",
        "sub": "PI3K-Akt signaling pathway",
        "path": [(420, 340), (680, 400), (900, 480), (1120, 540)],
        "notes": ["RTK", "PIP3/Akt", "mTOR/入核"],
    },
    {
        "src": "bio_base_14_hepatitis_c.png",
        "out": "11_hsa05160_丙型肝炎_Hepatitis_C_动画.gif",
        "kegg": "hsa05160",
        "title": "hsa05160 · 丙型肝炎",
        "sub": "Hepatitis C",
        "path": [(400, 350), (650, 410), (900, 480), (1120, 540)],
        "notes": ["HCV 入胞", "脂滴应激", "IFN 入核"],
    },
    {
        "src": "bio_base_15_egfr_tki.png",
        "out": "12_hsa01521_EGFR酪氨酸激酶抑制剂耐药_EGFR_tyrosine_kinase_inhibitor_resistance_动画.gif",
        "kegg": "hsa01521",
        "title": "hsa01521 · EGFR酪氨酸激酶抑制剂耐药",
        "sub": "EGFR tyrosine kinase inhibitor resistance",
        "path": [(430, 360), (680, 420), (920, 490), (1140, 550)],
        "notes": ["耐药旁路", "PI3K-Akt", "生存入核"],
    },
    {
        "src": "bio_base_16_pdl1_pd1.png",
        "out": "13_hsa05235_PD-L1与PD-1检查点通路_PD-L1_expression_and_PD-1_checkpoint_pathway_in_cancer_动画.gif",
        "kegg": "hsa05235",
        "title": "hsa05235 · PD-L1与PD-1检查点通路",
        "sub": "PD-L1 expression and PD-1 checkpoint pathway in cancer",
        "path": [(520, 380), (720, 420), (900, 460), (1080, 520)],
        "notes": ["免疫突触", "检查点抑制", "T 细胞失能"],
    },
    {
        "src": "bio_base_17_pancreatic.png",
        "out": "14_hsa05212_胰腺癌_Pancreatic_cancer_动画.gif",
        "kegg": "hsa05212",
        "title": "hsa05212 · 胰腺癌",
        "sub": "Pancreatic cancer",
        "path": [(440, 350), (680, 410), (920, 480), (1140, 540)],
        "notes": ["KRAS 驱动", "MAPK/PI3K", "MYC 入核"],
    },
    {
        "src": "bio_base_18_ros_carcino.png",
        "out": "15_hsa05208_化学致癌-活性氧_Chemical_carcinogenesis_-_reactive_oxygen_species_动画.gif",
        "kegg": "hsa05208",
        "title": "hsa05208 · 化学致癌-活性氧",
        "sub": "Chemical carcinogenesis - reactive oxygen species",
        "path": [(450, 360), (700, 420), (920, 490), (1120, 550)],
        "notes": ["ROS 爆发", "DNA 损伤", "Nrf2 应答"],
    },
    {
        "src": "bio_base_19_chagas.png",
        "out": "16_hsa05142_恰加斯病_Chagas_disease_动画.gif",
        "kegg": "hsa05142",
        "title": "hsa05142 · 恰加斯病",
        "sub": "Chagas disease",
        "path": [(420, 350), (680, 410), (920, 480), (1140, 540)],
        "notes": ["病原识别", "TLR 轴", "炎症入核"],
    },
    {
        "src": "bio_base_20_hcmv.png",
        "out": "17_hsa05163_人巨细胞病毒感染_Human_cytomegalovirus_infection_动画.gif",
        "kegg": "hsa05163",
        "title": "hsa05163 · 人巨细胞病毒感染",
        "sub": "Human cytomegalovirus infection",
        "path": [(430, 340), (680, 400), (920, 470), (1140, 540)],
        "notes": ["病毒入胞", "PI3K/NF-κB", "核内程序"],
    },
    {
        "src": "bio_base_21_endocrine_res.png",
        "out": "18_hsa01522_内分泌耐药_Endocrine_resistance_动画.gif",
        "kegg": "hsa01522",
        "title": "hsa01522 · 内分泌耐药",
        "sub": "Endocrine resistance",
        "path": [(440, 360), (700, 420), (940, 490), (1140, 550)],
        "notes": ["激素串扰", "旁路激活", "耐药入核"],
    },
]


def main():
    import sys

    only_new = "--all" not in sys.argv
    BASES.mkdir(parents=True, exist_ok=True)
    for spec in SPECS:
        out = ROOT / spec["out"]
        if only_new and out.exists() and out.stat().st_size > 1_000_000:
            print("SKIP", out.name)
            continue
        src = ASSETS / spec["src"]
        if not src.exists():
            src = BASES / spec["src"]
        if not src.exists():
            raise FileNotFoundError(src)
        shutil.copy2(src, BASES / spec["src"])
        base = prepare_base(src)
        frames = animate_frames(base, spec["title"], spec["sub"], spec["notes"], spec["path"])
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=DUR, loop=0, optimize=True)
        print("OK", out.name)

    items = [(s["out"], s["title"]) for s in SPECS]
    cards = "".join(
        f'<article class="card"><img src="{fn}" alt="{t}"/><h3>{t}</h3></article>' for fn, t in items
    )
    (ROOT / "动画图册.html").write_text(
        f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"/>
<title>生物结构动画图册</title>
<style>
body{{margin:0;font-family:"Microsoft YaHei",sans-serif;background:#E4D9C8;color:#1C2A24}}
header{{padding:28px;background:#12352E;color:#F4FFF9}}
main{{max-width:1600px;margin:0 auto;padding:20px;display:grid;gap:20px}}
.card{{background:#FFFCFA;border-radius:16px;overflow:hidden;border:1px solid #C9B8A0}}
.card img{{width:100%;display:block}}
.card h3{{margin:14px 18px 18px;color:#1A4F42}}
</style></head><body>
<header><h1>人体生物结构 · 生动解剖动画</h1>
<p>精细细胞/组织插画底图 + 信号流动动画层。底图见 _bases/。Top20 KEGG 通路已全覆盖。</p></header>
<main>{cards}</main></body></html>""",
        encoding="utf-8",
    )
    (ROOT / "README.txt").write_text(
        "生动生物结构动画\n"
        "- GIF：插画级细胞/组织底图 + 信号流动/呼吸高光\n"
        "- _bases/：高细节静帧底图\n"
        "- 含 Top20 KEGG 1:1 动画 + 组织学入口\n"
        "打开 动画图册.html 浏览。\n",
        encoding="utf-8",
    )
    print("DONE", ROOT)


if __name__ == "__main__":
    main()
