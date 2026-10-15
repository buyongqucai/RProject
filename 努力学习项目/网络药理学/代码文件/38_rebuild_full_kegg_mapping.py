# -*- coding: utf-8 -*-
"""Rebuild D:/数据库/KEGG数据库/KEGG通路动画映射表.xlsx for full KEGG.csv (001-183)."""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学/交付文件")
MAN = ROOT / "图片/KEGG官方通路图/00_全部通路图清单.csv"
ANIM = ROOT / "图片/动画_生物结构"
OUT = Path(r"D:/数据库/KEGG数据库")
PATH_DIR = OUT / "KEGG通路图"
ANIM_OUT = OUT / "KEGG动画图"
XLSX = OUT / "KEGG通路动画映射表.xlsx"

sys.path.insert(0, str(Path(r"E:/RProject/努力学习项目/网络药理学/代码文件")))
from kegg_zh_names import ZH  # noqa: E402


def safe_en(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", str(s), flags=re.UNICODE)
    return s.strip("_")[:80] or "pathway"


def expected_gif(rank: int, pid: str, en: str, zh: str) -> str:
    return f"{rank:03d}_{pid}_{zh}_{safe_en(en)}_动画.gif"


def find_gif(rank: int, pid: str) -> str:
    hits = sorted(ANIM.glob(f"{rank:03d}_{pid}_*_动画.gif"))
    if hits:
        return hits[0].name
    hits = sorted(ANIM.glob(f"{rank:02d}_{pid}_*_动画.gif"))
    if hits:
        return hits[0].name
    return ""


def main() -> None:
    df = pd.read_csv(MAN, encoding="utf-8-sig")
    PATH_DIR.mkdir(parents=True, exist_ok=True)
    ANIM_OUT.mkdir(parents=True, exist_ok=True)

    # sync pathway pngs
    for _, r in df.iterrows():
        src = ROOT / "图片/KEGG官方通路图" / r["file"]
        if src.exists():
            dst = PATH_DIR / r["file"]
            if not dst.exists() or src.stat().st_size != dst.stat().st_size:
                shutil.copy2(src, dst)

    # wipe DB anims and copy current (no 00)
    for p in ANIM_OUT.glob("*.gif"):
        p.unlink()
    for p in ANIM.glob("*.gif"):
        if p.name.startswith("00_"):
            continue
        shutil.copy2(p, ANIM_OUT / p.name)

    rows = []
    for _, r in df.iterrows():
        rank = int(r["rank"])
        pid = str(r["pathway_id"]).strip()
        en = str(r["description"]).strip()
        zh = ZH.get(pid, "")
        gif = find_gif(rank, pid)
        has = bool(gif) and (ANIM / gif).exists()
        rows.append(
            {
                "排名": rank,
                "KEGG编号": pid,
                "通路中文名": zh,
                "通路英文名": en,
                "动画状态": "已绘制" if has else "待绘制",
                "动画GIF": gif if has else expected_gif(rank, pid, en, zh or "待命名"),
                "官方通路图PNG": r["file"],
                "KEGG官方图URL": r["url"],
            }
        )
    out = pd.DataFrame(rows)
    n_done = int((out["动画状态"] == "已绘制").sum())
    n_pending = int((out["动画状态"] == "待绘制").sum())
    with pd.ExcelWriter(XLSX, engine="openpyxl") as w:
        out.to_excel(w, sheet_name="通路动画映射", index=False)
        pd.DataFrame(
            [
                {"项目": "通路总数(KEGG.csv)", "数值": len(out)},
                {"项目": "官方通路图已下载", "数值": len(list(PATH_DIR.glob('*.png')))},
                {"项目": "动画已绘制", "数值": n_done},
                {"项目": "动画待绘制", "数值": n_pending},
                {"项目": "命名规范", "数值": "{排名3位}_{KEGG}_{中文}_{English}_动画.gif"},
                {"项目": "计数起点", "数值": "001"},
            ]
        ).to_excel(w, sheet_name="统计摘要", index=False)

    print("OK", XLSX)
    print(f"png={len(list(PATH_DIR.glob('*.png')))} gif={len(list(ANIM_OUT.glob('*.gif')))} done={n_done} pending={n_pending}")


if __name__ == "__main__":
    main()
