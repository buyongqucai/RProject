# -*- coding: utf-8 -*-
"""校验报告内相对路径（src/href）都能解析到实体文件。"""
import re
from pathlib import Path

rpt = Path(r"C:\Users\10540\Desktop\婷婷\虚拟敲除\结果文件\_跨亚群\课题报告_ProjectReports\报告文件")
bad = 0
for f in list(rpt.glob("*.html")) + list(
    Path(r"C:\Users\10540\Desktop\婷婷\虚拟敲除\结果文件\_跨亚群\富集汇总_EnrichSummary\报告文件").glob("*.html")
):
    txt = f.read_text(encoding="utf-8")
    for attr in ("src", "href"):
        for m in re.findall(attr + r"='([^']+)'", txt):
            if m.startswith("#"):
                continue
            target = (f.parent / m.replace("%20", " ")).resolve()
            if not target.exists():
                print("MISSING", f.name, attr, m)
                bad += 1
print("BAD", bad)
