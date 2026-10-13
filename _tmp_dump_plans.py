# -*- coding: utf-8 -*-
from pathlib import Path

root = Path(r"E:/RProject") / "努力学习项目"
out = Path(r"E:/RProject/_tmp_plans_body.txt")
parts = []
wanted = [
    root / "存放规范_ProjectLayout.md",
]
# research plans
for p in (root / "03_三源交集_复方UC菌群").rglob("*.md"):
    if "研究计划" in str(p) or "README" in p.name:
        wanted.append(p)
for p in root.glob("0*/README*.md"):
    wanted.append(p)

seen = set()
for p in wanted:
    if not p.exists() or p in seen:
        continue
    seen.add(p)
    parts.append("\n\n======== " + str(p.relative_to(root)) + " ========\n")
    parts.append(p.read_text(encoding="utf-8", errors="replace")[:6000])

out.write_text("".join(parts), encoding="utf-8")
print("bytes", out.stat().st_size, "files", len(seen))
