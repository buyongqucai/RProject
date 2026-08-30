# -*- coding: utf-8 -*-
"""手调 detail.pse 后导出 PNG（标签所见即所得）。

每个任务只开一次 PyMOLWin，流程（唯一路径）：
  1. PyMOLWin.exe 打开 .pse 并 -r 加载 pymol_detail_export_hook.py
  2. 钩子内用 PyMOL Qt API 先 **收起底部代码区**（大黑框命令日志），使 3D 视口变高
  3. 最大化 → 截图 → 裁 3D 画布 → cover 正方形 PNG
禁止写回 / 改动 .pse；禁止 cmd.png 离屏重渲。
注意：「收起代码区」指截图前在 PyMOL 内折叠 UI，不是事后把黑框裁掉。
图像识别点击旧路径已废弃删除（议题 03），本文件不再依赖 cv2 / 模板 assets。
"""
from __future__ import annotations

import argparse
import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dock_export_common import collapse_console_qt, ensure_img_subdir

PYMOL_WIN = Path(r"E:\pymol\PyMOLWin.exe")
PYMOL_HOOK = Path(__file__).resolve().parent / "pymol_detail_export_hook.py"

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
GA_ROOT = 2


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


def root_hwnd(hwnd: int) -> int:
    """落到顶层窗口，避免对子控件截图。"""
    root = int(user32.GetAncestor(hwnd, GA_ROOT) or hwnd)
    return root or int(hwnd)


def _window_screen_box(hwnd: int) -> tuple[int, int, int, int]:
    """整窗外框（屏幕坐标）。"""
    hwnd = root_hwnd(hwnd)
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)


def _capture_hwnd_bitmap(hwnd: int, use_client: bool = False) -> Image.Image:
    """PrintWindow 截图，避免高分屏 ImageGrab 坐标错位。"""
    hwnd = root_hwnd(hwnd)
    if use_client:
        rect = wintypes.RECT()
        user32.GetClientRect(hwnd, ctypes.byref(rect))
        left_top = wintypes.POINT(0, 0)
        user32.ClientToScreen(hwnd, ctypes.byref(left_top))
        x, y = int(left_top.x), int(left_top.y)
        w = int(rect.right - rect.left)
        h = int(rect.bottom - rect.top)
    else:
        l, t, r, b = _window_screen_box(hwnd)
        x, y, w, h = l, t, r - l, b - t
    if w <= 0 or h <= 0:
        return Image.new("RGB", (1, 1), (255, 255, 255))

    hwnd_dc = user32.GetWindowDC(hwnd)
    mfc_dc = gdi32.CreateCompatibleDC(hwnd_dc)
    hbmp = gdi32.CreateCompatibleBitmap(hwnd_dc, w, h)
    gdi32.SelectObject(mfc_dc, hbmp)
    PW_RENDERFULLCONTENT = 2
    ok = user32.PrintWindow(hwnd, mfc_dc, PW_RENDERFULLCONTENT)
    if not ok:
        user32.PrintWindow(hwnd, mfc_dc, 0)

    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = w
    bmi.bmiHeader.biHeight = -h  # top-down
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0  # BI_RGB
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mfc_dc, hbmp, 0, h, buf, ctypes.byref(bmi), 0)
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(mfc_dc)
    user32.ReleaseDC(hwnd, hwnd_dc)

    arr = np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 4)
    rgb = arr[:, :, [2, 1, 0]].copy()
    return Image.fromarray(rgb, mode="RGB")


def normalize_job(job: Path) -> list[str]:
    return ensure_img_subdir(job)


def find_jobs(roots: list[Path]) -> list[Path]:
    jobs: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for p in sorted(root.iterdir(), key=lambda x: int(x.name) if x.name.isdigit() else 10**9):
            if p.is_dir() and p.name.isdigit():
                jobs.append(p)
    return jobs


def cover_square(img: Image.Image, side: int) -> Image.Image:
    """等比放大铺满正方形后居中裁切（避免信箱白边把最大化画面衬成一条）。"""
    rgb = img.convert("RGB")
    w, h = rgb.size
    if w <= 0 or h <= 0:
        return Image.new("RGB", (side, side), (255, 255, 255))
    scale = max(side / w, side / h)
    nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    resized = rgb.resize((nw, nh), Image.LANCZOS)
    left = max(0, (nw - side) // 2)
    top = max(0, (nh - side) // 2)
    return resized.crop((left, top, left + side, top + side))


def extract_pymol_3d_canvas(img: Image.Image) -> Image.Image:
    """从最大化截图中取出 3D 白底视口：去掉顶栏/工具条与右侧对象面板。

    注意：禁止再用「去黑白边」去裁分子图——白底是画面本身，裁掉会只剩中间一条。
    """
    rgb = img.convert("RGB")
    arr = np.asarray(rgb, dtype=np.float32)
    h, w, _ = arr.shape
    if h < 200 or w < 200:
        return rgb

    row_mean = arr.mean(axis=(1, 2))
    col_mean = arr.mean(axis=(0, 2))

    # 顶部：先跳过很亮的细缝，再吃掉连续暗色菜单/工具条
    y = 0
    while y < int(h * 0.15) and row_mean[y] >= 175:
        y += 1
    while y < int(h * 0.40) and row_mean[y] < 175:
        y += 1
    top = y

    # 右侧暗色对象面板
    x = w - 1
    while x > int(w * 0.55) and col_mean[x] < 175:
        x -= 1
    right = x

    # 底部控制台：自下往上吃掉最深的连续带（不限固定阈值）
    yb = h - 1
    if row_mean[yb] < 150:
        while yb > top and row_mean[yb - 1] < 165:
            yb -= 1
    bottom = yb

    left = 0
    while left < right and col_mean[left] < 175:
        left += 1

    if right - left < int(w * 0.45) or bottom - top < int(h * 0.45):
        top = 96 if h > 200 else 0
        right = max(200, w - 240)
        bottom = h - 1
        left = 0
        print(f"  [canvas-fallback] top={top} right={right}")
    else:
        print(f"  [canvas-detect] LTRB=({left},{top},{right},{bottom})")

    return rgb.crop((left, top, right + 1, bottom + 1))


def export_detail_png(
    job: Path, detail_size: int = 6000, dpi: int = 600, debug_window: bool = False
) -> tuple[bool, str]:
    pse_list = sorted(job.glob("detail-*.pse"))
    if not pse_list:
        return False, "no detail.pse"
    pse = pse_list[0]
    seq = pse.stem.split("-", 1)[-1]
    img_dir = job / "图片"
    img_dir.mkdir(parents=True, exist_ok=True)
    out = img_dir / f"detail-{seq}.png"
    before = (pse.stat().st_mtime_ns, pse.stat().st_size)

    if not PYMOL_HOOK.is_file():
        return False, f"missing hook: {PYMOL_HOOK}"

    env = os.environ.copy()
    env["PYMOL_DETAIL_OUT"] = str(out.resolve())
    env["PYMOL_DETAIL_SIZE"] = str(detail_size)
    env["PYMOL_DETAIL_DPI"] = str(dpi)
    env["PYMOL_EXPORT_HELPERS"] = str(Path(__file__).resolve())
    hook_log = job / "_hook_export.log"
    if hook_log.exists():
        hook_log.unlink()
    env["PYMOL_DETAIL_LOG"] = str(hook_log.resolve())
    if debug_window:
        env["PYMOL_DETAIL_DEBUG_WIN"] = str(
            (img_dir / f"detail-{seq}_debug_window.png").resolve()
        )

    try:
        proc = subprocess.run(
            [str(PYMOL_WIN), str(pse.resolve()), "-r", str(PYMOL_HOOK)],
            cwd=str(pse.parent),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        return False, "PyMOL hook timeout"

    hook_log = job / "_hook_export.log"
    for _ in range(5):
        if hook_log.is_file() and hook_log.stat().st_size > 0:
            break
        time.sleep(0.2)

    log = ((proc.stdout or "") + (proc.stderr or "")).strip()
    if hook_log.is_file():
        log = (log + "\n" + hook_log.read_text(encoding="utf-8", errors="replace")).strip()
    for ln in log.splitlines():
        if ln.strip().startswith("[hook]"):
            print(f"  {ln}")
    if hook_log.is_file():
        hook_log.unlink()

    after = (pse.stat().st_mtime_ns, pse.stat().st_size)
    if before != after:
        return False, f"PSE CHANGED unexpectedly: {pse}"

    if proc.returncode != 0:
        return False, f"hook exit {proc.returncode}"

    if not out.exists() or out.stat().st_size < 1000:
        return False, f"export failed: {out}"

    debug_png = img_dir / f"detail-{seq}_debug_window.png"
    verify = debug_png.name if debug_window and debug_png.is_file() else out.name
    return True, (
        f"ok {out.name} bytes={out.stat().st_size} "
        f"mode=pymol-collapse+dock-hide pse_unchanged=1 verify={verify}"
    )


def parse_only(arg: str | None) -> set[str] | None:
    if not arg:
        return None
    return {x.strip() for x in arg.split(",") if x.strip()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Open .pse in PyMOLWin, collapse console via Qt hook, screenshot"
    )
    ap.add_argument("--only", default="", help="comma-separated job ids")
    ap.add_argument("--detail-size", type=int, default=6000)
    ap.add_argument("--dpi", type=int, default=600)
    ap.add_argument("--skip-normalize", action="store_true")
    ap.add_argument(
        "--debug-window",
        action="store_true",
        help="save detail-N_debug_window.png for manual verification",
    )
    ap.add_argument(
        "--root",
        action="append",
        default=[],
        help="jobs root or a folder that directly contains detail-*.pse",
    )
    args = ap.parse_args(argv)

    desktop = Path.home() / "Desktop"
    if args.root:
        # 显式 --root 时只处理指定路径，避免叠加默认根目录导致一次导出全部任务
        roots = [Path(r) for r in args.root]
    else:
        roots = [
            desktop / "痤疮_分子对接_序号文件夹",
            desktop / "努力学习_分子对接" / "序号文件夹",
        ]

    jobs: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        if list(root.glob("detail-*.pse")):
            jobs.append(root)
            continue
        jobs.extend(find_jobs([root]))

    seen: set[str] = set()
    uniq: list[Path] = []
    for j in jobs:
        key = str(j.resolve())
        if key not in seen:
            seen.add(key)
            uniq.append(j)
    jobs = uniq

    only = parse_only(args.only)
    if not args.skip_normalize:
        for job in jobs:
            notes = normalize_job(job)
            if notes:
                print(f"[norm] {job.name}: " + "; ".join(notes))

    export_jobs = [j for j in jobs if list(j.glob("detail-*.pse"))]
    if only is not None:
        export_jobs = [
            j
            for j in export_jobs
            if j.name in only or j.name.split("_", 1)[0] in only
        ]
    print(f"export_jobs={len(export_jobs)} mode=pymol-collapse-before-screenshot")

    ok_n = 0
    for job in export_jobs:
        try:
            ok, msg = export_detail_png(
                job,
                detail_size=args.detail_size,
                dpi=args.dpi,
                debug_window=args.debug_window,
            )
        except Exception as exc:
            ok, msg = False, f"FAIL {exc}"
        print(f"[detail] {job.name}: {msg}")
        if ok:
            ok_n += 1
        time.sleep(0.6)
    print(f"DONE export {ok_n}/{len(export_jobs)}")
    return 0 if ok_n == len(export_jobs) else 2


if __name__ == "__main__":
    raise SystemExit(main())
