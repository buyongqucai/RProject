#!/usr/bin/env bash
# Resume ADA 100 ns after false-positive monitor abort (1 ns already done)
set -euo pipefail
source ~/activate-md.sh
SCRIPT=$(find /mnt/e/RProject -name '运行复合物MD_runComplexMd.sh' 2>/dev/null | head -1)
WD="$HOME/md_runs/ADA_Adenosine_7RTG"
cd "$WD"
rm -f monitor/ABORT_REASON.txt
# keep md.cpt / md.log / md.xtc — script will -cpi continue
export LIGAND_RES=LIG NET_CHARGE=0
export NS=100 CHUNK_NS=1 MONITOR=1 CHECK_MMGBSA=0
export COFACTORS_PDB="$WD/cofactors_ZN.pdb"
nohup bash "$SCRIPT" "$WD" "$WD/protein.pdb" "$WD/lig_h.mol2" \
  > "$HOME/md_runs/logs/ADA_Adenosine_7RTG.log" 2>&1 &
echo "RESUME ADA PID=$!"
# re-queue MMP9
pkill -f queue_mmp9_after_ada 2>/dev/null || true
nohup bash /mnt/e/md_kit/queue_mmp9_after_ada.sh > "$HOME/md_runs/logs/queue_mmp9.log" 2>&1 &
echo "QUEUE MMP9 PID=$!"
sleep 8
tail -15 "$HOME/md_runs/logs/ADA_Adenosine_7RTG.log"
# show ns done
awk '/^[[:space:]]*[0-9]+[[:space:]]+[0-9.]+/{t=$2} END{if(t!="") printf "md.log last time: %.3f ns\n", t/1000}' md.log
