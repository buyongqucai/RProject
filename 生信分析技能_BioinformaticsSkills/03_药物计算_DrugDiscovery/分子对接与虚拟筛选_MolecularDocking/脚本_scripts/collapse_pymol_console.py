# -*- coding: utf-8 -*-
"""在已打开的 PyMOLWin 中收起底部代码区（不退出，供手验）。

用法：
  PyMOLWin.exe detail-1.pse -r collapse_pymol_console.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dock_export_common import collapse_console_qt  # noqa: E402


def _run() -> None:
    from pymol.gui import get_qtwindow

    win = get_qtwindow()
    if win is None:
        print("[collapse] FAIL: no qt window")
        return
    win.showMaximized()
    QApplication.processEvents()
    QTimer.singleShot(300, lambda: collapse_console_qt(win))


QTimer.singleShot(500, _run)
