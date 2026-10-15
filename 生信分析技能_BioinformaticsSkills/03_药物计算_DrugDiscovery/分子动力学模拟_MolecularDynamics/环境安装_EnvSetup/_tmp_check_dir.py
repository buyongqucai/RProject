# -*- coding: utf-8 -*-
"""临时：批量体检任意目录下的 PNG（边缘出血）+ SVG（文本边界/占位）。"""
import re
import sys
from pathlib import Path

from PIL import Image


def bleed(p: Path):
    im = Image.open(p).convert("L")
    w, h = im.size
    px = im.load()
    e = {}
    n = sum(1 for y in range(h) if px[0, y] < 128)
    if n:
        e["left"] = n
    n = sum(1 for y in range(h) if px[w - 1, y] < 128)
    if n:
        e["right"] = n
    n = sum(1 for x in range(w) if px[x, 0] < 128)
    if n:
        e["top"] = n
    n = sum(1 for x in range(w) if px[x, h - 1] < 128)
    if n:
        e["bottom"] = n
    return (w, h), e


def svg_texts(p: Path):
    t = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'viewBox="0,0 ([\d.]+),([\d.]+)"', t)
    inner = re.findall(r'viewBox="0,0 ([\d.]+),([\d.]+)"', t)
    vw, vh = (float(inner[-1][0]), float(inner[-1][1])) if inner else (0, 0)
    out = []
    for tm in re.finditer(r"<text([^>]*)>(.*?)</text>", t, re.S):
        attrs, body = tm.group(1), re.sub(r"<[^>]+>", "", tm.group(2)).strip()
        if not body:
            continue
        xm = re.search(r'\bx="([\d.\-]+)"', attrs)
        ym = re.search(r'\by="([\d.\-]+)"', attrs)
        fs = re.search(r'font-size="([\d.]+)"', attrs)
        if not xm or not ym:
            continue
        x, y = float(xm.group(1)), float(ym.group(1))
        f = float(fs.group(1)) if fs else 117
        out.append((body, x, y, len(body) * 0.55 * f))
    return (vw, vh), out


base = Path(sys.argv[1])
for png in sorted(base.rglob("*.png")):
    size, e = bleed(png)
    svg = png.with_suffix(".svg")
    line = f"{png.parent.name}/{png.name} {size[0]}x{size[1]} bleed={e if e else 0}"
    if svg.is_file():
        (vw, vh), texts = svg_texts(svg)
        bad = []
        for body, x, y, w in texts:
            if x < 40 or x + w > vw - 40 or y - 120 < 0 or y + 60 > vh:
                bad.append((body[:26], round(x), round(x + w), round(y)))
        ph = [b for b, *_ in texts if "Color Scale Title" in b or "Lorem" in b]
        cbar = [b for b, x, y, w in texts if "kJ" in b]
        line += f" | page={vw:.0f}x{vh:.0f} texts={len(texts)}"
        if bad:
            line += f" | OUT_OF_BOUNDS {bad}"
        if ph:
            line += f" | PLACEHOLDER {ph}"
        if cbar:
            line += f" | CBAR {cbar}"
    print(line)
