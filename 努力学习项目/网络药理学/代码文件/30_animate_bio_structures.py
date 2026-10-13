# -*- coding: utf-8 -*-
"""UC NetPharm — vivid histology-style animated bio structures.

Organic cell silhouettes, dense brush border, domain-level receptors,
organelle-rich cytoplasm, tissue context — medical-animation look (not flat boxes).
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(r"E:/RProject/努力学习项目/网络药理学/交付文件/图片/动画_生物结构")
W, H = 1600, 1000
N = 42
DUR = 70


def F(size: int):
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def lerp(a, b, t):
    return a + (b - a) * t


def np_rgb(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def tissue_bg() -> np.ndarray:
    """Warm histology backdrop with faint fibrous texture."""
    yy, xx = np.mgrid[0:H, 0:W]
    base = np.zeros((H, W, 3), dtype=np.float32)
    gy = yy / H
    gx = xx / W
    base[..., 0] = 236 - 28 * gy + 6 * np.sin(xx / 70)
    base[..., 1] = 226 - 20 * gy + 4 * np.sin(yy / 55)
    base[..., 2] = 208 - 30 * gy
    # collagen-like fiber noise
    noise = (np.sin(xx / 11 + yy / 17) * np.cos(xx / 23 - yy / 13) * 6)
    base[..., 0] += noise
    base[..., 1] += noise * 0.7
    base[..., 2] += noise * 0.4
    # top lumen blush
    lumen = np.clip(1 - (yy - 80) / 160, 0, 1)[:, :, None]
    blush = np.array([245, 210, 195], dtype=np.float32)
    base = base * (1 - 0.22 * lumen) + blush * (0.22 * lumen)
    # basal lamina propria warm band
    basal = np.clip((yy - 780) / 180, 0, 1)[:, :, None]
    brown = np.array([180, 140, 105], dtype=np.float32)
    base = base * (1 - 0.35 * basal) + brown * (0.35 * basal)
    return base


def banner(im: Image.Image, title: str, sub: str):
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 78), fill=(16, 58, 50))
    d.rectangle((0, 70, W, 84), fill=(10, 40, 34))
    d.text((30, 12), title, fill=(244, 255, 248), font=F(28))
    d.text((30, 48), sub, fill=(170, 215, 200), font=F(14))


def shade_polygon(canvas: np.ndarray, poly, fill, light=(-0.35, -0.55), rim=None):
    """Fill irregular polygon with soft directional shading."""
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    m = np.asarray(mask, dtype=np.float32) / 255.0
    yy, xx = np.mgrid[0:H, 0:W]
    # light gradient across bbox
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    u = (xx - minx) / max(1, maxx - minx)
    v = (yy - miny) / max(1, maxy - miny)
    shade = 0.78 + 0.28 * (1 - (u * abs(light[0]) + v * abs(light[1])))
    shade = np.clip(shade, 0.55, 1.15)
    col = np.array(fill, dtype=np.float32)
    for c in range(3):
        canvas[..., c] = canvas[..., c] * (1 - m) + (col[c] * shade) * m
    if rim is not None:
        edge = Image.fromarray((m * 255).astype(np.uint8), "L").filter(ImageFilter.FIND_EDGES)
        e = np.asarray(edge, dtype=np.float32) / 255.0
        e = np.clip(e * 3.5, 0, 1)
        rc = np.array(rim, dtype=np.float32)
        for c in range(3):
            canvas[..., c] = canvas[..., c] * (1 - e) + rc[c] * e


def organic_column(cx, top, bot, width, phase=0.0, waviness=10):
    """Irregular columnar epithelial outline (not a rounded rectangle)."""
    half = width / 2
    pts = []
    # left wall apical→basal
    steps = 18
    for i in range(steps + 1):
        t = i / steps
        y = lerp(top, bot, t)
        bulge = waviness * math.sin(t * math.pi) * (0.6 + 0.4 * math.sin(phase * 4 + t * 3))
        # apical narrower slightly, basal wider
        w = half * (0.92 + 0.12 * t)
        pts.append((cx - w - bulge * 0.4, y))
    # basal curve
    for i in range(1, 6):
        t = i / 6
        x = lerp(cx - half * 1.02, cx + half * 1.02, t)
        y = bot + 6 * math.sin(t * math.pi)
        pts.append((x, y))
    # right wall basal→apical
    for i in range(steps + 1):
        t = i / steps
        y = lerp(bot, top, t)
        tt = 1 - t
        bulge = waviness * math.sin(tt * math.pi) * (0.6 + 0.4 * math.sin(phase * 4 + tt * 3 + 1))
        w = half * (0.92 + 0.12 * tt)
        pts.append((cx + w + bulge * 0.4, y))
    # apical dome
    for i in range(1, 8):
        t = i / 8
        x = lerp(cx + half * 0.95, cx - half * 0.95, t)
        y = top - 8 * math.sin(t * math.pi) + 2 * math.sin(phase * 6 + t * 5)
        pts.append((x, y))
    return pts


def draw_brush_border(draw: ImageDraw.ImageDraw, x0, x1, y_base, phase=0.0, n=None):
    n = n or max(40, (x1 - x0) // 5)
    for i in range(n):
        x = x0 + i * (x1 - x0) / n
        sway = 2.8 * math.sin(phase * 6.28 + i * 0.45)
        h = 38 + 12 * math.sin(phase * 6.28 + i * 0.85) + (i % 5)
        # tapered shaft
        draw.line((x + sway, y_base, x + sway * 0.4, y_base - h), fill=(48, 130, 105), width=3)
        draw.line((x + sway, y_base, x + sway * 0.4, y_base - h + 2), fill=(120, 190, 160), width=1)
        # tip + glycocalyx halo
        tx, ty = x + sway * 0.4, y_base - h
        draw.ellipse((tx - 5, ty - 8, tx + 5, ty + 1), fill=(35, 110, 90), outline=(20, 70, 55))
        draw.ellipse((tx - 9, ty - 14, tx + 9, ty - 2), outline=(150, 200, 175), width=1)


def draw_bilayer_curve(draw, x, y0, y1, phase=0.0):
    mid = x + 7
    draw.rectangle((mid - 3, y0, mid + 3, y1), fill=(235, 205, 145))
    for yi, y in enumerate(range(int(y0), int(y1), 6)):
        wob = math.sin(phase * 6 + yi * 0.4)
        draw.ellipse((x - 1 + wob, y, mid - 3 + wob, y + 5), fill=(42, 145, 118), outline=(20, 90, 70))
        draw.ellipse((mid + 3 - wob, y, x + 16 - wob, y + 5), fill=(55, 155, 128), outline=(20, 90, 70))
        if yi % 4 == 0:
            draw.line((mid - 2, y + 2, mid + 2, y + 2), fill=(190, 110, 60), width=1)


def mito(draw, x, y, w=64, h=30, phase=0.0):
    draw.ellipse((x - 3, y - 2, x + w + 3, y + h + 2), fill=(180, 100, 60))  # soft shadow blob via darker under
    draw.ellipse((x, y, x + w, y + h), fill=(205, 125, 80), outline=(130, 65, 35), width=2)
    draw.ellipse((x + 5, y + 4, x + w - 5, y + h - 4), fill=(235, 165, 115))
    for i in range(5):
        cx = x + 10 + i * (w - 20) / 4
        wave = 2.5 * math.sin(phase + i)
        draw.arc((cx - 7, y + 5 + wave, cx + 11, y + h - 5 + wave), 210, 330, fill=(145, 75, 40), width=2)
    # matrix granules
    for i in range(4):
        draw.ellipse((x + 14 + i * 10, y + h / 2 - 2, x + 18 + i * 10, y + h / 2 + 2), fill=(170, 90, 50))


def er_stack(draw, pts, phase=0.0):
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        draw.line((x0, y0, x1, y1), fill=(175, 145, 115), width=6)
        draw.line((x0, y0 + 5, x1, y1 + 5), fill=(205, 180, 150), width=3)
        for t in (0.15, 0.4, 0.65, 0.9):
            rx = lerp(x0, x1, t) + 1.5 * math.sin(phase * 5 + i + t)
            ry = lerp(y0, y1, t) - 5
            draw.ellipse((rx - 2.5, ry - 2.5, rx + 2.5, ry + 2.5), fill=(155, 85, 65))


def golgi(draw, x, y, phase=0.0):
    for i in range(6):
        yy = y + i * 7
        w = 28 + i * 5
        draw.arc((x - w, yy, x + w, yy + 18), 200, 340, fill=(165, 110, 155), width=3)
    for i in range(4):
        vx = x + 32 + 8 * math.sin(phase * 6 + i)
        vy = y + 6 + i * 9
        draw.ellipse((vx, vy, vx + 11, vy + 11), fill=(185, 135, 170), outline=(110, 65, 105))


def nucleus_rich(draw, cx, cy, rx=110, ry=85, phase=0.0, active=False):
    # shadow
    draw.ellipse((cx - rx + 6, cy - ry + 8, cx + rx + 6, cy + ry + 8), fill=(170, 140, 100))
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(248, 230, 200), outline=(140, 100, 65), width=3)
    draw.ellipse((cx - rx + 7, cy - ry + 6, cx + rx - 7, cy + ry - 6), outline=(175, 135, 90), width=2)
    # pores
    for i in range(14):
        ang = i * (2 * math.pi / 14) + phase * 0.3
        px = cx + (rx - 1) * math.cos(ang)
        py = cy + (ry - 1) * math.sin(ang)
        draw.ellipse((px - 5, py - 4, px + 5, py + 4), fill=(205, 175, 125), outline=(115, 80, 50))
    # chromatin
    for i in range(12):
        ang = i * 0.55 + phase
        px = cx + 34 * math.cos(ang) * (0.5 + 0.5 * ((i * 0.3) % 1))
        py = cy + 26 * math.sin(ang * 1.15)
        col = (190, 75, 60) if active and i % 3 == 0 else (170, 135, 90)
        draw.ellipse((px - 9, py - 6, px + 9, py + 6), fill=col)
    # nucleolus
    draw.ellipse((cx - 18, cy - 14, cx + 12, cy + 16), fill=(155, 90, 70), outline=(100, 55, 40))
    draw.text((cx - 12, cy - 8), "核", fill=(85, 55, 30), font=F(16))


def receptor_tlr(draw, x, y, act=0.0, label="TLR4"):
    gap = 6 + 12 * act
    for i in range(8):
        rr = 18 + i * 3.2
        draw.arc((x - rr - gap * 0.25, y - rr - 40, x + rr + gap * 0.25, y - 4), 205, 335, fill=(45 + i * 6, 145 - i * 4, 115), width=3)
    draw.ellipse((x - 9, y - 40, x + 9, y - 24), fill=(230, 185, 95), outline=(150, 105, 40))
    for dx in (-9, -2, 5):
        draw.rectangle((x + dx, y - 4, x + dx + 5, y + 26), fill=(28, 105, 85), outline=(12, 55, 45))
    draw.rounded_rectangle((x - 15, y + 26, x + 15, y + 52), radius=6, fill=(65, 155, 125), outline=(20, 75, 55))
    draw.text((x - 18, y + 54), label, fill=(20, 70, 55), font=F(12))


def receptor_tnfr(draw, x, y, act=0.0, label="TNFR1"):
    gap = 3 + 8 * act
    for i in range(4):
        yy = y - 62 + i * 13
        draw.ellipse((x - 13 - gap * 0.3, yy, x + 13 + gap * 0.3, yy + 15), fill=(215, 85 + i * 12, 75), outline=(125, 35, 30), width=2)
    for dx in (-5, 2):
        draw.rectangle((x + dx, y - 8, x + dx + 5, y + 26), fill=(155, 45, 40))
    draw.polygon([(x - 12, y + 26), (x + 14, y + 26), (x + 22, y + 55), (x - 5, y + 50)], fill=(185, 65, 55), outline=(100, 30, 25))
    draw.text((x - 22, y + 56), label, fill=(130, 35, 30), font=F(12))


def receptor_il17(draw, x, y, act=0.0, label="IL17RA"):
    gap = 4 + 8 * act
    draw.rounded_rectangle((x - 20 - gap, y - 58, x - 1, y - 22), radius=9, fill=(85, 165, 135), outline=(25, 85, 65), width=2)
    draw.rounded_rectangle((x + 1, y - 58, x + 20 + gap, y - 22), radius=9, fill=(70, 150, 120), outline=(25, 85, 65), width=2)
    for dx in (-6, 1):
        draw.rectangle((x + dx, y - 18, x + dx + 5, y + 24), fill=(35, 115, 90))
    draw.ellipse((x - 14, y + 24, x + 16, y + 52), fill=(95, 175, 145), outline=(25, 85, 65))
    draw.text((x - 24, y + 54), label, fill=(20, 75, 55), font=F(12))


def ligand(draw, x, y, kind, phase=0.0):
    if kind == "TNF":
        for i, a0 in enumerate((0, 2.094, 4.189)):
            a = a0 + phase * 1.5
            lx, ly = x + 12 * math.cos(a), y + 10 * math.sin(a)
            draw.ellipse((lx - 12, ly - 12, lx + 12, ly + 12), fill=(195 - i * 18, 48, 40), outline=(85, 18, 12))
        draw.text((x - 28, y + 22), "TNF 三聚体", fill=(120, 30, 25), font=F(11))
    elif kind == "IL17":
        draw.ellipse((x - 17, y - 11, x + 3, y + 13), fill=(40, 120, 95), outline=(15, 60, 45))
        draw.ellipse((x - 3, y - 13, x + 17, y + 11), fill=(55, 145, 115), outline=(15, 60, 45))
        draw.text((x - 20, y + 18), "IL-17A", fill=(20, 70, 55), font=F(11))
    else:  # LPS
        for i in range(6):
            ang = -0.5 + i * 0.28
            draw.line((x, y + 3, x + 20 * math.cos(ang + 1.2), y + 3 + 18 * math.sin(ang + 1.2)), fill=(155, 75, 20), width=2)
        for i in range(3):
            draw.ellipse((x - 16 + i * 11, y - 18, x - 4 + i * 11, y - 3), fill=(225, 135, 45), outline=(130, 70, 20))
        draw.rectangle((x - 14, y - 2, x + 14, y + 7), fill=(175, 85, 28))
        draw.text((x - 14, y + 12), "LPS", fill=(120, 55, 15), font=F(11))


def protein(draw, x, y, name, color, pulse=0.0, lobes=3):
    r = 17 + 3 * math.sin(pulse)
    draw.ellipse((x - r - 4, y - r + 2, x + r + 4, y + r + 6), fill=(60, 50, 40))  # contact shadow
    for i in range(lobes):
        ang = i * (2 * math.pi / lobes) + pulse * 0.15
        lx = x + (r * 0.5) * math.cos(ang)
        ly = y + (r * 0.4) * math.sin(ang)
        draw.ellipse((lx - r + 3, ly - r + 5, lx + r - 3, ly + r - 2), fill=color, outline=(35, 30, 28))
    draw.ellipse((x - max(3, r // 3), y - max(4, r // 3), x - 1, y - 2), fill=(255, 255, 255))
    draw.text((x - 3 * len(name), y - 6), name, fill=(255, 255, 255), font=F(11))


def capillary(draw, x, y, w=150, h=40, phase=0.0):
    draw.ellipse((x, y, x + w, y + h), fill=(165, 55, 50), outline=(110, 30, 28), width=2)
    draw.ellipse((x + 5, y + 5, x + w - 5, y + h - 5), outline=(210, 130, 120))
    for i in range(5):
        rx = x + 16 + i * 24 + 5 * math.sin(phase * 6.28 + i)
        draw.ellipse((rx, y + h / 2 - 6, rx + 16, y + h / 2 + 6), fill=(205, 65, 55), outline=(130, 35, 30))


def immune(draw, x, y, kind="n"):
    if kind == "n":
        draw.ellipse((x, y, x + 36, y + 36), fill=(235, 225, 205), outline=(150, 130, 100))
        for dx, dy in ((7, 8), (15, 6), (11, 16)):
            draw.ellipse((x + dx, y + dy, x + dx + 12, y + dy + 11), fill=(85, 70, 125))
    else:
        draw.ellipse((x, y, x + 30, y + 30), fill=(215, 220, 230), outline=(95, 105, 135))
        draw.ellipse((x + 6, y + 6, x + 24, y + 24), fill=(75, 85, 135))


def float_label(draw, x, y, text, color=(40, 70, 60)):
    tw = 8 * len(text) + 16
    draw.rounded_rectangle((x, y, x + tw, y + 24), radius=8, fill=(255, 252, 248), outline=(180, 160, 130))
    draw.text((x + 8, y + 4), text, fill=color, font=F(12))


def save_gif(frames, name):
    OUT.mkdir(parents=True, exist_ok=True)
    frames[0].save(OUT / name, save_all=True, append_images=frames[1:], duration=DUR, loop=0, optimize=True)
    print("OK", name, frames[0].size)


# ===================== animations =====================

def anim_01():
    frames = []
    for i in range(N):
        t = i / N
        canvas = tissue_bg()
        # neighbor cells
        for dx, fill in ((-210, (195, 215, 200)), (210, (190, 212, 198))):
            poly = organic_column(520 + dx, 175, 720, 170, phase=t + dx * 0.01, waviness=8)
            shade_polygon(canvas, poly, fill, rim=(90, 125, 105))
        # main cell
        poly = organic_column(520, 160, 740, 210, phase=t, waviness=12)
        shade_polygon(canvas, poly, (210, 232, 218), light=(-0.4, -0.5), rim=(25, 100, 78))
        im = np_rgb(canvas)
        d = ImageDraw.Draw(im)
        banner(im, "肠黏膜柱状上皮 · 受体与信号入口", "组织学动画：黏液/糖萼 → 刷状缘 → 结构域受体 → 胞质细胞器 → 基底核 → 固有层")

        # mucus strands
        for j in range(16):
            x = 80 + j * 90 + 10 * math.sin(t * 6 + j)
            d.arc((x, 95, x + 70, 150), 200, 340, fill=(120, 170, 145), width=2)
        d.text((50, 88), "肠腔 · 黏液层 / 糖萼", fill=(90, 110, 100), font=F(13))

        # brush borders
        draw_brush_border(d, 320, 410, 178, t, n=22)
        draw_brush_border(d, 425, 615, 165, t, n=48)
        draw_brush_border(d, 630, 720, 178, t + 0.2, n=22)

        draw_bilayer_curve(d, 410, 175, 720, t)
        draw_bilayer_curve(d, 615, 175, 720, t)
        d.line((412, 190, 412, 230), fill=(70, 80, 130), width=2)
        d.text((360, 175), "紧密连接", fill=(70, 80, 130), font=F(11))

        # receptors + ligands on apical
        receptor_tlr(d, 460, 175, 0.5 + 0.5 * math.sin(t * 6.28), "TLR4")
        receptor_tnfr(d, 520, 175, 0.5 + 0.5 * math.sin(t * 6.28 + 1), "TNFR1")
        receptor_il17(d, 580, 175, 0.5 + 0.5 * math.sin(t * 6.28 + 2), "IL17RA")
        ligand(d, 455 + 12 * math.sin(t * 6.28), 115, "LPS", t)
        ligand(d, 520 + 10 * math.sin(t * 6.28 + 1), 110, "TNF", t)
        ligand(d, 585 + 10 * math.sin(t * 6.28 + 2), 115, "IL17", t)

        er_stack(d, [(450, 260), (510, 285), (470, 330), (540, 360), (490, 410)], t)
        golgi(d, 575, 300, t)
        mito(d, 450, 450, phase=t * 3)
        mito(d, 540, 500, w=58, h=28, phase=t * 3 + 1)
        mito(d, 470, 560, w=60, phase=t * 3 + 2)
        nucleus_rich(d, 520, 655, rx=78, ry=58, phase=t, active=True)

        # signal stream
        for k in range(10):
            tt = (t + k * 0.1) % 1.0
            x = 520 + 14 * math.sin(tt * 9)
            y = lerp(230, 640, tt)
            d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(220, 70, 55), outline=(140, 35, 30))

        # lamina propria
        d.text((40, 790), "固有层 · UC 炎症微环境（微血管 / 免疫细胞浸润）", fill=(100, 70, 45), font=F(14))
        capillary(d, 60, 840, phase=t)
        capillary(d, 280, 860, w=130, phase=t + 0.3)
        immune(d, 480, 850, "n")
        immune(d, 540, 870, "l")
        immune(d, 600, 845, "n")
        immune(d, 660, 865, "l")

        float_label(d, 980, 200, "顶端刷状缘 + 结构域受体")
        float_label(d, 980, 250, "胞质：内质网 · 高尔基 · 线粒体嵴")
        float_label(d, 980, 300, "基底核：核孔 / 染色质 / 核仁")
        float_label(d, 980, 350, "网药靶点轴：受体→信号→转录", (130, 80, 40))
        # leader lines
        d.line((960, 212, 620, 200), fill=(150, 140, 120), width=1)
        d.line((960, 262, 575, 320), fill=(150, 140, 120), width=1)
        d.line((960, 312, 600, 650), fill=(150, 140, 120), width=1)

        frames.append(im)
    save_gif(frames, "01_肠上皮细胞_受体信号动画.gif")


def anim_02():
    frames = []
    for i in range(N):
        t = i / N
        canvas = tissue_bg()
        poly = organic_column(520, 150, 820, 520, phase=t, waviness=16)
        # reshape to wide epithelial panel
        poly = []
        left, right, top, bot = 120, 980, 155, 850
        for j in range(20):
            yy = lerp(top, bot, j / 19)
            bulge = 10 * math.sin(j / 19 * math.pi + t * 2)
            poly.append((left - bulge, yy))
        for j in range(8):
            poly.append((lerp(left, right, j / 7), bot + 5 * math.sin(j / 7 * math.pi)))
        for j in range(20):
            yy = lerp(bot, top, j / 19)
            bulge = 10 * math.sin((1 - j / 19) * math.pi + t * 2)
            poly.append((right + bulge, yy))
        for j in range(8):
            poly.append((lerp(right, left, j / 7), top - 6 * math.sin(j / 7 * math.pi)))
        shade_polygon(canvas, poly, (205, 228, 215), rim=(28, 105, 82))
        im = np_rgb(canvas)
        d = ImageDraw.Draw(im)
        banner(im, "hsa04657 · IL-17 在上皮细胞中的信号", "解剖动画：IL-17 二聚体 → IL17RA/C → SEFIR–Act1 小体 → 核孔入核 → 趋化因子")

        draw_brush_border(d, 150, 950, 160, t, n=90)
        draw_bilayer_curve(d, 118, 200, 780, t)
        ligand(d, 55 + 10 * math.sin(t * 6.28), 360, "IL17", t)
        receptor_il17(d, 160, 360, 0.6 + 0.4 * math.sin(t * 6.28), "IL17RA/C")

        er_stack(d, [(220, 260), (340, 290), (280, 350), (400, 390)], t)
        golgi(d, 520, 270, t)
        mito(d, 280, 520, phase=t)
        mito(d, 400, 580, phase=t + 1)

        path = [(240, 400), (380, 375), (520, 360), (650, 390)]
        names = ["Act1", "TRAF6", "TAK1", "IKK"]
        cols = [(230, 126, 34), (192, 57, 43), (146, 43, 33), (120, 40, 31)]
        for j in range(len(path) - 1):
            d.line((*path[j], *path[j + 1]), fill=(150, 170, 155), width=3)
            tt = (t + j * 0.14) % 1.0
            px, py = lerp(path[j][0], path[j + 1][0], tt), lerp(path[j][1], path[j + 1][1], tt)
            d.ellipse((px - 7, py - 7, px + 7, py + 7), fill=(244, 208, 63), outline=(180, 140, 20))
        for (x, y), name, col in zip(path, names, cols):
            protein(d, x, y, name, col, t * 6 + x * 0.01)

        nucleus_rich(d, 760, 620, rx=130, ry=100, phase=t, active=True)
        ntt = (math.sin(t * 6.28) + 1) / 2
        protein(d, int(lerp(650, 740, ntt)), int(lerp(420, 600, ntt)), "NF-κB", (231, 76, 60), t * 7, 2)
        for k, g in enumerate(["CXCL8", "IL6", "MMP9"]):
            gx = 680 + k * 85
            gy = 540 + 6 * math.sin(t * 6 + k)
            d.rounded_rectangle((gx - 32, gy - 14, gx + 32, gy + 14), radius=8, fill=(138, 90, 43))
            d.text((gx - 24, gy - 8), g, fill=(255, 255, 255), font=F(12))

        float_label(d, 1100, 220, "1 刷状缘上皮")
        float_label(d, 1100, 280, "2 受体 SEFIR 域")
        float_label(d, 1100, 340, "3 Act1 信号小体")
        float_label(d, 1100, 400, "4 NF-κB 入核")
        float_label(d, 1100, 460, "UC 中性粒募集轴", (130, 80, 40))
        frames.append(im)
    save_gif(frames, "02_IL17信号通路_动画.gif")


def anim_03():
    frames = []
    for i in range(N):
        t = i / N
        canvas = tissue_bg()
        # large cell oval as polygon approximation
        cx, cy, rx, ry = 820, 520, 480, 340
        poly = [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 48, endpoint=False)]
        shade_polygon(canvas, poly, (200, 225, 210), rim=(28, 105, 82))
        im = np_rgb(canvas)
        d = ImageDraw.Draw(im)
        banner(im, "hsa04668 · TNF 跨膜信号与核应答", "解剖动画：TNF 三聚体 → TNFR1 CRD → TRADD/TRAF 复合体 → NF-κB 经核孔入核")

        draw_bilayer_curve(d, 335, 260, 760, t)
        ligand(d, 200 + 14 * math.sin(t * 6.28), 480, "TNF", t)
        receptor_tnfr(d, 380, 480, 0.7 + 0.3 * math.sin(t * 6.28), "TNFR1")
        er_stack(d, [(430, 300), (560, 330), (500, 390), (640, 430)], t)
        golgi(d, 720, 300, t)
        mito(d, 480, 620, phase=t)
        mito(d, 620, 680, phase=t + 1)
        protein(d, 500, 450, "TRADD", (230, 126, 34), t * 6)
        protein(d, 500, 550, "TRAF2", (211, 84, 0), t * 6 + 1)
        protein(d, 640, 490, "IKK", (146, 43, 33), t * 6 + 2, 4)
        nucleus_rich(d, 980, 520, rx=140, ry=110, phase=t, active=True)
        ntt = (math.sin(t * 6.28) + 1) / 2
        protein(d, int(lerp(720, 940, ntt)), int(lerp(490, 520, ntt)), "NF-κB", (231, 76, 60), t * 8, 2)
        if ntt > 0.5:
            for gi, g in enumerate(["IL6", "MMP9", "SELE"]):
                d.rounded_rectangle((880 + gi * 100, 320, 965 + gi * 100, 355), radius=8, fill=(138, 90, 43))
                d.text((895 + gi * 100, 328), g, fill=(255, 255, 255), font=F(13))
        float_label(d, 40, 820, "抗 TNF 生物制剂靶点轴 · 网药交集常富集")
        float_label(d, 40, 870, "结构：三聚体配体 · CRD 胞外域 · 死亡结构域")
        frames.append(im)
    save_gif(frames, "03_TNF信号通路_动画.gif")


def anim_04():
    frames = []
    for i in range(N):
        t = i / N
        canvas = tissue_bg()
        cx, cy, rx, ry = 900, 500, 500, 360
        poly = [(cx + (rx + 8 * math.sin(3 * a + t)) * math.cos(a), cy + ry * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 60, endpoint=False)]
        shade_polygon(canvas, poly, (200, 220, 208), rim=(35, 100, 82))
        # pseudopod
        pad = [(260, 380), (200, 420), (220, 500), (300, 520), (340, 450)]
        shade_polygon(canvas, pad, (200, 220, 208), rim=(35, 100, 82))
        im = np_rgb(canvas)
        d = ImageDraw.Draw(im)
        banner(im, "hsa04620 · TLR4 识别与 MyD88 轴", "解剖动画：G− 细菌 LPS → TLR4/MD-2 马蹄 LRR 二聚 → Myddosome → 炎症基因")

        draw_bilayer_curve(d, 350, 240, 740, t)
        bx = 70 + 18 * math.sin(t * 6.28)
        d.ellipse((bx, 360, bx + 100, 460), fill=(85, 38, 8), outline=(45, 18, 4), width=2)
        for k in range(10):
            ang = k * 0.6 + t * 2
            d.line((bx + 50, 365, bx + 50 + 30 * math.cos(ang), 350 - 12 * abs(math.sin(ang))), fill=(200, 95, 35), width=2)
        d.text((bx + 20, 470), "G− 细菌", fill=(85, 40, 10), font=F(13))
        ligand(d, bx + 130, 400, "LPS", t)
        receptor_tlr(d, 410, 420, 0.85, "TLR4")
        receptor_tlr(d, 465, 470, 0.85, "TLR4")
        er_stack(d, [(540, 280), (660, 310), (600, 370)], t)
        golgi(d, 780, 270, t)
        mito(d, 620, 600, phase=t)
        mito(d, 760, 660, phase=t + 1)
        for j, (name, col, oy) in enumerate([("MyD88", (230, 126, 34), 0), ("IRAK", (192, 57, 43), 60), ("TRAF6", (146, 43, 33), 120)]):
            protein(d, 600, 400 + oy, name, col, t * 6 + j)
            if j < 2:
                d.line((600, 420 + oy, 600, 445 + oy), fill=(140, 160, 150), width=3)
        nucleus_rich(d, 1050, 520, rx=135, ry=105, phase=t, active=True)
        tt = (math.sin(t * 6.28 - 0.4) + 1) / 2
        protein(d, int(lerp(720, 1000, tt)), int(lerp(470, 520, tt)), "NF-κB", (231, 76, 60), t * 7, 2)
        for gi, g in enumerate(["IL6", "TNF", "CXCL8"]):
            d.rounded_rectangle((940 + gi * 100, 280, 1025 + gi * 100, 318), radius=8, fill=(138, 90, 43))
            d.text((955 + gi * 100, 288), g, fill=(255, 255, 255), font=F(13))
        float_label(d, 40, 860, "巨噬/上皮样细胞 · LPS–TLR4/MD-2 · Myddosome · 核孔入核")
        frames.append(im)
    save_gif(frames, "04_TLR信号通路_动画.gif")


def anim_05():
    frames = []
    for i in range(N):
        t = i / N
        o2 = 0.55 - 0.35 * ((math.sin(t * 6.28) + 1) / 2)
        canvas = tissue_bg()
        # hypoxia blue field
        yy, xx = np.mgrid[0:H, 0:W]
        depth = (1 - o2) * np.clip(1 - xx / 380, 0, 1)
        canvas[..., 0] = canvas[..., 0] * (1 - 0.35 * depth) + 50 * depth
        canvas[..., 1] = canvas[..., 1] * (1 - 0.25 * depth) + 95 * depth
        canvas[..., 2] = canvas[..., 2] * (1 - 0.1 * depth) + 150 * depth

        cyto = (185 + 40 * o2, 210 + 20 * o2, 225 - 15 * (1 - o2))
        poly = organic_column(700, 170, 820, 380, phase=t, waviness=14)
        shade_polygon(canvas, poly, cyto, rim=(28, 105, 82))
        im = np_rgb(canvas)
        d = ImageDraw.Draw(im)
        banner(im, "hsa04066 · 黏膜缺氧与 HIF-1α 入核", "解剖动画：炎症黏膜氧梯度 · HIF-1α 稳定 · 经核孔入核启动血管/糖酵解基因")

        d.text((36, 100), f"组织氧分压示意  {o2 * 100:.0f}%", fill=(30, 80, 120), font=F(15))
        draw_brush_border(d, 530, 870, 175, t, n=55)
        draw_bilayer_curve(d, 505, 200, 780, t)
        er_stack(d, [(560, 260), (660, 290), (600, 350), (720, 380)], t)
        golgi(d, 800, 280, t)
        mito(d, 580, 500, phase=t)
        mito(d, 720, 560, phase=t + 1)
        nucleus_rich(d, 700, 620, rx=115, ry=90, phase=t, active=o2 < 0.4)

        hif_t = 1 - o2
        protein(d, int(lerp(580, 700, hif_t)), int(lerp(340, 600, hif_t)), "HIF-1α", (40, 116, 166), t * 6, 3)
        if o2 > 0.45:
            float_label(d, 540, 220, "常氧：PHD 羟化 → 降解倾向")
        else:
            float_label(d, 540, 220, "低氧：HIF-1α 稳定 · 入核转录", (30, 80, 120))
            for gi, g in enumerate(["VEGFA", "SLC2A1", "NOS2"]):
                d.rounded_rectangle((620 + gi * 100, 400, 705 + gi * 100, 435), radius=8, fill=(31, 111, 91))
                d.text((632 + gi * 100, 408), g, fill=(255, 255, 255), font=F(12))

        capillary(d, 40, 860, w=170, phase=t)
        d.text((60, 920), "固有层微血管", fill=(120, 50, 45), font=F(12))
        float_label(d, 1100, 220, "黏膜氧梯度 / 低氧蓝带")
        float_label(d, 1100, 280, "HIF-1α 向核孔迁移")
        float_label(d, 1100, 340, "UC 炎症黏膜常见缺氧", (130, 80, 40))
        frames.append(im)
    save_gif(frames, "05_HIF1缺氧应答_动画.gif")


def write_index():
    items = [
        ("01_肠上皮细胞_受体信号动画.gif", "柱状上皮组织学：黏液·刷状缘·受体域·细胞器·固有层"),
        ("02_IL17信号通路_动画.gif", "IL-17 上皮细胞内结构 cascade"),
        ("03_TNF信号通路_动画.gif", "TNF 三聚体 → TNFR1 CRD → 入核"),
        ("04_TLR信号通路_动画.gif", "细菌 LPS → TLR4/MD-2 马蹄域 → Myddosome"),
        ("05_HIF1缺氧应答_动画.gif", "黏膜缺氧梯度与 HIF-1α 入核"),
    ]
    cards = "".join(
        f'<article class="card"><img src="{fn}" alt="{desc}"/><h3>{desc}</h3></article>'
        for fn, desc in items
    )
    (OUT / "动画图册.html").write_text(
        f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"/>
<title>生物结构动画图册</title>
<style>
body{{margin:0;font-family:"Microsoft YaHei",sans-serif;background:#E4D9C8;color:#1C2A24}}
header{{padding:28px;background:#12352E;color:#F4FFF9}}
main{{max-width:1600px;margin:0 auto;padding:20px;display:grid;gap:20px}}
.card{{background:#FFFCFA;border-radius:16px;overflow:hidden;border:1px solid #C9B8A0}}
.card img{{width:100%;display:block}}
.card h3{{margin:14px 18px 18px;color:#1A4F42}}
</style></head><body>
<header><h1>人体生物结构 · 精细组织学动画</h1>
<p>有机细胞轮廓 · 密集微绒毛 · 磷脂双层 · 受体结构域 · 线粒体嵴/内质网/高尔基 · 核孔核仁 · 固有层微环境</p>
</header><main>{cards}</main></body></html>""",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "精细组织学动画 GIF（非几何简图）\n打开 动画图册.html 浏览。\n",
        encoding="utf-8",
    )


def main():
    anim_01()
    anim_02()
    anim_03()
    anim_04()
    anim_05()
    write_index()
    print("DONE", OUT)


if __name__ == "__main__":
    main()
