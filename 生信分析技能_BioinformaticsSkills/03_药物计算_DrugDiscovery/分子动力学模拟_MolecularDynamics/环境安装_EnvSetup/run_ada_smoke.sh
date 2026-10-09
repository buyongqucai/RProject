#!/usr/bin/env bash
set -euo pipefail
source ~/activate-md.sh
SCRIPT=$(find /mnt/e/RProject -name '运行复合物MD_runComplexMd.sh' 2>/dev/null | head -1)
BASE=$(find /mnt/e/RProject -type d -name 'ADA_Adenosine_7RTG' 2>/dev/null | head -1)
echo SCRIPT="$SCRIPT"
echo BASE="$BASE"
test -f "$SCRIPT"
test -d "$BASE"
OUT="$HOME/md_runs"
mkdir -p "$OUT"
WORKDIR="$OUT/ADA_Adenosine_7RTG"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"
cp "$BASE/protein.pdb" "$BASE/lig_h.mol2" "$BASE"/cofactors_*.pdb "$WORKDIR/"
cd "$WORKDIR"
export LIGAND_RES=LIG NET_CHARGE=0 NS=0.02 CHUNK_NS=0.02 MONITOR=0
export COFACTORS_PDB="$WORKDIR/cofactors_ZN.pdb"
bash "$SCRIPT" "$WORKDIR" "$WORKDIR/protein.pdb" "$WORKDIR/lig_h.mol2" 2>&1 | tee run_smoke.log
echo SMOKE_EXIT=$?
ls -la em.gro metal_counts.txt index.ndx complex.gro 2>&1 | head
