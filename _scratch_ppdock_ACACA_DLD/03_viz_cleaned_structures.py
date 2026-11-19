# -*- coding: utf-8 -*-
"""PyMOL figures for cleaned monomers (pre-docking). Not a docking pose."""
from __future__ import annotations

from pathlib import Path
import subprocess
import textwrap

OUT = Path(__file__).resolve().parent
PYMOL_PY = Path(r"E:\pymol\python.exe")
if not PYMOL_PY.exists():
    PYMOL_PY = Path(r"E:\pymol\Scripts\python.exe")

PML = OUT / "_render_clean.pml"
PML.write_text(
    textwrap.dedent(
        f"""
        reinitialize
        bg_color white
        set ray_opaque_background, on
        set antialias, 2
        set ray_shadows, 0
        set cartoon_fancy_helices, 1

        load {OUT.as_posix()}/ACACA_6G2D_chainC_clean.pdb, ACACA
        load {OUT.as_posix()}/DLD_6I4Q_chainA_clean.pdb, DLD

        hide everything
        show cartoon, ACACA or DLD
        color marine, ACACA
        color tv_orange, DLD
        util.cnc ACACA or DLD

        # place DLD to the right of ACACA for inspection (NOT a docking result)
        center ACACA
        translate [180,0,0], DLD

        orient ACACA or DLD
        zoom ACACA or DLD, buffer=20

        png {OUT.as_posix()}/fig01_cleaned_ACACA_DLD_side_by_side.png, width=1800, height=1200, dpi=300, ray=1

        disable DLD
        orient ACACA
        zoom ACACA, buffer=8
        png {OUT.as_posix()}/fig02_ACACA_chainC_clean.png, width=1400, height=1200, dpi=300, ray=1

        enable DLD
        disable ACACA
        orient DLD
        zoom DLD, buffer=8
        png {OUT.as_posix()}/fig03_DLD_chainA_clean.png, width=1400, height=1200, dpi=300, ray=1

        save {OUT.as_posix()}/cleaned_ACACA_DLD_inspection.pse
        quit
        """
    ).strip()
    + "\n",
    encoding="utf-8",
)


def main() -> None:
    py = str(PYMOL_PY if PYMOL_PY.exists() else "python")
    cmd = [py, "-m", "pymol", "-cq", str(PML)]
    print("running", cmd)
    subprocess.check_call(cmd)
    for p in sorted(OUT.glob("fig*.png")):
        print("wrote", p.name, p.stat().st_size)


if __name__ == "__main__":
    main()
