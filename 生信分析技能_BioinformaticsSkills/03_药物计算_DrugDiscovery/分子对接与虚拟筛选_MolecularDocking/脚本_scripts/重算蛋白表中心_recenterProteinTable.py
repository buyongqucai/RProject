# -*- coding: utf-8 -*-
"""Regenerate docking protein-table centers from a single co-crystal ligand.

Center = geometric mean of heavy atoms of one chosen organic HETATM residue
(resname+chain+resi). Never averages all HETATM in the file.
"""
from __future__ import annotations

import csv
import math
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

SKIP_RES = {
    "HOH", "WAT", "DOD", "NA", "CL", "MG", "ZN", "CA", "K", "MN", "FE", "CU", "CO",
    "NI", "CD", "HG", "SO4", "PO4", "GOL", "EDO", "PEG", "PG4", "PGE", "ACT", "ACE",
    "DMS", "DMSO", "EPE", "HEP", "TRS", "BME", "MPD", "IPA", "FMT", "NH2", "NO3",
    # crystallization / glycan / trivial
    "NAG", "NDG", "MAN", "BMA", "FUC", "GAL", "GLC", "SIA", "XYL", "FUL",
    "MES", "TRS", "EOH", "MOH", "BU1", "OCT", "MLA", "MLI", "CIT", "TLA", "TAR",
    "GLY", "ALA", "SER", "BTB", "CAC", "IMD",
}

# Prefer drug-like organic ligands over cofactors when both exist
LOW_PRIORITY = {"HEM", "HEA", "HEB", "HEC", "FAD", "FMN", "NAD", "NAP", "NDP", "ATP", "ADP", "GTP", "GDP", "GNP", "ANP", "SEP", "PTR", "TYS", "ALY"}


def choose_ref(ligs: dict) -> tuple[tuple[str, str, str], list[tuple[float, float, float]]] | None:
    if not ligs:
        return None

    def score(item):
        key, coords = item
        res = key[0]
        n = len(coords)
        # prefer drug-like size (~8–80 heavy atoms)
        size_pen = 0
        if n < 8:
            size_pen = 1000 - n
        elif n > 80:
            size_pen = n
        prio = 10 if res in LOW_PRIORITY else 0
        return (prio, size_pen, -n, res, key[1], key[2])

    ranked = sorted(ligs.items(), key=score)
    return ranked[0]


def find_lib() -> Path:
    for parent in Path("D:/").iterdir():
        if parent.is_dir() and "数据" in parent.name:
            for child in parent.iterdir():
                if child.is_dir() and "对接数据库" in child.name:
                    return child
    raise SystemExit("lib not found")


def protein_table_path(lib: Path) -> Path:
    hits = [
        p
        for p in lib.glob("*.csv")
        if "蛋白表" in p.name and "扩展" not in p.name and ".bak" not in p.name.lower()
    ]
    # prefer exact stem
    exact = [p for p in hits if p.name.startswith("分子对接_蛋白表") and p.suffix == ".csv"]
    if exact:
        # shortest name = primary table
        return sorted(exact, key=lambda p: len(p.name))[0]
    if not hits:
        raise SystemExit("protein table not found")
    return sorted(hits, key=lambda p: len(p.name))[0]


def read_csv_auto(path: Path) -> tuple[list[dict], str]:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "gbk", "gb18030", "utf-8"):
        try:
            text = raw.decode(enc)
            rows = list(csv.DictReader(text.splitlines()))
            return rows, enc
        except Exception:
            continue
    raise SystemExit(f"cannot decode {path}")


def pdb_path(lib: Path, pdb: str) -> Path | None:
    pdb = pdb.lower().strip()
    test = lib / "test"
    root = test if test.is_dir() else lib
    for d in (root / "big", root / "big_clean", root):
        p = d / f"{pdb}.pdb"
        if p.is_file():
            return p
    hits = list(lib.rglob(f"{pdb}.pdb"))
    return hits[0] if hits else None


def collect_ligands(pdb_file: Path) -> dict[tuple[str, str, str], list[tuple[float, float, float]]]:
    """key=(resname, chain, resi) -> list of heavy-atom coords."""
    ligs: dict[tuple[str, str, str], list[tuple[float, float, float]]] = defaultdict(list)
    for ln in pdb_file.read_text(encoding="utf-8", errors="replace").splitlines():
        if not ln.startswith("HETATM"):
            continue
        res = ln[17:20].strip().upper()
        if res in SKIP_RES:
            continue
        name = ln[12:16].strip()
        if name.startswith("H"):
            continue
        chain = (ln[21] if len(ln) > 21 else " ").strip() or "_"
        resi = ln[22:26].strip()
        try:
            x, y, z = float(ln[30:38]), float(ln[38:46]), float(ln[46:54])
        except ValueError:
            continue
        ligs[(res, chain, resi)].append((x, y, z))
    return ligs


def centroid(coords: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    n = len(coords)
    return (
        sum(c[0] for c in coords) / n,
        sum(c[1] for c in coords) / n,
        sum(c[2] for c in coords) / n,
    )


def main() -> None:
    lib = find_lib()
    table = protein_table_path(lib)
    print(f"using table: {table}")
    rows, enc = read_csv_auto(table)
    keys = list(rows[0].keys())
    # expected: entry, gene, pdb, x, y, z — keep original headers
    entry_k, gene_k, pdb_k = keys[0], keys[1], keys[2]
    x_k, y_k, z_k = keys[3], keys[4], keys[5]

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = table.with_name(table.stem + f".bak_before_recenter_{stamp}" + table.suffix)
    shutil.copy2(table, bak)
    print(f"backup -> {bak}")

    out_fields = keys + [
        "ref_ligand",
        "ref_n_heavy",
        "center_method",
        "center_note",
        "old_x",
        "old_y",
        "old_z",
        "delta_old_new_A",
    ]
    # dedupe fields if re-run
    seen = set()
    fields = []
    for f in out_fields:
        if f not in seen:
            fields.append(f)
            seen.add(f)

    new_rows = []
    ok = fail = skip = 0
    for r in rows:
        pdb = (r.get(pdb_k) or "").strip().lower()
        gene = (r.get(gene_k) or "").strip()
        old_x, old_y, old_z = r.get(x_k, ""), r.get(y_k, ""), r.get(z_k, "")
        nr = dict(r)
        nr["old_x"], nr["old_y"], nr["old_z"] = old_x, old_y, old_z
        if not pdb or pdb.startswith("af-") or len(pdb) != 4:
            nr["center_method"] = "SKIP_non_pdb"
            nr["center_note"] = "not a 4-letter PDB id"
            nr["ref_ligand"] = ""
            nr["ref_n_heavy"] = ""
            nr["delta_old_new_A"] = ""
            skip += 1
            new_rows.append(nr)
            continue
        path = pdb_path(lib, pdb)
        if path is None:
            nr["center_method"] = "FAIL_no_pdb_file"
            nr["center_note"] = "pdb file missing in lib"
            nr["ref_ligand"] = ""
            nr["ref_n_heavy"] = ""
            nr["delta_old_new_A"] = ""
            fail += 1
            new_rows.append(nr)
            continue
        ligs = collect_ligands(path)
        chosen = choose_ref(ligs)
        if chosen is None:
            nr[x_k] = nr[y_k] = nr[z_k] = ""
            nr["center_method"] = "FAIL_no_organic_ligand"
            nr["center_note"] = "no non-solvent organic HETATM; do not use old center"
            nr["ref_ligand"] = ""
            nr["ref_n_heavy"] = "0"
            nr["delta_old_new_A"] = ""
            fail += 1
            new_rows.append(nr)
            print(f"[FAIL] {gene} {pdb}: no organic co-ligand")
            continue
        key, coords = chosen
        cx, cy, cz = centroid(coords)
        nr[x_k] = f"{cx:.3f}"
        nr[y_k] = f"{cy:.3f}"
        nr[z_k] = f"{cz:.3f}"
        nr["ref_ligand"] = f"{key[0]}:{key[1]}:{key[2]}"
        nr["ref_n_heavy"] = str(len(coords))
        nr["center_method"] = "cocrystal_single_ligand_COM"
        nr["center_note"] = f"heavy-atom centroid of {nr['ref_ligand']} from {path.name}"
        try:
            ox, oy, oz = float(old_x), float(old_y), float(old_z)
            d = math.sqrt((cx - ox) ** 2 + (cy - oy) ** 2 + (cz - oz) ** 2)
            nr["delta_old_new_A"] = f"{d:.3f}"
        except Exception:
            nr["delta_old_new_A"] = ""
        ok += 1
        new_rows.append(nr)
        print(f"[OK] {gene} {pdb} -> {nr['ref_ligand']} center=({nr[x_k]},{nr[y_k]},{nr[z_k]}) d_old={nr['delta_old_new_A']}")

    # write utf-8-sig for transparency; also keep gbk copy if original was gbk
    out_utf = table
    with out_utf.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(new_rows)
    print(f"wrote {out_utf} enc=utf-8-sig  ok={ok} fail={fail} skip={skip}")

    # report for our 11 targets
    focus = {"TP53", "AKT1", "ESR1", "JUN", "TNF", "PRKACA", "MAPK3", "EGFR", "MAPK1", "PIK3CA", "FGA"}
    print("\n=== focus genes ===")
    for r in new_rows:
        g = (r.get(gene_k) or "").upper()
        if g in focus:
            print(
                g,
                r.get(pdb_k),
                r.get(x_k),
                r.get(y_k),
                r.get(z_k),
                r.get("ref_ligand"),
                r.get("center_method"),
                "d=",
                r.get("delta_old_new_A"),
            )


if __name__ == "__main__":
    main()
