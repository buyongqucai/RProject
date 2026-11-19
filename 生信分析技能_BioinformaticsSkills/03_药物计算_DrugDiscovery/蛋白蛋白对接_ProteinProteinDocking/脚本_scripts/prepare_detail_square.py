#!/usr/bin/env python3
"""PP detail 切方（已定稿）：用户截图 → 对接按颜色裁 → 正方形 → 拉大。

只改输入/输出路径。颜色与包围盒调用分子对接拼图，禁止自造掩膜/cover/垫白。

SSOT 颜色：``E:\\PythonProject\\分子对接\\2.分子对接结果图组合.py``
  ``build_key_content_mask`` / ``_bbox_from_mask``

流程：
  1. 按残基/氢键/标签色定包围盒（裁掉无这些内容的多余幅面）
  2. 在原图内取能包住该盒的正方形（不垫白边）
  3. 拉到 ``--detail-size``²（默认 6000）

用户原图可放在任务 ``图片/``（如 ``detail-N_用户原图.png``）。
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

DOCK_COLLAGE = Path(r"E:\PythonProject\分子对接\2.分子对接结果图组合.py")


def _load_dock_collage():
    spec = importlib.util.spec_from_file_location("dock_collage", DOCK_COLLAGE)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(f"missing docking collage: {DOCK_COLLAGE}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def square_from_user_shot(
    src: Path,
    dst: Path,
    *,
    detail_size: int = 6000,
    dpi: int = 600,
) -> Path:
    """用户截图 → 颜色定界 → 正方形 → 拉大。返回 dst。"""
    from PIL import Image

    src = Path(src)
    dst = Path(dst)
    dock = _load_dock_collage()
    img = Image.open(src).convert("RGB")
    w, h = img.size
    profile = dock.DEFAULT_COLLAGE_PROFILE.with_auto_from_image(img)

    mask = dock.build_key_content_mask(img, dilate=True, profile=profile)
    bbox = dock._bbox_from_mask(mask)
    if bbox is None:
        raise RuntimeError("build_key_content_mask empty")
    cx, cy, bw, bh = bbox
    kl = max(0, int(round(cx - bw / 2.0)))
    kt = max(0, int(round(cy - bh / 2.0)))
    kr = min(w, int(round(cx + bw / 2.0)))
    kb = min(h, int(round(cy + bh / 2.0)))
    kw, kh = kr - kl, kb - kt
    if kw <= 0 or kh <= 0:
        raise RuntimeError(f"bad key box ({kl},{kt},{kr},{kb})")

    side = max(kw, kh)
    if side > w or side > h:
        side = min(w, h)
    left = int(max(0, min(max(kr - side, min(kl, w - side)), w - side)))
    top = int(max(0, min(max(kb - side, min(kt, h - side)), h - side)))
    square = img.crop((left, top, left + side, top + side))
    out = square.resize((detail_size, detail_size), Image.LANCZOS)

    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst, dpi=(dpi, dpi))
    print(
        f"ok color→square→enlarge {src.name} {img.size} "
        f"key=({kl},{kt},{kr},{kb}) side={side} crop=({left},{top}) "
        f"-> {dst.name} {out.size} "
        f"res:{profile.residue_color}/hb:{profile.hbond_color}",
        flush=True,
    )
    return dst


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path, help="用户截图，如 图片/detail-1_用户原图.png")
    ap.add_argument("-o", "--output", type=Path, required=True, help="图片/detail-N.png")
    ap.add_argument("--detail-size", type=int, default=6000)
    ap.add_argument("--dpi", type=int, default=600)
    args = ap.parse_args()
    src = args.input.resolve()
    if not src.is_file():
        print(f"ERROR: not found: {src}", file=sys.stderr)
        return 2
    if not DOCK_COLLAGE.is_file():
        print(f"ERROR: missing {DOCK_COLLAGE}", file=sys.stderr)
        return 2
    try:
        square_from_user_shot(
            src, args.output.resolve(), detail_size=args.detail_size, dpi=args.dpi
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
