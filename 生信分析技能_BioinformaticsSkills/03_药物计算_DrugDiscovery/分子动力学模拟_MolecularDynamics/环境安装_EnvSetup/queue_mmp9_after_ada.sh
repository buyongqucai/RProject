#!/usr/bin/env bash
# Wait until ADA production finishes (md.gro or DONE in log), then start MMP9 100 ns
set -euo pipefail
source ~/activate-md.sh
ADA_LOG="$HOME/md_runs/logs/ADA_Adenosine_7RTG.log"
ADA_WD="$HOME/md_runs/ADA_Adenosine_7RTG"
SCRIPT=$(find /mnt/e/RProject -name '运行复合物MD_runComplexMd.sh' 2>/dev/null | head -1)
TOP3=$(find /mnt/e/RProject -type d -name '课题top3输入' 2>/dev/null | head -1)

echo "[queue] waiting for ADA DONE..."
while true; do
  if grep -q 'DONE:' "$ADA_LOG" 2>/dev/null; then
    echo "[queue] ADA DONE"
    break
  fi
  if grep -q 'ABORT' "$ADA_LOG" 2>/dev/null; then
    echo "[queue] ADA ABORT — not starting MMP9"; exit 2
  fi
  sleep 120
done

name=MMP9_Tryptophan_4H3X
wd="$HOME/md_runs/$name"
src="$TOP3/$name"
mkdir -p "$wd"
# ensure repaired protein + fixed ligand
if [[ ! -f "$wd/protein.pdb" ]] || [[ ! -f "$wd/lig_h.mol2" ]]; then
  bash /mnt/e/md_kit/fix_all_ligands.sh
  bash /mnt/e/md_kit/repair_proteins.sh
fi
[[ -f "$wd/cofactors_ZN_CA.pdb" ]] || cp -f "$src"/cofactors_*.pdb "$wd/"
cd "$wd"
rm -rf ligand.acpype
find . -maxdepth 1 -type f \
  ! -name 'protein.pdb' ! -name 'lig_h.mol2' ! -name 'lig_raw.mol2' \
  ! -name 'cofactors_ZN_CA.pdb' ! -name 'protein_fixed.pdb' ! -name 'lig_noH.sdf' \
  -delete 2>/dev/null || true
export LIGAND_RES=LIG NET_CHARGE=0
export NS=100 CHUNK_NS=1 MONITOR=1 CHECK_MMGBSA=0
export COFACTORS_PDB="$wd/cofactors_ZN_CA.pdb"
nohup bash "$SCRIPT" "$wd" "$wd/protein.pdb" "$wd/lig_h.mol2" \
  > "$HOME/md_runs/logs/${name}.log" 2>&1 &
echo "[queue] MMP9 started PID=$! log=$HOME/md_runs/logs/${name}.log"
