#!/usr/bin/env python3
"""Combine PP-docking big + detail into result_N.png via MolecularDocking collage engine.

Default engine:
  E:\\PythonProject\\分子对接\\2.分子对接结果图组合.py
  E:\\PythonProject\\分子对接\\背景图.png

Usage:
  python combine_pp_result.py --img-dir ".../1/图片" --index 2
  python combine_pp_result.py --big big-1.png --detail detail-2.png -o result_2.png
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

DEFAULT_ENGINE = Path(r"E:\PythonProject\分子对接\2.分子对接结果图组合.py")
DEFAULT_BG = Path(r"E:\PythonProject\分子对接\背景图.png")


def load_engine(engine_path: Path):
    name = "dock_combine_pp"
    spec = importlib.util.spec_from_file_location(name, engine_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load collage engine: {engine_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--img-dir", type=Path, help="Folder with big-*.png / detail-*.png")
    ap.add_argument("--index", type=int, help="Use big-1 + detail-{index} → result_{index}")
    ap.add_argument("--big", type=Path, help="Explicit big PNG")
    ap.add_argument("--detail", type=Path, help="Explicit detail PNG (prefer square)")
    ap.add_argument("-o", "--output", type=Path, help="Output result PNG")
    ap.add_argument("--engine", type=Path, default=DEFAULT_ENGINE)
    ap.add_argument("--background", type=Path, default=DEFAULT_BG)
    args = ap.parse_args()

    if args.img_dir and args.index is not None:
        img_dir = args.img_dir
        big = args.big or (img_dir / "big-1.png")
        if not big.exists():
            # fallback big-N.png matching index folder convention
            cand = img_dir / f"big-{args.index}.png"
            big = cand if cand.exists() else big
        detail = args.detail or (img_dir / f"detail-{args.index}.png")
        out = args.output or (img_dir / f"result_{args.index}.png")
    else:
        if not (args.big and args.detail and args.output):
            ap.error("Provide --img-dir --index, or --big --detail -o")
        big, detail, out = args.big, args.detail, args.output

    if not args.engine.is_file():
        raise SystemExit(f"Missing collage engine: {args.engine}")
    if not args.background.is_file():
        raise SystemExit(f"Missing background: {args.background}")
    if not big.is_file() or not detail.is_file():
        raise SystemExit(f"Missing inputs: big={big} detail={detail}")

    mod = load_engine(args.engine)
    path = mod.combine_result(
        background_path=str(args.background),
        big_path=str(big),
        detail_path=str(detail),
        output_path=str(out),
    )
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
