# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(
    r"E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/"
    r"分子动力学模拟_MolecularDynamics/文档_docs/复合物MD流水线_GromacsSop.md"
)
text = p.read_text(encoding="utf-8")
marker = "### 9.8 环境安装 SOP"
idx = text.find(marker)
if idx < 0:
    raise SystemExit("marker not found")

new_tail = r"""### 9.8 本机环境安装（WSL2 · **2026-10-09 现行：UV Python + conda `md-tools`(仅 AmberTools) + GPU GROMACS**）

> **分工（用户确认 2026-10-09）：**
> - **UV** → 只管 Python：`~/md-venv`（acpype / gmx_MMPBSA / impi-rt）
> - **conda/Miniconda** → 只建隔离环境 `md-tools`，**只装 AmberTools 二进制**（不做 Python 环境管理）
> - **源码** → GPU 版 GROMACS → `~/gromacs-gpu`
> - **一键激活**：`~/activate-md.sh`（拼 PATH：`md-venv` 在前，保证 `python`/`acpype` 不落到 conda）
> 安装包（E 盘）：`努力学习项目/网络毒理学_菌群代谢物双交集/准备文件/MD环境/`；联接 `E:\md_kit`。
> 旧「整包 conda env `md`」与「AmberTools 仅 micromamba→/opt」见 git 历史；沙盒烟测见 `报告_P1-3_MD环境与烟测.md`。

1. **WSL2**：`wsl --install -d Ubuntu-24.04 --location E:\WSL\Ubuntu`（忽略 `docker-desktop`；虚拟盘 `E:\WSL\Ubuntu\ext4.vhdx`）。
2. **UV（Python 唯一管理器）**：
   - `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - `uv venv ~/md-venv --python 3.12`（**必须 ≥3.12**，acpype≥2026.9.4）
   - `uv pip install --python ~/md-venv/bin/python "acpype>=2026.9.4" "gmx_MMPBSA>=1.7.0" impi-rt`
     （**必须 `impi-rt`**，否则 gmx_MMPBSA 因 mpi4py 缺 libmpi 启动即崩）
3. **AmberTools（conda 隔离 env，推荐）**：
   - Miniconda → `~/miniconda3`；若遇 ToS：`conda tos accept` 后对 forge 使用 `--override-channels`
   - `conda create -y -n md-tools --override-channels -c <tuna conda-forge> ambertools`
   - **禁止**在 `md-tools` 里再 `pip install acpype`（Python 只走 UV）
   - 备选：`AMBER_METHOD=source` 装到 `/opt/ambertools`，或 `binary` micromamba 前缀（见准备包 `02_*.sh`）
4. **GROMACS GPU（源码，脚本 `03_构建GPU版GROMACS.sh`）**：
   - 最小 CUDA：`cuda-nvcc cuda-cudart-dev cuda-cccl`（WSL 仓库）
   - ⚠️ Ubuntu 24.04 默认 **GCC 13+**，CUDA 12.0 nvcc **不支持 >12** → 装 `gcc-12 g++-12`，
     cmake 使用 `-DCMAKE_C_COMPILER=gcc-12 -DCMAKE_CXX_COMPILER=g++-12 -DCMAKE_CUDA_HOST_COMPILER=g++-12`
   - 默认版本 **2024.4**，前缀 `~/gromacs-gpu`；验收：`gmx --version` 含 `GPU support: CUDA`
5. **激活脚本 `~/activate-md.sh`**（示例）：
   ```bash
   source "$HOME/miniconda3/etc/profile.d/conda.sh"
   conda activate md-tools
   export PATH="$HOME/.local/bin:$HOME/md-venv/bin:$HOME/gromacs-gpu/bin:$PATH"
   ```
6. **验证**：`source ~/activate-md.sh` →
   `which acpype` 含 `md-venv`；`which antechamber` 含 `envs/md-tools`；
   `gmx --version` 含 CUDA → 再跑准备包 `04_烟测_3HTB.sh`（`SMOKE PASS`）。

> 版本锚点（CreazyWork 2026-10-09）：uv 0.12.24；acpype 2026.10.8；gmx_MMPBSA 1.7.0；
> AmberTools 26.0（md-tools）；GROMACS 2024.4 CUDA；nvcc 12.0；host gcc-12；GPU RTX 4080 SUPER。

### 9.9 踩坑登记（回填提醒）

1. Windows 写出的 .sh/.mdp 是 CRLF → WSL bash/grompp 报错；**必须转 LF**。
2. mol2 分子名 GBK 中文 → acpype UnicodeDecodeError（见 9.1.3）。
3. ambermd.org 表单须 `multipart/form-data`（curl -F）；`-d` 会挂起。
4. Ubuntu 24.04 apt 无 ambertools 包；PyPI 无 antechamber；**UV 不能给 AmberTools 建 venv**。
5. solvate/genion 重复追加 topol.top（见 9.4）。
6. ions 步 grompp 需 `-maxwarn 1`（见 9.4）。
7. `gmx select` 赋值命名语法在 2023.3 不可用 → 全程默认组（见 9.5）。
8. 性能参考：GPU 版正式研究 ≥100 ns；演示/烟测 `NS=0.02`～`0.2`。
9. **CUDA nvcc + GCC>12**：`unsupported GNU version` → 用 gcc-12 作 host compiler（§9.8 第 4 条）。
10. **conda ToS**：`CondaToSNonInteractiveError` → `conda tos accept` 或 `--override-channels` 只用 forge。
11. **Windows 控制台托管 `wsl|Tee`**：UTF-8 中文进度易乱码 → 安装脚本 echo 用 ASCII；或 `chcp 65001`。
12. **PATH 顺序**：`conda activate` 后须把 `~/md-venv/bin` 放前面，否则 `python`/`acpype` 可能落到 conda。

## 10. 运行环境登记（**2026-10-09 本机实测现行**；更早 conda 整包/apt CPU 见 git）

| 项 | 值 | 备注 |
|----|----|------|
| GROMACS | **2024.4**（`~/gromacs-gpu`，CUDA） | host **gcc-12**；nvcc 12.0；非 apt CPU 版 |
| 运行层 | WSL2 `Ubuntu-24.04` | 虚拟磁盘 `E:\WSL\Ubuntu\ext4.vhdx` |
| Windows 调用 | `wsl -d Ubuntu-24.04 -- bash -lc 'source ~/activate-md.sh; …'` | E 盘 → `/mnt/e/...`；联接 `E:\md_kit` |
| Python（UV） | `~/md-venv`：acpype **2026.10.8**、gmx_MMPBSA **1.7.0**、impi-rt；Python **3.12.3** | **不**用 conda 管 Python |
| AmberTools | conda env **`md-tools`**：AmberTools **26.0** | 仅二进制；`antechamber` 等 |
| 激活 | `~/activate-md.sh` | 拼 PATH：UV + md-tools + gromacs-gpu |
| GPU | **RTX 4080 SUPER**（WSL 内 `nvidia-smi`） | |
| Origin | ⏸ 暂缓 | 出图层；计算不依赖 |
| LigPlot+ | `E:\LigPlus`（若已装） | 二维相互作用脚本见 `脚本_scripts/` |
| 配套（Windows） | PyMOL `E:\pymol`、OpenBabel 3.1.1、Vina、MGLTools | 对接/格式转换 |

**历史锚点（勿当作现行安装目标）：** 2026-08-30 曾用 apt GROMACS 2023.3 + Miniforge env `md` 跑通 3HTB 0.2 ns E2E（`STATUS=REAL`）；2026-10-08 沙盒 UV+conda-forge GROMACS 2026.3 烟测 PASS。现行以本表 2026-10-09 行为准。
"""

p.write_text(text[:idx] + new_tail, encoding="utf-8")
print("OK", p)