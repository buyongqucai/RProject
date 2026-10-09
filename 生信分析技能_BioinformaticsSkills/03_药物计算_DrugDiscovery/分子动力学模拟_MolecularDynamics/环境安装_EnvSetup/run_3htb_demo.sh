#!/usr/bin/env bash
# run_3htb_demo.sh — 3HTB 正式演示（NS=0.2，原始 mdp 模板，GPU 全流程+性能测定）
# 调用（WSL 内）： bash run_3htb_demo.sh    或双击 E:\05_演示_双击启动.bat
# 前置：~/activate-md.sh 存在（§9.8 环境已装）；输入预制于 kit 烟测输入_3HTB/
# 产物：/mnt/e/md_work/3HTB_demo/（ASCII 路径，避开 acpype/tleap 非 ASCII 坑）
set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SK="${SK:-/mnt/e/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics}"
NS="${NS:-0.2}"
WORK="${WORK:-/mnt/e/md_work/3HTB_demo}"

[ -f "$HOME/activate-md.sh" ] || { echo "FAIL: 缺 ~/activate-md.sh（按 SOP §9.8 装环境）"; exit 1; }
# shellcheck disable=SC1090
source "$HOME/activate-md.sh"
echo "gmx   = $(command -v gmx)"; gmx --version 2>/dev/null | grep -iE "GPU|CUDA|Version" | head -3
echo "acpype= $(command -v acpype)"
command -v antechamber >/dev/null || { echo "FAIL: antechamber 不在 PATH（md-tools 未激活）"; exit 1; }

mkdir -p "$WORK"
cp -f "$KIT/烟测输入_3HTB/protein.pdb" "$KIT/烟测输入_3HTB/jz4_h.mol2" "$WORK/"

T0=$(date +%s)
ACPYPE_BIN="$HOME/md-venv/bin" LIGAND_RES=JZ4 NET_CHARGE=0 NS="$NS" \
  bash "$SK/脚本_scripts/运行复合物MD_runComplexMd.sh" "$WORK" "$WORK/protein.pdb" "$WORK/jz4_h.mol2"
T1=$(date +%s)

echo ""
echo "== GPU 判定 =="
grep -ihE "CUDA acceleration|Using GPU|accelerating" "$WORK"/md.log "$WORK"/*.log 2>/dev/null | sort -u | head -4 || echo "日志无 GPU 字样"
echo "== 生产性能 =="
grep -iE "^Performance:" "$WORK"/md.log | tail -1
echo "== 平衡段耗时参考 =="
grep -ihE "Finished mdrun" "$WORK"/nvt.log "$WORK"/npt.log 2>/dev/null | tail -2
echo "== 关键产物 =="
ls "$WORK"/rmsd_backbone.xvg "$WORK"/gyrate.xvg "$WORK"/md.xtc 2>/dev/null && echo "DEMO PASS"
echo "总耗时 $((T1-T0)) 秒 | 工作目录: $WORK"
echo "下一步（可选）: 补算脚本 + MM-GBSA 见 SOP §9.6；归档用 整理样例目录_layoutMdSample.py"
