# -*- coding: utf-8 -*-
"""Recombine result collage only (no detail re-export, no big crop on disk)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image

JOBS = (
    Path(r"E:/RProject")
    / "\u52aa\u529b\u5b66\u4e60\u9879\u76ee"
    / "06_\u5206\u5b50\u5bf9\u63a5"
    / "\u5e8f\u53f7\u6587\u4ef6\u5939"
)
COMBINE_PY = Path(r"E:\PythonProject\分子对接\2.分子对接结果图组合.py")


def main() -> int:
    job_dirs = sorted(
        [p for p in JOBS.iterdir() if p.is_dir() and p.name.isdigit()],
        key=lambda p: int(p.name),
    )
    print(f"jobs={len(job_dirs)} root={JOBS}")
    ok = 0
    for job in job_dirs:
        img = job / "\u56fe\u7247"
        big = img / f"big-{job.name}.png"
        detail = img / f"detail-{job.name}.png"
        if not big.exists() or not detail.exists():
            print(f"[skip] {job.name}: missing big or detail png")
            continue
        for bad in img.glob("result_01.png"):
            bad.unlink()
        print(f"[combine] {job.name} big={Image.open(big).size} detail={Image.open(detail).size}")
        proc = subprocess.run(
            [sys.executable, str(COMBINE_PY), f"--dir={img}", job.name],
            cwd=str(COMBINE_PY.parent),
        )
        if proc.returncode != 0:
            print(f"[FAIL combine] {job.name}")
            continue
        res = list(img.glob(f"result*{job.name}*.png")) or list(img.glob("result_*.png"))
        print(f"[ok] {job.name} -> {[p.name for p in res]}")
        ok += 1
    print(f"DONE combine {ok}/{len(job_dirs)}")
    return 0 if ok == len(job_dirs) else 2


if __name__ == "__main__":
    raise SystemExit(main())
