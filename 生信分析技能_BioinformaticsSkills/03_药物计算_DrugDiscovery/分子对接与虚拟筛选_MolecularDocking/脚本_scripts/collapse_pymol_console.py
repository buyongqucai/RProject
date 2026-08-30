# -*- coding: utf-8 -*-
"""在已打开的 PyMOLWin 中收起底部代码区（不退出，供手验）。

用法（推荐）：
  PyMOLWin.exe detail-1.pse -r collapse_pymol_console.py

或在 PyMOL 命令行：
  run E:\\RProject\\...\\collapse_pymol_console.py
"""
from __future__ import annotations

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

# 脚本绝对路径（避免 run 命令下 __file__ 错位）
SCRIPT_DIR = r"E:\RProject\生信分析技能_BioinformaticsSkills\03_药物计算_DrugDiscovery\分子对接与虚拟筛选_MolecularDocking\脚本_scripts"


def _collapse(win) -> None:
    try:
        frame = win.contentsPanelFrame
        frame.toggleLogActive(False)
        tools = frame.contentsPanelTools
        tools.log_active = False
        tools._check_log_active()
    except Exception as exc:
        print(f"[collapse] panel: {exc}")

    try:
        win.toggle_command_log(False)
    except Exception as exc:
        print(f"[collapse] log: {exc}")

    try:
        if win.lineedit and win.lineedit.isVisible():
            win.toggle_lineedit()
    except Exception as exc:
        print(f"[collapse] lineedit: {exc}")

    try:
        win.browser.hide()
        if win.lineedit:
            win.lineedit.hide()
        if getattr(win, "command_label", None):
            win.command_label.hide()
        win._resize_docks(win.dockWidget, 0)
        win.dockWidget.hide()
    except Exception as exc:
        print(f"[collapse] dock: {exc}")

    QApplication.processEvents()
    print(
        f"[collapse] done browser={win.browser.isVisible()} "
        f"dock={win.dockWidget.isVisible()}"
    )


def _run() -> None:
    from pymol.gui import get_qtwindow

    win = get_qtwindow()
    if win is None:
        print("[collapse] FAIL: no qt window")
        return
    win.showMaximized()
    QApplication.processEvents()
    QTimer.singleShot(300, lambda: _collapse(win))


QTimer.singleShot(500, _run)
