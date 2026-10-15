# -*- coding: utf-8 -*-
"""Compose remaining pathway GIFs by REUSING material-library bases (no GenerateImage).

Usage:
  python 40_compose_from_library.py           # all pending
  python 40_compose_from_library.py 89 183    # rank range
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
BASES = ANIM / "_bases"
LIB = ANIM / "_素材库" / "全部底图"
ASSETS = Path(r"C:/Users/10540/.cursor/projects/e-RProject/assets")
DB_ANIM = Path(r"D:/数据库/KEGG数据库/KEGG动画图")
MAN = ROOT / "交付文件" / "图片" / "KEGG官方通路图" / "00_全部通路图清单.csv"

sys.path.insert(0, str(ROOT / "代码文件"))
from kegg_base_library import pick_archetype, resolve_base  # noqa: E402
from kegg_zh_names import ZH  # noqa: E402

W, H = 1600, 900
N = 28  # slightly fewer frames = faster compose, still smooth
DUR = 80
DEFAULT_PATH = [(420, 350), (680, 410), (920, 480), (1140, 540)]

NOTES_BY_ARCH = {
    "epithelium": ["上皮屏障", "膜受体", "核孔入核"],
    "macrophage": ["病原识别", "炎症小体", "核内转录"],
    "hepatocyte": ["肝细胞", "代谢/应激", "核应答"],
    "endothelium": ["内皮感受", "血管信号", "核内基因"],
    "cancer": ["癌细胞", "增殖信号", "核内癌基因"],
    "lymphocyte": ["免疫突触", "胞质激酶", "转录因子入核"],
    "virus": ["病毒入胞", "宿主劫持", "核内程序"],
    "signaling": ["配体-受体", "激酶级联", "核孔入核"],
    "apoptosis": ["死亡信号", "线粒体", "核固缩"],
    "hypoxia": ["氧感知", "HIF稳定", "适应基因"],
    "metabolism": ["代谢入口", "细胞器", "核内调控"],
    "neuron": ["突触信号", "胞质级联", "核内应答"],
    "adhesion": ["ECM黏附", "细胞骨架", "迁移信号"],
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


def prepare_base(src: Path) -> Image.Image:
    im = Image.open(src).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    return ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(1.05)).enhance(1.06)


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


def animate(base, title, sub, notes, path):
    frames = []
    for i in range(N):
        t = i / N
        pulse = 1.0 + 0.022 * math.sin(t * 6.28)
        frame = ImageEnhance.Brightness(base).enhance(pulse)
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
        gy = int(180 + 520 * ((math.sin(t * 6.28) + 1) / 2))
        od.ellipse((200, gy - 40, W - 200, gy + 40), fill=(255, 255, 230, 16))
        frame = Image.alpha_composite(frame.convert("RGBA"), overlay)
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
    start, end = 1, 10**9
    args = sys.argv[1:]
    if args and args[0].isdigit():
        start = int(args[0])
    if len(args) > 1 and args[1].isdigit():
        end = int(args[1])

    df = pd.read_csv(MAN, encoding="utf-8-sig")
    search = [LIB, ASSETS, BASES, ANIM / "_素材库" / "全部底图"]
    ANIM.mkdir(parents=True, exist_ok=True)
    BASES.mkdir(parents=True, exist_ok=True)
    DB_ANIM.mkdir(parents=True, exist_ok=True)

    usage = []
    n_ok = n_skip = n_miss = 0
    for _, r in df.iterrows():
        rank = int(r["rank"])
        if rank < start or rank > end:
            continue
        pid = str(r["pathway_id"]).strip()
        en = str(r["description"]).strip()
        zh = ZH.get(pid, en[:24])
        out_name = f"{rank:03d}_{pid}_{zh}_{safe_en(en)}_动画.gif"
        out = ANIM / out_name
        if out.exists() and out.stat().st_size > 400_000:
            print("SKIP", out_name)
            n_skip += 1
            if not (DB_ANIM / out_name).exists():
                shutil.copy2(out, DB_ANIM / out_name)
            continue

        arch = pick_archetype(en, pid)
        src = resolve_base(arch, search)
        if src is None:
            print("MISS", rank, pid, arch)
            n_miss += 1
            continue

        # cache chosen base under _bases with pathway tag for traceability
        tag = f"reuse_{arch}_{src.name}"
        shutil.copy2(src, BASES / tag)
        base = prepare_base(src)
        title = f"{pid} · {zh}"
        notes = NOTES_BY_ARCH.get(arch, NOTES_BY_ARCH["signaling"])
        frames = animate(base, title, en, notes, DEFAULT_PATH)
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=DUR, loop=0, optimize=True)
        shutil.copy2(out, DB_ANIM / out_name)
        usage.append({"rank": rank, "pathway_id": pid, "archetype": arch, "base": src.name, "gif": out_name})
        print("OK", rank, arch, "<-", src.name)
        n_ok += 1

    if usage:
        pd.DataFrame(usage).to_csv(ANIM / "_素材库" / "本次复用记录.csv", index=False, encoding="utf-8-sig")
        db_lib = Path(r"D:/数据库/KEGG数据库/KEGG动画素材库")
        db_lib.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(usage).to_csv(db_lib / "本次复用记录.csv", index=False, encoding="utf-8-sig")
    print(f"DONE ok={n_ok} skip={n_skip} miss={n_miss}")


if __name__ == "__main__":
    main()
