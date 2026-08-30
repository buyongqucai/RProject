# -*- coding: utf-8 -*-
"""
PyMOLWin -r 钩子：最大化后收起底部代码区 → 截图 → 退出。

仅由 export_detail_png_from_pse.py 通过 subprocess 调用：
  PyMOLWin.exe detail-N.pse -r pymol_detail_export_hook.py
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


def _collapse_console(win) -> None:
    """最大化之后强制收起底部代码区（.pse 会话常会恢复展开状态）。"""
    # 同步右侧工具条按钮状态
    try:
        frame = win.contentsPanelFrame
        frame.toggleLogActive(False)
        tools = frame.contentsPanelTools
        tools.log_active = False
        tools.timeline_active = False
        tools._check_log_active()
        tools._check_timeline_active()
    except Exception as exc:
        _log(f"[hook] panel sync warn: {exc}")

    try:
        win.toggle_command_log(False)
    except Exception as exc:
        _log(f"[hook] toggle_command_log warn: {exc}")

    try:
        if win.lineedit and win.lineedit.isVisible():
            win.toggle_lineedit()
    except Exception as exc:
        _log(f"[hook] toggle_lineedit warn: {exc}")

    # 直接隐藏 browser / lineedit，并把 dock 压到 0
    try:
        win.browser.hide()
        if getattr(win, "pymol_timeline_gui", None):
            win.pymol_timeline_gui.hide()
        if win.lineedit:
            win.lineedit.hide()
        if getattr(win, "command_label", None):
            win.command_label.hide()
        win._resize_docks(win.dockWidget, 0)
        win.dockWidget.hide()
    except Exception as exc:
        _log(f"[hook] dock hide warn: {exc}")

    QApplication.processEvents()

    try:
        browser_vis = win.browser.isVisible()
        line_vis = win.lineedit.isVisible() if win.lineedit else None
        dock_vis = win.dockWidget.isVisible()
        dock_h = int(win.dockWidget.height())
        _log(
            f"[hook] after collapse: browser={browser_vis} "
            f"lineedit={line_vis} dock_vis={dock_vis} dock_h={dock_h}px"
        )
    except Exception as exc:
        _log(f"[hook] status warn: {exc}")


def _run_export() -> None:
    out = Path(os.environ["PYMOL_DETAIL_OUT"])
    detail_size = int(os.environ.get("PYMOL_DETAIL_SIZE", "6000"))
    dpi = int(os.environ.get("PYMOL_DETAIL_DPI", "600"))
    debug_win = os.environ.get("PYMOL_DETAIL_DEBUG_WIN", "").strip()

    try:
        exp = _load_export_helpers()
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

    def _after_maximize() -> None:
        _collapse_console(win)
        QApplication.processEvents()
        # 再等一帧布局，防止 maximize 把 dock 又撑开
        QTimer.singleShot(500, _collapse_again)

    def _collapse_again() -> None:
        _collapse_console(win)
        QTimer.singleShot(900, _capture)

    def _capture() -> None:
        try:
            _collapse_console(win)
            hwnd = int(win.winId())
            shot = exp._capture_hwnd_bitmap(hwnd, use_client=True)
            _log(f"[hook] shot raw={shot.size}")
            if debug_win:
                Path(debug_win).parent.mkdir(parents=True, exist_ok=True)
                shot.save(debug_win)
                _log(f"[hook] debug window -> {debug_win}")
            canvas = exp.extract_pymol_3d_canvas(shot)
            _log(f"[hook] canvas={canvas.size}")
            squared = exp.cover_square(canvas, detail_size)
            out.parent.mkdir(parents=True, exist_ok=True)
            squared.save(out, dpi=(dpi, dpi))
            _log(f"[hook] ok {out} bytes={out.stat().st_size}")
        except Exception:
            traceback.print_exc()
            _log("[hook] FAIL capture")
        finally:
            pause_ms = int(os.environ.get("PYMOL_DETAIL_PAUSE_MS", "1800"))
            def _quit() -> None:
                try:
                    win.close()
                except Exception:
                    pass
                QApplication.quit()
            QTimer.singleShot(pause_ms, _quit)

    win.showMaximized()
    win.raise_()
    win.activateWindow()
    QApplication.processEvents()
    QTimer.singleShot(700, _after_maximize)


QTimer.singleShot(1200, _run_export)
