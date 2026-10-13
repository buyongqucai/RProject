# -*- coding: utf-8 -*-
"""Shared compose helpers: full illustration visible, NO title banner overlay."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

W, H = 1600, 900
MARGIN = 12  # small pad so edge biology is not flush-cropped by viewers
CONTENT_TOP = MARGIN
CONTENT_BOTTOM_PAD = MARGIN
CONTENT_H = H - CONTENT_TOP - CONTENT_BOTTOM_PAD
CONTENT_W = W - 2 * MARGIN
BG = (226, 238, 232)
N = 24  # batch-friendly; still smooth at 75ms/frame
DUR = 75
# Title banner DISABLED — user: do not cover illustration with dark header
DRAW_BANNER = False
DRAW_NOTES = False  # optional right-side chips; off by default to avoid covering biology


def F(size: int):
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def lerp(a, b, t):
    return a + (b - a) * t


def prepare_base(src: Path) -> Image.Image:
    """Fit entire illustration into full canvas (letterbox). Never stretch-crop."""
    im = Image.open(src).convert("RGB")
    sw, sh = im.size
    scale = min(CONTENT_W / sw, CONTENT_H / sh)
    nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (W, H), BG)
    x = (W - nw) // 2
    y = CONTENT_TOP + (CONTENT_H - nh) // 2
    canvas.paste(im, (x, y))
    canvas = ImageEnhance.Contrast(canvas).enhance(1.06)
    canvas = ImageEnhance.Color(canvas).enhance(1.04)
    return canvas


def shift_path(path: list[tuple[int, int]]) -> list[tuple[int, int]]:
    return [(x, max(CONTENT_TOP + 40, min(H - 40, y))) for x, y in path]


def draw_banner(d: ImageDraw.ImageDraw, title: str, sub: str):
    """Legacy helper — kept but unused when DRAW_BANNER is False."""
    if not DRAW_BANNER:
        return
    bh = 78
    d.rectangle((0, 0, W, bh), fill=(14, 48, 42))
    d.rectangle((0, bh - 8, W, bh), fill=(8, 32, 28))
    d.text((28, 10), title, fill=(244, 255, 248), font=F(24))
    d.text((28, 42), sub, fill=(168, 210, 195), font=F(13))


def draw_notes_soft(im: Image.Image, notes: list[str]) -> Image.Image:
    if not DRAW_NOTES or not notes:
        return im.convert("RGBA") if im.mode != "RGBA" else im
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    x1 = W - 24
    y = CONTENT_TOP + 16
    od.text((x1 - 72, y), "要点", fill=(255, 255, 255, 160), font=F(12))
    y += 22
    for line in notes:
        tw = 12 * len(line) + 28
        x0 = x1 - tw
        od.rounded_rectangle(
            (x0, y, x1, y + 26), radius=8, fill=(20, 40, 35, 110), outline=(255, 255, 255, 55)
        )
        od.text((x0 + 12, y + 5), line, fill=(245, 250, 248, 230), font=F(12))
        y += 32
    return Image.alpha_composite(im.convert("RGBA"), overlay)


def animate_frames(
    base: Image.Image,
    title: str,
    sub: str,
    notes: list[str],
    path: list[tuple[int, int]],
) -> list[Image.Image]:
    path = shift_path(path)
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
            od.line((x0, y0, x1, y1), fill=(255, 220, 120, 48), width=4)
            for k in range(3):
                tt = (t + seg * 0.18 + k * 0.12) % 1.0
                x = lerp(x0, x1, tt)
                y = lerp(y0, y1, tt)
                r = 7 + 2 * math.sin(t * 8 + k)
                od.ellipse((x - r - 4, y - r - 4, x + r + 4, y + r + 4), fill=(255, 180, 60, 65))
                od.ellipse((x - r, y - r, x + r, y + r), fill=(255, 230, 120, 210), outline=(220, 140, 40, 255))
        gy = int(CONTENT_TOP + 80 + (CONTENT_H - 160) * ((math.sin(t * 6.28) + 1) / 2))
        od.ellipse((200, gy - 40, W - 200, gy + 40), fill=(255, 255, 230, 16))
        frame = Image.alpha_composite(frame.convert("RGBA"), overlay)
        frame = draw_notes_soft(frame, notes)
        out = frame.convert("RGB")
        d = ImageDraw.Draw(out)
        if DRAW_BANNER:
            draw_banner(d, title, sub)
        nx, ny = path[-1]
        rr = 26 + 7 * math.sin(t * 6.28)
        d.ellipse((nx - rr, ny - rr, nx + rr, ny + rr), outline=(231, 76, 60), width=2)
        frames.append(out)
    return frames
