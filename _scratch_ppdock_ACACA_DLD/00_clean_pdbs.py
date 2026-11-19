# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parent


def is_hydrogen(line: str) -> bool:
    if len(line) >= 78:
        elem = line[76:78].strip().upper()
        if elem == "H":
            return True
    aname = line[12:16].strip()
    # PDB atom name: H*, or digit+H*
    if aname.startswith("H"):
        return True
    if len(aname) >= 2 and aname[0].isdigit() and aname[1] == "H":
        return True
    return False


def clean_pdb(src: Path, dst: Path, keep_chains: list[str], rename_map: dict[str, str] | None = None) -> dict:
    lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
    keep = set(keep_chains)
    rename_map = rename_map or {}
    out: list[str] = []
    for L in lines:
        if L.startswith(("HEADER", "TITLE", "COMPND", "SOURCE", "EXPDTA", "CRYST1")):
            out.append(L.rstrip())
        elif L.startswith("REMARK   2") or L.startswith("REMARK  2 "):
            out.append(L.rstrip())
    out.append(
        f"REMARK   1 CLEANED FOR PP-DOCKING; ATOM only; no H; chains={','.join(keep_chains)}"
    )
    n_atom = 0
    residues = set()
    for L in lines:
        if not L.startswith("ATOM"):
            continue
        if len(L) < 54:
            continue
        ch = L[21]
        if ch not in keep:
            continue
        alt = L[16]
        if alt not in (" ", "A"):
            continue
        if is_hydrogen(L):
            continue
        new_ch = rename_map.get(ch, ch)
        if new_ch != ch:
            L = L[:21] + new_ch + L[22:]
        out.append(L.rstrip())
        n_atom += 1
        residues.add((new_ch, L[22:26], L[17:20]))
    out.append("END")
    dst.write_text("\n".join(out) + "\n", encoding="ascii", errors="ignore")
    return {
        "file": dst.name,
        "atoms": n_atom,
        "residues": len(residues),
        "bytes": dst.stat().st_size,
    }


def main() -> None:
    acaca = Path(r"C:\Users\10540\Downloads\ACACA-6G2D.pdb")
    dld = Path(r"C:\Users\10540\Downloads\DLD-6I4Q.pdb")
    reports = []
    # ACACA: chain C = largest protomer (~2121 res); rename to A
    reports.append(
        clean_pdb(
            acaca,
            OUT / "ACACA_6G2D_chainC_clean.pdb",
            ["C"],
            {"C": "A"},
        )
    )
    # DLD monomer A -> chain B (partner)
    reports.append(
        clean_pdb(
            dld,
            OUT / "DLD_6I4Q_chainA_clean.pdb",
            ["A"],
            {"A": "B"},
        )
    )
    reports.append(clean_pdb(dld, OUT / "DLD_6I4Q_dimerAB_clean.pdb", ["A", "B"]))
    for r in reports:
        print(
            f"{r['file']}: atoms={r['atoms']} residues={r['residues']} "
            f"KB={r['bytes']/1024:.1f}"
        )


if __name__ == "__main__":
    main()
