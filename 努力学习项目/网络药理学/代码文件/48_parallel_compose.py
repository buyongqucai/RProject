# -*- coding: utf-8 -*-
"""Parallel CPU compose for bio GIFs (ProcessPool). Usage: python 48_parallel_compose.py 117 132"""
from __future__ import annotations

import re
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学")
CODE = ROOT / "代码文件"
ANIM = ROOT / "交付文件" / "图片" / "动画_生物结构"
BASES = ANIM / "_bases"
ASSETS = Path(r"C:/Users/10540/.cursor/projects/e-RProject/assets")
ASSETS_BIO = Path(r"C:/Users/10540/.cursor/projects/e-RProject-BioinformaticsSkills/assets")
SEARCH_DIRS = (BASES, ASSETS_BIO, ASSETS)
DB_ANIM = Path(r"D:/数据库/KEGG数据库/KEGG动画图")
MAN = ROOT / "交付文件/图片/KEGG官方通路图/00_全部通路图清单.csv"

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
    names += [f"bio_base_{rank:03d}_{pid}.png"]
    for name in names:
        for d in SEARCH_DIRS:
            p = d / name
            if p.exists():
                return p
    for d in SEARCH_DIRS:
        cands = sorted(d.glob(f"bio_base_{rank:03d}_*.png")) or sorted(d.glob(f"*{pid}*.png"))
        if cands:
            return cands[0]
    return None


def safe_en(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", str(s), flags=re.UNICODE)
    return s.strip("_")[:80] or "pathway"


def safe_zh(s: str) -> str:
    s = str(s).replace("/", "与").replace("\\", "").replace(":", "")
    s = re.sub(r"[^\w\u4e00-\u9fff\-]+", "", s)
    return s.strip("_")[:40] or "通路"


def compose_one(job: dict) -> str:
    rank, pid, en, zh = job["rank"], job["pid"], job["en"], job["zh"]
    base_path = find_base(rank, pid)
    if base_path is None:
        return f"MISS {rank:03d} {pid}"
    out_name = f"{rank:03d}_{pid}_{safe_zh(zh)}_{safe_en(en)}_动画.gif"
    out = ANIM / out_name
    # remove stale differently-named gif for same rank
    for old in ANIM.glob(f"{rank:03d}_{pid}_*_动画.gif"):
        if old.name != out_name:
            try:
                old.unlink()
            except OSError:
                pass
    base = prepare_base(base_path)
    frames = animate_frames(base, f"{pid} · {zh}", en, DEFAULT_NOTES, DEFAULT_PATH)
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=DUR, loop=0, optimize=True)
    DB_ANIM.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out, DB_ANIM / out_name)
    return f"OK {rank:03d} {out_name[:50]}"


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 117
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 183
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else max(4, (os_cpu := __import__("os").cpu_count() or 4) - 1)
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    df = pd.read_csv(MAN, encoding="utf-8-sig")
    jobs = []
    for _, r in df.iterrows():
        rank = int(r["rank"])
        if rank < start or rank > end:
            continue
        pid = str(r["pathway_id"]).strip()
        en = str(r["description"]).strip()
        zh = ZH.get(pid, en[:20])
        jobs.append({"rank": rank, "pid": pid, "en": en, "zh": zh})
    print(f"compose {len(jobs)} jobs workers={workers}", flush=True)
    ok = miss = 0
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(compose_one, j): j for j in jobs}
        for fut in as_completed(futs):
            msg = fut.result()
            print(msg, flush=True)
            if msg.startswith("OK"):
                ok += 1
            else:
                miss += 1
    print(f"DONE ok={ok} miss={miss}", flush=True)


if __name__ == "__main__":
    main()
