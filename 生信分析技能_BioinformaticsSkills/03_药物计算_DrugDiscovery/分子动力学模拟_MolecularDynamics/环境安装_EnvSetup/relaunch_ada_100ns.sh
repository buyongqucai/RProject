#!/usr/bin/env bash
set -euo pipefail
source ~/activate-md.sh
# stop current ADA mdrun if any
pkill -f 'gmx mdrun.*deffnm md' 2>/dev/null || true
sleep 2
SCRIPT=$(find /mnt/e/RProject -name '运行复合物MD_runComplexMd.sh' 2>/dev/null | head -1)
WD="$HOME/md_runs/ADA_Adenosine_7RTG"
cd "$WD"
rm -rf ligand.acpype .acpype_tmp_ligand
find . -maxdepth 1 -type f \
  ! -name 'protein.pdb' ! -name 'lig_h.mol2' ! -name 'lig_raw.mol2' \
  ! -name 'cofactors_ZN.pdb' ! -name 'protein_fixed.pdb' ! -name 'lig_noH.sdf' \
  -delete
export LIGAND_RES=LIG NET_CHARGE=0
export NS=100 CHUNK_NS=1 MONITOR=1 CHECK_MMGBSA=0
export COFACTORS_PDB="$WD/cofactors_ZN.pdb"
nohup bash "$SCRIPT" "$WD" "$WD/protein.pdb" "$WD/lig_h.mol2" \
  > "$HOME/md_runs/logs/ADA_Adenosine_7RTG.log" 2>&1 &
echo "RESTARTED ADA PID=$!"
sleep 45
grep -E 'residue ->|index:|FAIL|ABORT|生产 MD|mdrun chunk' "$HOME/md_runs/logs/ADA_Adenosine_7RTG.log" | tail -20
# verify LIG survives genion
if [[ -f solv_ions.gro ]]; then
  python3 - <<'PY'
lines=open("solv_ions.gro").read().splitlines(); n=int(lines[1]); atoms=lines[2:2+n]
print("solv_ions LIG", sum(1 for a in atoms if a[5:10].strip()=="LIG"))
print("solv_ions A1", sum(1 for a in atoms if a[5:10].strip()=="A1"))
PY
fi
