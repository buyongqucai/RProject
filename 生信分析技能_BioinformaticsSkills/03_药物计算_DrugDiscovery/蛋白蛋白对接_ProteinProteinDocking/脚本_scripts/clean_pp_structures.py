# -*- coding: utf-8 -*-
"""Clean PDB for protein-protein docking (SOP §3)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# Catalytic / cofactor residue names (extend as needed)
KEEP_HET_DEFAULT = {
    "MG",
    "MN",
    "ZN",
    "FE",
    "CU",
    "CO",
    "NI",
    "CA",  # structural/catalytic Ca; review if crystal-only
    "FAD",
    "FMN",
    "NAD",
    "NAP",
    "NDP",
    "ADP",
    "ATP",
    "GTP",
    "GDP",
    "HEM",
    "HEA",
    "SF4",
    "FES",
    "F3S",
    "PLP",
    "TPP",
    "COA",
    "ACO",
    "BTN",
}

DROP_HET_DEFAULT = {
    "HOH",
    "WAT",
    "DOD",
    "SO4",
    "PO4",
    "GOL",
    "EDO",
    "PEG",
    "PGE",
    "PG4",
    "BTB",
    "ACT",
    "DMS",
    "BME",
    "CL",
    "NA",
    "K",
    "BR",
    "IOD",
}


def is_hydrogen(line: str) -> bool:
    if len(line) >= 78 and line[76:78].strip().upper() == "H":
        return True
    aname = line[12:16].strip()
    if aname.startswith("H"):
        return True
    if len(aname) >= 2 and aname[0].isdigit() and aname[1] == "H":
        return True
    return False


def clean_one(
    src: Path,
    dst: Path,
    chains: list[str],
    *,
    het_policy: str = "keep_cofactor",
    rename: dict[str, str] | None = None,
    keep_het: set[str] | None = None,
    drop_het: set[str] | None = None,
) -> dict:
    rename = rename or {}
    keep_het = set(keep_het or KEEP_HET_DEFAULT)
    drop_het = set(drop_het or DROP_HET_DEFAULT)
    keep_ch = set(chains)
    lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
    out: list[str] = []
    for L in lines:
        if L.startswith(("HEADER", "TITLE", "COMPND", "SOURCE", "EXPDTA", "CRYST1")):
            out.append(L.rstrip())
    out.append(
        f"REMARK   1 PP-DOCK CLEAN het_policy={het_policy} chains={','.join(chains)}"
    )
    n_atom = 0
    kept_het: dict[str, int] = {}
    dropped_het: dict[str, int] = {}
    for L in lines:
        if L.startswith("ATOM"):
            if len(L) < 54:
                continue
            ch = L[21]
            if ch not in keep_ch:
                continue
            if L[16] not in (" ", "A"):
                continue
            if is_hydrogen(L):
                continue
            new_ch = rename.get(ch, ch)
            if new_ch != ch:
                L = L[:21] + new_ch + L[22:]
            out.append(L.rstrip())
            n_atom += 1
        elif L.startswith("HETATM"):
            if het_policy == "protein_only":
                if len(L) >= 20:
                    rn = L[17:20].strip()
                    dropped_het[rn] = dropped_het.get(rn, 0) + 1
                continue
            if len(L) < 54:
                continue
            ch = L[21]
            if ch not in keep_ch:
                continue
            rn = L[17:20].strip()
            if rn in drop_het or (rn not in keep_het):
                dropped_het[rn] = dropped_het.get(rn, 0) + 1
                continue
            if L[16] not in (" ", "A"):
                continue
            if is_hydrogen(L):
                continue
            new_ch = rename.get(ch, ch)
            if new_ch != ch:
                L = L[:21] + new_ch + L[22:]
            out.append(L.rstrip())
            kept_het[rn] = kept_het.get(rn, 0) + 1
    out.append("END")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(out) + "\n", encoding="ascii", errors="ignore")
    report = {
        "src": str(src),
        "dst": str(dst),
        "chains": chains,
        "rename": rename,
        "het_policy": het_policy,
        "n_atom": n_atom,
        "het_kept": kept_het,
        "het_dropped": dropped_het,
        "bytes": dst.stat().st_size,
    }
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src", type=Path)
    ap.add_argument("dst", type=Path)
    ap.add_argument("--chains", required=True, help="comma-separated chain IDs")
    ap.add_argument("--rename", default="", help="e.g. C:A,A:B")
    ap.add_argument(
        "--het-policy",
        choices=("keep_cofactor", "protein_only"),
        default="keep_cofactor",
    )
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()
    rename: dict[str, str] = {}
    if args.rename:
        for part in args.rename.split(","):
            a, b = part.split(":")
            rename[a.strip()] = b.strip()
    report = clean_one(
        args.src,
        args.dst,
        [c.strip() for c in args.chains.split(",") if c.strip()],
        het_policy=args.het_policy,
        rename=rename,
    )
    rep_path = args.report or args.dst.with_suffix(".clean_report.json")
    rep_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
