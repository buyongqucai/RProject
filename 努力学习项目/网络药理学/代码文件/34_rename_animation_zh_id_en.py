# -*- coding: utf-8 -*-
"""Rename / rebuild bio-structure animations with 中文 + KEGG编号 + 英文 names.

Filename pattern:
  {Top20排名:02d}_{hsaXXXXX}_{中文}_{English}_动画.gif
  00_UC-EPITHELIUM_{中文}_{English}_动画.gif   # histology overview
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学/交付文件/图片/动画_生物结构")
DB_ANIM = Path(r"D:/数据库/KEGG数据库/KEGG动画图")

# old_out -> meta (rank uses Top20 for pathways; 00 for epithelium)
RENAME = [
    {
        "old": "01_肠上皮细胞_受体信号动画.gif",
        "rank": "00",
        "kegg": "UC-EPITHELIUM",
        "zh": "肠黏膜柱状上皮受体入口",
        "en": "Intestinal_columnar_epithelium_receptor_entry",
        "title": "UC-EPITHELIUM · 肠黏膜柱状上皮受体入口",
        "sub": "Intestinal columnar epithelium · receptor entry (UC context)",
    },
    {
        "old": "02_IL17信号通路_动画.gif",
        "rank": "05",
        "kegg": "hsa04657",
        "zh": "IL-17信号通路",
        "en": "IL-17_signaling_pathway",
        "title": "hsa04657 · IL-17信号通路",
        "sub": "IL-17 signaling pathway",
    },
    {
        "old": "03_TNF信号通路_动画.gif",
        "rank": "06",
        "kegg": "hsa04668",
        "zh": "TNF信号通路",
        "en": "TNF_signaling_pathway",
        "title": "hsa04668 · TNF信号通路",
        "sub": "TNF signaling pathway",
    },
    {
        "old": "04_TLR信号通路_动画.gif",
        "rank": "19",
        "kegg": "hsa04620",
        "zh": "Toll样受体信号通路",
        "en": "Toll-like_receptor_signaling_pathway",
        "title": "hsa04620 · Toll样受体信号通路",
        "sub": "Toll-like receptor signaling pathway",
    },
    {
        "old": "05_HIF1缺氧应答_动画.gif",
        "rank": "20",
        "kegg": "hsa04066",
        "zh": "HIF-1信号通路",
        "en": "HIF-1_signaling_pathway",
        "title": "hsa04066 · HIF-1信号通路",
        "sub": "HIF-1 signaling pathway",
    },
    {
        "old": "06_脂质动脉粥样硬化_动画.gif",
        "rank": "01",
        "kegg": "hsa05417",
        "zh": "脂质与动脉粥样硬化",
        "en": "Lipid_and_atherosclerosis",
        "title": "hsa05417 · 脂质与动脉粥样硬化",
        "sub": "Lipid and atherosclerosis",
    },
    {
        "old": "07_AGE-RAGE信号_动画.gif",
        "rank": "02",
        "kegg": "hsa04933",
        "zh": "AGE-RAGE信号通路",
        "en": "AGE-RAGE_signaling_pathway_in_diabetic_complications",
        "title": "hsa04933 · AGE-RAGE信号通路",
        "sub": "AGE-RAGE signaling pathway in diabetic complications",
    },
    {
        "old": "08_乙肝病毒感染_动画.gif",
        "rank": "03",
        "kegg": "hsa05161",
        "zh": "乙型肝炎",
        "en": "Hepatitis_B",
        "title": "hsa05161 · 乙型肝炎",
        "sub": "Hepatitis B",
    },
    {
        "old": "09_卡波西疱疹病毒_动画.gif",
        "rank": "04",
        "kegg": "hsa05167",
        "zh": "卡波西肉瘤疱疹病毒感染",
        "en": "Kaposi_sarcoma-associated_herpesvirus_infection",
        "title": "hsa05167 · 卡波西肉瘤疱疹病毒感染",
        "sub": "Kaposi sarcoma-associated herpesvirus infection",
    },
    {
        "old": "10_肿瘤蛋白聚糖_动画.gif",
        "rank": "07",
        "kegg": "hsa05205",
        "zh": "肿瘤中的蛋白聚糖",
        "en": "Proteoglycans_in_cancer",
        "title": "hsa05205 · 肿瘤中的蛋白聚糖",
        "sub": "Proteoglycans in cancer",
    },
    {
        "old": "11_血流剪切应力_动画.gif",
        "rank": "08",
        "kegg": "hsa05418",
        "zh": "血流剪切应力与动脉粥样硬化",
        "en": "Fluid_shear_stress_and_atherosclerosis",
        "title": "hsa05418 · 血流剪切应力与动脉粥样硬化",
        "sub": "Fluid shear stress and atherosclerosis",
    },
    {
        "old": "12_前列腺癌通路_动画.gif",
        "rank": "09",
        "kegg": "hsa05215",
        "zh": "前列腺癌",
        "en": "Prostate_cancer",
        "title": "hsa05215 · 前列腺癌",
        "sub": "Prostate cancer",
    },
    {
        "old": "13_PI3K-Akt信号_动画.gif",
        "rank": "10",
        "kegg": "hsa04151",
        "zh": "PI3K-Akt信号通路",
        "en": "PI3K-Akt_signaling_pathway",
        "title": "hsa04151 · PI3K-Akt信号通路",
        "sub": "PI3K-Akt signaling pathway",
    },
    {
        "old": "14_丙肝病毒感染_动画.gif",
        "rank": "11",
        "kegg": "hsa05160",
        "zh": "丙型肝炎",
        "en": "Hepatitis_C",
        "title": "hsa05160 · 丙型肝炎",
        "sub": "Hepatitis C",
    },
    {
        "old": "15_EGFR抑制剂耐药_动画.gif",
        "rank": "12",
        "kegg": "hsa01521",
        "zh": "EGFR酪氨酸激酶抑制剂耐药",
        "en": "EGFR_tyrosine_kinase_inhibitor_resistance",
        "title": "hsa01521 · EGFR酪氨酸激酶抑制剂耐药",
        "sub": "EGFR tyrosine kinase inhibitor resistance",
    },
    {
        "old": "16_PD-L1_PD-1检查点_动画.gif",
        "rank": "13",
        "kegg": "hsa05235",
        "zh": "PD-L1与PD-1检查点通路",
        "en": "PD-L1_expression_and_PD-1_checkpoint_pathway_in_cancer",
        "title": "hsa05235 · PD-L1与PD-1检查点通路",
        "sub": "PD-L1 expression and PD-1 checkpoint pathway in cancer",
    },
    {
        "old": "17_胰腺癌通路_动画.gif",
        "rank": "14",
        "kegg": "hsa05212",
        "zh": "胰腺癌",
        "en": "Pancreatic_cancer",
        "title": "hsa05212 · 胰腺癌",
        "sub": "Pancreatic cancer",
    },
    {
        "old": "18_化学致癌ROS_动画.gif",
        "rank": "15",
        "kegg": "hsa05208",
        "zh": "化学致癌-活性氧",
        "en": "Chemical_carcinogenesis_-_reactive_oxygen_species",
        "title": "hsa05208 · 化学致癌-活性氧",
        "sub": "Chemical carcinogenesis - reactive oxygen species",
    },
    {
        "old": "19_恰加斯病_动画.gif",
        "rank": "16",
        "kegg": "hsa05142",
        "zh": "恰加斯病",
        "en": "Chagas_disease",
        "title": "hsa05142 · 恰加斯病",
        "sub": "Chagas disease",
    },
    {
        "old": "20_巨细胞病毒感染_动画.gif",
        "rank": "17",
        "kegg": "hsa05163",
        "zh": "人巨细胞病毒感染",
        "en": "Human_cytomegalovirus_infection",
        "title": "hsa05163 · 人巨细胞病毒感染",
        "sub": "Human cytomegalovirus infection",
    },
    {
        "old": "21_内分泌耐药_动画.gif",
        "rank": "18",
        "kegg": "hsa01522",
        "zh": "内分泌耐药",
        "en": "Endocrine_resistance",
        "title": "hsa01522 · 内分泌耐药",
        "sub": "Endocrine resistance",
    },
]


def safe_en(s: str) -> str:
    s = s.replace(" ", "_")
    s = re.sub(r'[<>:"/\\|?*]', "-", s)
    return s


def make_name(m: dict) -> str:
    en = safe_en(m["en"])
    return f"{m['rank']}_{m['kegg']}_{m['zh']}_{en}_动画.gif"


def stamp_banner_on_gif(src: Path, dst: Path, title: str, sub: str) -> None:
    """Re-stamp only the top banner text onto each frame (no full recompose)."""
    from PIL import Image, ImageDraw, ImageFont

    def font(size: int):
        for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
        return ImageFont.load_default()

    im = Image.open(src)
    frames = []
    durations = []
    n = getattr(im, "n_frames", 1)
    for i in range(n):
        im.seek(i)
        frame = im.convert("RGB").copy()
        d = ImageDraw.Draw(frame)
        w, _ = frame.size
        d.rectangle((0, 0, w, 74), fill=(14, 48, 42))
        d.rectangle((0, 66, w, 78), fill=(8, 32, 28))
        d.text((28, 10), title, fill=(244, 255, 248), font=font(24))
        d.text((28, 44), sub, fill=(168, 210, 195), font=font(13))
        frames.append(frame)
        durations.append(im.info.get("duration", 75))
    frames[0].save(
        dst,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )


def main() -> None:
    dry = "--dry" in sys.argv
    restamp = "--no-restamp" not in sys.argv

    mapping_rows = []
    tmp = ROOT / "_rename_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()

    for m in RENAME:
        new_name = make_name(m)
        old_path = ROOT / m["old"]
        # also accept already-new name
        if not old_path.exists():
            cand = ROOT / new_name
            if cand.exists():
                old_path = cand
            else:
                print("MISSING", m["old"])
                continue
        mid = tmp / new_name
        if restamp and not dry:
            print("RESTAMP", new_name)
            stamp_banner_on_gif(old_path, mid, m["title"], m["sub"])
        else:
            print("COPY", new_name)
            if not dry:
                shutil.copy2(old_path, mid)
        mapping_rows.append((m["old"], new_name, m))

    if dry:
        for o, n, _ in mapping_rows:
            print(f"{o}\n  -> {n}")
        shutil.rmtree(tmp)
        return

    # remove old gifs in ROOT, move new in
    for p in ROOT.glob("*.gif"):
        p.unlink()
    for p in tmp.glob("*.gif"):
        shutil.move(str(p), str(ROOT / p.name))
    shutil.rmtree(tmp)

    # sync DB folder: wipe old, copy new
    DB_ANIM.mkdir(parents=True, exist_ok=True)
    for p in DB_ANIM.glob("*.gif"):
        p.unlink()
    for p in ROOT.glob("*.gif"):
        shutil.copy2(p, DB_ANIM / p.name)

    print("GIF count", len(list(ROOT.glob('*.gif'))))
    print("DB count", len(list(DB_ANIM.glob('*.gif'))))


if __name__ == "__main__":
    main()
