# -*- coding: utf-8 -*-
"""收口：图册时序核对 → 报告路径规范化 → 撤 junction → 门禁/出血终验。"""
import os
import shutil
import subprocess
from pathlib import Path

base = Path(r"E:\RProject\努力学习项目\08_分子动力学")
fig_root = base / "结果文件" / "图片文件" / "分子动力学图_MD"
old_link = base / "文档文件" / "图片文件" / "分子动力学图_MD"

# 1) 时序：图新于 CSV = 用定稿数据画的
for sys_dir in sorted(fig_root.iterdir()):
    if not sys_dir.is_dir():
        continue
    csvs = list((Path(r"E:\Origin_Data") / sys_dir.name).glob("*.csv"))
    figs = list(sys_dir.rglob("*.png"))
    if csvs and figs:
        newest_csv = max(c.stat().st_mtime for c in csvs)
        newest_fig = max(f.stat().st_mtime for f in figs)
        oldest_fig = min(f.stat().st_mtime for f in figs)
        print(f"{sys_dir.name}: fig_newest>=csv_newest? {newest_fig >= newest_csv}")

# 2) 报告路径替换（文档文件\图片文件 → 结果文件\图片文件）
n_rep = 0
for rep in Path(r"E:\RProject\努力学习项目").rglob("*.html"):
    t = rep.read_text(encoding="utf-8", errors="replace")
    t2 = t.replace("08_分子动力学/文档文件/图片文件", "08_分子动力学/结果文件/图片文件")
    t2 = t2.replace("08_分子动力学\\文档文件\\图片文件", "08_分子动力学\\结果文件\\图片文件")
    if t2 != t:
        rep.write_text(t2, encoding="utf-8")
        n_rep += 1
        print("path fixed:", rep)
print("reports updated:", n_rep)

# 3) 撤 junction（先确认无残留引用）
leftover = 0
for rep in Path(r"E:\RProject\努力学习项目").rglob("*.html"):
    if "文档文件/图片文件" in rep.read_text(encoding="utf-8", errors="replace"):
        leftover += 1
if leftover == 0 and os.path.isjunction(old_link):
    os.rmdir(old_link)
    print("junction removed")
else:
    print("junction kept | leftover refs:", leftover)

# 4) 终验
for cmd in (
    ["python", r"E:\md_kit\audit_fig_canvas_clip.py"],
    ["python", r"E:\md_kit\图交付门禁_gateMdFigures.py", str(fig_root)],
):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = "\n".join(r.stdout.splitlines()[-3:])
    print(">>", cmd[1].split("\\")[-1], "rc=", r.returncode, "|", tail)
