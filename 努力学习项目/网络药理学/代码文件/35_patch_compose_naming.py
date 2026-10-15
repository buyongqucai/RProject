# -*- coding: utf-8 -*-
"""Patch 31_compose SPECS out/title/sub to zh+id+en naming."""
from __future__ import annotations

import re
import runpy
from pathlib import Path

ns = runpy.run_path(str(Path(__file__).with_name("34_rename_animation_zh_id_en.py")))
RENAME = ns["RENAME"]
make_name = ns["make_name"]

path = Path(__file__).with_name("31_compose_vivid_bio_gifs.py")
text = path.read_text(encoding="utf-8")

for m in RENAME:
    text = text.replace(m["old"], make_name(m))

for m in RENAME:
    kegg = m["kegg"]
    if kegg == "UC-EPITHELIUM":
        pat = r'("kegg": "",\s*\n\s*"title": ")[^"]*(",\s*\n\s*"sub": ")[^"]*'
    else:
        pat = rf'("kegg": "{re.escape(kegg)}",\s*\n\s*"title": ")[^"]*(",\s*\n\s*"sub": ")[^"]*'
    repl = rf'\1{m["title"]}\2{m["sub"]}'
    text, n = re.subn(pat, repl, text, count=1)
    print(kegg, "title_patched", n)

path.write_text(text, encoding="utf-8")
print("OK", path)
