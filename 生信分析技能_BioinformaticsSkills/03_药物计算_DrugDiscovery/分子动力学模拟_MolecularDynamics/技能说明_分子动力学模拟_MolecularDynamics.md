---
name: bioinfo-molecular-dynamics
description: >-
  分子动力学模拟 / MolecularDynamics：对接后稳定性/结合自由能；山水 M17；勿假装纯 R 跑 MD。
  工具栈：GROMACS GPU(CUDA)、UV(md-venv: acpype/gmx_MMPBSA)、conda env md-tools(仅 AmberTools)。
  触发：分子动力学, GROMACS, MD, RMSD, acpype, MM-GBSA, AmberTools。交付范式 FROZEN（2026-09-03）。
---

# 分子动力学模拟 / MolecularDynamics

> **出图与交付 SSOT：** [`文档_docs/出图与交付约束_MdFigureStandards.md`](文档_docs/出图与交付约束_MdFigureStandards.md) — **`FROZEN`（2026-09-03）**。改图册序/Origin recipe/报告结构前须你说「解冻」。  
> **计算/环境 SSOT：** [`文档_docs/复合物MD流水线_GromacsSop.md`](文档_docs/复合物MD流水线_GromacsSop.md)（§9 流程、§9.8 安装、§10 本机登记）。本入口不复述长 SOP。  
> 登记：[`已跑通范式登记_FrozenParadigms.md`](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/已跑通范式登记_FrozenParadigms.md)。

## 1. 数据来源

实验复合物优先；没有目标配体共晶时用同口袋近缘结构作参照；两者都没有才用对接姿态。判据与口袋限制见 SOP §9.0.1。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 对接后稳定性/结合自由能；山水 M17；勿假装纯 R 跑 MD
- 山水用途层标签：药物-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。高斯不是必备（电荷默认可 AM1-BCC）。

## 4. 数据处理方法

溶剂化→最小化→平衡→生产→RMSD/RMSF/氢键/MM-GBSA（细节见 SOP）

## 5. 工具链（2026-10-09 现行）

| 步骤 | 工具 | 作用 | 备注 |
|------|------|------|------|
| 激活 | `source ~/activate-md.sh` | 拼 PATH | **每次跑 MD 前** |
| Python | UV `~/md-venv` | acpype、gmx_MMPBSA、impi-rt | Python≥3.12；**不用 conda 管 Python** |
| 配体拓扑引擎 | conda env `md-tools` | AmberTools（antechamber 等） | 仅二进制隔离；禁止往里 pip acpype |
| 动力学 | `~/gromacs-gpu/bin/gmx` | GROMACS **2024.4 CUDA** | 源码编；host **gcc-12**（Ubuntu 24.04） |
| 分析 CSV | R `bio3d` 等 | xvg→表 | |
| 出图 | Origin（`origin出图_plotMdOrigin.py`） | DPI≥600 PNG+SVG | 分析曲线/FEL/能量柱必须 Origin |

安装步骤见 SOP §9.8；安装包在本技能 `环境安装_EnvSetup/`（联接 `E:\md_kit`）。

## 6. 数据可视化

RMSD/RMSF 曲线；**DPI≥600；SVG+PNG；图面 English；防遮挡**。本技能出图 **FROZEN**（见出图约束）。

## 7. 数据结果解读

力场、时长和有无熵项决定能说什么。短轨迹（如 0.2 ns）禁止写成发表级 ΔG / 长期稳定结合。

报告金标：`01_样例_sample/代码文件/结果文件/报告文件/样例报告_SampleReport_v1.html`

## 8. 能否结合其它生信

分子对接、蛋白结构；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 9. 蛋白-配体复合物 MD 流水线

**执行 SOP（强制）：** [`文档_docs/复合物MD流水线_GromacsSop.md`](文档_docs/复合物MD流水线_GromacsSop.md)。  
**出图/交付 FROZEN：** [`文档_docs/出图与交付约束_MdFigureStandards.md`](文档_docs/出图与交付约束_MdFigureStandards.md)。

```bash
wsl -d Ubuntu-24.04 -- bash -lc '
  source ~/activate-md.sh
  cd <工作目录> && \
  LIGAND_RES=JZ4 NET_CHARGE=0 NS=1 \
  bash <技能根>/脚本_scripts/运行复合物MD_runComplexMd.sh . protein.pdb jz4_h.mol2
'
```

烟测：`source ~/activate-md.sh && bash /mnt/e/md_kit/04_烟测_3HTB.sh` → 期望 `SMOKE PASS` + `CUDA acceleration`。

**过程监控 / 异常即停（正式长轨迹）：** SOP §9.5.1；`CHUNK_NS=1 MONITOR=1`。飞出则停并留 `md.cpt`，**不续跑同一对接初态**；按 §9.0.1 用实验位姿重搭后排队。口袋不要撑开再对接（§9.0.1「口袋不放大」）。过程草图在 `monitor/`（非 Origin 金标）；交付图仍为样例 **01–26**。

## 样例验证

样例：`01_样例_sample/`（**范式 FROZEN 2026-09-03**）。MD 计算侧见上述 SOP。
