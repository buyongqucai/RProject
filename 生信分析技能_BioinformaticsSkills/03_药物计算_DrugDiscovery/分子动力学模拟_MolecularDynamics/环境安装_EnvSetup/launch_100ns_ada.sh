#!/usr/bin/env bash
# Fresh 100 ns ADA after LIG residue-name fix in runComplexMd.sh
set -euo pipefail
source ~/activate-md.sh
SCRIPT=$(find /mnt/e/RProject -name '运行复合物MD_runComplexMd.sh' 2>/dev/null | head -1)
BASE=$(find /mnt/e/RProject -type d -name ADA_Adenosine_7RTG | head -1)
WD="$HOME/md_runs/ADA_Adenosine_7RTG"
mkdir -p "$HOME/md_runs/logs" "$WD"
cd "$WD"
# keep repaired protein + fixed single-mol ligand + Zn
test -f protein.pdb && test -f lig_h.mol2 && test -f cofactors_ZN.pdb
# wipe MD products for clean rebuild (keep inputs)
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
echo "ADA_100ns PID=$!"
echo "log=$HOME/md_runs/logs/ADA_Adenosine_7RTG.log"
sleep 2
tail -20 "$HOME/md_runs/logs/ADA_Adenosine_7RTG.log" || true
