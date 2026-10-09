#!/usr/bin/env bash
# After MMP9 production exits, start mouse ADA A2 (1ADD -> adenosine). Do not resume 7RTG.
set -euo pipefail
source "$HOME/activate-md.sh"
mkdir -p "$HOME/md_runs/logs"
echo "[queue] $(date -Is) waiting for MMP9_Tryptophan_4H3X to exit"
while pgrep -f "md_runs/MMP9_Tryptophan_4H3X" >/dev/null; do
  sleep 120
done
echo "[queue] $(date -Is) MMP9 process gone"

name=ADA_Adenosine_1ADD
src=$(find /mnt/e/RProject -type d -name "$name" | head -1)
wd="$HOME/md_runs/$name"
mkdir -p "$wd"
cp -f "$src/protein.pdb" "$src/lig_h.mol2" "$src/cofactors_ZN.pdb" "$wd/"
cd "$wd"
PY="$HOME/md-venv/bin/python3"
"$PY" -c "import pdbfixer" 2>/dev/null || uv pip install --python "$PY" pdbfixer openmm
"$PY" <<'PY'
from pdbfixer import PDBFixer
from openmm.app import PDBFile
fixer = PDBFixer(filename="protein.pdb")
fixer.findMissingResidues()
fixer.missingResidues = {}
fixer.findNonstandardResidues()
fixer.replaceNonstandardResidues()
fixer.findMissingAtoms()
fixer.addMissingAtoms()
fixer.addMissingHydrogens(7.0)
with open("protein_fixed.pdb", "w") as fh:
    PDBFile.writeFile(fixer.topology, fixer.positions, fh, keepIds=True)
out = []
for line in open("protein_fixed.pdb"):
    if not line.startswith("ATOM"):
        continue
    name = line[12:16].strip()
    elem = line[76:78].strip() if len(line) >= 78 else ""
    if elem == "H" or (not elem and name.startswith("H")):
        continue
    out.append(line if line.endswith("\n") else line + "\n")
open("protein.pdb", "w").writelines(out)
print("repaired protein atoms", len(out))
PY

SCRIPT=$(find /mnt/e/RProject -name '运行复合物MD_runComplexMd.sh' | head -1)
export LIGAND_RES=LIG NET_CHARGE=0 NS=100 CHUNK_NS=1 MONITOR=1 CHECK_MMGBSA=0
export COFACTORS_PDB="$wd/cofactors_ZN.pdb"
nohup bash "$SCRIPT" "$wd" "$wd/protein.pdb" "$wd/lig_h.mol2" \
  > "$HOME/md_runs/logs/${name}.log" 2>&1 &
echo "[queue] $(date -Is) ADA_Adenosine_1ADD PID=$!"
