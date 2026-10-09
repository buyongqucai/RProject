#!/usr/bin/env bash
# 04_烟测_3HTB.sh — 一键烟测（WSL 内执行；前置：02 引导完成，建议 03 GPU 构建后再跑）
# 用法： bash 04_烟测_3HTB.sh
#   NS=0.02        生产时长（默认0.02 ns）
#   SMOKE_FAST=1   默认开启：NVT/NPT 用2000步快速版（只验链路，非平衡；正式跑用 SOP 模板原步数）
# 输入已预制：本目录 烟测输入_3HTB/{protein.pdb, jz4_h.mol2}（mol2 分子名=JZ4，已修踩坑2）
# 通过标志：流水线 DONE + rmsd/rmsf/gyate 产出 + md.log 出现 "CUDA acceleration"（03 构建的 GPU 版）
set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SK="${SK:-/mnt/e/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics}"
# AmberTools bin: conda env md-tools (default) or /opt/ambertools (source install)
AMB_BIN="${AMB_BIN:-$HOME/miniconda3/envs/md-tools/bin}"
NS="${NS:-0.02}"
SMOKE_FAST="${SMOKE_FAST:-1}"
WORK="${WORK:-/tmp/md_smoke_3htb}"

# Prefer activate-md.sh in interactive use; this export keeps one-shot smoke self-contained
export PATH="$HOME/.local/bin:$HOME/md-venv/bin:$AMB_BIN:$HOME/gromacs-gpu/bin:$PATH"
echo "gmx   = $(command -v gmx || echo 未找到)"
echo "acpype= $(command -v acpype || echo 未找到)"
command -v antechamber >/dev/null || { echo "FAIL: antechamber 不在 PATH（跑02）"; exit 1; }
command -v gmx >/dev/null || { echo "FAIL: gmx 不在 PATH（跑03 GPU 构建，或02加 INSTALL_CPU_GMX=1）"; exit 1; }

# 输入复制 + mdp 快速版
rm -rf "$WORK"; mkdir -p "$WORK/mdp_smoke"
cp "$KIT/烟测输入_3HTB/protein.pdb" "$KIT/烟测输入_3HTB/jz4_h.mol2" "$WORK/"
for f in "$SK/脚本_scripts/mdp模板_mdps"/*.mdp; do cp "$f" "$WORK/mdp_smoke/"; done
if [[ "$SMOKE_FAST" == "1" ]]; then
  sed -i 's/^nsteps.*/nsteps = 400/'  "$WORK/mdp_smoke/em.mdp"
  sed -i 's/^nsteps.*/nsteps = 2000/' "$WORK/mdp_smoke/nvt.mdp"
  sed -i 's/^nsteps.*/nsteps = 2000/' "$WORK/mdp_smoke/npt.mdp"
fi

ACPYPE_BIN="$HOME/md-venv/bin" MDP_DIR="$WORK/mdp_smoke" LIGAND_RES=JZ4 NET_CHARGE=0 NS="$NS" \
  bash "$SK/脚本_scripts/运行复合物MD_runComplexMd.sh" "$WORK" "$WORK/protein.pdb" "$WORK/jz4_h.mol2"

echo ""
echo "== GPU 判定（03 的 GPU 版应出现 CUDA acceleration 行） =="
grep -ihE "CUDA acceleration|Using GPU|Device" "$WORK"/*.log | sort -u | head -5 || echo "日志无 GPU 字样 → 当前为 CPU 构建"
echo "== 关键产物 =="
ls "$WORK"/rmsd_backbone.xvg "$WORK"/rmsf_calpha.xvg "$WORK"/gyrate.xvg 2>/dev/null && echo "SMOKE PASS"
echo "工作目录: $WORK"
