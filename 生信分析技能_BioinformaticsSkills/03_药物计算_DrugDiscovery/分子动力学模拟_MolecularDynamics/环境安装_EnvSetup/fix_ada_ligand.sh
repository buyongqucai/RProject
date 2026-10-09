#!/usr/bin/env bash
set -euo pipefail
source ~/activate-md.sh
BASE=$(find /mnt/e/RProject -type d -name ADA_Adenosine_7RTG | head -1)
WD="$HOME/md_runs/ADA_Adenosine_7RTG"
mkdir -p "$WD"
cp -f "$BASE/protein.pdb" "$BASE/lig_h.mol2" "$BASE"/cofactors_*.pdb "$WD/"
cd "$WD"
echo "BASE=$BASE"
ls -la lig_h.mol2 protein.pdb

python3 <<'PY'
from pathlib import Path
import itertools, math
lines = Path("lig_h.mol2").read_text().splitlines()
i = lines.index("@<TRIPOS>ATOM") + 1
atoms = []
while i < len(lines) and not lines[i].startswith("@"):
    p = lines[i].split()
    atoms.append((p[0], p[1], float(p[2]), float(p[3]), float(p[4])))
    i += 1
print("natoms", len(atoms))
for a, b in itertools.combinations(atoms, 2):
    d = math.dist(a[2:], b[2:])
    if d < 0.8:
        print(f"{d:.3f} {a[1]}({a[0]})-{b[1]}({b[0]})")
PY

# 只删氢重加，不 minimize，保留对接重原子坐标
obabel lig_h.mol2 -O lig_noH.sdf -d
obabel lig_noH.sdf -O lig_h_new.mol2 -h
# force residue name LIG (line 2 of mol2)
python3 <<'PY'
from pathlib import Path
import itertools, math
p = Path("lig_h_new.mol2")
t = p.read_text().splitlines()
t[1] = "LIG"
p.write_text("\n".join(t) + "\n")
lines = t
i = lines.index("@<TRIPOS>ATOM") + 1
atoms = []
while i < len(lines) and not lines[i].startswith("@"):
    p_ = lines[i].split()
    atoms.append((p_[1], float(p_[2]), float(p_[3]), float(p_[4])))
    i += 1
bad = []
for a, b in itertools.combinations(atoms, 2):
    d = math.dist(a[1:], b[1:])
    if d < 0.5:
        bad.append((d, a[0], b[0]))
print("fixed natoms", len(atoms), "close<0.5", bad)
PY
cp -f lig_h_new.mol2 lig_h.mol2
echo "ligand fixed OK"
