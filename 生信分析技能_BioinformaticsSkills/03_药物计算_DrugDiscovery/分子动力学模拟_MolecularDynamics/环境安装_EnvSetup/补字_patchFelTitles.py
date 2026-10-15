# -*- coding: utf-8 -*-
"""导出后补字（MdFigureStandards 2026-10-11 修订允许）：
FEL 图色阶占位「Color Scale Title」→「G (kJ/mol)」。
SVG：文本节点替换；PNG：右上角暗色文本簇白底覆盖后重写。"""
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"E:\RProject\努力学习项目\08_分子动力学\文档文件\图片文件\分子动力学图_MD")
FEL_STEMS = [
    "FreeEnergyLandscape", "FreeEnergyLandscape3D",
    "FreeEnergyRmsdCom", "FreeEnergyRmsdCom3D",
    "FreeEnergyRmsdSasa", "FreeEnergyRmsdSasa3D",
    "FreeEnergyLigandProteinRmsd", "FreeEnergyLigandProteinRmsd3D",
]
NEW = "G (kJ/mol)"


def patch_svg(p: Path) -> bool:
    t = p.read_text(encoding="utf-8", errors="replace")
    if "Color Scale Title" not in t:
        return False
    t2 = t.replace("Color Scale Title", NEW)
    p.write_text(t2, encoding="utf-8")
    return True


def patch_png(p: Path) -> bool:
    im = Image.open(p).convert("RGB")
    w, h = im.size
    zone = (int(w * 0.50), 0, int(w * 0.97), int(h * 0.12))
    crop = im.crop(zone)
    px = crop.load()
    cw, ch = crop.size
    dark = [(x, y) for y in range(ch) for x in range(cw)
            if sum(px[x, y]) < 250]
    if not dark:
        return False
    xs = [d[0] for d in dark]
    ys = [d[1] for d in dark]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    if (y1 - y0) > h * 0.08 or (x1 - x0) > w * 0.35:
        return False  # 捕获到非标题内容，放弃补字（防误伤）
    pad = 4
    draw = ImageDraw.Draw(im)
    draw.rectangle([zone[0] + x0 - pad, y0 - pad, zone[0] + x1 + pad, y1 + pad],
                   fill=(255, 255, 255))
    fs = max(12, y1 - y0 + 2)
    try:
        font = ImageFont.truetype("arial.ttf", fs)
    except OSError:
        font = ImageFont.load_default()
    draw.text((zone[0] + x0, y0 - 1), NEW, fill=(0, 0, 0), font=font)
    im.save(p)
    return True


def main():
    n_svg = n_png = 0
    for sys_dir in sorted(ROOT.iterdir()):
        if not sys_dir.is_dir():
            continue
        for stem in FEL_STEMS:
            for f in sys_dir.rglob(f"*_{stem}.*"):
                if f.suffix.lower() == ".svg" and patch_svg(f):
                    n_svg += 1
                    print("svg patched", f.relative_to(ROOT))
                elif f.suffix.lower() == ".png" and patch_png(f):
                    n_png += 1
                    print("png patched", f.relative_to(ROOT))
    print(f"patched svg={n_svg} png={n_png}")


if __name__ == "__main__":
    main()
