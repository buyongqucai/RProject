# -*- coding: utf-8 -*-
"""Cleanup old 2-digit PNGs; sync DB pathway folder to 001-183 only."""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

DELIV = Path(r"E:/RProject/努力学习项目/网络药理学/交付文件/图片/KEGG官方通路图")
DB = Path(r"D:/数据库/KEGG数据库/KEGG通路图")
MAN = DELIV / "00_全部通路图清单.csv"

df = pd.read_csv(MAN, encoding="utf-8-sig")
keep = set(df["file"].tolist())

# remove obsolete 2-digit in delivery
for p in DELIV.glob("[0-9][0-9]_hsa*.png"):
    print("RM deliv", p.name)
    p.unlink()

# rebuild DB folder from manifest
DB.mkdir(parents=True, exist_ok=True)
for p in list(DB.glob("*.png")):
    if p.name not in keep:
        p.unlink()
for fname in keep:
    src = DELIV / fname
    dst = DB / fname
    if src.exists():
        if not dst.exists() or src.stat().st_size != dst.stat().st_size:
            shutil.copy2(src, dst)

print("deliv png", len(list(DELIV.glob("*.png"))))
print("db png", len(list(DB.glob("*.png"))))
print("manifest", len(df))
