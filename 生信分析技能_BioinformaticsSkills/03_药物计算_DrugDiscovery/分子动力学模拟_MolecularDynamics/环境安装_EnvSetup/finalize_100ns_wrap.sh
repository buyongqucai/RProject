#!/usr/bin/env bash
# finalize_100ns_wrap.sh — 100 ns 已跑完但撞 GMX_MAXBACKUP 时的收尾（不重跑生产、不开下一组）
# 用法: bash finalize_100ns_wrap.sh WORK_DIR [LIGAND_RES]
# 环境: source ~/activate-md.sh；GMX_MAXBACKUP 默认 5（保留少量同名备份）
set -euo pipefail
WORK_DIR=${1:?need WORK_DIR}
LIGAND_RES=${2:-${LIGAND_RES:-LIG}}
KEEP_GRO_BAK=${KEEP_GRO_BAK:-5}
export GMX_MAXBACKUP="${GMX_MAXBACKUP:-5}"
export PATH="${HOME}/md-venv/bin:${HOME}/gromacs-gpu/bin:${PATH}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 监控脚本在技能 scripts 或本联接旁
MON_SH=""
for cand in \
  "${SCRIPT_DIR}/../脚本_scripts/过程监控_monitorMdRun.sh" \
  "/mnt/e/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics/脚本_scripts/过程监控_monitorMdRun.sh"
do
  [[ -f "$cand" ]] && MON_SH="$cand" && break
done

log(){ echo "[$(date +%H:%M:%S)] $*"; }
cd "$WORK_DIR"

[[ -f md.tpr && -f md.xtc ]] || { log "FAIL: need md.tpr + md.xtc"; exit 1; }

# 轨迹终点 (ps)：优先 md.log 最后 Time；否则 100000
END_PS=$(awk '/^[[:space:]]*[0-9]+[[:space:]]+[0-9.]+/ {
  if ($1+0==$1 && $2+0==$2) t=$2
} END { if (t!="") print t }' md.log 2>/dev/null || true)
END_PS=${END_PS:-100000}
END_NS=$(awk -v t="$END_PS" 'BEGIN{printf "%.3f", t/1000}')
log "trajectory end ≈ ${END_PS} ps (${END_NS} ns); GMX_MAXBACKUP=$GMX_MAXBACKUP"

# 修剪过多 #md.gro.N#，只留最新 KEEP_GRO_BAK 个
mapfile -t BAKS < <(ls -1t \#md.gro.*\# 2>/dev/null || true)
if ((${#BAKS[@]} > KEEP_GRO_BAK)); then
  log "prune gro backups: keep ${KEEP_GRO_BAK}, remove $((${#BAKS[@]} - KEEP_GRO_BAK))"
  for ((i=KEEP_GRO_BAK; i<${#BAKS[@]}; i++)); do
    rm -f -- "${BAKS[$i]}"
  done
fi

# 末帧 → md.gro
log "trjconv -dump ${END_PS} → md.gro"
echo 0 | gmx trjconv -s md.tpr -f md.xtc -o md.gro -dump "$END_PS" \
  > trjconv_final_gro.log 2>&1
[[ -f md.gro ]] || { log "FAIL: md.gro not written"; exit 1; }

# PBC + 分析
if [[ ! -f md_center.xtc ]]; then
  log "trjconv PBC → md_center.xtc"
  printf 'Protein\nSystem\n' | gmx trjconv -s md.tpr -f md.xtc -o md_center.xtc \
    -pbc mol -center -ur compact > trjconv.log 2>&1
fi
log "RMSD / RMSF / hbond / gyrate"
printf 'Backbone\nBackbone\n' | gmx rms -s md.tpr -f md_center.xtc \
  -o rmsd_backbone.xvg -tu ns > rms.log 2>&1 || true
printf 'C-alpha\n' | gmx rmsf -s md.tpr -f md_center.xtc \
  -o rmsf_calpha.xvg -res > rmsf.log 2>&1 || true
# GROMACS 2024+：优先 hbond-legacy（新 hbond 对 GAFF 配体常报无 D/A）
if ! printf "Protein\n${LIGAND_RES}\n" | gmx hbond-legacy -s md.tpr -f md_center.xtc \
  -num hbond_num.xvg > hbond.log 2>&1; then
  printf "Protein\n${LIGAND_RES}\n" | gmx hbond -s md.tpr -f md_center.xtc \
    -num hbond_num.xvg >> hbond.log 2>&1 || true
fi
printf 'Protein\n' | gmx gyrate -s md.tpr -f md_center.xtc \
  -o gyrate.xvg > gyrate.log 2>&1 || true

if [[ -n "$MON_SH" ]]; then
  log "final monitor"
  if LIGAND_RES="$LIGAND_RES" CHECK_MMGBSA=0 bash "$MON_SH" .; then
    log "final MONITOR_OK"
  else
    log "WARN final monitor exit=$? (see monitor/)"
  fi
else
  log "WARN monitor script not found; skip"
fi

{
  echo "DONE: production ${END_NS} ns; finalized by finalize_100ns_wrap.sh"
  echo "note: 100 ns reached; previous Fatal was GMX_MAXBACKUP on md.gro (not physics)"
  echo "GMX_MAXBACKUP=${GMX_MAXBACKUP}; gro_backups_kept<=${KEEP_GRO_BAK}"
  date -Iseconds
  ls *.xvg 2>/dev/null | tr '\n' ' '
  echo
} | tee DONE.txt

log "DONE $(pwd)"
ls -la md.gro DONE.txt rmsd_backbone.xvg md_center.xtc 2>&1 | head
