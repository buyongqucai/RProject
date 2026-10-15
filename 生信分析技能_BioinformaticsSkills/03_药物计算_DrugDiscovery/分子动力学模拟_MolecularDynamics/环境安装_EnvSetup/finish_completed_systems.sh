#!/usr/bin/env bash
# 已完成体系串行：补算 → SASA → Origin CSV → 归档项目目录（ADA_A2 / MMP9）
set -u
echo "[batch] start $(date -Is) pid=$$"
source ~/activate-md.sh
SCR="/mnt/e/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics/脚本_scripts"
sed -i 's/\r$//' "$SCR/补算必备分析_extraMdAnalysis.sh" "$SCR/导出Origin数据_exportMdOriginCsv.py" \
  /mnt/e/md_kit/archive_md_run_to_project.py
PY="$HOME/md-venv/bin/python3"

# 等 FOS 的 sasa/导出收尾，避免 I/O 抢占
while pgrep -f "gmx sasa" >/dev/null 2>&1 || pgrep -f "exportMdOriginCsv" >/dev/null 2>&1; do sleep 30; done

for NAME in ADA_Adenosine_7RTG_A2 MMP9_Tryptophan_4H3X; do
  WD="$HOME/md_runs/$NAME"
  [[ -d "$WD" ]] || { echo "[batch] skip $NAME (no dir)"; continue; }
  echo "[batch] $(date -Is) $NAME 补算"
  ( cd "$WD" && export LIGAND_RES=LIG && bash "$SCR/补算必备分析_extraMdAnalysis.sh" \
      >> extra_analysis.log 2>&1 || echo "[batch] WARN 补算 $NAME rc=$?" )
  if [[ ! -f "$WD/sasa.xvg" ]]; then
    ( cd "$WD" && echo "Protein_Ligand" | gmx sasa -s md.tpr -f md_center.xtc \
        -n index_analysis.ndx -o sasa.xvg > sasa.log 2>&1 \
        || printf "Protein\n" | gmx sasa -s md.tpr -f md_center.xtc -o sasa.xvg >> sasa.log 2>&1 )
  fi
  echo "[batch] $(date -Is) $NAME 导出 CSV"
  "$PY" "$SCR/导出Origin数据_exportMdOriginCsv.py" --work "$WD" --project "$NAME" \
    --origin-root /mnt/e/Origin_Data >> "$WD/export_csv.log" 2>&1 \
    || echo "[batch] WARN export $NAME rc=$?"
  echo "[batch] $(date -Is) $NAME 归档"
  "$PY" /mnt/e/md_kit/archive_md_run_to_project.py "$NAME"
done
echo "[batch] $(date -Is) ALL_BATCH_DONE"
