# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(r"E:/RProject") / "努力学习项目"
OLD = "结果文件/数据文件"
OLD_WIN = "结果文件\\数据文件"
NEW = "数据文件/结果数据"
NEW_WIN = "数据文件\\结果数据"

# Also common Path("结果文件") / "数据文件" patterns — handled via text replace of slash form first.

changed = []
scanned = 0
for p in ROOT.rglob("*"):
    if "交付文件" in p.parts:
        continue
    if p.suffix.lower() not in {".py", ".r", ".md", ".txt", ".html", ".json"}:
        continue
    if not p.is_file():
        continue
    scanned += 1
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        continue
    if OLD not in text and OLD_WIN not in text:
        # Path parts style: / "数据文件" after 结果文件 — leave complex cases
        continue
    new = text.replace(OLD, NEW).replace(OLD_WIN, NEW_WIN)
    if new != text:
        p.write_text(new, encoding="utf-8")
        changed.append(str(p.relative_to(ROOT)))

# Path("结果文件") / "数据文件" in Python
import re

pat = re.compile(
    r'(Path\([\'"]结果文件[\'"]\)\s*/\s*[\'"]数据文件[\'"])'
)
pat2 = re.compile(
    r'([\'"]结果文件[\'"]\s*,\s*[\'"]数据文件[\'"])'
)

for p in list(ROOT.rglob("*.py")) + list(ROOT.rglob("*.R")) + list(ROOT.rglob("*.r")):
    if "交付文件" in p.parts:
        continue
    text = p.read_text(encoding="utf-8")
    new = pat.sub('Path("数据文件") / "结果数据"', text)
    new = pat2.sub('"数据文件", "结果数据"', new)
    # ROOT / "结果文件" / "数据文件"
    new = new.replace('/ "结果文件" / "数据文件"', '/ "数据文件" / "结果数据"')
    new = new.replace("/ '结果文件' / '数据文件'", "/ '数据文件' / '结果数据'")
    new = new.replace('file.path("结果文件", "数据文件"', 'file.path("数据文件", "结果数据"')
    new = new.replace("file.path('结果文件', '数据文件'", "file.path('数据文件', '结果数据'")
    if new != text:
        p.write_text(new, encoding="utf-8")
        rel = str(p.relative_to(ROOT))
        if rel not in changed:
            changed.append(rel)

out = Path(r"E:/RProject/_tmp_path_fix_log.txt")
out.write_text(
    f"scanned={scanned}\nchanged={len(changed)}\n" + "\n".join(changed),
    encoding="utf-8",
)
print(out.read_text(encoding="utf-8")[:3000])
