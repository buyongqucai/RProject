#!/usr/bin/env bash
# Extract first @<TRIPOS>MOLECULE only; rebuild H; write lig_h.mol2 (LIG)
set -euo pipefail
source ~/activate-md.sh

extract_first_mol() {
  python3 - "$1" "$2" <<'PY'
import sys
from pathlib import Path
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
text = src.read_text(errors="replace")
parts = text.split("@<TRIPOS>MOLECULE")
# parts[0] may be empty/preamble; first mol is parts[1]
if len(parts) < 2:
    raise SystemExit(f"no MOLECULE in {src}")
mol = "@<TRIPOS>MOLECULE" + parts[1]
# if next content leaked — split already did
# ensure single molecule: stop at second marker if present in mol (shouldn't)
dst.write_text(mol if mol.endswith("\n") else mol + "\n")
print(f"{src.name}: molecules_in={len(parts)-1} -> wrote first only ({dst})")
PY
}

fix_one() {
  local name="$1"
  local src
  src=$(find /mnt/e/RProject -type d -name "$name" | head -1)
  local wd="$HOME/md_runs/$name"
  mkdir -p "$wd"
  cp -f "$src/protein.pdb" "$src"/cofactors_*.pdb "$wd/"
  extract_first_mol "$src/lig_h.mol2" "$wd/lig_raw.mol2"
  cd "$wd"
  obabel lig_raw.mol2 -O lig_noH.sdf -d
  obabel lig_noH.sdf -O lig_h.mol2 -h
  python3 <<'PY'
from pathlib import Path
import itertools, math
t = Path("lig_h.mol2").read_text().splitlines()
# keep only first molecule if obabel somehow multi
text = "\n".join(t)
chunks = text.split("@<TRIPOS>MOLECULE")
mol = "@<TRIPOS>MOLECULE" + chunks[1]
lines = mol.splitlines()
lines[1] = "LIG"
Path("lig_h.mol2").write_text("\n".join(lines) + "\n")
i = lines.index("@<TRIPOS>ATOM") + 1
atoms = []
while i < len(lines) and not lines[i].startswith("@"):
    p = lines[i].split()
    atoms.append((p[1], float(p[2]), float(p[3]), float(p[4])))
    i += 1
bad = [(math.dist(a[1:], b[1:]), a[0], b[0]) for a, b in itertools.combinations(atoms, 2) if math.dist(a[1:], b[1:]) < 0.5]
n_mol = Path("lig_h.mol2").read_text().count("@<TRIPOS>MOLECULE")
print(f"  natoms={len(atoms)} n_mol={n_mol} close<0.5={bad}")
PY
}

fix_one ADA_Adenosine_7RTG
fix_one MMP9_Tryptophan_4H3X
fix_one CYP1A1_Indole_4I8V
echo ALL_LIGANDS_FIXED
