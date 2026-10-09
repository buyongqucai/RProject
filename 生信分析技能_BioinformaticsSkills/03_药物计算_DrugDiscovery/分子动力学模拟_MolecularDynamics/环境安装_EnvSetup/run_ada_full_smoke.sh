#!/usr/bin/env bash
set -euo pipefail
source ~/activate-md.sh
SCRIPT=$(find /mnt/e/RProject -name '运行复合物MD_runComplexMd.sh' 2>/dev/null | head -1)
BASE=$(find /mnt/e/RProject -type d -name ADA_Adenosine_7RTG | head -1)
WD="$HOME/md_runs/ADA_Adenosine_7RTG"
cd "$WD"
# ligand already fixed in wd; do not re-copy protein from source (would undo pdbfixer)
test -f lig_h.mol2 && test -f protein.pdb
cp -f protein.pdb lig_h.mol2 "$BASE/" 2>/dev/null || true
# clean intermediates, keep inputs
rm -rf ligand.acpype .acpype_tmp_ligand
for f in complex.gro protein.gro topol.top posre.itp metal_counts.txt index.ndx \
  solv.gro solv_ions.gro newbox.gro em.gro nvt.gro npt.gro md.gro \
  *.tpr *.cpt *.xtc *.edr *.trr *.log run_*.mdp mdout.mdp; do
  rm -f $f 2>/dev/null || true
done
export LIGAND_RES=LIG NET_CHARGE=0 NS=0.02 CHUNK_NS=0.02 MONITOR=0
export COFACTORS_PDB="$WD/cofactors_ZN.pdb"
bash "$SCRIPT" "$WD" "$WD/protein.pdb" "$WD/lig_h.mol2" 2>&1 | tee run_smoke.log
echo SMOKE_EXIT=$?
cat metal_counts.txt 2>/dev/null || true
ls -la em.gro nvt.gro npt.gro md.gro 2>&1
