# -*- coding: utf-8 -*-
"""分子对接脚本群公共 helper（议题 06：消除跨脚本重复）。

- log: GBK 控制台安全打印
- ensure_img_subdir: 根目录散落 PNG 归入 图片/ 并清 _png_tmp
- collapse_console_qt: PyMOL Qt 收起底部代码区（导出钩子与手验脚本共用）
"""
from __future__ import annotations

import shutil
from pathlib import Path


def log(msg: str) -> None:
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode("gbk", errors="replace").decode("gbk"), flush=True)


def ensure_img_subdir(folder: Path) -> list[str]:
    """根目录散落 PNG 归入 图片/（同名且源更新则覆盖后删源），清 _png_tmp；返回操作记录。"""
    notes: list[str] = []
    img = folder / "图片"
    img.mkdir(parents=True, exist_ok=True)
    for p in list(folder.glob("*.png")):
        dst = img / p.name
        if dst.exists():
            if p.stat().st_mtime >= dst.stat().st_mtime:
                shutil.copy2(p, dst)
            p.unlink()
            notes.append(f"absorbed duplicate root png: {p.name}")
        else:
            shutil.move(str(p), str(dst))
            notes.append(f"moved root png -> 图片/{p.name}")
    tmp = folder / "_png_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
        notes.append("deleted _png_tmp")
    return notes


def collapse_console_qt(win, log_fn=log) -> None:
    """最大化后强制收起 PyMOL 底部代码区（.pse 会话常会恢复展开状态）。

    仅在 PyMOL 进程内可用（PyQt5 延迟导入，避免普通 Python 环境 import 本模块失败）。
    """
    from PyQt5.QtWidgets import QApplication

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
        log_fn(f"[collapse] panel sync warn: {exc}")

    try:
        win.toggle_command_log(False)
    except Exception as exc:
        log_fn(f"[collapse] toggle_command_log warn: {exc}")

    try:
        if win.lineedit and win.lineedit.isVisible():
            win.toggle_lineedit()
    except Exception as exc:
        log_fn(f"[collapse] toggle_lineedit warn: {exc}")

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
        log_fn(f"[collapse] dock hide warn: {exc}")

    QApplication.processEvents()

    try:
        browser_vis = win.browser.isVisible()
        line_vis = win.lineedit.isVisible() if win.lineedit else None
        dock_vis = win.dockWidget.isVisible()
        dock_h = int(win.dockWidget.height())
        log_fn(
            f"[collapse] done browser={browser_vis} "
            f"lineedit={line_vis} dock_vis={dock_vis} dock_h={dock_h}px"
        )
    except Exception as exc:
        log_fn(f"[collapse] status warn: {exc}")
