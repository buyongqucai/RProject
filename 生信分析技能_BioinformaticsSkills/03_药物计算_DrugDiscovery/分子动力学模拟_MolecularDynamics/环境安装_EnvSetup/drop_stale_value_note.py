# -*- coding: utf-8 -*-
from pathlib import Path

old = "注：热图 luteolin–PCNA 格按旧值 −4.60 绘制"
out = []
for f in [
    Path(r"E:\RProject\努力学习项目\00_全流程报告\结果文件\报告文件\方法版_全流程.html"),
    Path(r"E:\RProject\努力学习项目\交付文件\00_全流程报告\结果文件\报告文件\方法版_全流程.html"),
]:
    t = f.read_text(encoding="utf-8", errors="replace")
    n = t.count(old)
    t = t.replace(old, "")
    f.write_text(t, encoding="utf-8")
    out.append(f"{f.parent.parent.parent.name}: replaced {n}; remaining {t.count(old)}; 4.60 绘制 count now {t.count('4.60 绘制')}")
Path(r"E:\md_kit\_note_probe.txt").write_text("\n".join(out), encoding="utf-8")
print("done")
