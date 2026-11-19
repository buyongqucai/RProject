"""Split HDOCK complex PDB into ST (receptor chains) and PT (ligand chains)."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def split_model(src: Path, st_out: Path, pt_out: Path, st_chains: set[str], pt_chains: set[str]) -> dict:
    st_lines: list[str] = []
    pt_lines: list[str] = []
    meta: dict[str, str] = {}
    n_st = n_pt = 0
    with src.open(encoding="latin-1", errors="replace") as f:
        for L in f:
            if L.startswith("REMARK"):
                m = re.match(r"REMARK\s+(\w+):\s*(.*)$", L.strip())
                if m:
                    meta[m.group(1).lower()] = m.group(2).strip()
            if not L.startswith(("ATOM", "HETATM")):
                continue
            ch = L[21]
            if ch in st_chains:
                st_lines.append(L)
                n_st += 1
            elif ch in pt_chains:
                pt_lines.append(L)
                n_pt += 1
    st_out.parent.mkdir(parents=True, exist_ok=True)
    st_out.write_text("".join(st_lines) + "END\n", encoding="utf-8")
    pt_out.write_text("".join(pt_lines) + "END\n", encoding="utf-8")
    return {"n_st": n_st, "n_pt": n_pt, **meta}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--st-out", type=Path, required=True)
    ap.add_argument("--pt-out", type=Path, required=True)
    ap.add_argument("--st-chains", default="C")
    ap.add_argument("--pt-chains", default="A,B")
    args = ap.parse_args()
    info = split_model(
        args.model,
        args.st_out,
        args.pt_out,
        set(args.st_chains.replace(",", "")),
        set(args.pt_chains.replace(",", "")),
    )
    print(info)
    print("wrote", args.st_out, args.pt_out)


if __name__ == "__main__":
    main()
