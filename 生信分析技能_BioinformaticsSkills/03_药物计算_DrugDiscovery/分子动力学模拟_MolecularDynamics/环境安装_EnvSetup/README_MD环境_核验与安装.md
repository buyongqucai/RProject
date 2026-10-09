# MD 环境：核验结论与安装指引（E 盘 · **2026-10-09 现行**）

> 依据：[`复合物MD流水线_GromacsSop.md`](../文档_docs/复合物MD流水线_GromacsSop.md) **§9.8 / §10**  
> 分工：**UV** = Python（`~/md-venv`）；**conda env `md-tools`** = 仅 AmberTools；**源码** = GPU GROMACS（`~/gromacs-gpu`）。  
> 联接：`E:\md_kit` → 本目录。出图 FROZEN 文件勿改。  
> Origin：✅ 已装 `E:\Origin\Origin64.exe`（2026-10-09）；CSV 建议 `E:\Origin_Data\<项目>\`。

## 装什么

| 组件 | 方案 | 说明 |
|------|------|------|
| WSL2 Ubuntu-24.04 | → `E:\WSL\Ubuntu` | 忽略 docker-desktop |
| UV + `~/md-venv` | acpype / gmx_MMPBSA / impi-rt | Python ≥3.12 |
| conda `md-tools` | AmberTools 26.x | **不要**在此 env pip 装 acpype |
| GROMACS GPU | `03_构建GPU版GROMACS.sh` | 2024.4；**gcc-12** host（防 nvcc×gcc13） |
| 激活 | `~/activate-md.sh` | 每次跑 MD 前 `source` |

## 推荐手输顺序（隔离栈）

```bash
# 1) UV（若尚未）
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv venv ~/md-venv --python 3.12
uv pip install --python ~/md-venv/bin/python "acpype>=2026.9.4" "gmx_MMPBSA>=1.7.0" impi-rt

# 2) Miniconda + md-tools（仅 AmberTools；遇 ToS 先 conda tos accept）
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
source $HOME/miniconda3/bin/activate
conda create -y -n md-tools --override-channels \
  -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge ambertools

# 3) activate-md.sh（见 SOP §9.8 示例）后编 GROMACS
source ~/activate-md.sh
bash /mnt/e/md_kit/03_构建GPU版GROMACS.sh   # 需 gcc-12

# 4) 烟测
source ~/activate-md.sh
bash /mnt/e/md_kit/04_烟测_3HTB.sh           # SMOKE PASS
```

## 脚本说明

| 文件 | 用途 |
|------|------|
| `02_环境内引导_bootstrap_md_env.sh` | 默认 `AMBER_METHOD=conda`（跳过 Amber，只装 UV）；`source`/`binary` 为备选 |
| `03_构建GPU版GROMACS.sh` | GPU 构建；强制 gcc-12 |
| `04_烟测_3HTB.sh` | 默认 Amber 路径：`~/miniconda3/envs/md-tools/bin` |
| `00_*.ps1` / 桌面 bat | 可选一键；编码敏感，手输更稳 |

## 验收

`source ~/activate-md.sh` 后：

- `which acpype` → `.../md-venv/...`
- `which antechamber` → `.../envs/md-tools/...`
- `gmx --version` → `GPU support: CUDA`
- 烟测 → `SMOKE PASS`

本机锚点（2026-10-09）：见技能 SOP §10。
