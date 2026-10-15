# -*- coding: utf-8 -*-
"""热图新图分发到报告副本位 + 清除报告中「热图滞后」注（图已重绘）。"""
import re
import shutil
from pathlib import Path

src_png = Path(r"E:\RProject\努力学习项目\06_分子对接\结果文件\图片文件\矩阵_结合能热图_多对多3x4_DockingAffinityHeatmap3x4.png")
src_svg = src_png.with_suffix(".svg")
targets = [
    Path(r"E:\RProject\努力学习项目\00_全流程报告\结果文件\图片文件"),
    Path(r"E:\RProject\努力学习项目\交付文件\06_分子对接\结果文件\图片文件"),
    Path(r"E:\RProject\努力学习项目\交付文件\00_全流程报告\结果文件\图片文件"),
]
for t in targets:
    if t.is_dir():
        shutil.copy2(src_png, t / src_png.name)
        shutil.copy2(src_svg, t / src_svg.name)
        print("copied ->", t)

reports = [
    Path(r"E:\RProject\努力学习项目\00_全流程报告\结果文件\报告文件\论文版_全流程.html"),
    Path(r"E:\RProject\努力学习项目\00_全流程报告\结果文件\报告文件\方法版_全流程.html"),
    Path(r"E:\RProject\努力学习项目\交付文件\00_全流程报告\结果文件\报告文件\论文版_全流程.html"),
    Path(r"E:\RProject\努力学习项目\交付文件\00_全流程报告\结果文件\报告文件\方法版_全流程.html"),
]
pat = re.compile(r"[^。<>]{0,80}滞后[^。<>]{0,120}。?")
for rp in reports:
    t = rp.read_text(encoding="utf-8", errors="replace")
    hits = pat.findall(t)
    if hits:
        t2 = pat.sub("", t)
        rp.write_text(t2, encoding="utf-8")
        print("removed note in", rp.name, "->", [h[:60] for h in hits])
    else:
        print("no note in", rp.name)
