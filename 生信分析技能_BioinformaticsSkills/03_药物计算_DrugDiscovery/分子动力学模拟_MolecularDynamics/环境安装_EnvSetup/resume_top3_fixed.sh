#!/usr/bin/env bash
# 修复后串行恢复 Top3 生产：ESR2 新配体全新跑；FOS/PPARG 从 1ns md.cpt 续跑。
set -u
source ~/activate-md.sh
RUNSH="/mnt/e/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics/脚本_scripts/运行复合物MD_runComplexMd.sh"
MON="/mnt/e/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics/脚本_scripts/过程监控_monitorMdRun.sh"
TOP3="/mnt/e/RProject/努力学习项目/08_分子动力学/数据文件/原始数据/RCSB与对接姿态_MD输入_Top3"
sed -i 's/\r$//' "$RUNSH" "$MON"
chmod +x "$RUNSH" "$MON"

export LIGAND_RES=LIG NET_CHARGE=0 NS=100 CHUNK_NS=1 MONITOR=1 CHECK_MMGBSA=0
export GMX_MAXBACKUP=-1 MD_ALERT_DEFER=1 MD_ALERT_SH=/mnt/e/md_kit/notify_md_alert.sh
mkdir -p ~/md_runs/logs

# ---- ESR2: 新配体全新体系（旧目录改名留证，非删除）----
OLD=~/md_runs/ESR2_Anhydroicaritin_1L2J
if [[ -d "$OLD" && ! -f "$OLD/DONE.txt" ]]; then
  mv "$OLD" ~/md_runs/ESR2_Anhydroicaritin_1L2J_badlig_20261013
fi
WD=~/md_runs/ESR2_Anhydroicaritin_1L2J
if [[ ! -f "$WD/DONE.txt" && ! -f "$WD/md.cpt" ]]; then
  mkdir -p "$WD/monitor"
  cp -f ~/md_runs/ESR2_Anhydroicaritin_1L2J_badlig_20261013/protein.pdb "$WD/" 2>/dev/null \
    || cp -f "$TOP3/ESR2_Anhydroicaritin_1L2J/protein.pdb" "$WD/"
  cp -f "$TOP3/ESR2_Anhydroicaritin_1L2J/lig_h.mol2" "$WD/"
  echo "[runner] $(date -Is) ESR2 fresh start (fixed ligand)"
  ( cd "$WD" && bash "$RUNSH" "$PWD" "$PWD/protein.pdb" "$PWD/lig_h.mol2" \
      >> ~/md_runs/logs/ESR2_fresh.log 2>&1 )
  echo "[runner] $(date -Is) ESR2 end rc=$?"
fi

# ---- FOS: 1ns 后续跑 ----
WD=~/md_runs/FOS_quercetin_1A02
if [[ -f "$WD/md.cpt" && ! -f "$WD/DONE.txt" ]]; then
  echo "[runner] $(date -Is) FOS resume from $(grep -c 'Writing checkpoint' "$WD/md.log" 2>/dev/null || echo 0) chunks"
  ( cd "$WD" && bash "$RUNSH" "$PWD" "$PWD/protein.pdb" "$PWD/lig_h.mol2" \
      >> ~/md_runs/logs/FOS_resume.log 2>&1 )
  echo "[runner] $(date -Is) FOS end rc=$?"
fi

# ---- PPARG: 1ns 后续跑 ----
WD=~/md_runs/PPARG_kaempferol_1FM9
if [[ -f "$WD/md.cpt" && ! -f "$WD/DONE.txt" ]]; then
  echo "[runner] $(date -Is) PPARG resume"
  ( cd "$WD" && bash "$RUNSH" "$PWD" "$PWD/protein.pdb" "$PWD/lig_h.mol2" \
      >> ~/md_runs/logs/PPARG_resume.log 2>&1 )
  echo "[runner] $(date -Is) PPARG end rc=$?"
fi

echo "[runner] $(date -Is) ALL SERIAL JOBS DONE"
