# -*- coding: utf-8 -*-
from pathlib import Path
import re

t = Path(__file__).with_name("zdock_submit_CA_CA.html").read_text(encoding="utf-8", errors="replace")
for m in re.finditer(r'href=["\']([^"\']+)["\'][^>]*>([^<]{0,80})', t):
    href, txt = m.group(1), m.group(2).strip()
    if any(k in (href + txt).lower() for k in ["academic", "commercial", "submit", "php", "form"]):
        print(repr(txt), "->", href)
i = t.lower().find("please")
print("---please---")
print(t[max(0, i - 80) : i + 220] if i >= 0 else "none")
print("---academic context---")
i = t.lower().find("academic")
print(t[max(0, i - 80) : i + 300] if i >= 0 else "none")
