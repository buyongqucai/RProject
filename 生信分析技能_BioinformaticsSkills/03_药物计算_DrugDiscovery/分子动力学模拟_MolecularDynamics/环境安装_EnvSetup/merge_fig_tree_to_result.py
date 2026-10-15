# -*- coding: utf-8 -*-
"""合并 图册 旧层级→新层级（课题交付：结果文件/与代码文件、数据文件平级），旧路径留 junction。"""
import shutil
import subprocess
from pathlib import Path

base = Path(r"E:\RProject\努力学习项目\08_分子动力学")
old = base / "文档文件" / "图片文件" / "分子动力学图_MD"
new = base / "结果文件" / "图片文件" / "分子动力学图_MD"
new.mkdir(parents=True, exist_ok=True)

for item in sorted(old.iterdir()):
    dst = new / item.name
    if item.is_dir():
        shutil.copytree(item, dst, dirs_exist_ok=True)
        shutil.rmtree(item)
    else:
        shutil.move(str(item), str(dst))

n_old = sum(1 for x in old.rglob("*") if x.is_file())
n_new = sum(1 for x in new.rglob("*") if x.is_file())
print(f"old={n_old} new={n_new}")
if n_old == 0 and old.is_dir():
    old.rmdir()
    print("old dir removed")
    r = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(old), str(new)],
        capture_output=True, text=True,
    )
    print("junction:", r.stdout.strip() or r.stderr.strip())
