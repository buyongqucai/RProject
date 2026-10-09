# -*- coding: utf-8 -*-
"""入口：皮损 M2-like × AHR GenKI（转调 genki_tingting_ahr.py）。"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    script = Path(__file__).resolve().parent / "genki_tingting_ahr.py"
    sys.argv = [str(script), "M2-like macrophage", "tingting_ahr_m2"]
    runpy.run_path(str(script), run_name="__main__")
