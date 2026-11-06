# -*- coding: utf-8 -*-
"""Summarize ATOM/HETATM per chain for PP docking chain_survey (read-only)."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def summarize(path: Path) -> dict:
    atoms: dict[str, int] = defaultdict(int)
    residues: dict[str, set] = defaultdict(set)
    het: dict[str, Counter] = defaultdict(Counter)
    title: list[str] = []
    exp: list[str] = []
    for L in path.open(encoding="ascii", errors="ignore"):
        if L.startswith("TITLE"):
            title.append(L[10:].strip())
        elif L.startswith("EXPDTA"):
            exp.append(L[10:].strip())
        elif L.startswith(("ATOM", "HETATM")) and len(L) >= 54:
            ch = L[21]
            rn = L[17:20].strip()
            ri = L[22:26]
            if L.startswith("ATOM"):
                atoms[ch] += 1
                residues[ch].add((ri, rn))
            else:
                het[ch][rn] += 1
    chains = sorted(set(atoms) | set(het))
    rows = []
    for ch in chains:
        rows.append(
            {
                "chain": ch,
                "n_atom": atoms.get(ch, 0),
                "n_res": len(residues.get(ch, ())),
                "het": dict(het.get(ch, {})),
            }
        )
    return {
        "file": str(path),
        "title": " ".join(title).strip(),
        "expdta": " ".join(exp).strip(),
        "chains": rows,
        "n_chains": len(chains),
        "bytes": path.stat().st_size,
        "MB": round(path.stat().st_size / (1024 * 1024), 3),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdb", type=Path, nargs="+")
    ap.add_argument("--json", type=Path, default=None, help="optional JSON out")
    args = ap.parse_args()
    reports = [summarize(p) for p in args.pdb]
    for r in reports:
        print(f"==== {r['file']}  ({r['MB']} MB)")
        print(f"TITLE  {r['title'][:160]}")
        print(f"EXPDTA {r['expdta'][:120]}")
        print(f"{'chain':>5} {'n_res':>6} {'n_atom':>8}  HET")
        for row in r["chains"]:
            het_s = ",".join(f"{k}:{v}" for k, v in sorted(row["het"].items())) or "-"
            print(f"{row['chain']:>5} {row['n_res']:6d} {row['n_atom']:8d}  {het_s}")
        print()
    if args.json:
        args.json.write_text(json.dumps(reports, indent=2, ensure_ascii=False), encoding="utf-8")
        print("wrote", args.json)


if __name__ == "__main__":
    main()
