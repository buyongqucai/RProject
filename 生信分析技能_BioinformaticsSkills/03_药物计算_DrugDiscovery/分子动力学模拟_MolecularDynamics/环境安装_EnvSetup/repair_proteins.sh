#!/usr/bin/env bash
# Fill missing heavy atoms (pdbfixer) then keep ATOM-only for pdb2gmx
set -euo pipefail
source ~/activate-md.sh
PY="$HOME/md-venv/bin/python3"
"$PY" -c "import pdbfixer" 2>/dev/null || uv pip install --python "$PY" pdbfixer openmm

repair_one() {
  local name="$1"
  local wd="$HOME/md_runs/$name"
  mkdir -p "$wd"
  cd "$wd"
  [[ -f protein.pdb ]] || {
    local src
    src=$(find /mnt/e/RProject -type d -name "$name" | head -1)
    cp -f "$src/protein.pdb" "$src"/cofactors_*.pdb "$wd/"
  }
  "$PY" <<'PY'
from pdbfixer import PDBFixer
from openmm.app import PDBFile
fixer = PDBFixer(filename="protein.pdb")
fixer.findMissingResidues()
# do not add whole missing loops at termini for MD box — only missing atoms in existing residues
fixer.missingResidues = {}
fixer.findNonstandardResidues()
fixer.replaceNonstandardResidues()
fixer.findMissingAtoms()
fixer.addMissingAtoms()
fixer.addMissingHydrogens(7.0)
with open("protein_fixed.pdb", "w") as fh:
    PDBFile.writeFile(fixer.topology, fixer.positions, fh, keepIds=True)
# ATOM-only, strip H for pdb2gmx -ignh
out = []
for line in open("protein_fixed.pdb"):
    if line.startswith("ATOM"):
        # drop hydrogens (element col 77-78 or name starts with H)
        name = line[12:16].strip()
        elem = line[76:78].strip() if len(line) >= 78 else ""
        if elem == "H" or (not elem and name.startswith("H")):
            continue
        out.append(line)
    elif line.startswith("TER") or line.startswith("END"):
        out.append(line)
open("protein.pdb", "w").write("".join(out) + ("\n" if out and not out[-1].endswith("\n") else ""))
print("repaired -> protein.pdb atoms", sum(1 for l in out if l.startswith("ATOM")))
PY
}

repair_one ADA_Adenosine_7RTG
repair_one MMP9_Tryptophan_4H3X
repair_one CYP1A1_Indole_4I8V
echo REPAIR_DONE
