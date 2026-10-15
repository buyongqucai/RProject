# -*- coding: utf-8 -*-
"""Export organelle element PNGs to _元素库 and D:/数据库/KEGG数据库/KEGG元素库."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学")
OUT_DELIV = ROOT / "交付文件" / "图片" / "动画_生物结构" / "_元素库"
OUT_DB = Path(r"D:/数据库/KEGG数据库/KEGG元素库")

sys.path.insert(0, str(ROOT / "代码文件"))
from bio_element_library import ELEMENTS, render_element  # noqa: E402


def main() -> None:
    for d in (OUT_DELIV, OUT_DB):
        d.mkdir(parents=True, exist_ok=True)
    rows = []
    for spec in ELEMENTS:
        im = render_element(spec)
        fname = f"{spec.id}_{spec.name_zh}.png"
        im.save(OUT_DELIV / fname)
        im.save(OUT_DB / fname)
        rows.append(
            {
                "元素ID": spec.id,
                "中文名": spec.name_zh,
                "英文名": spec.name_en,
                "宽": spec.width,
                "高": spec.height,
                "文件": fname,
            }
        )
    cat = pd.DataFrame(rows)
    cat.to_csv(OUT_DELIV / "元素库目录.csv", index=False, encoding="utf-8-sig")
    cat.to_excel(OUT_DB / "元素库目录.xlsx", index=False)
    shutil.copy2(OUT_DELIV / "元素库目录.csv", OUT_DB / "元素库目录.csv")
    (OUT_DELIV / "README.txt").write_text(
        "细胞器小元素库（线粒体/内质网/细胞核等）\n"
        "由 bio_element_library.py 本地绘制，可拼装通路动画。\n"
        "运行 42_compose_from_elements.py 合成。\n",
        encoding="utf-8",
    )
    shutil.copy2(OUT_DELIV / "README.txt", OUT_DB / "README.txt")
    print("OK elements", len(rows), "->", OUT_DB)


if __name__ == "__main__":
    main()
