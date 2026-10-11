#!/usr/bin/env bash
# launch_cyp_100ns.sh — CYP1A1/4I8V + 吲哚；HEME 用 Shahrokh IC6
set -euo pipefail
source ~/activate-md.sh
export GMX_MAXBACKUP="${GMX_MAXBACKUP:-5}"
export PATH="${HOME}/md-venv/bin:${HOME}/gromacs-gpu/bin:${HOME}/miniconda3/envs/md-tools/bin:${PATH}"

ROOT="/mnt/e/md_kit"
IN="$ROOT/课题top3输入/CYP1A1_Indole_4I8V"
WORK="${HOME}/md_runs/CYP1A1_Indole_4I8V"
HEME_IC6="$ROOT/heme_params_shahrokh/heme_params/IC6"
BUILD_SH="$ROOT/build_cyp_heme_topology.sh"
RUN_SH="/mnt/e/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics/脚本_scripts/运行复合物MD_runComplexMd.sh"
LOG="${HOME}/md_runs/logs/CYP1A1_Indole_4I8V.log"
mkdir -p "$WORK" "$(dirname "$LOG")"

exec > >(tee -a "$LOG") 2>&1
echo "[$(date -Iseconds)] CYP launch start"
ls -la "$IN" "$HEME_IC6"

cp -f "$IN/protein.pdb" "$IN/lig_h.mol2" "$IN/cofactors_HEM.pdb" "$WORK/"
cp -f "$HEME_IC6/HEM.mol2" "$HEME_IC6/CYP.mol2" "$HEME_IC6/IC6.frcmod" "$WORK/"

if [[ ! -f "$WORK/heme_ready.flag" || ! -f "$WORK/complex_heme.gro" || ! -f "$WORK/topol_heme.top" ]]; then
  echo "[$(date -Iseconds)] building HEME topology (Shahrokh IC6 + tleap)..."
  if ! bash "$BUILD_SH" "$WORK"; then
    rc=$?
    echo "[$(date -Iseconds)] HEME topology FAILED (exit $rc). Not starting MD without HEME."
    echo "STAGED_ONLY" > "$WORK/CYP_STATUS.txt"
    exit 3
  fi
fi
[[ -f "$WORK/heme_ready.flag" && -s "$WORK/complex_heme.gro" && -s "$WORK/topol_heme.top" ]] || {
  echo "[$(date -Iseconds)] HEME outputs missing after build"; exit 3
}

cp -f "$WORK/complex_heme.gro" "$WORK/complex.gro"
cp -f "$WORK/topol_heme.top" "$WORK/topol.top"
echo "READY $(date -Iseconds)" > "$WORK/CYP_STATUS.txt"

export LIGAND_RES=LIG NET_CHARGE=0 NS=100 CHUNK_NS=1 MONITOR=1 CHECK_MMGBSA=0
export USE_PREBUILT_COMPLEX=1
export GMX_MAXBACKUP=5

echo "[$(date -Iseconds)] start production NS=$NS USE_PREBUILT_COMPLEX=1"
bash "$RUN_SH" "$WORK" "$WORK/protein.pdb" "$WORK/lig_h.mol2"
echo "[$(date -Iseconds)] CYP DONE"
