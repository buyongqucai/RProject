#!/usr/bin/env bash
# Prep MMP9 workdir (protein repaired, ligand single-mol) — do not start MD yet
set -euo pipefail
source ~/activate-md.sh
name=MMP9_Tryptophan_4H3X
src=$(find /mnt/e/RProject -type d -name "$name" | head -1)
wd="$HOME/md_runs/$name"
mkdir -p "$wd"
# copy repaired protein from prior repair if present else from src + repair
if [[ -f "$wd/protein.pdb" ]]; then
  echo "protein already in $wd"
else
  cp -f "$src/protein.pdb" "$src"/cofactors_*.pdb "$wd/"
  bash /mnt/e/md_kit/repair_proteins.sh
fi
# ligand
bash /mnt/e/md_kit/fix_all_ligands.sh
cp -f "$wd/lig_h.mol2" "$wd/protein.pdb" "$src/" || true
ls -la "$wd/protein.pdb" "$wd/lig_h.mol2" "$wd"/cofactors_*.pdb
echo MMP9_PREP_OK
