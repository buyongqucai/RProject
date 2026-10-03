"""Launch the formal GenKI run. Progress is written next to the desktop results."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from genki_formal import main

if __name__ == "__main__":
    raise SystemExit(main())
