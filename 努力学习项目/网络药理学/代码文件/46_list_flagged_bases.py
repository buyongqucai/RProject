# -*- coding: utf-8
"""List / regenerate bases flagged for top-edge clipping (see 44_audit_edge_clip.py)."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

AUDIT = Path(r"E:/RProject/努力学习项目/网络药理学/交付文件/图片/动画_生物结构/_audit_edge_clip.csv")


def main():
    if not AUDIT.exists():
        print("Run 44_audit_edge_clip.py first", file=sys.stderr)
        sys.exit(1)
    tops, bots, miss = [], [], []
    with AUDIT.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rank = int(row["rank"])
            if row.get("base") == "":
                miss.append(rank)
            elif int(row.get("flag_top", 0)) == 1:
                tops.append((rank, row["pid"], row["base"]))
            elif int(row.get("flag_bot", 0)) == 1:
                bots.append((rank, row["pid"], row["base"]))
    print("FLAG_TOP (regenerate base — title/inset strip or cut top):", len(tops))
    for r, pid, b in tops:
        print(f"  {r:03d} {pid} {b}")
    print("\nFLAG_BOT (optional regen):", len(bots))
    print("MISS base:", len(miss))
    print("\nRegenerate with GenerateImage or: python 45_local_sd_bases.py --rank R --pid PID --prompt-file ...")


if __name__ == "__main__":
    main()
