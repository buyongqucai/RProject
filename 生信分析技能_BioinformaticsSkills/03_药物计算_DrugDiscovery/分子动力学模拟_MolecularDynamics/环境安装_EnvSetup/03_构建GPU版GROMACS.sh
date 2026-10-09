#!/usr/bin/env bash
# 03_构建GPU版GROMACS.sh — WSL2 + CUDA 源码构建 GPU 加速 GROMACS（SOP §9.8 第2条）
# 用法： bash 03_构建GPU版GROMACS.sh [版本]     # 默认 2024.4
# 前置：WSL2 + NVIDIA Windows 驱动（wsl 内 nvidia-smi 可见）；约 20-60 min
# 产物：~/gromacs-gpu/bin/gmx（--version 显示 GPU-accelerated: CUDA）
set -euo pipefail

GMX_VER="${1:-2024.4}"
PREFIX="$HOME/gromacs-gpu"
JOBS="$(nproc)"

if [[ -x "$PREFIX/bin/gmx" ]]; then
  echo "已构建过，跳过：$PREFIX/bin/gmx（删除该目录可强制重建）"
  "$PREFIX/bin/gmx" --version | grep -iE "CUDA|GPU" || true
  exit 0
fi

echo "== 1) GPU 可见性检查 =="
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,driver_version --format=csv,noheader | head -1
else
  echo "FAIL: wsl 内无 nvidia-smi。请先在 Windows 装/更新 NVIDIA 驱动（WSL2 支持版），并确认 wsl --status 正常。"
  exit 1
fi

echo "== 2) CUDA 编译器（nvcc） =="
if ! command -v nvcc >/dev/null 2>&1; then
  # 路线1：NVIDIA 官方 WSL 仓库（推荐，版本新）
  if ! dpkg -s cuda-keyring >/dev/null 2>&1; then
    wget -q https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
    sudo dpkg -i cuda-keyring_1.1-1_all.deb && sudo apt-get update -y
  fi
  sudo apt-get install -y cuda-nvcc cuda-cudart-dev cuda-cccl || {
    # 路线2：Ubuntu 通用包兜底（版本略旧，够用）
    echo "WARN: NVIDIA 仓库失败，改用 Ubuntu nvidia-cuda-toolkit"
    sudo apt-get install -y nvidia-cuda-toolkit
  }
fi
nvcc --version | tail -2

echo "== 2b) Host compiler for nvcc (Ubuntu 24.04 needs GCC<=12) =="
# Default gcc on noble is often 13+; many CUDA toolkits error: unsupported GNU version >12.
if ! command -v gcc-12 >/dev/null 2>&1 || ! command -v g++-12 >/dev/null 2>&1; then
  sudo apt-get install -y gcc-12 g++-12
fi
export CC=gcc-12 CXX=g++-12 CUDAHOSTCXX=g++-12
gcc-12 --version | head -1
g++-12 --version | head -1

echo "== 3) 下载 GROMACS ${GMX_VER} 源码 =="
SRC="$HOME/gromacs-src"
if [[ ! -d "$SRC/gromacs-${GMX_VER}" ]]; then
  mkdir -p "$SRC"
  TARBALL="gromacs-${GMX_VER}.tar.gz"
  curl -fL --retry 3 -o "/tmp/$TARBALL" "https://ftp.gromacs.org/gromacs/${TARBALL}" || \
    curl -fL --retry 3 -o "/tmp/$TARBALL" "https://github.com/gromacs/gromacs/archive/refs/tags/v${GMX_VER}.tar.gz"
  tar -xzf "/tmp/$TARBALL" -C "$SRC"
fi
cd "$SRC"/gromacs-"${GMX_VER}"* 2>/dev/null || cd "$SRC"/gromacs-*"$(echo "$GMX_VER" | tr -d .)"*

echo "== 4) 配置（GPU/CUDA，自带 FFTW，单机无 MPI；host=gcc-12） =="
rm -rf build
cmake -B build -DGMX_GPU=CUDA -DGMX_BUILD_OWN_FFTW=ON -DGMX_MPI=OFF \
      -DCMAKE_C_COMPILER=gcc-12 -DCMAKE_CXX_COMPILER=g++-12 \
      -DCMAKE_CUDA_HOST_COMPILER=g++-12 \
      -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$PREFIX"

echo "== 5) 编译（${JOBS} 线程，20-60 min） =="
cmake --build build -j"$JOBS"
cmake --install build

echo "== 6) 验证 =="
"$PREFIX/bin/gmx" --version | grep -iE "CUDA|GPU" || { echo "FAIL: 版本未显示 CUDA"; exit 1; }
grep -qxF 'export PATH="$HOME/gromacs-gpu/bin:$PATH"' "$HOME/.bashrc" || \
  echo 'export PATH="$HOME/gromacs-gpu/bin:$PATH"' >> "$HOME/.bashrc"
echo "GPU GROMACS 就绪：$PREFIX/bin/gmx"
echo "下一步：用 3HTB 烟测（NS=0.02）确认 mdrun 走 GPU，对比 CPU 版步/s。"
