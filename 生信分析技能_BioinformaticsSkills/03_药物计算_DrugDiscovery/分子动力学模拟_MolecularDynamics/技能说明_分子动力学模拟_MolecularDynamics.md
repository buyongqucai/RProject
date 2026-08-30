---
name: bioinfo-molecular-dynamics
description: >-
  分子动力学模拟 / MolecularDynamics：对接后稳定性/结合自由能；山水 M17；勿假装纯 R 跑 MD。工具：bio3d, ggplot2, GROMACS, Amber。
  触发：分子动力学, GROMACS, MD, RMSD。
---

# 分子动力学模拟 / MolecularDynamics

## 1. 数据来源

对接复合物或已知复合物

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 对接后稳定性/结合自由能；山水 M17；勿假装纯 R 跑 MD
- 山水用途层标签：药物-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

溶剂化→最小化→平衡→生产→RMSD/RMSF/氢键/MM-PBSA

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `bio3d` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `GROMACS` | CLI 工具 | 非 R |
| 上游/主分析 | `Amber` | CLI 工具 | 非 R |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

RMSD/RMSF 曲线；**DPI≥600；SVG+PNG；图面 English；防遮挡**。

**对齐高分期刊范式：** 遵循 [期刊范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) + [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)；近邻折线/箱线。网药视觉 **FROZEN**，勿改。

## 7. 数据结果解读

力场与时长影响结论；MM-PBSA 有近似

## 8. 能否结合其它生信

分子对接、蛋白结构；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 9. 外部软件操作 SOP（BLOCKED 样例）

样例 `STATUS=BLOCKED`。GROMACS：pdb2gmx → solvate → NVT/NPT → production → RMSD/RMSF 英文图。

## 10. 运行环境登记（2026-08-30）

| 项 | 值 | 备注 |
|----|----|------|
| GROMACS | 2023.3（Ubuntu apt `gromacs` 2023.3-1ubuntu3） | mixed precision / thread_mpi / SSE4.1，CPU 通用构建 |
| 运行层 | WSL2 `Ubuntu-24.04`（WSL 2.7.12.0） | 虚拟磁盘 `E:\WSL\Ubuntu\ext4.vhdx`（数据落 E 盘） |
| Windows 调用 | `wsl -d Ubuntu-24.04 -- gmx <args>` | 默认 root；E 盘文件经 `/mnt/e/...` 访问 |
| GPU | RTX 4060 已对 WSL2 可见（`nvidia-smi` 通过） | apt 版不含 CUDA；GPU 加速需源码构建（后续议题） |
| 配套（Windows 侧已装） | PyMOL `E:\pymol`、OpenBabel 3.1.1、Vina、MGLTools、LigPlot+ | 对接/格式转换/可视化沿用 |

**解除 BLOCKED 的前置已满足**（GROMACS 可用）。样例真实数据 E2E（pdb2gmx→生产→RMSD/RMSF 出图 + 审计 REAL）按 ADR 0002 独占迭代进行，完成前 `STATUS` 保持 BLOCKED。

## 样例验证

样例：`01_样例_sample/`
