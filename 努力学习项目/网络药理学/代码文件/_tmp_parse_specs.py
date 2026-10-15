# -*- coding: utf-8 -*-
import re
from pathlib import Path

t = Path(r"E:/RProject/努力学习项目/网络药理学/代码文件/31_compose_vivid_bio_gifs.py").read_text(encoding="utf-8")
srcs = re.findall(r'"src":\s*"([^"]+)"', t)
outs = re.findall(r'"out":\s*"([^"]+)"', t)
print(len(srcs), len(outs))
for s, o in zip(srcs, outs):
    print(o[:6], "->", s)
