# -*- coding: utf-8 -*-
"""Collect 努力学习 Top10 docking viz into one folder.

Safety:
- Default: merge/copy only; never wipe destination
- --force-wipe: explicit wipe (discouraged after manual .pse edits)
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dock_summary_schema import load_summary_rows

# ---- 项目专用路径常量（本机桌面「努力学习_分子对接」布局，移植时需改） ----
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

    rows = [(r["affinity_kcal_mol"], r) for r in load_summary_rows(SUMMARY)]
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
        seq = str(r.get("task") or "").strip()
        src = JOBS / seq
        name = f"{seq}_{safe(r.get('protein'))}_{safe(r.get('pdb'))}_{safe(r.get('ligand'))}"
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
                    f"蛋白={r.get('protein')}",
                    f"PDB={r.get('pdb')}",
                    f"成分={r.get('ligand')}",
                    f"CID={r.get('cid')}",
                    f"best_affinity_kcal={aff}",
                    f"status={r.get('status')}",
                    f"source={src}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        index_lines.append(
            f"{seq}\t{aff}\t{r.get('protein')}\t{r.get('pdb')}\t{r.get('ligand')}\t{name}"
        )
        print(f"copied {name} files={n}")

    (OUT / "README.txt").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"OUT={OUT}")
    print(f"n_dirs={len([p for p in OUT.iterdir() if p.is_dir()])}")


if __name__ == "__main__":
    main()
