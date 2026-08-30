# -*- coding: utf-8 -*-
"""Collect 努力学习 Top10 docking viz into one folder.

Safety:
- Default: merge/copy only; never wipe destination
- --force-wipe: explicit wipe (discouraged after manual .pse edits)
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
from pathlib import Path

ROOT = Path.home() / "Desktop" / "努力学习_分子对接"
JOBS = ROOT / "序号文件夹"
OUT = ROOT / "可视化组合_Top10"
SUMMARY = ROOT / "summary_vina.csv"


def safe(s: object) -> str:
    t = re.sub(r'[<>:"/\\|?*]+', "_", str(s).strip())
    t = re.sub(r"\s+", "_", t)
    return (t[:80] or "NA")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--force-wipe",
        action="store_true",
        help="DELETE entire OUT then rebuild (dangerous if user adjusted labels in Top10)",
    )
    args = ap.parse_args()

    rows = []
    with SUMMARY.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            try:
                aff = float(r.get("best_affinity_kcal") or 999)
            except Exception:
                aff = 999.0
            rows.append((aff, r))
    rows.sort(key=lambda x: x[0])
    top = rows[:10]

    if args.force_wipe and OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    index_lines = [
        "努力学习 · 分子对接可视化组合（Top10，按 best_affinity 升序）",
        f"源任务目录: {JOBS}",
        "",
        "序号\t亲和力\t蛋白\tPDB\t成分\t子目录",
    ]

    for aff, r in top:
        seq = str(r.get("对接序号") or "").strip()
        src = JOBS / seq
        name = f"{seq}_{safe(r.get('蛋白'))}_{safe(r.get('PDB'))}_{safe(r.get('成分'))}"
        dst = OUT / name
        dst.mkdir(parents=True, exist_ok=True)
        dst_img = dst / "图片"
        dst_img.mkdir(parents=True, exist_ok=True)
        n = 0
        img = src / "图片"
        if img.exists():
            for p in img.glob("*.png"):
                shutil.copy2(p, dst_img / p.name)
                n += 1
        if src.exists():
            for p in src.glob("*.pse"):
                shutil.copy2(p, dst / p.name)
                n += 1
        # 清理旧版扁平 PNG（若曾放在子目录根）
        for p in list(dst.glob("*.png")):
            target = dst_img / p.name
            if not target.exists():
                shutil.move(str(p), str(target))
            else:
                p.unlink()
        (dst / "组合信息.txt").write_text(
            "\n".join(
                [
                    f"对接序号={seq}",
                    f"蛋白={r.get('蛋白')}",
                    f"PDB={r.get('PDB')}",
                    f"成分={r.get('成分')}",
                    f"CID={r.get('CID')}",
                    f"best_affinity_kcal={r.get('best_affinity_kcal')}",
                    f"status={r.get('status')}",
                    f"source={src}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        index_lines.append(
            f"{seq}\t{r.get('best_affinity_kcal')}\t{r.get('蛋白')}\t{r.get('PDB')}\t{r.get('成分')}\t{name}"
        )
        print(f"copied {name} files={n}")

    (OUT / "README.txt").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"OUT={OUT}")
    print(f"n_dirs={len([p for p in OUT.iterdir() if p.is_dir()])}")


if __name__ == "__main__":
    main()
