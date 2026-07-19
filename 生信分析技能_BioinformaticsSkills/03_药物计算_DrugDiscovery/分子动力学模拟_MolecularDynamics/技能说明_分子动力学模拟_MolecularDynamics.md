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

## 样例验证

样例：`01_样例_sample/`
