# -*- coding: utf-8 -*-
"""Copy GenerateImage bases into 努力学习项目 _bases."""
from __future__ import annotations
import shutil
from pathlib import Path

SRC = Path(r"C:\Users\10540\.cursor\projects\e-RProject-BioinformaticsSkills\assets")
DST = Path(r"E:\RProject\努力学习项目\网络药理学\交付文件\图片\动画_生物结构\_bases")
DST.mkdir(parents=True, exist_ok=True)
n = 0
for p in SRC.glob("bio_base_*.png"):
    shutil.copy2(p, DST / p.name)
    n += 1
print("copied", n, "to", DST)
