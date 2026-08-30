# -*- coding: utf-8 -*-
"""议题 04：环热图文字标签颜色合规（SOP §6 标签一律黑色 #000000）。"""
import re
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1] / "脚本_scripts" / "plot_docking_ring_heatmap.py"
)


def test_all_text_labels_black() -> None:
    src = SCRIPT.read_text(encoding="utf-8")
    text_blocks = re.findall(r"ax\.text\((.*?)\)", src, flags=re.DOTALL)
    assert text_blocks, "no ax.text calls found"
    for blk in text_blocks:
        colors = re.findall(r'color\s*=\s*"(#[0-9A-Fa-f]{6})"', blk)
        for c in colors:
            assert c == "#000000", f"non-black text label color {c} in ax.text block"
