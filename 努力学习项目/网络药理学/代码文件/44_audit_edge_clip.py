# -*- coding: utf-8 -*-
"""Audit bio BASE PNGs for top/bottom edge clipping (incomplete AI illustration)."""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学")
ANIM = ROOT / "交付文件" / "图片" / "动画_生物结构"
BASES = ANIM / "_bases"
ASSETS = Path(r"C:/Users/10540/.cursor/projects/e-RProject/assets")
MAN = ROOT / "交付文件" / "图片/KEGG官方通路图/00_全部通路图清单.csv"
OUT = ANIM / "_audit_edge_clip.csv"
CODE = ROOT / "代码文件"
sys.path.insert(0, str(CODE))
from bio_base_src_map import SRC_BY_RANK  # noqa: E402


def edge_metrics(arr: np.ndarray, band_pct: float = 0.06) -> dict:
    h, w, _ = arr.shape
    band = max(4, int(h * band_pct))
    top = arr[:band]
    bot = arr[-band:]
    mid = arr[h // 3 : h // 3 + band]

    def score(edge, inward):
        # high = likely hard-cut biology at canvas edge
        diff = float(np.abs(edge.astype(np.float32) - inward.astype(np.float32)).mean())
        med = np.median(edge.reshape(-1, 3), axis=0)
        d = np.linalg.norm(edge - med, axis=2)
        nonbg = float((d > 22).mean())
        sat = float(edge.std())
        return diff, nonbg, sat

    td, tn, ts = score(top, arr[band : band * 2])
    bd, bn, bs = score(bot, arr[-band * 2 : -band])
    md, mn, ms = score(mid, arr[h // 3 + band : h // 3 + band * 2])
    # flag if top has much more edge activity than mid (content cut at top)
    top_clip = (tn > 0.28 and td > md + 4) or (tn > 0.42 and ts > 35)
    bot_clip = (bn > 0.28 and bd > md + 4) or (bn > 0.42 and bs > 35)
    return {
        "top_nonbg": round(tn, 3),
        "top_diff": round(td, 2),
        "mid_nonbg": round(mn, 3),
        "bot_nonbg": round(bn, 3),
        "flag_top": int(top_clip),
        "flag_bot": int(bot_clip),
    }


def find_base(rank: int, pid: str) -> Path | None:
    names = []
    if rank in SRC_BY_RANK:
        names.append(SRC_BY_RANK[rank])
    names += [f"bio_base_{rank:03d}_{pid}.png"]
    for name in names:
        for d in (BASES, ASSETS):
            p = d / name
            if p.exists():
                return p
    for d in (BASES, ASSETS):
        c = sorted(d.glob(f"bio_base_{rank:03d}_*.png")) or sorted(d.glob(f"*{pid}*.png"))
        if c:
            return c[0]
    return None


def main():
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    import pandas as pd

    df = pd.read_csv(MAN, encoding="utf-8-sig")
    rows = []
    for _, r in df.iterrows():
        rank = int(r["rank"])
        pid = str(r["pathway_id"]).strip()
        base = find_base(rank, pid)
        if base is None:
            rows.append({"rank": rank, "pid": pid, "base": "", "flag_top": -1, "flag_bot": -1})
            print(f"MISS {rank:03d} {pid}", flush=True)
            continue
        im = Image.open(base).convert("RGB")
        m = edge_metrics(np.asarray(im, dtype=np.float32))
        row = {"rank": rank, "pid": pid, "base": base.name, **m}
        rows.append(row)
        mark = "FLAG_TOP" if m["flag_top"] else ("FLAG_BOT" if m["flag_bot"] else "ok")
        print(f"{mark} {rank:03d} {base.name} top={m['top_nonbg']}", flush=True)

    if rows:
        with OUT.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    ntop = sum(1 for r in rows if r.get("flag_top") == 1)
    nbot = sum(1 for r in rows if r.get("flag_bot") == 1)
    print(f"DONE bases={len(rows)} flag_top={ntop} flag_bot={nbot} -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
