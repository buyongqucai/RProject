# -*- coding: utf-8 -*-
"""整理 D:/数据库/KEGG数据库：扁平三目录结构。

  KEGG通路动画映射表.xlsx
  KEGG通路图/          ← Top20 官方通路 PNG
  KEGG动画图/          ← 已绘制生物结构 GIF

动画命名规范：
  {Top20排名}_{hsaXXXXX}_{中文}_{English}_动画.gif
  00_UC-EPITHELIUM_{中文}_{English}_动画.gif
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学/交付文件")
TOP20_CSV = ROOT / "图片/KEGG官方通路图/00_Top20通路图清单.csv"
ANIM_DIR = ROOT / "图片/动画_生物结构"
KEGG_PNG_DIR = ROOT / "图片/KEGG官方通路图"
OUT = Path(r"D:/数据库/KEGG数据库")

PATH_DIR = OUT / "KEGG通路图"
ANIM_OUT = OUT / "KEGG动画图"
XLSX = OUT / "KEGG通路动画映射表.xlsx"

# Top20 KEGG id -> animation meta
PATHWAY_ANIM = {
    "hsa05417": {
        "gif": "01_hsa05417_脂质与动脉粥样硬化_Lipid_and_atherosclerosis_动画.gif",
        "zh": "脂质与动脉粥样硬化",
        "en": "Lipid and atherosclerosis",
    },
    "hsa04933": {
        "gif": "02_hsa04933_AGE-RAGE信号通路_AGE-RAGE_signaling_pathway_in_diabetic_complications_动画.gif",
        "zh": "AGE-RAGE信号通路",
        "en": "AGE-RAGE signaling pathway in diabetic complications",
    },
    "hsa05161": {
        "gif": "03_hsa05161_乙型肝炎_Hepatitis_B_动画.gif",
        "zh": "乙型肝炎",
        "en": "Hepatitis B",
    },
    "hsa05167": {
        "gif": "04_hsa05167_卡波西肉瘤疱疹病毒感染_Kaposi_sarcoma-associated_herpesvirus_infection_动画.gif",
        "zh": "卡波西肉瘤疱疹病毒感染",
        "en": "Kaposi sarcoma-associated herpesvirus infection",
    },
    "hsa04657": {
        "gif": "05_hsa04657_IL-17信号通路_IL-17_signaling_pathway_动画.gif",
        "zh": "IL-17信号通路",
        "en": "IL-17 signaling pathway",
    },
    "hsa04668": {
        "gif": "06_hsa04668_TNF信号通路_TNF_signaling_pathway_动画.gif",
        "zh": "TNF信号通路",
        "en": "TNF signaling pathway",
    },
    "hsa05205": {
        "gif": "07_hsa05205_肿瘤中的蛋白聚糖_Proteoglycans_in_cancer_动画.gif",
        "zh": "肿瘤中的蛋白聚糖",
        "en": "Proteoglycans in cancer",
    },
    "hsa05418": {
        "gif": "08_hsa05418_血流剪切应力与动脉粥样硬化_Fluid_shear_stress_and_atherosclerosis_动画.gif",
        "zh": "血流剪切应力与动脉粥样硬化",
        "en": "Fluid shear stress and atherosclerosis",
    },
    "hsa05215": {
        "gif": "09_hsa05215_前列腺癌_Prostate_cancer_动画.gif",
        "zh": "前列腺癌",
        "en": "Prostate cancer",
    },
    "hsa04151": {
        "gif": "10_hsa04151_PI3K-Akt信号通路_PI3K-Akt_signaling_pathway_动画.gif",
        "zh": "PI3K-Akt信号通路",
        "en": "PI3K-Akt signaling pathway",
    },
    "hsa05160": {
        "gif": "11_hsa05160_丙型肝炎_Hepatitis_C_动画.gif",
        "zh": "丙型肝炎",
        "en": "Hepatitis C",
    },
    "hsa01521": {
        "gif": "12_hsa01521_EGFR酪氨酸激酶抑制剂耐药_EGFR_tyrosine_kinase_inhibitor_resistance_动画.gif",
        "zh": "EGFR酪氨酸激酶抑制剂耐药",
        "en": "EGFR tyrosine kinase inhibitor resistance",
    },
    "hsa05235": {
        "gif": "13_hsa05235_PD-L1与PD-1检查点通路_PD-L1_expression_and_PD-1_checkpoint_pathway_in_cancer_动画.gif",
        "zh": "PD-L1与PD-1检查点通路",
        "en": "PD-L1 expression and PD-1 checkpoint pathway in cancer",
    },
    "hsa05212": {
        "gif": "14_hsa05212_胰腺癌_Pancreatic_cancer_动画.gif",
        "zh": "胰腺癌",
        "en": "Pancreatic cancer",
    },
    "hsa05208": {
        "gif": "15_hsa05208_化学致癌-活性氧_Chemical_carcinogenesis_-_reactive_oxygen_species_动画.gif",
        "zh": "化学致癌-活性氧",
        "en": "Chemical carcinogenesis - reactive oxygen species",
    },
    "hsa05142": {
        "gif": "16_hsa05142_恰加斯病_Chagas_disease_动画.gif",
        "zh": "恰加斯病",
        "en": "Chagas disease",
    },
    "hsa05163": {
        "gif": "17_hsa05163_人巨细胞病毒感染_Human_cytomegalovirus_infection_动画.gif",
        "zh": "人巨细胞病毒感染",
        "en": "Human cytomegalovirus infection",
    },
    "hsa01522": {
        "gif": "18_hsa01522_内分泌耐药_Endocrine_resistance_动画.gif",
        "zh": "内分泌耐药",
        "en": "Endocrine resistance",
    },
    "hsa04620": {
        "gif": "19_hsa04620_Toll样受体信号通路_Toll-like_receptor_signaling_pathway_动画.gif",
        "zh": "Toll样受体信号通路",
        "en": "Toll-like receptor signaling pathway",
    },
    "hsa04066": {
        "gif": "20_hsa04066_HIF-1信号通路_HIF-1_signaling_pathway_动画.gif",
        "zh": "HIF-1信号通路",
        "en": "HIF-1 signaling pathway",
    },
}

CONTEXT_ANIM = {
    "模块类型": "组织学总览（非单一KEGG）",
    "模块编号": "UC-EPITHELIUM",
    "Top20排名": "",
    "KEGG编号": "UC-EPITHELIUM",
    "通路中文名": "肠黏膜柱状上皮受体入口",
    "通路英文名": "Intestinal columnar epithelium · receptor entry (UC context)",
    "动画状态": "已绘制",
    "动画GIF": "00_UC-EPITHELIUM_肠黏膜柱状上皮受体入口_Intestinal_columnar_epithelium_receptor_entry_动画.gif",
    "官方通路图PNG": "",
    "KEGG官方图URL": "",
    "说明": "组织学总览，不对应单一 Top20 通路编号；覆盖 LPS/TNF/IL-17 等入口",
}

OLD_DIRS = ["映射表", "官方通路图_副本", "生物结构动画_索引", "已绘制", "待绘制"]
OLD_FILES = ["README.txt"]


def rmtree(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.is_file():
        path.unlink()


def sync_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if (
        not dst.exists()
        or src.stat().st_mtime > dst.stat().st_mtime
        or src.stat().st_size != dst.stat().st_size
    ):
        shutil.copy2(src, dst)


def main() -> None:
    PATH_DIR.mkdir(parents=True, exist_ok=True)
    ANIM_OUT.mkdir(parents=True, exist_ok=True)

    for p in sorted(KEGG_PNG_DIR.glob("*.png")):
        sync_file(p, PATH_DIR / p.name)

    # wipe then copy all current gifs (avoid stale old names)
    for p in ANIM_OUT.glob("*.gif"):
        p.unlink()
    gifs = [CONTEXT_ANIM["动画GIF"]] + [v["gif"] for v in PATHWAY_ANIM.values()]
    for name in gifs:
        src = ANIM_DIR / name
        if src.exists():
            sync_file(src, ANIM_OUT / name)

    top = pd.read_csv(TOP20_CSV, encoding="utf-8-sig")
    rows = []
    for _, r in top.iterrows():
        pid = str(r["pathway_id"]).strip()
        info = PATHWAY_ANIM.get(pid, {})
        gif = info.get("gif", "")
        has_anim = bool(gif) and (ANIM_DIR / gif).exists()
        rows.append(
            {
                "模块类型": "Top20通路",
                "模块编号": pid,
                "Top20排名": int(r["rank"]),
                "KEGG编号": pid,
                "通路中文名": info.get("zh", ""),
                "通路英文名": info.get("en", r["description"]),
                "动画状态": "已绘制" if has_anim else "待绘制",
                "动画GIF": gif if has_anim else "",
                "官方通路图PNG": r["file"],
                "KEGG官方图URL": r["url"],
                "说明": "",
            }
        )
    rows.append(CONTEXT_ANIM)
    df = pd.DataFrame(rows)

    with pd.ExcelWriter(XLSX, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="通路动画映射", index=False)
        n_top = int((df["模块类型"] == "Top20通路").sum())
        n_done = int(((df["模块类型"] == "Top20通路") & (df["动画状态"] == "已绘制")).sum())
        n_pending = int(((df["模块类型"] == "Top20通路") & (df["动画状态"] == "待绘制")).sum())
        summary = pd.DataFrame(
            [
                {"项目": "Top20通路总数", "数值": n_top},
                {"项目": "Top20已绘制动画", "数值": n_done},
                {"项目": "Top20待绘制动画", "数值": n_pending},
                {"项目": "组织学入口动画", "数值": 1},
                {"项目": "命名规范", "数值": "{排名}_{KEGG编号}_{中文}_{English}_动画.gif"},
                {"项目": "KEGG通路图目录", "数值": str(PATH_DIR)},
                {"项目": "KEGG动画图目录", "数值": str(ANIM_OUT)},
            ]
        )
        summary.to_excel(writer, sheet_name="统计摘要", index=False)

    for name in OLD_DIRS:
        rmtree(OUT / name)
    for name in OLD_FILES:
        rmtree(OUT / name)

    # refresh album html from current gifs
    cards = []
    for p in sorted(ANIM_DIR.glob("*.gif")):
        cards.append(f'<article class="card"><img src="{p.name}" alt="{p.stem}"/><h3>{p.stem}</h3></article>')
    (ANIM_DIR / "动画图册.html").write_text(
        f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"/>
<title>生物结构动画图册</title>
<style>
body{{margin:0;font-family:"Microsoft YaHei",sans-serif;background:#E4D9C8;color:#1C2A24}}
header{{padding:28px;background:#12352E;color:#F4FFF9}}
main{{max-width:1600px;margin:0 auto;padding:20px;display:grid;gap:20px}}
.card{{background:#FFFCFA;border-radius:16px;overflow:hidden;border:1px solid #C9B8A0}}
.card img{{width:100%;display:block}}
.card h3{{margin:14px 18px 18px;color:#1A4F42;font-size:15px;word-break:break-all}}
</style></head><body>
<header><h1>人体生物结构 · 生动解剖动画</h1>
<p>命名：排名_KEGG编号_中文_English_动画.gif · 顶栏含编号+中文+英文</p></header>
<main>{''.join(cards)}</main></body></html>""",
        encoding="utf-8",
    )
    (ANIM_DIR / "README.txt").write_text(
        "生动生物结构动画\n"
        "命名规范：{Top20排名}_{hsaXXXXX}_{中文}_{English}_动画.gif\n"
        "组织学入口：00_UC-EPITHELIUM_{中文}_{English}_动画.gif\n"
        "顶栏：KEGG编号 · 中文名 / 英文全称\n"
        "打开 动画图册.html 浏览。\n",
        encoding="utf-8",
    )

    print("OK", XLSX)
    print(f"通路图={len(list(PATH_DIR.glob('*.png')))} 动画GIF={len(list(ANIM_OUT.glob('*.gif')))}")
    print(f"done={n_done} pending={n_pending}")


if __name__ == "__main__":
    main()
