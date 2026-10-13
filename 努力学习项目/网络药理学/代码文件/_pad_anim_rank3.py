# -*- coding: utf-8 -*-
from pathlib import Path
import re

for folder in (
    Path(r"E:/RProject/努力学习项目/网络药理学/交付文件/图片/动画_生物结构"),
    Path(r"D:/数据库/KEGG数据库/KEGG动画图"),
):
    for p in list(folder.glob("*.gif")):
        m = re.match(r"^(\d{2})_(.+)$", p.name)
        if not m:
            continue
        new = folder / f"{int(m.group(1)):03d}_{m.group(2)}"
        if new.exists():
            print("exists", new.name)
            continue
        p.rename(new)
        print(folder.name, "->", new.name)
print("done")
