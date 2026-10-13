# -*- coding: utf-8 -*-
"""Recompose ALL bio GIFs: full canvas, NO dark title banner."""
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
DB_ANIM = Path(r"D:/数据库/KEGG数据库/KEGG动画图")
MAN = ROOT / "交付文件" / "图片/KEGG官方通路图/00_全部通路图清单.csv"
CODE = ROOT / "代码文件"
sys.path.insert(0, str(CODE))

from bio_base_src_map import SRC_BY_RANK  # noqa: E402
from bio_compose_utils import DUR, animate_frames, prepare_base  # noqa: E402
from kegg_zh_names import ZH  # noqa: E402

DEFAULT_PATH = [(420, 350), (680, 410), (920, 480), (1140, 540)]
DEFAULT_NOTES = ["膜受体入口", "胞质信号复合体", "核孔入核"]


def find_base(rank: int, pid: str) -> Path | None:
    names = []
    if rank in SRC_BY_RANK:
        names.append(SRC_BY_RANK[rank])
    names += [
        f"bio_base_{rank:03d}_{pid}.png",
        f"bio_base_{rank}_{pid}.png",
    ]
    for name in names:
        for d in (BASES, ASSETS):
            p = d / name
            if p.exists():
                return p
    for d in (BASES, ASSETS):
        for pat in (f"bio_base_{rank:03d}_*.png", f"*{pid}*.png"):
            cands = sorted(d.glob(pat))
            if cands:
                return cands[0]
    return None


def main():
    start = 0
    args = sys.argv[1:]
    if args and args[0].isdigit():
        start = int(args[0])
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    df = pd.read_csv(MAN, encoding="utf-8-sig")
    rank_map = {int(r["rank"]): r for _, r in df.iterrows()}
    DB_ANIM.mkdir(parents=True, exist_ok=True)

    gifs = sorted(ANIM.glob("*.gif"))
    n_ok = n_miss = 0
    for gif in gifs:
        m = re.match(r"^(\d{3})_(hsa\d+)_(.+)_动画\.gif$", gif.name)
        if not m:
            print("SKIP name", gif.name, flush=True)
            continue
        rank = int(m.group(1))
        if rank < start:
            continue
        pid = m.group(2)
        row = rank_map.get(rank)
        en = str(row["description"]) if row is not None else m.group(3)
        zh = ZH.get(pid, m.group(3).split("_")[0] if "_" in m.group(3) else m.group(3)[:20])
        base_path = find_base(rank, pid)
        if base_path is None:
            print("MISS base", rank, pid, gif.name, flush=True)
            n_miss += 1
            continue
        title = f"{pid} · {zh}"
        base = prepare_base(base_path)
        frames = animate_frames(base, title, en, DEFAULT_NOTES, DEFAULT_PATH)
        frames[0].save(
            gif, save_all=True, append_images=frames[1:], duration=DUR, loop=0, optimize=True
        )
        shutil.copy2(gif, DB_ANIM / gif.name)
        print("OK", f"{rank:03d}", base_path.name, flush=True)
        n_ok += 1

    print(f"DONE ok={n_ok} miss={n_miss} total_gifs={len(gifs)}", flush=True)


if __name__ == "__main__":
    main()
