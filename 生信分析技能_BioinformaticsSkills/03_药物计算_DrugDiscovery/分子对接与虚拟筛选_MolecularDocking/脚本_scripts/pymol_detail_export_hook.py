# -*- coding: utf-8 -*-
"""
PyMOLWin -r 钩子：最大化窗口 → 收起面板/代码区 → 紧取景 → 截图 → 中间正方形 → 退出。

仅由 export_detail_png_from_pse.py 通过 subprocess 调用：
  PyMOLWin.exe detail-N.pse -r pymol_detail_export_hook.py

要点（对照用户审核通过的 detail-4 / result_4）：
- **必须最大化窗口再截图**（showMaximized + SW_MAXIMIZE；截图前再压一次）。
  手调标签在最大化视口里做，同一窗口状态截图标签布局才不变。
- 隐藏右侧对象面板（Qt dock）+ 收起底部代码区，让 3D 视口尽量大。
- **紧取景**：始终 zoom(PT or CJ, buffer)，**禁止**「手调更宽就保留」——
  那会让残基/配体/标签只占画面三成（71 实测 fill≈33%；金标 detail-4 ≈71%）。
  `cmd.zoom` 不改旋转，手调朝向自然保留（禁止 zoom 后再写回旧旋转，会挤偏中心）。
  buffer 默认 4Å（标签引线余量；可用 PYMOL_DETAIL_BUFFER 调）。
  自适应满度目标默认 **0.72**（`PYMOL_DETAIL_FILL_TARGET`；曾用 0.88 过紧会切标签）。
- 宽视口 → 正方形：紧取景（zoom 已居中）后取**视口几何中心**正方形（边长=视口高）
  → 等比放大到 6000²。禁止用颜色估内容中心（绿色 Educational 水印会拉偏导致右切）。
  顶栏剥离：浅色标题条 + 深色菜单两段式，外加 strip_dark_chrome_edges 二次保险。
"""
from __future__ import annotations

import importlib.util
import os
import traceback
from pathlib import Path

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication


def _log(msg: str) -> None:
    print(msg, flush=True)
    try:
        log_path = os.environ.get("PYMOL_DETAIL_LOG", "").strip()
        if log_path:
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write(msg + "\n")
    except Exception:
        pass


def _export_helpers_path() -> Path:
    env = os.environ.get("PYMOL_EXPORT_HELPERS", "").strip()
    if env:
        p = Path(env)
        if p.is_file():
            return p
    here = Path(__file__).resolve().parent / "export_detail_png_from_pse.py"
    if here.is_file():
        return here
    raise FileNotFoundError(
        "export_detail_png_from_pse.py not found; set PYMOL_EXPORT_HELPERS"
    )


def _load_export_helpers():
    mod_path = _export_helpers_path()
    spec = importlib.util.spec_from_file_location("dock_export_helpers", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_common():
    mod_path = _export_helpers_path().parent / "dock_export_common.py"
    spec = importlib.util.spec_from_file_location("dock_export_common", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_EXP = None
_COMMON = None


def _collapse_console(win) -> None:
    _COMMON.collapse_console_qt(win, _log)


def _hide_side_panel(win) -> None:
    """隐藏右侧对象面板，让 3D 视口吃满最大化客户区。"""
    for attr in ("contentsPanelDockWidget", "dockWidget", "scenesDockWidget"):
        try:
            w = getattr(win, attr, None)
            if w is not None and hasattr(w, "hide"):
                w.hide()
                _log(f"[hook] hide {attr}")
        except Exception as exc:
            _log(f"[hook] hide {attr} warn: {exc}")
    try:
        from pymol import cmd

        cmd.set("internal_gui", 0)
        cmd.refresh()
    except Exception:
        pass


def _reframe_key_content() -> None:
    """紧取景：残基+配体+氢键+标签尽可能抵住截图框（对齐金标 detail-4 满度）。

    - **始终** zoom，不再保留过宽的手调缩放（那是 71 内容只占三成的根因）。
    - `cmd.zoom` 本身不改旋转矩阵，手调朝向/标签相对原子关系自然保留——
      **禁止** zoom 后再写回旧旋转（会把选择中心挤偏，出现左右边距不对称）。
    - buffer 默认 4Å：覆盖标签引线；自适应满度目标约 72%（勿冲到 88%，会切掉浅色标签）。
    """
    try:
        from pymol import cmd

        has_cj = cmd.count_atoms("CJ") > 0
        sel = "PT or CJ" if has_cj else "PT"
        if cmd.count_atoms(sel) <= 0:
            _log("[hook] reframe skipped: no PT/CJ atoms")
            return
        buf = float(os.environ.get("PYMOL_DETAIL_BUFFER", "4"))

        try:
            cmd.zoom(sel, buf, complete=1)
        except TypeError:
            cmd.zoom(sel, buf)
        # 放宽裁剪面，避免近远裁切切到 sticks
        v2 = list(cmd.get_view())
        if len(v2) >= 17:
            front, rear = float(v2[15]), float(v2[16])
            mid = 0.5 * (front + rear)
            half = max(abs(rear - front) * 3.0, 120.0)
            v2[15] = mid - half
            v2[16] = mid + half
            cmd.set_view(v2)
        mid = 0.5 * (float(v2[15]) + float(v2[16])) if len(v2) >= 17 else float("nan")
        _log(f"[hook] reframe: ALWAYS tight zoom sel={sel} buffer={buf} mid={mid:.1f}")
    except Exception:
        traceback.print_exc()
        _log("[hook] reframe warn")


def _scale_view(factor: float) -> None:
    """factor<1 拉近（内容变大），factor>1 拉远。

    实测 get_view()[11] 为相机距离（越接近 0 越近）；15/16 裁剪面中点 ≈ -v[11]。
    只改裁剪面不会改变缩放（旧实现无效）。
    """
    from pymol import cmd

    v = list(cmd.get_view())
    if len(v) < 17:
        return
    v[11] = float(v[11]) * factor
    dist = abs(float(v[11]))
    front, rear = float(v[15]), float(v[16])
    half = max(abs(rear - front) * 0.5 * abs(factor), 40.0)
    v[15] = dist - half
    v[16] = dist + half
    cmd.set_view(v)


def _reliable_content_span(canvas, box: tuple[int, int, int, int] | None = None) -> float | None:
    """正方形取景框内，可靠内容（饱和 sticks/氢键 + 深色字）的最大边长（像素）。

    排除左上角 Educational 水印带，避免估偏。
    """
    import numpy as np

    a = np.asarray(canvas.convert("RGB"), dtype=np.uint8)
    if box is not None:
        l, t, r, b = box
        a = a[t:b, l:r]
    h, w, _ = a.shape
    if h < 20 or w < 20:
        return None
    mx = a.max(axis=2).astype(np.int32)
    mn = a.min(axis=2).astype(np.int32)
    sat = (mx - mn) * 255 // np.maximum(mx, 1)
    mask = ((sat > 70) | (mx < 190)) & (mx < 250)
    mask[: max(1, int(h * 0.06)), : max(1, int(w * 0.35))] = False
    cols = mask.sum(axis=0)
    rows = mask.sum(axis=1)
    xs = np.where(cols > max(2, int(h * 0.002)))[0]
    ys = np.where(rows > max(2, int(w * 0.002)))[0]
    if xs.size < 10 or ys.size < 10:
        return None
    return float(max(int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)))


def _win32_is_zoomed(hwnd: int) -> bool:
    import ctypes

    return bool(ctypes.windll.user32.IsZoomed(hwnd))


def _force_maximize(win, hwnd: int) -> None:
    import ctypes

    win.showMaximized()
    ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
    QApplication.processEvents()
    _log(
        f"[hook] maximize: qt={win.width()}x{win.height()} "
        f"IsZoomed={_win32_is_zoomed(hwnd)}"
    )


def _run_export() -> None:
    out = Path(os.environ["PYMOL_DETAIL_OUT"])
    detail_size = int(os.environ.get("PYMOL_DETAIL_SIZE", "6000"))
    dpi = int(os.environ.get("PYMOL_DETAIL_DPI", "600"))
    debug_win = os.environ.get("PYMOL_DETAIL_DEBUG_WIN", "").strip()

    try:
        global _EXP, _COMMON
        _EXP = _load_export_helpers()
        exp = _EXP
        _COMMON = _load_common()
        _log(f"[hook] helpers={_export_helpers_path()}")
    except Exception:
        traceback.print_exc()
        _log("[hook] FAIL load export helpers")
        QApplication.quit()
        return

    from pymol.gui import get_qtwindow

    win = get_qtwindow()
    if win is None:
        _log("[hook] FAIL no qt window")
        QApplication.quit()
        return
    hwnd = int(win.winId())

    def _capture_canvas():
        _force_maximize(win, hwnd)  # 截图前再压一次，防会话间隙还原
        shot = exp._capture_hwnd_bitmap(hwnd, use_client=True)
        _log(f"[hook] shot raw={shot.size} IsZoomed={_win32_is_zoomed(hwnd)}")
        if debug_win:
            Path(debug_win).parent.mkdir(parents=True, exist_ok=True)
            shot.save(debug_win)
            _log(f"[hook] debug window -> {debug_win}")
        return exp.extract_pymol_3d_canvas(shot)

    def _save(img) -> None:
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(out, dpi=(dpi, dpi))
        _log(f"[hook] ok {out} bytes={out.stat().st_size}")

    def _step1_maximize() -> None:
        _force_maximize(win, hwnd)
        _hide_side_panel(win)
        QApplication.processEvents()
        QTimer.singleShot(800, _step2_collapse)

    def _step2_collapse() -> None:
        _collapse_console(win)
        _hide_side_panel(win)  # 收控制台后可能又把布局撑开
        _force_maximize(win, hwnd)
        QApplication.processEvents()
        QTimer.singleShot(600, _step3_reframe)

    def _step3_reframe() -> None:
        _reframe_key_content()
        QApplication.processEvents()
        QTimer.singleShot(700, _step4_capture)

    def _step4_capture() -> None:
        try:
            from PIL import Image

            _collapse_console(win)
            _hide_side_panel(win)

            # 目标约 72%（金标 ~71%）：过满（曾 0.88）会切掉浅色标签/引线。
            # 测 span 时加 15% 标签余量，再决定是否拉近——宁可略空，不要裁切。
            target = float(os.environ.get("PYMOL_DETAIL_FILL_TARGET", "0.72"))
            label_pad = float(os.environ.get("PYMOL_DETAIL_LABEL_PAD", "1.15"))
            canvas = None
            side = left = top = 0
            for attempt in range(3):
                canvas = exp.strip_dark_chrome_edges(_capture_canvas())
                cw, ch = canvas.size
                side = min(cw, ch)
                left = (cw - side) // 2
                top = (ch - side) // 2
                sq = (left, top, left + side, top + side)
                span = _reliable_content_span(canvas, sq)
                if span is None:
                    _log(f"[hook] fill attempt={attempt} span=None canvas={canvas.size}")
                    break
                # 用「sticks+标签余量」占比判断，避免按 sticks 拉满后切掉标签
                ratio = (span * label_pad) / side
                _log(
                    f"[hook] fill attempt={attempt} span={span:.0f} pad={label_pad:.2f} "
                    f"side={side} ratio={ratio:.3f} target={target:.2f} canvas={canvas.size}"
                )
                if abs(ratio - target) <= 0.05 or attempt == 2:
                    break
                # 拉近不要太狠（下限 0.75）；偏空时才拉近，偏满时略拉远保完整
                factor = max(0.75, min(1.30, ratio / target))
                if abs(factor - 1.0) < 0.04:
                    break
                _scale_view(factor)
                QApplication.processEvents()
                import time as _time

                _time.sleep(0.35)

            assert canvas is not None
            box = (left, top, left + side, top + side)
            crop = canvas.crop(box)
            squared = crop.resize((detail_size, detail_size), Image.LANCZOS)
            _log(f"[hook] viewport-centered square side={side} box={box} -> {detail_size}")
            _save(squared)
        except Exception:
            traceback.print_exc()
            _log("[hook] FAIL capture")
        _finish()

    def _finish() -> None:
        pause_ms = int(os.environ.get("PYMOL_DETAIL_PAUSE_MS", "1800"))

        def _quit() -> None:
            try:
                win.close()
            except Exception:
                pass
            QApplication.quit()

        QTimer.singleShot(pause_ms, _quit)

    QTimer.singleShot(600, _step1_maximize)


QTimer.singleShot(1200, _run_export)
