# -*- coding: utf-8 -*-
"""临时诊断：把 PNG 区域渲染成 ASCII 图，用纯文本“看”标签是否完整（只读，不改图）。
用法: python _tmp_ascii_art.py <png路径> x0 y0 x1 y1 [cols] [transpose]
"""
import sys
from pathlib import Path

from PIL import Image


def art(png: Path, x0: int, y0: int, x1: int, y1: int, cols: int = 150,
        transpose: bool = False):
    im = Image.open(png).convert("L")
    w, h = im.size
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    crop = im.crop((x0, y0, x1, y1))
    if transpose:
        crop = crop.transpose(Image.ROTATE_90)
    cw, ch = crop.size
    rows = max(1, int(cols * ch / cw / 2.1))
    small = crop.resize((cols, rows))
    px = small.load()
    chars = " .:-=+*#%@"
    print(f"# {png.name} region=({x0},{y0})-({x1},{y1}) transpose={transpose} -> {cols}x{rows}")
    for j in range(rows):
        line = "".join(chars[min(9, (255 - px[i, j]) * 10 // 256)] for i in range(cols))
        print("|" + line + "|")


if __name__ == "__main__":
    p = Path(sys.argv[1])
    box = [int(v) for v in sys.argv[2:6]]
    cols = int(sys.argv[6]) if len(sys.argv) > 6 else 150
    tr = len(sys.argv) > 7 and sys.argv[7] in ("1", "t", "true")
    art(p, *box, cols=cols, transpose=tr)
