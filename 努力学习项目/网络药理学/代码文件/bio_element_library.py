# -*- coding: utf-8 -*-
"""Draw reusable biological organelle sprites (RGBA PNGs).

One-time local generation — no GenerateImage / token cost.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


@dataclass
class ElementSpec:
    id: str
    name_zh: str
    name_en: str
    width: int
    height: int


ELEMENTS: list[ElementSpec] = [
    ElementSpec("nucleus", "细胞核", "Nucleus", 420, 320),
    ElementSpec("mitochondria", "线粒体", "Mitochondria", 220, 120),
    ElementSpec("er_rough", "粗面内质网", "Rough ER", 300, 200),
    ElementSpec("er_smooth", "光面内质网", "Smooth ER", 260, 160),
    ElementSpec("golgi", "高尔基体", "Golgi", 240, 180),
    ElementSpec("lysosome", "溶酶体", "Lysosome", 90, 90),
    ElementSpec("ribosome_cluster", "核糖体簇", "Ribosomes", 120, 80),
    ElementSpec("membrane_patch", "细胞膜片段", "Membrane", 520, 140),
    ElementSpec("receptor_tk", "受体酪氨酸激酶", "RTK receptor", 160, 200),
    ElementSpec("receptor_tlr", "TLR受体", "TLR receptor", 140, 180),
    ElementSpec("lipid_droplet", "脂滴", "Lipid droplet", 110, 110),
    ElementSpec("virus_particle", "病毒颗粒", "Virus", 100, 100),
    ElementSpec("ecm_fiber", "细胞外基质纤维", "ECM fiber", 400, 120),
    ElementSpec("brush_border", "刷状缘", "Brush border", 360, 100),
    ElementSpec("nuclear_pore_glow", "核孔", "Nuclear pore", 80, 80),
]


def _alpha_im(w: int, h: int) -> Image.Image:
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def draw_nucleus(w: int, h: int) -> Image.Image:
    im = _alpha_im(w, h)
    d = ImageDraw.Draw(im)
    cx, cy = w // 2, h // 2
    # outer envelope
    d.ellipse((20, 30, w - 20, h - 20), fill=(120, 80, 180, 200), outline=(80, 50, 140, 230), width=4)
    d.ellipse((35, 45, w - 35, h - 35), fill=(150, 110, 210, 120), outline=(100, 70, 160, 180), width=2)
    # chromatin
    rng = random.Random(7)
    for _ in range(18):
        x0 = rng.randint(60, w - 80)
        y0 = rng.randint(70, h - 70)
        d.ellipse((x0, y0, x0 + rng.randint(30, 70), y0 + rng.randint(20, 45)), fill=(90, 60, 150, 90))
    # nucleolus
    d.ellipse((cx - 35, cy - 25, cx + 35, cy + 25), fill=(200, 170, 230, 180))
    # pores
    for ang in range(0, 360, 28):
        rad = math.radians(ang)
        px = cx + int((w * 0.38) * math.cos(rad))
        py = cy + int((h * 0.36) * math.sin(rad))
        d.ellipse((px - 8, py - 8, px + 8, py + 8), fill=(255, 230, 180, 200), outline=(255, 200, 120, 220))
    return im.filter(ImageFilter.GaussianBlur(0.3))


def draw_mitochondria(w: int, h: int) -> Image.Image:
    im = _alpha_im(w, h)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 25, w - 10, h - 25), radius=45, fill=(70, 140, 200, 220), outline=(40, 100, 160, 240), width=3)
    for i in range(5):
        x = 35 + i * 32
        d.arc((x, 20, x + 50, h - 20), 200, 340, fill=(180, 230, 255, 200), width=3)
    return im


def draw_er_rough(w: int, h: int) -> Image.Image:
    im = _alpha_im(w, h)
    d = ImageDraw.Draw(im)
    pts = [(20, h // 2), (80, 30), (160, h - 40), (240, 50), (w - 20, h // 2 + 10)]
    d.line(pts, fill=(100, 180, 160, 220), width=18)
    d.line([(p[0], p[1] + 12) for p in pts], fill=(80, 150, 140, 180), width=10)
    rng = random.Random(3)
    for _ in range(40):
        x, y = rng.randint(25, w - 25), rng.randint(20, h - 20)
        d.ellipse((x, y, x + 6, y + 6), fill=(60, 60, 80, 200))
    return im


def draw_er_smooth(w: int, h: int) -> Image.Image:
    im = _alpha_im(w, h)
    d = ImageDraw.Draw(im)
    for off in (0, 18, 36):
        pts = [(10, h // 2 + off), (100, 20 + off), (200, h - 30 + off), (w - 10, 40 + off)]
        d.line(pts, fill=(90, 170, 150, 200), width=12)
    return im


def draw_golgi(w: int, h: int) -> Image.Image:
    im = _alpha_im(w, h)
    d = ImageDraw.Draw(im)
    for i in range(5):
        y = 25 + i * 28
        d.arc((30, y, w - 30, y + 50), 0, 180, fill=(180, 140, 200, 220), width=10)
    return im


def draw_lysosome(w: int, h: int) -> Image.Image:
    im = _alpha_im(w, h)
    d = ImageDraw.Draw(im)
    d.ellipse((8, 8, w - 8, h - 8), fill=(200, 120, 80, 210), outline=(160, 80, 50, 230), width=3)
    d.ellipse((20, 20, w - 30, h - 30), fill=(230, 160, 100, 80))
    return im


def draw_ribosome_cluster(w: int, h: int) -> Image.Image:
    im = _alpha_im(w, h)
    d = ImageDraw.Draw(im)
    rng = random.Random(11)
    for _ in range(55):
        x, y = rng.randint(5, w - 10), rng.randint(5, h - 10)
        d.ellipse((x, y, x + 7, y + 7), fill=(80, 80, 100, 220))
    return im


def draw_membrane_patch(w: int, h: int) -> Image.Image:
    im = _alpha_im(w, h)
    d = ImageDraw.Draw(im)
    cy = h // 2
    # bilayer wave
    for layer, col in ((cy - 18, (120, 200, 180, 200)), (cy + 18, (100, 180, 160, 200))):
        pts = [(x, layer + int(8 * math.sin(x / 28))) for x in range(0, w, 8)]
        d.line(pts, fill=col, width=6)
    # phospholipid heads
    for x in range(20, w - 20, 22):
        y = cy + int(8 * math.sin(x / 28))
        d.ellipse((x - 5, y - 22, x + 5, y - 12), fill=(200, 240, 230, 220))
        d.ellipse((x - 5, y + 12, x + 5, y + 22), fill=(200, 240, 230, 220))
    return im


def draw_receptor_tk(w: int, h: int) -> Image.Image:
    im = _alpha_im(w, h)
    d = ImageDraw.Draw(im)
    cx = w // 2
    d.rectangle((cx - 12, h - 40, cx + 12, h - 5), fill=(90, 160, 200, 230))
    d.ellipse((cx - 45, 20, cx + 45, 90), fill=(120, 190, 220, 220), outline=(70, 140, 180, 240), width=3)
    d.line((cx, 90, cx, h - 40), fill=(100, 170, 210, 230), width=8)
  # Y arms
    d.line((cx, 50, cx - 35, 10), fill=(100, 170, 210, 220), width=6)
    d.line((cx, 50, cx + 35, 10), fill=(100, 170, 210, 220), width=6)
    return im


def draw_receptor_tlr(w: int, h: int) -> Image.Image:
    im = _alpha_im(w, h)
    d = ImageDraw.Draw(im)
    cx = w // 2
    d.rectangle((cx - 10, h - 35, cx + 10, h - 5), fill=(90, 160, 200, 230))
    for i in range(6):
        y = 25 + i * 18
        d.arc((cx - 50, y, cx + 50, y + 30), 200, 340, fill=(140, 200, 180, 220), width=5)
    return im


def draw_lipid_droplet(w: int, h: int) -> Image.Image:
    im = _alpha_im(w, h)
    d = ImageDraw.Draw(im)
    d.ellipse((5, 5, w - 5, h - 5), fill=(255, 220, 80, 230), outline=(220, 170, 40, 240), width=3)
    d.ellipse((18, 12, w - 30, h - 35), fill=(255, 245, 180, 100))
    return im


def draw_virus_particle(w: int, h: int) -> Image.Image:
    im = _alpha_im(w, h)
    d = ImageDraw.Draw(im)
    d.ellipse((10, 10, w - 10, h - 10), fill=(180, 100, 200, 220), outline=(140, 60, 170, 240), width=3)
    for ang in range(0, 360, 45):
        rad = math.radians(ang)
        x1 = w // 2 + int(35 * math.cos(rad))
        y1 = h // 2 + int(35 * math.sin(rad))
        x2 = w // 2 + int(48 * math.cos(rad))
        y2 = h // 2 + int(48 * math.sin(rad))
        d.line((x1, y1, x2, y2), fill=(220, 160, 240, 220), width=4)
    return im


def draw_ecm_fiber(w: int, h: int) -> Image.Image:
    im = _alpha_im(w, h)
    d = ImageDraw.Draw(im)
    rng = random.Random(5)
    for _ in range(12):
        y = rng.randint(10, h - 10)
        pts = [(x, y + rng.randint(-8, 8)) for x in range(0, w, 15)]
        d.line(pts, fill=(180, 140, 100, 160), width=rng.randint(3, 6))
    return im


def draw_brush_border(w: int, h: int) -> Image.Image:
    im = _alpha_im(w, h)
    d = ImageDraw.Draw(im)
    for x in range(15, w - 15, 8):
        d.line((x, h - 10, x, 15), fill=(160, 210, 190, 220), width=3)
    d.line((10, h - 8, w - 10, h - 8), fill=(120, 180, 160, 200), width=5)
    return im


def draw_nuclear_pore_glow(w: int, h: int) -> Image.Image:
    im = _alpha_im(w, h)
    d = ImageDraw.Draw(im)
    d.ellipse((10, 10, w - 10, h - 10), fill=(255, 230, 150, 180), outline=(255, 200, 80, 220), width=3)
    d.ellipse((25, 25, w - 25, h - 25), fill=(255, 255, 220, 80))
    return im


DRAWERS = {
    "nucleus": draw_nucleus,
    "mitochondria": draw_mitochondria,
    "er_rough": draw_er_rough,
    "er_smooth": draw_er_smooth,
    "golgi": draw_golgi,
    "lysosome": draw_lysosome,
    "ribosome_cluster": draw_ribosome_cluster,
    "membrane_patch": draw_membrane_patch,
    "receptor_tk": draw_receptor_tk,
    "receptor_tlr": draw_receptor_tlr,
    "lipid_droplet": draw_lipid_droplet,
    "virus_particle": draw_virus_particle,
    "ecm_fiber": draw_ecm_fiber,
    "brush_border": draw_brush_border,
    "nuclear_pore_glow": draw_nuclear_pore_glow,
}


# Layout for AI cutout elements: (element_id, x, y, scale)
# Tuned for detailed medical-illustration sprites (not schematic icons).
LAYOUTS: dict[str, list[tuple[str, int, int, float]]] = {
    "epithelium": [
        ("ecm_fiber", 40, 740, 1.15),
        ("membrane_patch", 80, 100, 1.15),
        ("brush_border", 180, 55, 1.05),
        ("receptor_tlr", 560, 70, 0.95),
        ("receptor_tk", 980, 85, 0.9),
        ("er_rough", 220, 300, 1.05),
        ("mitochondria", 700, 340, 1.1),
        ("golgi", 1050, 300, 0.95),
        ("lysosome", 1180, 480, 0.9),
        ("nucleus", 560, 470, 0.85),
    ],
    "macrophage": [
        ("ecm_fiber", 30, 730, 1.0),
        ("membrane_patch", 70, 150, 1.1),
        ("receptor_tlr", 500, 130, 1.05),
        ("virus_particle", 160, 60, 1.15),
        ("virus_particle", 320, 90, 0.85),
        ("mitochondria", 220, 380, 1.15),
        ("mitochondria", 900, 400, 0.95),
        ("er_rough", 480, 290, 1.0),
        ("golgi", 1080, 280, 0.95),
        ("lysosome", 1220, 360, 0.95),
        ("nucleus", 580, 480, 0.82),
    ],
    "hepatocyte": [
        ("membrane_patch", 60, 140, 1.1),
        ("lipid_droplet", 180, 280, 1.2),
        ("lipid_droplet", 360, 400, 1.0),
        ("lipid_droplet", 780, 320, 1.25),
        ("er_smooth", 280, 260, 1.05),
        ("mitochondria", 600, 380, 1.2),
        ("golgi", 1080, 300, 0.95),
        ("nucleus", 600, 500, 0.8),
    ],
    "endothelium": [
        ("ecm_fiber", 20, 760, 1.2),
        ("membrane_patch", 70, 170, 1.15),
        ("receptor_tk", 560, 150, 1.0),
        ("mitochondria", 280, 380, 1.15),
        ("er_smooth", 780, 320, 1.05),
        ("nucleus", 560, 500, 0.82),
    ],
    "cancer": [
        ("membrane_patch", 70, 140, 1.15),
        ("receptor_tk", 540, 120, 1.1),
        ("mitochondria", 220, 360, 1.2),
        ("er_rough", 500, 300, 1.05),
        ("golgi", 1050, 300, 1.0),
        ("nucleus", 580, 480, 0.88),
    ],
    "lymphocyte": [
        ("membrane_patch", 90, 160, 1.05),
        ("receptor_tk", 560, 140, 0.95),
        ("mitochondria", 280, 390, 1.05),
        ("er_rough", 760, 330, 0.95),
        ("nucleus", 560, 500, 0.78),
    ],
    "virus": [
        ("membrane_patch", 70, 150, 1.1),
        ("virus_particle", 180, 50, 1.25),
        ("virus_particle", 340, 90, 0.95),
        ("receptor_tlr", 560, 130, 1.05),
        ("mitochondria", 250, 380, 1.15),
        ("er_rough", 720, 300, 1.0),
        ("nucleus", 580, 490, 0.82),
    ],
    "signaling": [
        ("membrane_patch", 70, 150, 1.15),
        ("receptor_tk", 560, 130, 1.1),
        ("mitochondria", 240, 380, 1.2),
        ("er_rough", 520, 300, 1.05),
        ("golgi", 1080, 320, 0.95),
        ("nucleus", 580, 480, 0.85),
    ],
    "apoptosis": [
        ("membrane_patch", 70, 150, 1.1),
        ("mitochondria", 280, 380, 1.25),
        ("er_smooth", 760, 320, 1.0),
        ("lysosome", 1100, 420, 1.0),
        ("nucleus", 580, 500, 0.8),
    ],
    "hypoxia": [
        ("membrane_patch", 70, 150, 1.1),
        ("mitochondria", 300, 380, 1.15),
        ("er_rough", 560, 300, 1.0),
        ("nucleus", 580, 490, 0.88),
    ],
    "metabolism": [
        ("membrane_patch", 70, 150, 1.1),
        ("lipid_droplet", 220, 320, 1.15),
        ("mitochondria", 520, 380, 1.25),
        ("er_smooth", 880, 300, 1.0),
        ("nucleus", 580, 500, 0.8),
    ],
    "neuron": [
        ("membrane_patch", 60, 200, 1.1),
        ("receptor_tk", 500, 180, 1.0),
        ("mitochondria", 280, 420, 1.05),
        ("er_rough", 720, 350, 0.95),
        ("nucleus", 540, 520, 0.72),
    ],
    "adhesion": [
        ("ecm_fiber", 20, 740, 1.25),
        ("membrane_patch", 80, 170, 1.15),
        ("receptor_tk", 560, 150, 1.0),
        ("mitochondria", 300, 400, 1.15),
        ("nucleus", 580, 500, 0.82),
    ],
}


def render_element(spec: ElementSpec) -> Image.Image:
    fn = DRAWERS[spec.id]
    return fn(spec.width, spec.height)


def paste_element(canvas: Image.Image, elem: Image.Image, x: int, y: int, scale: float = 1.0, pulse: float = 0.0):
    if scale != 1.0:
        nw = max(1, int(elem.width * scale))
        nh = max(1, int(elem.height * scale))
        elem = elem.resize((nw, nh), Image.Resampling.LANCZOS)
    if pulse:
        elem = ImageEnhance.Brightness(elem).enhance(1.0 + pulse)
    cw, ch = canvas.size
    ew, eh = elem.size
    # clip if partially outside
    dx, dy = max(0, -x), max(0, -y)
    sx2 = min(ew, cw - x)
    sy2 = min(eh, ch - y)
    if sx2 <= dx or sy2 <= dy:
        return
    crop = elem.crop((dx, dy, sx2, sy2))
    canvas.alpha_composite(crop, (max(0, x), max(0, y)))
