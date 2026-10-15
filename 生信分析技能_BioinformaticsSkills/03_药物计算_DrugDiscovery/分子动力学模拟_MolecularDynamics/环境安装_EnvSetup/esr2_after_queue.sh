#!/usr/bin/env bash
# 等前一个串行 runner（resume_top3_fixed）退出后，再跑 ESR2（3OLL 初态 + 微调配体）。
set -u
source ~/activate-md.sh
while pgrep -f "resume_top3_fixed.sh" >/dev/null 2>&1; do sleep 120; done
while pgrep -f "runComplexMd" >/dev/null 2>&1; do sleep 120; done
sed -i 's/\r$//' /mnt/e/md_kit/nudge_esr2_retry_lig.py
python3 /mnt/e/md_kit/nudge_esr2_retry_lig.py
SRC="/mnt/e/RProject/努力学习项目/08_分子动力学/数据文件/原始数据/RCSB与对接姿态_MD输入_Top3/ESR2_Anhydroicaritin_1L2J_retry1"
WD=~/md_runs/ESR2_Anhydroicaritin_1L2J_retry2
mkdir -p "$WD/monitor"
cp -f "$SRC/protein.pdb" "$SRC/lig_h.mol2" "$WD/"
export LIGAND_RES=LIG NET_CHARGE=0 NS=100 CHUNK_NS=1 MONITOR=1 CHECK_MMGBSA=0
export GMX_MAXBACKUP=-1 MD_ALERT_DEFER=1 MD_ALERT_SH=/mnt/e/md_kit/notify_md_alert.sh
cd "$WD"
bash "/mnt/e/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics/脚本_scripts/运行复合物MD_runComplexMd.sh" \
  "$PWD" "$PWD/protein.pdb" "$PWD/lig_h.mol2" >> ~/md_runs/logs/ESR2_retry2.log 2>&1
echo "[esr2-waiter] $(date -Is) ESR2_retry2 end rc=$?"
