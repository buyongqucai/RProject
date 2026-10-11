# -*- coding: utf-8 -*-
from pathlib import Path
import re

proj = next(p for p in Path(r"E:/RProject").iterdir() if p.is_dir() and "努力" in p.name)
ph = proj / "交付文件" / "网络药理学"
for html in [ph / "图注与解读说明.html", ph / "报告文件" / "图注与解读说明.html"]:
    if not html.exists():
        print("missing", html)
        continue
    t = html.read_text(encoding="utf-8")
    refs = sorted(set(re.findall(r"""(?:src|href)=["']([^"']+)""", t)))
    local = [r for r in refs if not r.startswith(("http", "#", "mailto"))]
    bad, good = [], []
    for r in local:
        target = (html.parent / r).resolve()
        (good if target.exists() else bad).append(r)
    print(html.relative_to(proj), "local", len(local), "bad", len(bad), "good", len(good))
    for b in bad[:20]:
        print("  BAD", b)

# fix root html: 图片/ -> 图片文件/, 数据/ -> 数据文件/, 报告/ -> 报告文件/
html = ph / "图注与解读说明.html"
t = html.read_text(encoding="utf-8")
t2 = t
for old, new in (
    ("图片/", "图片文件/"),
    ("数据/", "数据文件/"),
    ("报告/", "报告文件/"),
):
    # avoid double-replacing 图片文件/
    t2 = t2.replace(old, new)
    t2 = t2.replace(new.replace("文件/", "文件/文件/"), new)  # noop safety
# undo double prefix if any
t2 = t2.replace("图片文件/文件/", "图片文件/")
t2 = t2.replace("数据文件/文件/", "数据文件/")
t2 = t2.replace("报告文件/文件/", "报告文件/")
if t2 != t:
    html.write_text(t2, encoding="utf-8")
    print("fixed root html paths")
else:
    print("root html unchanged")

# recheck
t = html.read_text(encoding="utf-8")
refs = sorted(set(re.findall(r"""(?:src|href)=["']([^"']+)""", t)))
local = [r for r in refs if not r.startswith(("http", "#", "mailto"))]
bad = [r for r in local if not (html.parent / r).exists()]
print("after fix bad", len(bad))
for b in bad[:20]:
    print("  BAD", b)
