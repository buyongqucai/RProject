# -*- coding: utf-8 -*-
"""Compose pathway GIFs by assembling organelle element sprites.

Usage:
  python 42_compose_from_elements.py 89 183
"""
from __future__ import annotations

import math
import re
import shutil
import sys
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学")
ANIM = ROOT / "交付文件" / "图片" / "动画_生物结构"
ELEM_DIR = ANIM / "_元素库"
DB_ANIM = Path(r"D:/数据库/KEGG数据库/KEGG动画图")
DB_ELEM = Path(r"D:/数据库/KEGG数据库/KEGG元素库")
MAN = ROOT / "交付文件" / "图片" / "KEGG官方通路图" / "00_全部通路图清单.csv"
REUSE_CSV = DB_ELEM.parent / "KEGG动画素材库" / "本次复用记录.csv"

sys.path.insert(0, str(ROOT / "代码文件"))
from bio_element_library import ELEMENTS, LAYOUTS, paste_element, render_element  # noqa: E402
from kegg_base_library import pick_archetype  # noqa: E402
from kegg_zh_names import ZH  # noqa: E402

W, H = 1600, 900
N = 28
DUR = 80
BG = (226, 238, 232)  # soft histology wash matching AI element mint

NOTES_BY_ARCH = {
    "epithelium": ["刷状缘/屏障", "胞质细胞器", "核孔入核"],
    "macrophage": ["病原识别", "线粒体应激", "炎症入核"],
    "hepatocyte": ["脂滴堆积", "ER/线粒体", "核内应答"],
    "endothelium": ["剪切/受体", "内皮信号", "核内基因"],
    "cancer": ["RTK激活", "PI3K/MAPK", "癌基因入核"],
    "lymphocyte": ["免疫受体", "激酶级联", "转录入核"],
    "virus": ["病毒入胞", "宿主劫持", "核内程序"],
    "signaling": ["配体-受体", "胞质级联", "核孔入核"],
    "apoptosis": ["死亡受体", "线粒体", "核固缩"],
    "hypoxia": ["低氧感知", "HIF稳定", "适应基因"],
    "metabolism": ["代谢酶", "线粒体", "核内调控"],
    "neuron": ["突触受体", "胞质信号", "核应答"],
    "adhesion": ["ECM黏附", "整合素", "迁移信号"],
}

SIGNAL_PATHS = {
    "epithelium": [(400, 200), (620, 320), (820, 450), (980, 560)],
    "default": [(420, 280), (680, 360), (920, 460), (1100, 540)],
}


def F(size: int):
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def safe_en(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", str(s), flags=re.UNICODE)
    return s.strip("_")[:80] or "pathway"


def lerp(a, b, t):
    return a + (b - a) * t


def load_elements() -> dict[str, Image.Image]:
    """Prefer AI cutouts in _元素库; never fall back to schematic drawers for known ids."""
    cache: dict[str, Image.Image] = {}
    for p in ELEM_DIR.glob("*.png"):
        if p.name.startswith("_") or p.name.startswith("elem_ai"):
            continue
        eid = p.name.split("_", 1)[0]
        # files are {id}_{zh}.png — id may contain no underscore except multiword handled below
        # our ids: nucleus, mitochondria, er_rough, er_smooth, membrane_patch, ...
        for known in (
            "membrane_patch",
            "receptor_tk",
            "receptor_tlr",
            "lipid_droplet",
            "virus_particle",
            "brush_border",
            "ecm_fiber",
            "er_rough",
            "er_smooth",
            "nuclear_pore_glow",
            "ribosome_cluster",
            "mitochondria",
            "lysosome",
            "nucleus",
            "golgi",
        ):
            if p.name.startswith(known + "_"):
                eid = known
                break
        cache[eid] = Image.open(p).convert("RGBA")
    # optional schematic fallback only if completely missing
    for spec in ELEMENTS:
        if spec.id not in cache:
            try:
                cache[spec.id] = render_element(spec)
            except Exception:
                pass
    return cache


def make_cytoplasm_bg() -> Image.Image:
    """Soft histology cytoplasm matching AI element style (not flat mint)."""
    base = Image.new("RGBA", (W, H), (*BG, 255))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i, alpha in enumerate((22, 14, 8)):
        margin = 40 + i * 70
        d.ellipse((margin, 80 + margin // 2, W - margin, H - margin // 2), fill=(255, 255, 245, alpha))
    d.rectangle((0, 0, W, H), fill=(170, 205, 195, 20))
    return Image.alpha_composite(base, overlay)


def draw_banner(d, title, sub):
    d.rectangle((0, 0, W, 74), fill=(14, 48, 42))
    d.rectangle((0, 66, W, 78), fill=(8, 32, 28))
    d.text((28, 10), title, fill=(244, 255, 248), font=F(24))
    d.text((28, 44), sub, fill=(168, 210, 195), font=F(13))


def draw_notes_soft(im, notes):
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    x1 = W - 24
    y = 96
    od.text((x1 - 72, y), "要点", fill=(255, 255, 255, 160), font=F(12))
    y += 22
    for line in notes:
        tw = 12 * len(line) + 28
        x0 = x1 - tw
        od.rounded_rectangle((x0, y, x1, y + 26), radius=8, fill=(20, 40, 35, 110), outline=(255, 255, 255, 55))
        od.text((x0 + 12, y + 5), line, fill=(245, 250, 248, 230), font=F(12))
        y += 32
    return Image.alpha_composite(im.convert("RGBA"), overlay)


def compose_frame(elements: dict[str, Image.Image], arch: str, t: float) -> Image.Image:
    canvas = make_cytoplasm_bg()
    layout = LAYOUTS.get(arch, LAYOUTS["signaling"])
    pulse = 0.025 * math.sin(t * 6.28)
    for eid, x, y, scale in layout:
        elem = elements.get(eid)
        if elem is None:
            continue
        dy = int(3 * math.sin(t * 6.28 + x * 0.01)) if eid in ("mitochondria", "er_rough", "er_smooth", "golgi") else 0
        ep = pulse if eid == "nucleus" else pulse * 0.45
        paste_element(canvas, elem.copy(), x, y + dy, scale, ep)
    return canvas.convert("RGB")


def animate_scene(elements, arch, title, sub, notes, path):
    frames = []
    for i in range(N):
        t = i / N
        base = compose_frame(elements, arch, t)
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        for seg in range(len(path) - 1):
            x0, y0 = path[seg]
            x1, y1 = path[seg + 1]
            od.line((x0, y0, x1, y1), fill=(255, 220, 120, 45), width=4)
            for k in range(3):
                tt = (t + seg * 0.18 + k * 0.12) % 1.0
                x = lerp(x0, x1, tt)
                y = lerp(y0, y1, tt)
                r = 7 + 2 * math.sin(t * 8 + k)
                od.ellipse((x - r - 4, y - r - 4, x + r + 4, y + r + 4), fill=(255, 180, 60, 65))
                od.ellipse((x - r, y - r, x + r, y + r), fill=(255, 230, 120, 210), outline=(220, 140, 40, 255))
        frame = Image.alpha_composite(base.convert("RGBA"), overlay)
        frame = draw_notes_soft(frame, notes)
        out = frame.convert("RGB")
        d = ImageDraw.Draw(out)
        draw_banner(d, title, sub)
        nx, ny = path[-1]
        rr = 26 + 7 * math.sin(t * 6.28)
        d.ellipse((nx - rr, ny - rr, nx + rr, ny + rr), outline=(231, 76, 60), width=2)
        frames.append(out)
    return frames


def main():
    start, end = 89, 183
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args and args[0].isdigit():
        start = int(args[0])
    if len(args) > 1 and args[1].isdigit():
        end = int(args[1])

    df = pd.read_csv(MAN, encoding="utf-8-sig")
    elements = load_elements()
    print("loaded elements:", sorted(elements.keys()))
    ANIM.mkdir(parents=True, exist_ok=True)
    DB_ANIM.mkdir(parents=True, exist_ok=True)

    usage = []
    n_ok = n_skip = 0
    for _, r in df.iterrows():
        rank = int(r["rank"])
        if rank < start or rank > end:
            continue
        pid = str(r["pathway_id"]).strip()
        en = str(r["description"]).strip()
        zh = ZH.get(pid, en[:24])
        out_name = f"{rank:03d}_{pid}_{zh}_{safe_en(en)}_动画.gif"
        out = ANIM / out_name
        if out.exists() and out.stat().st_size > 400_000 and not force and start > 88:
            # when refreshing AI-element batch, always overwrite 89+ unless skip flag
            pass

        arch = pick_archetype(en, pid)
        title = f"{pid} · {zh}"
        notes = NOTES_BY_ARCH.get(arch, NOTES_BY_ARCH["signaling"])
        path = SIGNAL_PATHS.get(arch, SIGNAL_PATHS["default"])
        frames = animate_scene(elements, arch, title, en, notes, path)
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=DUR, loop=0, optimize=True)
        shutil.copy2(out, DB_ANIM / out_name)
        usage.append({"rank": rank, "pathway_id": pid, "archetype": arch, "method": "element_compose", "gif": out_name})
        print("OK", rank, arch, out_name[:60])
        n_ok += 1

    if usage:
        log = ELEM_DIR / "元素拼装记录.csv"
        pd.DataFrame(usage).to_csv(log, index=False, encoding="utf-8-sig")
        pd.DataFrame(usage).to_csv(DB_ELEM / "元素拼装记录.csv", index=False, encoding="utf-8-sig")
    print(f"DONE ok={n_ok} skip={n_skip}")


if __name__ == "__main__":
    main()
