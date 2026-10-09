#!/usr/bin/env bash
set -euo pipefail
source ~/activate-md.sh
SCRIPT=$(find /mnt/e/RProject -name '运行复合物MD_runComplexMd.sh' 2>/dev/null | head -1)
WD="$HOME/md_runs/ADA_Adenosine_7RTG"
# keep fixed lig_h.mol2 / protein / cofactors; wipe MD intermediates
cd "$WD"
rm -rf ligand.acpype complex.gro protein.gro topol.top posre.itp *.gro *.tpr *.cpt *.xtc *.edr *.log *.ndx metal_counts.txt index.ndx run_*.mdp 2>/dev/null || true
# restore inputs if wiped
BASE=$(find /mnt/e/RProject -type d -name ADA_Adenosine_7RTG | head -1)
[[ -f lig_h.mol2 ]] || cp "$BASE/lig_h.mol2" .
[[ -f protein.pdb ]] || cp "$BASE/protein.pdb" .
[[ -f cofactors_ZN.pdb ]] || cp "$BASE"/cofactors_*.pdb .
# re-apply H rebuild (idempotent)
obabel lig_h.mol2 -O lig_noH.sdf -d
obabel lig_noH.sdf -O lig_h.mol2 -h
python3 - <<'PY'
from pathlib import Path
t = Path("lig_h.mol2").read_text().splitlines()
t[1] = "LIG"
Path("lig_h.mol2").write_text("\n".join(t) + "\n")
PY
export LIGAND_RES=LIG NET_CHARGE=0 NS=0.02 CHUNK_NS=0.02 MONITOR=0
export COFACTORS_PDB="$WD/cofactors_ZN.pdb"
bash "$SCRIPT" "$WD" "$WD/protein.pdb" "$WD/lig_h.mol2" 2>&1 | tee run_smoke.log
echo SMOKE_EXIT=$?
ls -la em.gro nvt.gro npt.gro md.gro metal_counts.txt index.ndx 2>&1 | head
