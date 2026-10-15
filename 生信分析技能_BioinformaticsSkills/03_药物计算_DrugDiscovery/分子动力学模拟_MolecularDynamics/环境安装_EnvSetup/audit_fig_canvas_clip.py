# -*- coding: utf-8 -*-
"""图幅/裁剪审计：PNG 尺寸统计 + 边缘出血暗像素 + SVG 文本越界（viewBox）。"""
import re
from pathlib import Path

from PIL import Image

ROOT = Path(r"E:\RProject\努力学习项目\08_分子动力学\结果文件\图片文件\分子动力学图_MD")


def svg_overflow(svg: Path):
    t = svg.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'viewBox="([\d.\-]+) ([\d.\-]+) ([\d.\-]+) ([\d.\-]+)"', t)
    if not m:
        return []
    vw, vh = float(m.group(3)), float(m.group(4))
    bad = []
    for tm in re.finditer(r'<text([^>]*)>(.*?)</text>', t, re.S):
        attrs, body = tm.group(1), re.sub(r"<[^>]+>", "", tm.group(2)).strip()
        if not body:
            continue
        xm = re.search(r'\bx="([\d.\-]+)"', attrs)
        ym = re.search(r'\by="([\d.\-]+)"', attrs)
        if not xm or not ym:
            continue
        x, y = float(xm.group(1)), float(ym.group(1))
        est_w = len(body) * 7  # 粗估 7px/字符
        rot = "rotate(-90" in attrs or "rotate(270" in attrs
        if rot:
            if x < -2 or x > vw + 2 or y - est_w < -2 or y > vh + 2:
                bad.append((body[:24], x, y, "rot"))
        else:
            if x < -2 or x + est_w > vw + 2 or y < -2 or y > vh + 2:
                bad.append((body[:24], x, y, "flat"))
    return bad


def png_bleed(p: Path):
    im = Image.open(p).convert("L")
    w, h = im.size
    px = im.load()
    edges = {"left": 0, "right": 0, "top": 0, "bottom": 0}
    for y in range(h):
        if px[0, y] < 128:
            edges["left"] += 1
        if px[w - 1, y] < 128:
            edges["right"] += 1
    for x in range(w):
        if px[x, 0] < 128:
            edges["top"] += 1
        if px[x, h - 1] < 128:
            edges["bottom"] += 1
    return (w, h), {k: v for k, v in edges.items() if v > 0}


sizes = {}
problems = []
for sys_dir in sorted(ROOT.iterdir()):
    if not sys_dir.is_dir():
        continue
    for png in sorted(sys_dir.rglob("*.png")):
        size, bleed = png_bleed(png)
        sizes.setdefault(size, []).append(f"{sys_dir.name}/{png.name}")
        svg = png.with_suffix(".svg")
        ov = svg_overflow(svg) if svg.is_file() else []
        if bleed or ov:
            problems.append((sys_dir.name, png.name, size, bleed, ov[:4]))

print("== 画幅尺寸分布 ==")
for size, files in sorted(sizes.items()):
    print(f"{size[0]}x{size[1]}: {len(files)} 张")
print(f"\n== 疑似裁剪 {len(problems)} 张 ==")
for s, n, size, bleed, ov in problems:
    msg = []
    if bleed:
        msg.append(f"边缘出血{bleed}")
    if ov:
        msg.append(f"SVG文本越界{ov}")
    print(f"{s} | {n} | {size[0]}x{size[1]} | {'; '.join(msg)}")
