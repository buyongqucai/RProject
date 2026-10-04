"""GenKI smoke for the current subtypes (default PEP).

Reduced trials/epochs/permutations. Only checks that the path works:
export -> HVG -> GRN -> small search -> fit -> 3 permutations -> tables.
Not the paper protocol. Outputs stay under <subtype>/GenKI/_烟测/.

Windows spawn note: keep all work under __main__ and import genki_formal as
a normal module so ProcessPoolExecutor can pickle search_one.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import genki_formal as g


def main() -> int:
    subtype = sys.argv[1] if len(sys.argv) >= 2 else "PEP"
    g.N_TRIALS = 2
    g.MAX_EPOCHS = 3
    g.MIN_EPOCHS = 1
    g.EARLY_STOP_PATIENCE = 2
    g.N_PERMUTATIONS = 3
    g.RUN_ID = f"smoke_{subtype.lower()}"

    smoke_dir = g.DESKTOP / "结果文件" / subtype / "GenKI" / "_烟测"

    completed = subprocess.run(
        [str(g.RSCRIPT), str(g.EXPORT_R), subtype],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if completed.returncode != 0:
        print("export failed: " + (completed.stderr[-2000:] or completed.stdout[-2000:]))
        return 1

    cap = g.load_cap()
    plan = cap.prepare("grn", bind_device=False)
    print(cap.format_plan(plan), flush=True)
    g.run_subtype(cap, subtype, int(plan["search"]["trials"]), out_dir=smoke_dir)
    print("SMOKE_DONE", subtype, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
