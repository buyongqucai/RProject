#!/usr/bin/env bash
# 烟测 WSL MD 环境：GPU gmx + AmberTools/acpype + 短 mdrun
# 用法：wsl -d Ubuntu-24.04 -- bash 脚本_scripts/烟测环境_smokeMdEnv.sh
set -euo pipefail

PASS=0
FAIL=0
ok()  { echo "PASS: $*"; PASS=$((PASS + 1)); }
bad() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }
warn(){ echo "WARN: $*"; }

# Never drop coreutils even if caller narrowed PATH
export PATH="/usr/local/gromacs/bin:/opt/miniforge3/envs/md/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"

echo "======== WSL MD smoke $(date -Is) ========"

command -v head >/dev/null && ok "head=$(command -v head)" || bad "head missing from PATH"
command -v gmx  >/dev/null && ok "gmx=$(command -v gmx)" || bad "gmx missing"

VER=$(gmx --version 2>&1 || true)
echo "$VER" | grep -q 'GPU support: *CUDA' && ok "GPU support CUDA" || bad "gmx without CUDA"
echo "$VER" | grep -q 'GROMACS version: *2023.3' && ok "version 2023.3" || bad "unexpected gmx version"

if nvidia-smi -L >/tmp/smi.txt 2>&1; then
  ok "nvidia-smi: $(sed -n '1p' /tmp/smi.txt)"
else
  bad "nvidia-smi failed"
fi

for b in acpype antechamber tleap parmchk2 gmx_MMPBSA; do
  if command -v "$b" >/dev/null 2>&1; then ok "$b=$(command -v "$b")"; else bad "missing $b"; fi
done

# Match anywhere in banner (first line is ==== separators)
if acpype -v 2>&1 | grep -qi 'acpype'; then ok "acpype runs"; else bad "acpype -v failed"; fi

python -c 'import importlib.metadata as m; print(m.version("gmx_MMPBSA"))' >/tmp/mmp.txt 2>&1 \
  && ok "gmx_MMPBSA $(cat /tmp/mmp.txt)" || bad "gmx_MMPBSA import"

[[ -x /usr/bin/gmx ]] && ok "apt CPU fallback /usr/bin/gmx" || warn "no apt gmx"

SAMPLE_TPR=""
ROOT="/mnt/e/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics/01_样例_sample/工作文件_MdWork/3HTB"
for p in \
  "$ROOT/06_NPT平衡_NPT/npt.tpr" \
  "$ROOT/05_NVT平衡_NVT/nvt.tpr" \
  "$ROOT/07_生产_Production/md.tpr"
do
  [[ -f "$p" ]] && SAMPLE_TPR="$p" && break
done

WORKDIR=$(mktemp -d /tmp/gmx-smoke-XXXX)
cd "$WORKDIR"
if [[ -n "$SAMPLE_TPR" ]]; then
  echo "Using tpr: $SAMPLE_TPR"
  set +e
  gmx mdrun -s "$SAMPLE_TPR" -deffnm smoke -nsteps 50 \
    -nb gpu -pme gpu -update gpu -ntomp 2 -ntmpi 1 -v >smoke.log 2>&1
  rc=$?
  set -e
  if grep -Eiq '1 GPU selected|PME tasks will do all aspects on the GPU|Updating on GPU|Number of GPUs detected: 1' smoke.log; then
    ok "mdrun GPU init (nsteps=50, rc=$rc)"
    grep -Ei 'GPU selected|Mapping of GPU|ns/day|Performance:' smoke.log | sed -n '1,15p' || true
  else
    bad "mdrun did not show GPU activity (rc=$rc)"
    sed -n '1,40p' smoke.log
  fi
  [[ $rc -eq 0 ]] && ok "mdrun finished 50 steps" || warn "mdrun rc=$rc"
else
  warn "no sample tpr; skipped mdrun GPU step"
fi

echo "======== SUMMARY pass=$PASS fail=$FAIL ========"
[[ "$FAIL" -eq 0 ]]
