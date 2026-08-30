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


_EXP = None


def _collapse_console(win) -> None:
    """最大化之后强制收起底部代码区（.pse 会话常会恢复展开状态）。"""
    _EXP.collapse_console_qt(win, _log)


def _run_export() -> None:
    out = Path(os.environ["PYMOL_DETAIL_OUT"])
    detail_size = int(os.environ.get("PYMOL_DETAIL_SIZE", "6000"))
    dpi = int(os.environ.get("PYMOL_DETAIL_DPI", "600"))
    debug_win = os.environ.get("PYMOL_DETAIL_DEBUG_WIN", "").strip()

    try:
        global _EXP
        _EXP = _load_export_helpers()
        exp = _EXP
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
