# -*- coding: utf-8 -*-
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "脚本_scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
