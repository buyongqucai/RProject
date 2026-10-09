#!/usr/bin/env bash
# 02_环境内引导_bootstrap_md_env.sh — Ubuntu-24.04(WSL2) 内构建 MD 环境（UV 版）
# 规格 = 复合物MD流水线 SOP §9.8（2026-10-08 修订：环境管理全面转 UV）
#   本脚本：apt 系统依赖 + UV + uv venv(acpype, gmx_MMPBSA) + AmberTools 二进制
#   GROMACS(GPU) 由 03_构建GPU版GROMACS.sh 负责（本脚本只做 CPU 退路可选安装）
# 用法： bash 02_环境内引导_bootstrap_md_env.sh
#   AMBER_METHOD=source   # 选方案A：源码构建 AmberTools（无 conda，耗时30-60min）
#   AMBER_METHOD=binary   # 默认：micromamba 单包分发二进制（秒级；Python 仍归 UV）
#   INSTALL_CPU_GMX=1     # 附带 apt 装 CPU 版 gromacs 作退路
set -euo pipefail

# AmberTools: binary=micromamba prefix (legacy); source=compile; conda=skip here (use conda env md-tools)
# Preferred on workstation 2026-10-09: conda create -n md-tools ambertools + UV ~/md-venv (see SOP §9.8)
AMBER_METHOD="${AMBER_METHOD:-conda}"
INSTALL_CPU_GMX="${INSTALL_CPU_GMX:-0}"

# Progress echoes are ASCII-only: Windows console hosting `wsl | Tee` is often GBK;
# WSL itself is UTF-8 (LANG=C.UTF-8). Comments may stay Chinese; stdout banners must not.
echo "== 1) apt system deps =="
sudo apt-get update -y
sudo apt-get install -y build-essential cmake curl git gfortran \
  flex bison csh libfl-dev zlib1g-dev unzip
# tleap 源码构建才需要的 GUI 库（方案A用）：libfltk1.3-dev libxft-dev —— 方案A分支内按需装

if [[ "$INSTALL_CPU_GMX" == "1" ]] && ! command -v gmx >/dev/null 2>&1; then
  echo "== 1b) CPU GROMACS fallback (GPU build = script 03) =="
  sudo apt-get install -y gromacs || echo "WARN: apt gromacs failed; script 03 can cover"
fi

echo "== 2) UV (Python env manager) =="
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"
uv --version

echo "== 3) uv venv + acpype + gmx_MMPBSA + impi-rt =="
# 坑A: acpype≥2026.9.4 要求 Python>=3.12（3.11 直接 unsatisfiable）
# 坑B: gmx_MMPBSA 启动 import mpi4py，系统无 libmpi 时启动即崩 → 装 impi-rt（PyPI Intel MPI 运行时）
VENV="$HOME/md-venv"
[[ -d "$VENV" ]] || uv venv "$VENV" --python 3.12
uv pip install --python "$VENV/bin/python" \
  "acpype>=2026.9.4" "gmx_MMPBSA>=1.7.0" impi-rt
"$VENV/bin/acpype" -h >/dev/null 2>&1 && echo "  OK acpype" || { echo "FAIL acpype"; exit 1; }
"$VENV/bin/gmx_MMPBSA" --help >/dev/null 2>&1 && echo "  OK gmx_MMPBSA (MPI loads)" || { echo "FAIL gmx_MMPBSA"; exit 1; }

echo "== 4) AmberTools (non-UV; SOP 9.8) =="
AMBER_PREFIX="${AMBER_PREFIX:-/opt/ambertools}"
if command -v antechamber >/dev/null 2>&1; then
  echo "  already present: $(command -v antechamber)"
elif [[ "$AMBER_METHOD" == "conda" ]]; then
  echo "  method conda: skip install in this script"
  echo "  Create separately: conda create -n md-tools --override-channels -c conda-forge ambertools"
  echo "  Then: source ~/activate-md.sh  (UV md-venv + conda md-tools + gromacs-gpu)"
elif [[ "$AMBER_METHOD" == "source" ]]; then
  echo "  method source: compile (30-60 min)"
  sudo apt-get install -y libfltk1.3-dev libxft-dev
  SRC=/tmp/ambertools-src
  [[ -d "$SRC" ]] || git clone --depth 1 https://github.com/Amber-MD/ambertools.git "$SRC"
  cd "$SRC"
  ./configure -prefix "$AMBER_PREFIX" || ./configure
  make -j"$(nproc)"
  sudo make install
elif [[ "$AMBER_METHOD" == "binary" ]]; then
  echo "  method binary: micromamba prefix (tuna; Python still UV)"
  if [[ ! -x "$AMBER_PREFIX/bin/antechamber" ]]; then
    curl -LsSf https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj bin/micromamba
    sudo mkdir -p "$AMBER_PREFIX"
    MAMBA_ROOT_PREFIX=/tmp/mamba-root ./bin/micromamba create -y -p "$AMBER_PREFIX" \
      --override-channels -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge ambertools
  fi
else
  echo "FAIL: AMBER_METHOD=$AMBER_METHOD (use conda|source|binary)"; exit 1
fi
if [[ "$AMBER_METHOD" != "conda" ]]; then
  command -v antechamber >/dev/null 2>&1 || ls "$AMBER_PREFIX/bin/antechamber" >/dev/null
fi

echo "== 5) PATH / activate-md.sh hint =="
PROFILE="$HOME/.bashrc"
# Prefer ~/activate-md.sh (conda md-tools + UV + gmx). Keep a minimal PATH fallback for UV+gmx only.
for line in \
  'export PATH="$HOME/.local/bin:$HOME/md-venv/bin:$HOME/gromacs-gpu/bin:$PATH"'; do
  grep -qxF "$line" "$PROFILE" 2>/dev/null || echo "$line" >> "$PROFILE"
done
export PATH="$HOME/.local/bin:$VENV/bin:$HOME/gromacs-gpu/bin:$PATH"
if [[ -x "$HOME/miniconda3/envs/md-tools/bin/antechamber" ]]; then
  export PATH="$HOME/miniconda3/envs/md-tools/bin:$PATH"
fi

echo "== 6) verify =="
for b in uv acpype gmx_MMPBSA; do
  if command -v "$b" >/dev/null 2>&1; then echo "  OK  $b -> $(command -v $b)";
  else echo "  MISS $b"; fi
done
for b in antechamber tleap sqm parmchk2; do
  if command -v "$b" >/dev/null 2>&1; then echo "  OK  $b -> $(command -v $b)";
  elif [[ "$AMBER_METHOD" == "conda" ]]; then echo "  SKIP $b (install via conda env md-tools)";
  else echo "  MISS $b"; fi
done
command -v gmx >/dev/null 2>&1 && gmx --version | head -3 || \
  echo "  NOTE: gmx not installed yet -- next: script 03 GPU GROMACS"
echo "BOOTSTRAP DONE -- next: conda md-tools (if needed) -> script 03 -> smoke (README)."
