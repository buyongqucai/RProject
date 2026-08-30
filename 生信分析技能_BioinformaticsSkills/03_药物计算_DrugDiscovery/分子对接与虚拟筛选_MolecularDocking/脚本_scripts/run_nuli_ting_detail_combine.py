# -*- coding: utf-8 -*-
"""努力学习 Top10 + 婷婷(痤疮)：截图重导 detail、拼接 result，PNG 归入 图片/。

每个 detail 用独立 PyMOL 进程导出，避免批量 draw 崩溃。
项目专用脚本：路径常量绑定本机桌面项目布局，非通用交付件。
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dock_export_common import ensure_img_subdir

# ---- 项目专用路径常量（本机桌面布局，移植时需改） ----
DESKTOP = Path.home() / "Desktop"
COMBINE_PY = Path(r"E:\PythonProject\分子对接\2.分子对接结果图组合.py")
EXPORT_PY = Path(
    r"E:\RProject\生信分析技能_BioinformaticsSkills\03_药物计算_DrugDiscovery"
    r"\分子对接与虚拟筛选_MolecularDocking\脚本_scripts\export_detail_png_from_pse.py"
)
PYMOL = Path(r"E:\pymol\python.exe")


def find_dir(parent: Path, *keys: str) -> Path:
    for p in parent.iterdir():
        if p.is_dir() and all(k in p.name for k in keys):
            return p
    raise FileNotFoundError(f"{keys} under {parent}")


def crop_bw(path: Path, tolerance: int = 0) -> None:
    img = Image.open(path).convert("RGB")
    arr = np.array(img)
    h, w, _ = arr.shape
    is_black = np.all(arr <= 0 + tolerance, axis=2)
    is_white = np.all(arr >= 255 - tolerance, axis=2)
    non_bw = ~(is_black | is_white)
    if not np.any(non_bw):
        return
    left = int(np.argmax(np.any(non_bw, axis=0)))
    right = w - 1 - int(np.argmax(np.any(non_bw[:, ::-1], axis=0)))
    top = int(np.argmax(np.any(non_bw, axis=1)))
    bottom = h - 1 - int(np.argmax(np.any(non_bw[::-1, :], axis=1)))
    cropped = img.crop((left, top, right + 1, bottom + 1))
    dpi = img.info.get("dpi", (600, 600))
    cropped.save(path, dpi=dpi)


def sync_pse_top10_to_jobs(viz: Path, jobs: Path) -> None:
    for d in sorted(viz.iterdir()):
        if not d.is_dir():
            continue
        seq = d.name.split("_", 1)[0]
        if not seq.isdigit():
            continue
        job = jobs / seq
        job.mkdir(parents=True, exist_ok=True)
        for pse in d.glob("*.pse"):
            dst = job / pse.name
            if (
                (not dst.exists())
                or pse.stat().st_mtime > dst.stat().st_mtime + 0.5
                or pse.stat().st_size != dst.stat().st_size
            ):
                shutil.copy2(pse, dst)
                print(f"[sync-pse] {pse.name} -> 序号文件夹/{seq}/")


def sync_png_to_jobs(viz: Path, jobs: Path) -> None:
    for d in sorted(viz.iterdir()):
        if not d.is_dir():
            continue
        seq = d.name.split("_", 1)[0]
        if not seq.isdigit():
            continue
        src_img = d / "图片"
        if not src_img.exists():
            continue
        dst_img = jobs / seq / "图片"
        dst_img.mkdir(parents=True, exist_ok=True)
        for png in src_img.glob("*.png"):
            # result_01.png 是早期拼接流程的残留废图（首张占位），不属于交付集，跳过
            if png.name.lower().startswith("result_01"):
                continue
            shutil.copy2(png, dst_img / png.name)


def export_one_folder(folder: Path) -> None:
    """PyMOLWin -r 钩子：最大化后 Qt API 收起代码区 → 截图（export_detail_png_from_pse）。"""
    ensure_img_subdir(folder)
    proc = subprocess.run(
        [
            sys.executable,
            "-u",
            str(EXPORT_PY),
            "--root",
            str(folder),
            "--skip-normalize",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    print(f"[detail] {folder.name}: {out.splitlines()[-1] if out else proc.returncode}")
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        raise RuntimeError(f"export failed: {folder}")


def combine_dirs(img_dirs: list[Path]) -> None:
    for img in img_dirs:
        # result_01.png 为早期拼接残留废图，重拼前必须删除，否则会被 combiner 当作有效结果
        for bad in img.glob("result_01.png"):
            bad.unlink()
            print(f"[clean] removed {bad}")
        for big in img.glob("big-*.png"):
            before = Image.open(big).size
            crop_bw(big)
            after = Image.open(big).size
            print(f"[crop] {img.parent.name}/{big.name}: {before} -> {after}")
        idxs = []
        for name in img.iterdir():
            if name.name.lower().startswith("big-") and name.suffix.lower() == ".png":
                try:
                    idxs.append(int(name.stem.split("-", 1)[1]))
                except Exception:
                    pass
        if not idxs:
            print(f"[skip combine] no big in {img}")
            continue
        idx = idxs[0]
        cmd = [sys.executable, str(COMBINE_PY), f"--dir={img}", str(idx)]
        print(f"[combine] {img.parent.name} idx={idx}")
        proc = subprocess.run(cmd, cwd=str(COMBINE_PY.parent))
        if proc.returncode != 0:
            raise RuntimeError(f"combine failed: {img}")


def main() -> int:
    nuli = find_dir(DESKTOP, "努力学习")
    acne = find_dir(DESKTOP, "痤疮")
    viz = find_dir(nuli, "Top10")
    jobs = find_dir(nuli, "序号")

    top10_dirs = sorted([p for p in viz.iterdir() if p.is_dir()])
    acne_dirs = sorted(
        [p for p in acne.iterdir() if p.is_dir() and p.name.isdigit()],
        key=lambda p: int(p.name),
    )
    print(f"Top10={len(top10_dirs)} acne={len(acne_dirs)}")

    sync_pse_top10_to_jobs(viz, jobs)

    print("=== export 努力学习 Top10 detail (screenshot, 1 process each) ===")
    for d in top10_dirs:
        export_one_folder(d)

    print("=== export 婷婷/痤疮 detail (screenshot, 1 process each) ===")
    for d in acne_dirs:
        export_one_folder(d)

    print("=== combine 努力学习 Top10 ===")
    combine_dirs([d / "图片" for d in top10_dirs])
    sync_png_to_jobs(viz, jobs)

    print("=== combine 婷婷/痤疮 ===")
    acne_img = [
        d / "图片"
        for d in acne_dirs
        if list((d / "图片").glob("big-*.png")) and list((d / "图片").glob("detail-*.png"))
    ]
    combine_dirs(acne_img)

    print("ALL_DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
