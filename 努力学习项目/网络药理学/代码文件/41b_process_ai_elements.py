# -*- coding: utf-8 -*-
"""Process AI organelle plates → transparent RGBA element library.

Removes mint background, tight-crops, writes to:
  交付/.../_元素库/
  D:/数据库/KEGG数据库/KEGG元素库/
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

ASSETS = Path(r"C:/Users/10540/.cursor/projects/e-RProject/assets")
OUT_DELIV = Path(r"E:/RProject/努力学习项目/网络药理学/交付文件/图片/动画_生物结构/_元素库")
OUT_DB = Path(r"D:/数据库/KEGG数据库/KEGG元素库")

# source file -> (element_id, name_zh, name_en, target_max_side)
MAP = {
    "elem_ai_nucleus.png": ("nucleus", "细胞核", "Nucleus", 480),
    "elem_ai_mitochondria.png": ("mitochondria", "线粒体", "Mitochondria", 320),
    "elem_ai_er_rough.png": ("er_rough", "粗面内质网", "Rough ER", 420),
    "elem_ai_er_smooth.png": ("er_smooth", "光面内质网", "Smooth ER", 400),
    "elem_ai_golgi.png": ("golgi", "高尔基体", "Golgi", 380),
    "elem_ai_lysosome.png": ("lysosome", "溶酶体", "Lysosome", 160),
    "elem_ai_membrane.png": ("membrane_patch", "细胞膜片段", "Membrane", 700),
    "elem_ai_receptor_tk.png": ("receptor_tk", "受体酪氨酸激酶", "RTK receptor", 280),
    "elem_ai_receptor_tlr.png": ("receptor_tlr", "TLR受体", "TLR receptor", 260),
    "elem_ai_lipid_droplet.png": ("lipid_droplet", "脂滴", "Lipid droplet", 180),
    "elem_ai_virus.png": ("virus_particle", "病毒颗粒", "Virus", 160),
    "elem_ai_ecm.png": ("ecm_fiber", "细胞外基质纤维", "ECM fiber", 560),
    "elem_ai_brush_border.png": ("brush_border", "刷状缘", "Brush border", 520),
}


def cutout_mint(im: Image.Image, thr: int = 28) -> Image.Image:
    """Remove near-mint / near-white background → RGBA."""
    rgba = im.convert("RGBA")
    arr = np.asarray(rgba).astype(np.float32)
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    # mint / pale green / near white
    mint = (g > r - 5) & (g > b - 5) & (r > 180) & (g > 200) & (b > 180)
    pale = (r > 220) & (g > 230) & (b > 220)
    # also light cyan backgrounds
    cyan = (g > 200) & (b > 200) & (r > 160) & ((g + b) / 2 > r + 15)
    mask_bg = mint | pale | cyan
    a = np.where(mask_bg, 0, a)
    # soft edge: lower alpha near bg
    edge = (r > 170) & (g > 190) & (b > 170) & (~mask_bg)
    a = np.where(edge, np.minimum(a, 140), a)
    out = np.stack([r, g, b, a], axis=-1).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def tight_crop(im: Image.Image, pad: int = 8) -> Image.Image:
    alpha = np.asarray(im.split()[-1])
    ys, xs = np.where(alpha > 12)
    if len(xs) == 0:
        return im
    x0, x1 = max(0, xs.min() - pad), min(im.width, xs.max() + pad)
    y0, y1 = max(0, ys.min() - pad), min(im.height, ys.max() + pad)
    return im.crop((x0, y0, x1, y1))


def fit_max(im: Image.Image, max_side: int) -> Image.Image:
    w, h = im.size
    s = max(w, h)
    if s <= max_side:
        return im
    scale = max_side / s
    return im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)


def main() -> None:
    for d in (OUT_DELIV, OUT_DB):
        d.mkdir(parents=True, exist_ok=True)
        # archive old schematic elements
        old = d / "_旧简笔"
        old.mkdir(exist_ok=True)
        for p in d.glob("*.png"):
            if p.name.startswith("elem_ai"):
                continue
            shutil.move(str(p), str(old / p.name))

    rows = []
    for src_name, (eid, zh, en, max_side) in MAP.items():
        src = ASSETS / src_name
        if not src.exists():
            print("MISS", src_name)
            continue
        im = Image.open(src)
        cut = cutout_mint(im)
        cut = tight_crop(cut)
        cut = fit_max(cut, max_side)
        fname = f"{eid}_{zh}.png"
        cut.save(OUT_DELIV / fname)
        cut.save(OUT_DB / fname)
        # also keep raw AI plate
        shutil.copy2(src, OUT_DELIV / f"_raw_{src_name}")
        shutil.copy2(src, OUT_DB / f"_raw_{src_name}")
        rows.append(
            {
                "元素ID": eid,
                "中文名": zh,
                "英文名": en,
                "宽": cut.width,
                "高": cut.height,
                "文件": fname,
                "风格": "AI精细医学插画",
                "来源": src_name,
            }
        )
        print("OK", fname, cut.size)

    # ribosome / nuclear_pore: derive small crops from ER / nucleus if missing
    cat = pd.DataFrame(rows)
    cat.to_csv(OUT_DELIV / "元素库目录.csv", index=False, encoding="utf-8-sig")
    cat.to_excel(OUT_DB / "元素库目录.xlsx", index=False)
    shutil.copy2(OUT_DELIV / "元素库目录.csv", OUT_DB / "元素库目录.csv")
    (OUT_DELIV / "README.txt").write_text(
        "KEGG 细胞器元素库 · AI 精细医学插画风格\n"
        "与前80条生物结构动画同审美：3D soft shading / 组织学质感。\n"
        "旧简笔已移至 _旧简笔/\n"
        "拼装：42_compose_from_elements.py\n",
        encoding="utf-8",
    )
    shutil.copy2(OUT_DELIV / "README.txt", OUT_DB / "README.txt")
    print("DONE", len(rows), "->", OUT_DB)


if __name__ == "__main__":
    main()
