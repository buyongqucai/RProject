# -*- coding: utf-8 -*-
"""重建序号任务前：按 ligand+gene 备份/回填手调 detail-*.pse。

用法：
  备份：python 保护手调detail_preserveDetailPse.py backup
  回填：python 保护手调detail_preserveDetailPse.py restore

规则：永远不要对「已有手调 detail」的任务跑 pymol --all 覆盖；
仅缺 detail 时再生成；手调文件按 ascii_prefix 存到 _手调detail备份/。
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / "序号文件夹"
BAK = ROOT / "数据文件" / "_手调detail备份"


def key_from_task(job: Path) -> str | None:
    info = job / "task_info.txt"
    if not info.exists():
        return None
    d = {}
    for line in info.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    pref = d.get("ascii_prefix")
    if pref:
        return pref
    gene, lig = d.get("gene"), d.get("ligand")
    if gene and lig:
        return f"{gene}__{lig}"
    return job.name


def backup() -> int:
    BAK.mkdir(parents=True, exist_ok=True)
    n = 0
    if not JOBS.exists():
        print("no jobs")
        return 0
    for job in sorted(JOBS.iterdir()):
        if not job.is_dir() or not job.name.isdigit():
            continue
        pse = job / f"detail-{job.name}.pse"
        if not pse.exists():
            continue
        k = key_from_task(job) or job.name
        dest = BAK / f"{k}__detail.pse"
        shutil.copy2(pse, dest)
        # also copy task_info for mapping
        shutil.copy2(job / "task_info.txt", BAK / f"{k}__task_info.txt")
        print("backup", job.name, "->", dest.name)
        n += 1
    print("backed", n, "into", BAK)
    return n


def restore() -> int:
    if not BAK.exists() or not JOBS.exists():
        print("nothing to restore")
        return 0
    by_key = {p.name.split("__detail.pse")[0]: p for p in BAK.glob("*__detail.pse")}
    n = 0
    for job in sorted(JOBS.iterdir()):
        if not job.is_dir() or not job.name.isdigit():
            continue
        k = key_from_task(job)
        if not k or k not in by_key:
            continue
        dest = job / f"detail-{job.name}.pse"
        shutil.copy2(by_key[k], dest)
        print("restore", by_key[k].name, "->", dest)
        n += 1
    print("restored", n)
    return n


if __name__ == "__main__":
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
    if cmd == "backup":
        backup()
    elif cmd == "restore":
        restore()
    else:
        print(__doc__)
        sys.exit(2)
