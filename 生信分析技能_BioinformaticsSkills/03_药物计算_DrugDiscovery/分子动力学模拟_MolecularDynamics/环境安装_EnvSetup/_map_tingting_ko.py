# -*- coding: utf-8 -*-
from pathlib import Path
root = Path(r"C:/Users/10540/Desktop/婷婷/虚拟敲除")

def walk(p: Path, depth=0, maxd=3):
    if depth > maxd:
        return
    kids = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    dirs = [k for k in kids if k.is_dir()]
    files = [k for k in kids if k.is_file()]
    ind = "  " * depth
    if depth == 0:
        print(f"{p}  dirs={len(dirs)} files={len(files)}")
    else:
        n = sum(1 for x in p.rglob("*") if x.is_file())
        print(f"{ind}{p.name}/  ({n} files)")
    if depth < maxd:
        for d in dirs:
            walk(d, depth + 1, maxd)
    if depth <= 1:
        for f in files[:15]:
            print(f"{ind}  {f.name}")
        if len(files) > 15:
            print(f"{ind}  ... +{len(files)-15} files")

walk(root, 0, 3)
print("TOTAL_FILES", sum(1 for x in root.rglob("*") if x.is_file()))
