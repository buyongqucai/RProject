#!/usr/bin/env bash
# Resume CYP1A1 100 ns from existing em.gro / solv_ions (detached-safe)
set -euo pipefail
source ~/activate-md.sh
export PATH="${HOME}/md-venv/bin:${HOME}/gromacs-gpu/bin:${HOME}/miniconda3/envs/md-tools/bin:${PATH}"
export GMX_MAXBACKUP="${GMX_MAXBACKUP:-5}"
export LIGAND_RES=LIG NET_CHARGE=0 NS=100 CHUNK_NS=1 MONITOR=1 CHECK_MMGBSA=0
export USE_PREBUILT_COMPLEX=1
export MDP_DIR="${HOME}/md_runs/mdp_templates"

WORK="${HOME}/md_runs/CYP1A1_Indole_4I8V"
RUN_SH="/mnt/e/md_kit/runComplexMd.sh"
LOG="${HOME}/md_runs/logs/CYP1A1_Indole_4I8V.log"
mkdir -p "$(dirname "$LOG")"

cd "$WORK"
[[ -f complex.gro && -f topol.top && -f solv_ions.gro && -f em.gro ]] || {
  echo "FAIL: missing complex/topol/solv_ions/em"; exit 1
}
echo "RUNNING $(date -Iseconds)" > CYP_STATUS.txt
echo "[$(date -Iseconds)] resume CYP NS=$NS from em.gro" | tee -a "$LOG"
exec >>"$LOG" 2>&1
bash "$RUN_SH" "$WORK" "$WORK/protein.pdb" "$WORK/lig_h.mol2"
echo "[$(date -Iseconds)] CYP DONE"
echo "DONE $(date -Iseconds)" > CYP_STATUS.txt
