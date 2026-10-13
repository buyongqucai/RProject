# -*- coding: utf-8 -*-
"""Trim excess white margins from Venn PNGs (Track A + Track B)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学")
PAIRS = [
    (
        ROOT / "代码文件/结果文件/图片文件/01_韦恩图_DiseaseDatabases_Venn.png",
        ROOT / "交付文件/图片/韦恩图/疾病数据库可视化韦恩图.png",
    ),
    (
        ROOT / "代码文件/结果文件/图片文件/02_韦恩图_DrugDisease_Venn.png",
        ROOT / "交付文件/图片/韦恩图/疾病药物交集韦恩图.png",
    ),
]
PAD = 24  # keep a little breathing room


def trim_white(im: Image.Image, pad: int = PAD, thr: int = 250) -> Image.Image:
    rgb = im.convert("RGB")
    bg = Image.new("RGB", rgb.size, (255, 255, 255))
    diff = ImageChops.difference(rgb, bg)
    # treat near-white as background
    gray = diff.convert("L").point(lambda p: 255 if p > (255 - thr) else 0)
    bbox = gray.getbbox()
    if not bbox:
        return im
    l, t, r, b = bbox
    l = max(0, l - pad)
    t = max(0, t - pad)
    r = min(rgb.width, r + pad)
    b = min(rgb.height, b + pad)
    return im.crop((l, t, r, b))


def main() -> None:
    for track_a, track_b in PAIRS:
        src = track_a if track_a.exists() else track_b
        if not src.exists():
            print("SKIP missing", src)
            continue
        im = Image.open(src)
        before = im.size
        out = trim_white(im)
        after = out.size
        for dest in {track_a, track_b}:
            dest.parent.mkdir(parents=True, exist_ok=True)
            out.save(dest, optimize=True)
            print(f"TRIM {dest.name}: {before} -> {after}")


if __name__ == "__main__":
    main()
