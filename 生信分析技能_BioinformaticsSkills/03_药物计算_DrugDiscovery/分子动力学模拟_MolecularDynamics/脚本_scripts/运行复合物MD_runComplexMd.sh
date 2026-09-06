#!/usr/bin/env bash
# 运行复合物MD_runComplexMd.sh — 蛋白-配体复合物 GROMACS MD 全流程（WSL2/Linux 内运行）
#
# 流程: pdb2gmx(蛋白, AMBER99SB-ILDN+TIP3P) → acpype/antechamber(配体 GAFF2)
#       → 复合物合并 → editconf/solvate/genion → EM → NVT → NPT → 生产 MD
#       → trjconv PBC 校正 → RMSD/RMSF/氢键/回旋半径
#
# 用法:
#   bash 运行复合物MD_runComplexMd.sh WORK_DIR PROTEIN_PDB LIGAND_MOL2 [选项]
# 选项(环境变量):
#   LIGAND_RES=JZ4      配体残基名(三字母)
#   NET_CHARGE=0        配体净电荷(antechamber -n)
#   NS=1                生产时长 ns(演示 1；正式研究 50–100)
#   MDP_DIR=...         mdp 模板目录(默认取脚本同目录 mdp模板_mdps)
#   ACPYPE_BIN=/opt/miniforge3/envs/md/bin   acpype/antechamber 所在目录
#
# 依赖: gmx (PATH 内), acpype+ambertools (ACPYPE_BIN)
set -euo pipefail

WORK_DIR=${1:?用法: runComplexMd.sh WORK_DIR PROTEIN_PDB LIGAND_MOL2}
PROTEIN_PDB=${2:?缺蛋白 PDB}
LIGAND_MOL2=${3:?缺配体 mol2(须已加氢)}
LIGAND_RES=${LIGAND_RES:-JZ4}
NET_CHARGE=${NET_CHARGE:-0}
NS=${NS:-1}
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
MDP_DIR=${MDP_DIR:-"$SCRIPT_DIR/mdp模板_mdps"}
ACPYPE_BIN=${ACPYPE_BIN:-/opt/miniforge3/envs/md/bin}
export PATH="$ACPYPE_BIN:$PATH"

log(){ echo "[$(date +%H:%M:%S)] $*"; }
cd "$WORK_DIR"

# ---- 01 配体 GAFF2 拓扑(acpype → antechamber AM1-BCC + parmchk2) ----
if [[ ! -f ligand.acpype/ligand_GMX.itp ]]; then
  log "01 acpype 配体拓扑 (GAFF2, 净电荷 $NET_CHARGE)"
  rm -rf ligand.acpype acpype_tmp.mol2
  cp "$LIGAND_MOL2" acpype_tmp.mol2
  acpype -i acpype_tmp.mol2 -n "$NET_CHARGE" -a gaff2 -o gmx -b ligand > acpype.log 2>&1
  rm -f acpype_tmp.mol2
fi
LIG_ITP=ligand.acpype/ligand_GMX.itp
LIG_GRO=ligand.acpype/ligand_GMX.gro
[[ -f $LIG_ITP && -f $LIG_GRO ]] || { log "FAIL: acpype 未产出 $LIG_ITP"; exit 1; }
# acpype 的 moleculetype 名取自 -b 基名而非残基名；统一改名为 $LIGAND_RES 以对齐 topol.top
awk -v r="$LIGAND_RES" '
  /\[ moleculetype \]/ {f=1; print; next}
  f==1 && /^[ \t]*;/   {print; next}
  f==1 && NF>=2        {$1=r; f=0; print; next}
  {print}' "$LIG_ITP" > "$LIG_ITP.tmp" && mv "$LIG_ITP.tmp" "$LIG_ITP"
grep -q "^$LIGAND_RES " <(awk '/\[ moleculetype \]/{f=1;next} f&&NF&&!/^;/{print;exit}' "$LIG_ITP") \
  && log "01 配体 moleculetype=$LIGAND_RES OK" || { log "FAIL: moleculetype 改名失败"; exit 1; }

# ---- 02 蛋白拓扑(pdb2gmx) ----
if [[ ! -f protein.gro ]]; then
  log "02 pdb2gmx 蛋白拓扑 (amber99sb-ildn/tip3p)"
  gmx pdb2gmx -f "$PROTEIN_PDB" -o protein.gro -p topol.top -i posre.itp \
      -ff amber99sb-ildn -water tip3p -ignh > pdb2gmx.log 2>&1
fi

# ---- 03 合并复合物 complex.gro + topol.top 接入配体 ----
if [[ ! -f complex.gro ]]; then
  log "03 合并蛋白+配体坐标"
  python3 - "$LIG_GRO" <<'PY'
import sys
prot = open("protein.gro").read().splitlines()
lig  = open(sys.argv[1]).read().splitlines()
title = prot[0]
np_, nl = int(prot[1]), int(lig[1])
patoms = prot[2:2+np_]
latoms = lig[2:2+nl]
box = prot[2+np_]
with open("complex.gro", "w") as fh:
    fh.write(title + "\n")
    fh.write(f"{np_+nl}\n")
    fh.write("\n".join(patoms + latoms) + "\n")
    fh.write(box + "\n")
PY
fi
if ! grep -q "ligand_GMX.itp" topol.top; then
  log "03 topol.top 接入配体 itp + molecules"
  sed -i "s|^\(#include .*forcefield.itp.*\)$|\1\n#include \"ligand.acpype/ligand_GMX.itp\"|" topol.top
  printf '%-20s %s\n' "$LIGAND_RES" "1" >> topol.top
fi
grep -q "$LIGAND_RES" topol.top || { log "FAIL: topol.top 未登记配体"; exit 1; }

# ---- 04 盒子 + 溶剂化 + 离子 ----
if [[ ! -f solv_ions.gro ]]; then
  log "04 editconf/solvate/genion (0.15 M NaCl 中和)"
  # 防重入：solvate/genion 会向 topol.top 追加 SOL/NA/CL 行，重跑前剔除旧行
  sed -i '/^SOL[ \t]/d; /^NA[ \t]/d; /^CL[ \t]/d' topol.top
  gmx editconf -f complex.gro -o newbox.gro -bt dodecahedron -d 1.0 > editconf.log 2>&1
  gmx solvate -cp newbox.gro -cs spc216 -p topol.top -o solv.gro > solvate.log 2>&1
  # -maxwarn 1: 加离子前体系净电荷非零是预期状态（genion 随即中和），仅此步放行该警告
  gmx grompp -f "$MDP_DIR/ions.mdp" -c solv.gro -p topol.top -o ions.tpr -maxwarn 1 > grompp_ions.log 2>&1
  echo SOL | gmx genion -s ions.tpr -o solv_ions.gro -p topol.top \
      -pname NA -nname CL -neutral -conc 0.15 > genion.log 2>&1
fi

# ---- 05 能量最小化 ----
if [[ ! -f em.gro ]]; then
  log "05 能量最小化"
  gmx grompp -f "$MDP_DIR/em.mdp" -c solv_ions.gro -p topol.top -o em.tpr > grompp_em.log 2>&1
  gmx mdrun -v -deffnm em > mdrun_em.log 2>&1
fi

# ---- 06 渲染 mdp 模板（__LIG__ → 实际配体残基名；温控/分析全用默认组，免索引文件） ----
for m in nvt npt md; do
  sed "s/__LIG__/$LIGAND_RES/g" "$MDP_DIR/$m.mdp" > "run_$m.mdp"
done

# ---- 07 NVT ----
if [[ ! -f nvt.gro ]]; then
  log "07 NVT 100 ps"
  gmx grompp -f run_nvt.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr > grompp_nvt.log 2>&1
  gmx mdrun -v -deffnm nvt > mdrun_nvt.log 2>&1
fi

# ---- 08 NPT ----
if [[ ! -f npt.gro ]]; then
  log "08 NPT 100 ps"
  gmx grompp -f run_npt.mdp -c nvt.gro -r nvt.gro -t nvt.cpt -p topol.top -o npt.tpr > grompp_npt.log 2>&1
  gmx mdrun -v -deffnm npt > mdrun_npt.log 2>&1
fi

# ---- 09 生产 MD ----
NSTEPS=$(awk -v ns="$NS" 'BEGIN{printf "%d", ns*1000/0.002}')
if [[ ! -f md.gro ]]; then
  log "09 生产 MD ${NS} ns ($NSTEPS 步)"
  sed -i "s/^nsteps .*/nsteps          = $NSTEPS/" run_md.mdp
  gmx grompp -f run_md.mdp -c npt.gro -t npt.cpt -p topol.top -o md.tpr > grompp_md.log 2>&1
  gmx mdrun -v -deffnm md > mdrun_md.log 2>&1
fi

# ---- 10 PBC 校正 + 分析（默认组：Backbone/C-alpha/Protein/$LIGAND_RES） ----
if [[ ! -f md_center.xtc ]]; then
  log "10 trjconv PBC 校正"
  printf 'Protein\nSystem\n' | gmx trjconv -s md.tpr -f md.xtc -o md_center.xtc \
      -pbc mol -center -ur compact > trjconv.log 2>&1
fi
log "10 RMSD/RMSF/氢键/回旋半径"
printf 'Backbone\nBackbone\n' | gmx rms -s md.tpr -f md_center.xtc \
    -o rmsd_backbone.xvg -tu ns > rms.log 2>&1 || true
printf 'C-alpha\n' | gmx rmsf -s md.tpr -f md_center.xtc \
    -o rmsf_calpha.xvg -res > rmsf.log 2>&1 || true
printf "Protein\n$LIGAND_RES\n" | gmx hbond -s md.tpr -f md_center.xtc \
    -num hbond_num.xvg > hbond.log 2>&1 || true
printf 'Protein\n' | gmx gyrate -s md.tpr -f md_center.xtc \
    -o gyrate.xvg > gyrate.log 2>&1 || true

log "DONE: $(ls *.xvg 2>/dev/null | tr '\n' ' ')"
log "样例归档（分类目录+中英对照）: python 整理样例目录_layoutMdSample.py"
