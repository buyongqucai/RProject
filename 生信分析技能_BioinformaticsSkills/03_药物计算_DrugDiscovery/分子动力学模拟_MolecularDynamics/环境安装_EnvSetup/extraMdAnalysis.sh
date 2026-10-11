#!/usr/bin/env bash
# 补算样例必备分析：蛋白/配体/复合物 RMSD、质心距离、氢键、NVT/NPT 平衡曲线
# 用法：在 GROMACS 扁平工作目录内执行（归档前）。
# 环境变量：LIGAND_RES（默认 LIG）、XTC、TPR
set -euo pipefail
LIGAND_RES="${LIGAND_RES:-LIG}"
XTC="${XTC:-md_center.xtc}"
TPR="${TPR:-md.tpr}"

if [[ ! -f "$XTC" ]]; then
  echo "缺 $XTC" >&2; exit 1
fi
if [[ ! -f "$TPR" ]]; then
  echo "缺 $TPR" >&2; exit 1
fi

# ---- 索引：保证有配体组与 Protein_Ligand（兼容已有 Protein_LIG）----
ensure_index() {
  if [[ ! -f index_analysis.ndx ]]; then
    printf "q\n" | gmx make_ndx -f "$TPR" -o index_analysis.ndx > make_ndx_analysis.log 2>&1 || true
  fi
  # 已有 Protein_Ligand / Protein_LIG 任一即可
  if grep -qE '^\[ *(Protein_Ligand|Protein_LIG) *\]' index_analysis.ndx 2>/dev/null; then
    # 统一别名：若只有 Protein_LIG，再挂一个 Protein_Ligand 同原子组
    if ! grep -qE '^\[ *Protein_Ligand *\]' index_analysis.ndx; then
      {
        echo "\"Protein_LIG\""
        echo "name Protein_Ligand"
        echo q
      } | gmx make_ndx -f "$TPR" -n index_analysis.ndx -o index_analysis.ndx >> make_ndx_analysis.log 2>&1 || true
    fi
    return 0
  fi
  {
    echo "\"Protein\" | \"${LIGAND_RES}\""
    echo "name Protein_Ligand"
    echo q
  } | gmx make_ndx -f "$TPR" -n index_analysis.ndx -o index_analysis.ndx >> make_ndx_analysis.log 2>&1 || true
}

# 返回复合物组的**组号**（按名选若有重复 Protein_LIG 会 Fatal）
complex_group_id() {
  python3 - <<'PY'
from pathlib import Path
text = Path("index_analysis.ndx").read_text(errors="replace").splitlines()
names = []
for ln in text:
    ln = ln.strip()
    if ln.startswith("[") and ln.endswith("]"):
        names.append(ln[1:-1].strip())
for prefer in ("Protein_Ligand", "Protein_LIG"):
    hits = [i for i, n in enumerate(names) if n == prefer]
    if hits:
        print(hits[0])  # first match
        raise SystemExit(0)
print("")
PY
}

ensure_index
CX_ID="$(complex_group_id)"
if [[ -z "$CX_ID" ]]; then
  echo "WARN: 无法创建 Protein_Ligand 索引组（LIGAND_RES=${LIGAND_RES}）" >&2
else
  echo "complex index group id=${CX_ID}"
fi

# Protein RMSD（Backbone 拟合，Protein 计算）
if [[ ! -s rmsd_protein.xvg ]]; then
  printf "Backbone\nProtein\n" | gmx rms -s "$TPR" -f "$XTC" -n index_analysis.ndx \
      -o rmsd_protein.xvg -tu ns > rms_protein.log 2>&1 || true
fi
# Ligand RMSD（Backbone 拟合蛋白，计算配体）
if [[ ! -s rmsd_ligand.xvg ]]; then
  printf "Backbone\n${LIGAND_RES}\n" | gmx rms -s "$TPR" -f "$XTC" -n index_analysis.ndx \
      -o rmsd_ligand.xvg -tu ns > rms_ligand.log 2>&1 || true
fi
# Complex RMSD（Backbone 拟合，Protein+Ligand 计算；必须用组号，避免重名）
if [[ ! -s rmsd_complex.xvg ]]; then
  if [[ -n "$CX_ID" ]]; then
    printf "Backbone\n${CX_ID}\n" | gmx rms -s "$TPR" -f "$XTC" -n index_analysis.ndx \
        -o rmsd_complex.xvg -tu ns > rms_complex.log 2>&1 || true
  fi
  if [[ ! -s rmsd_complex.xvg ]]; then
    echo "FAIL: rmsd_complex.xvg 未生成（组号=${CX_ID:-none}）；见 rms_complex.log" >&2
  fi
fi

# 质心距离 Protein ↔ Ligand
if [[ ! -s com_distance.xvg ]]; then
  printf "Protein\n${LIGAND_RES}\n" | gmx distance -s "$TPR" -f "$XTC" -n index_analysis.ndx \
      -select "com of group Protein plus com of group ${LIGAND_RES}" \
      -oav com_distance.xvg -tu ns > com_distance.log 2>&1 || true
  if [[ ! -s com_distance.xvg ]]; then
    printf "Protein\n${LIGAND_RES}\n" | gmx distance -s "$TPR" -f "$XTC" -n index_analysis.ndx \
        -oav com_distance.xvg -tu ns > com_distance.log 2>&1 || true
  fi
fi

# 氢键：GROMACS 2024+ 新 gmx hbond 对 GAFF 配体常报「无 donor/acceptor」
# 优先 hbond-legacy（旧几何定义，与样例 SOP 一致）；失败再试新版 -r/-t + -an
if [[ ! -s hbond_num.xvg ]]; then
  if command -v gmx >/dev/null; then
    if gmx help hbond-legacy >/dev/null 2>&1 || gmx hbond-legacy -h >/dev/null 2>&1; then
      printf "Protein\n${LIGAND_RES}\n" | gmx hbond-legacy -s "$TPR" -f "$XTC" -n index_analysis.ndx \
          -num hbond_num.xvg > hbond.log 2>&1 || true
    fi
  fi
  if [[ ! -s hbond_num.xvg ]]; then
    # 新版：显式 selection + 允许 N 作受体
    gmx hbond -s "$TPR" -f "$XTC" -n index_analysis.ndx \
        -r "group Protein" -t "group ${LIGAND_RES}" -an \
        -num hbond_num.xvg > hbond.log 2>&1 || true
  fi
  if [[ ! -s hbond_num.xvg ]]; then
    echo "WARN: hbond_num.xvg 未生成（配体可能无经典 D/A）；见 hbond.log" >&2
  fi
fi

# NVT/NPT/MD 能量曲线（温度、压力、密度、势能）
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
if [[ ! -f snapshot_mid.pdb && -s rmsd_backbone.xvg ]]; then
  tmax=$(awk '!/^[#@]/ {t=$1} END{print t}' rmsd_backbone.xvg)
  mid=$(python3 -c "print(float('${tmax:-0}')/2)")
  printf "System\n" | gmx trjconv -s "$TPR" -f "$XTC" -o snapshot_mid.pdb -dump "$mid" > snap_mid.log 2>&1 || true
fi
if [[ ! -f snapshot_end.pdb ]]; then
  printf "System\n" | gmx trjconv -s "$TPR" -f "$XTC" -o snapshot_end.pdb -dump 999999 > snap_end.log 2>&1 || true
fi

echo "---- extra analysis status ----"
for f in rmsd_protein.xvg rmsd_ligand.xvg rmsd_complex.xvg com_distance.xvg hbond_num.xvg \
         energy_nvt_temp.xvg energy_npt_temp.xvg energy_npt_press.xvg energy_npt_dens.xvg \
         energy_md_temp.xvg energy_md_potential.xvg; do
  if [[ -s "$f" ]]; then
    echo "OK  $f"
  else
    echo "MISS $f"
  fi
done
echo DONE_EXTRA_ANALYSIS
