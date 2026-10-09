#!/usr/bin/env bash
set -euo pipefail
source ~/activate-md.sh
SCRIPT=$(find /mnt/e/RProject -name '运行复合物MD_runComplexMd.sh' 2>/dev/null | head -1)
BASE=$(find /mnt/e/RProject -type d -name ADA_Adenosine_7RTG | head -1)
WD="$HOME/md_runs/ADA_Adenosine_7RTG"
cd "$WD"
# persist fixed ligand into课题输入
cp -f lig_h.mol2 "$BASE/lig_h.mol2"
# wipe MD intermediates only
rm -rf ligand.acpype #.acpype_tmp* 2>/dev/null || true
find . -maxdepth 1 -type f ! -name 'protein.pdb' ! -name 'lig_h.mol2' ! -name 'lig_raw.mol2' \
  ! -name 'cofactors_*.pdb' ! -name 'lig_noH.sdf' -delete 2>/dev/null || true
rm -rf ligand.acpype .acpype_tmp_ligand 2>/dev/null || true
export LIGAND_RES=LIG NET_CHARGE=0 NS=0.02 CHUNK_NS=0.02 MONITOR=0
export COFACTORS_PDB="$WD/cofactors_ZN.pdb"
bash "$SCRIPT" "$WD" "$WD/protein.pdb" "$WD/lig_h.mol2" 2>&1 | tee run_smoke.log
echo SMOKE_EXIT=$?
echo '--- metal_counts ---'; cat metal_counts.txt 2>/dev/null || true
ls -la em.gro nvt.gro npt.gro md.gro 2>&1
