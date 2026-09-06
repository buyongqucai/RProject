#!/usr/bin/env bash
# 补算样例必备分析：蛋白/配体/复合物 RMSD、质心距离、NVT/NPT 平衡曲线
# 用法：在 GROMACS 扁平工作目录内执行（归档前）。归档后文件在
#   工作文件_MdWork/<体系>/08_轨迹分析_Analysis/ 等阶段目录。
# 归档：python 脚本_scripts/整理样例目录_layoutMdSample.py
set -euo pipefail
LIGAND_RES="${LIGAND_RES:-JZ4}"
XTC="${XTC:-md_center.xtc}"
TPR="${TPR:-md.tpr}"

if [[ ! -f "$XTC" ]]; then
  echo "缺 $XTC" >&2; exit 1
fi

# 索引：Protein | Ligand → Protein_Ligand
if [[ ! -f index_analysis.ndx ]]; then
  printf "1 | 13\nname 21 Protein_Ligand\nq\n" | gmx make_ndx -f "$TPR" -o index_analysis.ndx > make_ndx_analysis.log 2>&1
fi

# Protein RMSD（Backbone 拟合，Protein 计算）
if [[ ! -s rmsd_protein.xvg ]]; then
  printf "Backbone\nProtein\n" | gmx rms -s "$TPR" -f "$XTC" -n index_analysis.ndx \
      -o rmsd_protein.xvg -tu ns > rms_protein.log 2>&1 || true
fi
# Ligand RMSD（Backbone 拟合蛋白，计算配体；再算配体自拟合）
if [[ ! -s rmsd_ligand.xvg ]]; then
  printf "Backbone\n${LIGAND_RES}\n" | gmx rms -s "$TPR" -f "$XTC" -n index_analysis.ndx \
      -o rmsd_ligand.xvg -tu ns > rms_ligand.log 2>&1 || true
fi
# Complex RMSD（Backbone 拟合，Protein+Ligand 计算）
if [[ ! -s rmsd_complex.xvg ]]; then
  printf "Backbone\nProtein_Ligand\n" | gmx rms -s "$TPR" -f "$XTC" -n index_analysis.ndx \
      -o rmsd_complex.xvg -tu ns > rms_complex.log 2>&1 || true
fi

# 质心距离 Protein ↔ Ligand
if [[ ! -s com_distance.xvg ]]; then
  printf "Protein\n${LIGAND_RES}\n" | gmx distance -s "$TPR" -f "$XTC" -n index_analysis.ndx \
      -select "com of group Protein plus com of group ${LIGAND_RES}" \
      -oav com_distance.xvg -tu ns > com_distance.log 2>&1 || true
  # 若 -select 语法失败，退回交互式
  if [[ ! -s com_distance.xvg ]]; then
    printf "Protein\n${LIGAND_RES}\n" | gmx distance -s "$TPR" -f "$XTC" -n index_analysis.ndx \
        -oav com_distance.xvg -tu ns > com_distance.log 2>&1 || true
  fi
fi

# NVT/NPT/MD 能量曲线（温度、压力、密度、势能）
extract_energy() {
  local edr="$1" out="$2" terms="$3"
  if [[ -f "$edr" && ! -s "$out" ]]; then
    echo "$terms" | gmx energy -f "$edr" -o "$out" > "${out%.xvg}.log" 2>&1 || true
  fi
}
# terms 序号因体系而异，用名称更稳：先列出
if [[ -f nvt.edr && ! -s energy_nvt_temp.xvg ]]; then
  printf "Temperature\n0\n" | gmx energy -f nvt.edr -o energy_nvt_temp.xvg > energy_nvt_temp.log 2>&1 || true
fi
if [[ -f npt.edr && ! -s energy_npt_temp.xvg ]]; then
  printf "Temperature\n0\n" | gmx energy -f npt.edr -o energy_npt_temp.xvg > energy_npt_temp.log 2>&1 || true
fi
if [[ -f npt.edr && ! -s energy_npt_press.xvg ]]; then
  printf "Pressure\n0\n" | gmx energy -f npt.edr -o energy_npt_press.xvg > energy_npt_press.log 2>&1 || true
fi
if [[ -f npt.edr && ! -s energy_npt_dens.xvg ]]; then
  printf "Density\n0\n" | gmx energy -f npt.edr -o energy_npt_dens.xvg > energy_npt_dens.log 2>&1 || true
fi
if [[ -f md.edr && ! -s energy_md_temp.xvg ]]; then
  printf "Temperature\n0\n" | gmx energy -f md.edr -o energy_md_temp.xvg > energy_md_temp.log 2>&1 || true
fi
if [[ -f md.edr && ! -s energy_md_potential.xvg ]]; then
  printf "Potential\n0\n" | gmx energy -f md.edr -o energy_md_potential.xvg > energy_md_potential.log 2>&1 || true
fi

# 帧数快照：首/中/末（pdb）
if [[ ! -f snapshot_start.pdb ]]; then
  printf "System\n" | gmx trjconv -s "$TPR" -f "$XTC" -o snapshot_start.pdb -dump 0 > snap_start.log 2>&1 || true
fi
if [[ ! -f snapshot_mid.pdb ]]; then
  # 取轨迹中点时间（演示 0.2 ns → 0.1）
  mid=$(awk '!/^[#@]/ {print $1; exit}' rmsd_backbone.xvg)
  # 用最后时间的一半
  tmax=$(awk '!/^[#@]/ {t=$1} END{print t}' rmsd_backbone.xvg)
  mid=$(python3 -c "print(float('$tmax')/2)")
  printf "System\n" | gmx trjconv -s "$TPR" -f "$XTC" -o snapshot_mid.pdb -dump "$mid" > snap_mid.log 2>&1 || true
fi
if [[ ! -f snapshot_end.pdb ]]; then
  printf "System\n" | gmx trjconv -s "$TPR" -f "$XTC" -o snapshot_end.pdb -dump 9999 > snap_end.log 2>&1 || true
fi

ls -la rmsd_protein.xvg rmsd_ligand.xvg rmsd_complex.xvg com_distance.xvg \
       energy_nvt_temp.xvg energy_npt_temp.xvg energy_npt_press.xvg energy_npt_dens.xvg \
       energy_md_temp.xvg energy_md_potential.xvg \
       snapshot_*.pdb 2>/dev/null || true
echo DONE_EXTRA_ANALYSIS
