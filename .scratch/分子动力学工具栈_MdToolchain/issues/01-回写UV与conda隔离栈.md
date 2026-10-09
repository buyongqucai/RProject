# 回写 MD 工具栈：UV Python + conda md-tools(AmberTools) + GPU GROMACS

标签: 已完成
Blocked by: （无）

## 目标
将 2026-10-09 本机实测工具栈写入技能 SSOT（安装与使用），技能说明只留指针。

## 验收
- [x] SOP §9.0/9.6/9.8/9.9/§10 反映：UV `~/md-venv`、conda env `md-tools`、`~/activate-md.sh`、GPU GROMACS 2024.4 + gcc-12 host、踩坑 gcc>12
- [x] 技能说明软件栈表 + 一键调用含 `source ~/activate-md.sh`
- [x] 脚本 README 指向 SOP
- [x] 准备包 README / 02 说明默认 Amber 走 conda `md-tools`（源码为备选）
- [x] 出图 FROZEN 文件一字未动

## 实测版本锚点（2026-10-09 CreazyWork）
- Ubuntu-24.04 @ E:\WSL\Ubuntu\ext4.vhdx
- uv 0.12.24；Python 3.12.3；acpype 2026.10.8；gmx_MMPBSA 1.7.0；impi-rt
- AmberTools 26.0 @ conda env md-tools
- GROMACS 2024.4 CUDA @ ~/gromacs-gpu；nvcc 12.0；host gcc-12；GPU RTX 4080 SUPER
