#!/usr/bin/env python3
"""Prepare a user detail screenshot into a square PNG for PP docking collage.

Pipeline (BASELINE):
  1) docking-style trim_white_border (whole near-white rows/cols)
  2) aggressive near-white row/col trim (flecked anti-aliased borders)
  3) center-crop to square (no white padding)

Usage:
  python prepare_detail_square.py INPUT.jpg -o detail-2.png
  python prepare_detail_square.py INPUT.png --thresh 248 --white-frac 0.92
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def trim_white_border(
    img: Image.Image,
    thresh: int = 250,
    dust_frac: float = 0.001,
) -> Image.Image:
    """Match MolecularDocking collage trim_white_border semantics."""
    rgb = np.array(img.convert("RGB"))
    non_white = np.any(rgb < thresh, axis=2)
    cols = non_white.sum(axis=0)
    rows = non_white.sum(axis=1)
    min_cols = max(1, int(non_white.shape[0] * dust_frac))
    min_rows = max(1, int(non_white.shape[1] * dust_frac))
    xs = np.where(cols > min_cols)[0]
    ys = np.where(rows > min_rows)[0]
    if xs.size == 0 or ys.size == 0:
        return img
    return img.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))


def trim_near_white(
    img: Image.Image,
    thresh: int = 248,
    white_frac: float = 0.92,
) -> Image.Image:
    """Drop rows/cols that are mostly near-white (anti-aliased flecks)."""
    rgb = np.asarray(img.convert("RGB"))
    white = (rgb >= thresh).all(axis=2)
    rows = white.mean(axis=1)
    cols = white.mean(axis=0)
    ys = np.where(rows < white_frac)[0]
    xs = np.where(cols < white_frac)[0]
    if ys.size == 0 or xs.size == 0:
        return img
    return img.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))


def square_center(img: Image.Image) -> Image.Image:
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side))


def prepare_detail_square(
    src: Path,
    thresh: int = 248,
    white_frac: float = 0.92,
) -> Image.Image:
    im = Image.open(src).convert("RGB")
    im = trim_white_border(im, thresh=min(250, thresh + 2))
    im = trim_near_white(im, thresh=thresh, white_frac=white_frac)
    return square_center(im)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path, help="User detail screenshot")
    ap.add_argument("-o", "--output", type=Path, required=True, help="Output square PNG")
    ap.add_argument("--thresh", type=int, default=248)
    ap.add_argument("--white-frac", type=float, default=0.92)
    ap.add_argument("--also-jpeg", action="store_true", help="Also write .jpeg sibling")
    args = ap.parse_args()

    out = prepare_detail_square(args.input, thresh=args.thresh, white_frac=args.white_frac)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.save(args.output)
    print(f"saved {args.output} {out.size[0]}x{out.size[1]}")
    if args.also_jpeg:
        jpeg = args.output.with_suffix(".jpeg")
        out.save(jpeg, quality=95)
        print(f"saved {jpeg}")


if __name__ == "__main__":
    main()
