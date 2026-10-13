# -*- coding: utf-8
"""Compose remaining KEGG pathway bio-structure GIFs (rank >= START).

Expects AI bases at:
  assets/bio_base_{rank:03d}_{pathway_id}.png
Naming:
  {rank:03d}_{pid}_{zh}_{en}_动画.gif
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学")
ANIM = ROOT / "交付文件" / "图片" / "动画_生物结构"
BASES = ANIM / "_bases"
ASSETS = Path(r"C:/Users/10540/.cursor/projects/e-RProject/assets")
ASSETS_BIO = Path(r"C:/Users/10540/.cursor/projects/e-RProject-BioinformaticsSkills/assets")
ASSET_DIRS = [ASSETS_BIO, ASSETS, BASES]
DB_ANIM = Path(r"D:/数据库/KEGG数据库/KEGG动画图")
MAN = ROOT / "交付文件" / "图片" / "KEGG官方通路图" / "00_全部通路图清单.csv"
CODE = ROOT / "代码文件"
sys.path.insert(0, str(CODE))
from bio_compose_utils import DUR, animate_frames, prepare_base  # noqa: E402
from kegg_zh_names import ZH  # noqa: E402

DEFAULT_PATH = [(420, 350), (680, 410), (920, 480), (1140, 540)]


def safe_en(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", str(s), flags=re.UNICODE)
    return s.strip("_")[:80] or "pathway"


def main():
    start = 21
    end = 10**9
    only = set()
    args = sys.argv[1:]
    if args and args[0].isdigit():
        start = int(args[0])
    if len(args) > 1 and args[1].isdigit():
        end = int(args[1])
    if "--only" in args:
        i = args.index("--only")
        only = {int(x) for x in args[i + 1].split(",")}
    force = "--force" in args

    df = pd.read_csv(MAN, encoding="utf-8-sig")
    ANIM.mkdir(parents=True, exist_ok=True)
    BASES.mkdir(parents=True, exist_ok=True)
    DB_ANIM.mkdir(parents=True, exist_ok=True)

    n_ok = n_skip = n_miss = 0
    for _, r in df.iterrows():
        rank = int(r["rank"])
        if rank < start or rank > end:
            continue
        if only and rank not in only:
            continue
        pid = str(r["pathway_id"]).strip()
        en = str(r["description"]).strip()
        zh = ZH.get(pid, en[:20])
        en_slug = safe_en(en)
        out_name = f"{rank:03d}_{pid}_{zh}_{en_slug}_动画.gif"
        out = ANIM / out_name
        if not force and out.exists() and out.stat().st_size > 500_000:
            print("SKIP", out_name)
            n_skip += 1
            shutil.copy2(out, DB_ANIM / out_name)
            continue

        src = None
        wanted = f"bio_base_{rank:03d}_{pid}.png"
        for d in ASSET_DIRS:
            p = d / wanted
            if p.exists():
                src = p
                break
        if src is None:
            cands = []
            for d in ASSET_DIRS:
                if d.exists():
                    cands.extend(d.glob(f"bio_base_{rank:03d}_*.png"))
                    cands.extend(d.glob(f"*{pid}*.png"))
            src = cands[0] if cands else None
        if src is None or not Path(src).exists():
            print("MISS base", rank, pid)
            n_miss += 1
            continue

        shutil.copy2(src, BASES / Path(src).name)
        base = prepare_base(Path(src))
        title = f"{pid} · {zh}"
        sub = en
        notes = ["膜受体入口", "胞质信号复合体", "核孔入核"]
        frames = animate_frames(base, title, sub, notes, DEFAULT_PATH)
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=DUR, loop=0, optimize=True)
        shutil.copy2(out, DB_ANIM / out_name)
        print("OK", out_name)
        n_ok += 1

    print(f"DONE ok={n_ok} skip={n_skip} miss={n_miss}")


if __name__ == "__main__":
    main()
