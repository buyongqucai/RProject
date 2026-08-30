# -*- coding: utf-8 -*-
"""手调 detail.pse 后导出 PNG（标签所见即所得）。

每个任务只开一次 PyMOLWin，流程（主路径）：
  1. PyMOLWin.exe 打开 .pse 并 -r 加载 pymol_detail_export_hook.py
  2. 钩子内用 PyMOL Qt API 先 **收起底部代码区**（大黑框命令日志），使 3D 视口变高
  3. 最大化 → 截图 → 裁 3D 画布 → cover 正方形 PNG
禁止写回 / 改动 .pse；禁止 cmd.png 离屏重渲。
注意：「收起代码区」指截图前在 PyMOL 内折叠 UI，不是事后把黑框裁掉。
备用：export_detail_png_legacy() 为旧版图像识别点击（不可靠）。
"""
from __future__ import annotations

import argparse
import ctypes
import os
import shutil
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

import numpy as np
from PIL import Image, ImageGrab

PYMOL_WIN = Path(r"E:\pymol\PyMOLWin.exe")
PYMOL_HOOK = Path(__file__).resolve().parent / "pymol_detail_export_hook.py"
TEMPLATE_TOGGLE = (
    Path(__file__).resolve().parent / "assets" / "pymol_console_toggle_template.png"
)

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
SW_HIDE = 0
SW_NORMAL = 1
SW_MAXIMIZE = 3
SW_SHOW = 5
SW_RESTORE = 9
SW_SHOWMAXIMIZED = 3
GA_ROOT = 2
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040


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


class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ("length", wintypes.UINT),
        ("flags", wintypes.UINT),
        ("showCmd", wintypes.UINT),
        ("ptMinPosition", wintypes.POINT),
        ("ptMaxPosition", wintypes.POINT),
        ("rcNormalPosition", wintypes.RECT),
    ]

VK_LWIN = 0x5B
VK_UP = 0x26
VK_DOWN = 0x28
VK_MENU = 0x12
VK_SPACE = 0x20
VK_X = 0x58
VK_F4 = 0x73
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


def normalize_job(job: Path) -> list[str]:
    notes: list[str] = []
    img = job / "图片"
    img.mkdir(parents=True, exist_ok=True)
    for p in list(job.glob("*.png")):
        dst = img / p.name
        if dst.exists():
            p.unlink()
            notes.append(f"removed duplicate root png: {p.name}")
        else:
            shutil.move(str(p), str(dst))
            notes.append(f"moved root png -> 图片/{p.name}")
    tmp = job / "_png_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
        notes.append("deleted _png_tmp")
    return notes


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


def _key_down(vk: int) -> None:
    user32.keybd_event(vk, 0, 0, 0)


def _key_up(vk: int) -> None:
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def _tap(vk: int, hold: float = 0.05) -> None:
    _key_down(vk)
    time.sleep(hold)
    _key_up(vk)


def send_win_up() -> None:
    _key_down(VK_LWIN)
    time.sleep(0.05)
    _tap(VK_UP)
    time.sleep(0.05)
    _key_up(VK_LWIN)


def send_alt_space_x() -> None:
    _key_down(VK_MENU)
    time.sleep(0.05)
    _tap(VK_SPACE)
    time.sleep(0.05)
    _key_up(VK_MENU)
    time.sleep(0.15)
    _tap(VK_X)


def send_alt_f4() -> None:
    _key_down(VK_MENU)
    time.sleep(0.05)
    _tap(VK_F4)
    time.sleep(0.05)
    _key_up(VK_MENU)


def enum_pymol_hwnds() -> list[int]:
    found: list[int] = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def _enum(hwnd, _lp):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = (buf.value or "").lower()
        if "pymol" in title:
            found.append(int(hwnd))
        return True

    user32.EnumWindows(_enum, 0)
    return found


def wait_pymol_window(timeout_s: float = 60.0, prefer_new: set[int] | None = None) -> int | None:
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout_s:
        hwnds = enum_pymol_hwnds()
        if prefer_new is not None:
            hwnds = [h for h in hwnds if h not in prefer_new]
        if hwnds:
            last = hwnds[-1]
            rect = wintypes.RECT()
            user32.GetClientRect(last, ctypes.byref(rect))
            cw = int(rect.right - rect.left)
            ch = int(rect.bottom - rect.top)
            if cw >= 400 and ch >= 300:
                time.sleep(1.2)
                return last
        time.sleep(0.25)
    return last


def root_hwnd(hwnd: int) -> int:
    """落到顶层窗口，避免对子控件 Maximize/截图。"""
    root = int(user32.GetAncestor(hwnd, GA_ROOT) or hwnd)
    return root or int(hwnd)


def _window_size(hwnd: int) -> tuple[int, int]:
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return int(rect.right - rect.left), int(rect.bottom - rect.top)


def is_maximized(hwnd: int, ratio: float = 0.92) -> bool:
    hwnd = root_hwnd(hwnd)
    place = WINDOWPLACEMENT()
    place.length = ctypes.sizeof(WINDOWPLACEMENT)
    if user32.GetWindowPlacement(hwnd, ctypes.byref(place)):
        if int(place.showCmd) == SW_SHOWMAXIMIZED:
            return True
    ww, wh = _window_size(hwnd)
    scr_w = user32.GetSystemMetrics(0)
    scr_h = user32.GetSystemMetrics(1)
    # 宽和高都要接近屏幕，防止「只有横向全宽、高度被压扁」被误判为最大化
    return ww >= scr_w * ratio and wh >= scr_h * ratio


def ensure_maximized(hwnd: int) -> int:
    """保持/恢复最大化并钉在主屏。禁止 SW_RESTORE；禁止在已最大化时再发 Win+↑。"""
    hwnd = root_hwnd(hwnd)
    user32.ShowWindow(hwnd, SW_SHOW)
    # 若窗口跑到副屏，先拉回主屏再最大化
    wr = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(wr))
    scr_w = user32.GetSystemMetrics(0)
    scr_h = user32.GetSystemMetrics(1)
    ww, wh = _window_size(hwnd)
    off_primary = (
        wr.left < -50
        or wr.left > scr_w - 200
        or wr.top < -50
        or wr.top > scr_h - 200
        or ww > scr_w * 1.08
        or wh > scr_h * 1.08
    )
    if off_primary:
        # 唯一允许 SW_RESTORE：把副屏最大化窗拉回主屏（日常流程禁止乱 restore）
        user32.ShowWindow(hwnd, SW_RESTORE)
        time.sleep(0.2)
        user32.SetWindowPos(
            hwnd,
            0,
            80,
            80,
            min(1400, scr_w - 100),
            min(900, scr_h - 100),
            SWP_SHOWWINDOW,
        )
        time.sleep(0.35)
        print(f"  [geom] pinned to primary {scr_w}x{scr_h}")
    user32.SetForegroundWindow(hwnd)
    if is_maximized(hwnd) and not off_primary:
        return hwnd

    user32.ShowWindow(hwnd, SW_MAXIMIZE)
    time.sleep(0.4)
    if is_maximized(hwnd):
        return hwnd

    # 仅在仍未最大化时用快捷键；已最大化绝不发 Win+↑
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.15)
    send_alt_space_x()
    time.sleep(0.45)
    if not is_maximized(hwnd):
        user32.SetForegroundWindow(hwnd)
        send_win_up()
        time.sleep(0.45)
    if not is_maximized(hwnd):
        user32.ShowWindow(hwnd, SW_MAXIMIZE)
        time.sleep(0.35)
    return hwnd


def focus_window(hwnd: int, keep_size: bool = False) -> int:
    """前置窗口；keep_size=True 时不强制最大化（用于命令行折叠检测）。"""
    if keep_size:
        hwnd = root_hwnd(hwnd)
        user32.ShowWindow(hwnd, SW_SHOW)
    else:
        hwnd = ensure_maximized(hwnd)
    user32.SetWindowPos(
        hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
    )
    time.sleep(0.08)
    user32.SetWindowPos(
        hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
    )
    time.sleep(0.12)
    return hwnd


def maximize_by_hotkey(hwnd: int) -> int:
    """加载完成后再最大化（打开阶段绝不调用）。"""
    hwnd = ensure_maximized(hwnd)
    time.sleep(0.3)
    return hwnd


def _client_screen_box(hwnd: int) -> tuple[int, int, int, int]:
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    left_top = wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(left_top))
    l, t = int(left_top.x), int(left_top.y)
    r = l + int(rect.right - rect.left)
    b = t + int(rect.bottom - rect.top)
    if r <= l or b <= t:
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        l, t, r, b = int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)
    return l, t, r, b


def click_screen(x: int, y: int) -> None:
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.06)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.06)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def _cv2_read_bgr(path: Path):
    import cv2

    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def detect_console_black_band(shot: Image.Image) -> tuple[bool, int, int]:
    """
    判断底部是否仍有 PyMOL 黑色命令行大框。
    策略：自底向上统计连续「深色行」；或底部条带深色像素占比超阈值。
  返回 (是否可见, 黑框顶边 y, 黑框高度)。
    """
    arr = np.asarray(shot.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]
    view_w = max(1, int(w * 0.90))

    # 1) 底部条带深色像素占比（放宽阈值，适配 2K 最大化）
    for ratio in (0.14, 0.18, 0.22, 0.26):
        y0 = int(h * (1.0 - ratio))
        band = arr[y0:, :view_w, :]
        dark_frac = float((band.mean(axis=2) < 58).mean())
        if dark_frac >= 0.38:
            band_top = h
            for y in range(y0, h):
                df = float((arr[y, :view_w, :].mean(axis=1) < 58).mean())
                if df > 0.62:
                    band_top = min(band_top, y)
            band_h = h - band_top
            if band_h >= 90:
                return True, band_top, band_h

    # 2) 自底向上连续深色行
    run = 0
    band_top = h
    for y in range(h - 8, int(h * 0.68), -1):
        df = float((arr[y, :view_w, :].mean(axis=1) < 58).mean())
        if df > 0.55:
            run += 1
            band_top = y
        elif run >= 90:
            return True, band_top, run
        else:
            run = 0
    if run >= 90:
        return True, band_top, run

    return False, 0, 0


def locate_toggle_click(
    shot: Image.Image,
    band_top: int,
) -> tuple[int, int, str]:
    """
    在黑框上缘附近定位 `>_` 点击点。
    先按窗口比例给锚点，再在小 ROI 内模板匹配 refine。
    """
    import cv2

    w, h = shot.size
    anchor_x = int(w * 0.965)
    anchor_y = max(0, band_top - max(18, int(h * 0.022)))

    if not TEMPLATE_TOGGLE.exists():
        return anchor_x, anchor_y, "geometry"

    hay = cv2.cvtColor(np.asarray(shot.convert("RGB")), cv2.COLOR_RGB2BGR)
    tpl = _cv2_read_bgr(TEMPLATE_TOGGLE)
    if tpl is None:
        return anchor_x, anchor_y, "geometry"

    pad_x, pad_y = 140, 55
    x0 = max(0, anchor_x - pad_x)
    y0 = max(0, anchor_y - pad_y)
    x1 = min(w, anchor_x + pad_x)
    y1 = min(h, anchor_y + pad_y)
    roi = hay[y0:y1, x0:x1, :]
    if roi.size == 0:
        return anchor_x, anchor_y, "geometry"

    best: tuple[float, int, int, float] | None = None
    for scale in (0.45, 0.60, 0.75, 0.90, 1.05, 1.25, 1.50, 1.80, 2.10):
        t = cv2.resize(tpl, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        th, tw = t.shape[:2]
        if th < 4 or tw < 4 or th > roi.shape[0] or tw > roi.shape[1]:
            continue
        res = cv2.matchTemplate(roi, t, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if best is None or max_val > best[0]:
            best = (
                float(max_val),
                int(max_loc[0] + tw // 2 + x0),
                int(max_loc[1] + th // 2 + y0),
                scale,
            )

    if best and best[0] >= 0.42:
        score, cx, cy, scale = best
        print(
            f"  [console-img] template refine score={score:.3f} "
            f"click=({cx},{cy}) scale={scale:.2f}"
        )
        return cx, cy, "template"

    print(
        f"  [console-img] template weak; use geometry anchor=({anchor_x},{anchor_y})"
    )
    return anchor_x, anchor_y, "geometry"


def force_window_restore(hwnd: int) -> int:
    """强制退出最大化，缩至常规窗口（便于露出底部命令行黑框）。"""
    hwnd = root_hwnd(hwnd)
    place = WINDOWPLACEMENT()
    place.length = ctypes.sizeof(WINDOWPLACEMENT)
    if user32.GetWindowPlacement(hwnd, ctypes.byref(place)):
        place.showCmd = SW_RESTORE
        user32.SetWindowPlacement(hwnd, ctypes.byref(place))
    user32.ShowWindow(hwnd, SW_RESTORE)
    time.sleep(0.35)
  # Win+Down 再还原一次（Win11 最大化时有效）
    user32.SetForegroundWindow(hwnd)
    _key_down(VK_LWIN)
    time.sleep(0.05)
    _tap(VK_DOWN)
    time.sleep(0.05)
    _key_up(VK_LWIN)
    time.sleep(0.45)
    scr_w = user32.GetSystemMetrics(0)
    scr_h = user32.GetSystemMetrics(1)
    user32.MoveWindow(hwnd, 80, 60, min(1280, scr_w - 120), min(920, scr_h - 120), True)
    time.sleep(0.65)
    return hwnd


def prepare_window_for_console_check(hwnd: int) -> int:
    """先还原为窗口模式（非最大化），便于露出底部黑色命令行区。"""
    hwnd = root_hwnd(hwnd)
    l, t, r, b = _window_screen_box(hwnd)
    w, h = r - l, b - t
    if is_maximized(hwnd) or w > 1500 or h > 1000:
        hwnd = force_window_restore(hwnd)
    return hwnd


def hide_code_console(hwnd: int) -> int:
    """
    先还原窗口 → 检测底部黑框命令行区是否展开；
    若展开则图像识别 `>_` 并点击，直到黑框消失（最多 3 次）→ 再最大化。
    """
    hwnd = prepare_window_for_console_check(hwnd)
    hwnd = focus_window(hwnd, keep_size=True)

    for attempt in range(1, 4):
        preview = capture_window_full(hwnd)
        visible, top_y, band_h = detect_console_black_band(preview)
        print(
            f"  [console] attempt={attempt} black_band={visible} "
            f"top_y={top_y} height={band_h} shot={preview.size}"
        )
        if not visible:
            arr = np.asarray(preview.convert("RGB"), dtype=np.float32)
            hh, ww = arr.shape[:2]
            tail = arr[int(hh * 0.82) :, : int(ww * 0.92), :]
            tail_dark = float((tail.mean(axis=2) < 70).mean())
            if tail_dark < 0.12:
                print("  [console] folded OK (no black code band)")
                break
            print(f"  [console] dark tail detected (tail_dark={tail_dark:.3f}), will click")
            top_y = int(hh * 0.86)

        cx, cy, how = locate_toggle_click(preview, band_top=top_y)
        wl, wt, _, _ = _window_screen_box(hwnd)
        sx, sy = wl + cx, wt + cy
        user32.SetForegroundWindow(hwnd)
        print(f"  [console] clicking ({how}) screen=({sx},{sy})")
        click_screen(sx, sy)
        time.sleep(0.85)
        hwnd = focus_window(hwnd, keep_size=True)

    final = capture_window_full(hwnd)
    visible, _, _ = detect_console_black_band(final)
    print(f"  [console] final black_band={visible}")
    return ensure_maximized(hwnd)


def capture_window(hwnd: int) -> Image.Image:
    """截取客户区（用于最终 detail 导出）。"""
    hwnd = ensure_maximized(hwnd)
    time.sleep(0.25)
    return _capture_hwnd_bitmap(hwnd, use_client=True)


def _window_screen_box(hwnd: int) -> tuple[int, int, int, int]:
    """整窗外框（含底部命令行区）。"""
    hwnd = root_hwnd(hwnd)
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)


def capture_window_full(hwnd: int) -> Image.Image:
    """截取整窗（含底部黑色命令行大框），用于折叠判断与点击定位。"""
    hwnd = root_hwnd(hwnd)
    time.sleep(0.2)
    return _capture_hwnd_bitmap(hwnd, use_client=False)


def close_pymol(hwnd: int | None, proc: subprocess.Popen | None) -> None:
    try:
        if hwnd:
            focus_window(hwnd)
            send_alt_f4()
            time.sleep(0.8)
    except Exception:
        pass
    if proc is not None and proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def open_pse_with_pymolwin(pse: Path) -> tuple[subprocess.Popen, int]:
    if not PYMOL_WIN.exists():
        raise FileNotFoundError(PYMOL_WIN)
    before = set(enum_pymol_hwnds())
    proc = subprocess.Popen([str(PYMOL_WIN), str(pse.resolve())], cwd=str(pse.parent))
    hwnd = wait_pymol_window(timeout_s=60.0, prefer_new=before)
    if hwnd is None:
        close_pymol(None, proc)
        raise RuntimeError(f"PyMOL window not ready for {pse}")
    # 仅等待加载，此时绝不 maximize
    time.sleep(3.0)
    return proc, hwnd


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


def export_detail_png_legacy(job: Path, detail_size: int = 6000, dpi: int = 600) -> tuple[bool, str]:
    """旧版：PyMOLWin 外挂截图 + 图像识别（保留备用）。"""
    pse_list = sorted(job.glob("detail-*.pse"))
    if not pse_list:
        return False, "no detail.pse"
    pse = pse_list[0]
    seq = pse.stem.split("-", 1)[-1]
    img_dir = job / "图片"
    img_dir.mkdir(parents=True, exist_ok=True)
    out = img_dir / f"detail-{seq}.png"
    before = (pse.stat().st_mtime_ns, pse.stat().st_size)

    proc = None
    hwnd = None
    try:
        proc, hwnd = open_pse_with_pymolwin(pse)
        hwnd = root_hwnd(hwnd)
        hwnd = hide_code_console(hwnd)
        time.sleep(0.4)
        hwnd = ensure_maximized(hwnd)
        ww, wh = _window_size(hwnd)
        print(f"  [geom] maximized={is_maximized(hwnd)} size={ww}x{wh}")
        shot = capture_window(hwnd)
        print(f"  [shot] raw={shot.size}")
    finally:
        close_pymol(hwnd, proc)

    after = (pse.stat().st_mtime_ns, pse.stat().st_size)
    if before != after:
        return False, f"PSE CHANGED unexpectedly: {pse}"

    canvas = extract_pymol_3d_canvas(shot)
    print(f"  [canvas] {canvas.size}")
    squared = cover_square(canvas, detail_size)
    squared.save(out, dpi=(dpi, dpi))

    after2 = (pse.stat().st_mtime_ns, pse.stat().st_size)
    if before != after2:
        return False, f"PSE CHANGED after save: {pse}"
    if not out.exists() or out.stat().st_size < 1000:
        return False, f"export failed: {out}"
    return True, (
        f"ok {out.name} bytes={out.stat().st_size} "
        f"mode=legacy-img-toggle+screenshot pse_unchanged=1"
    )


def parse_only(arg: str | None) -> set[str] | None:
    if not arg:
        return None
    return {x.strip() for x in arg.split(",") if x.strip()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Open .pse in PyMOLWin, maximize by hotkey, screenshot"
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
