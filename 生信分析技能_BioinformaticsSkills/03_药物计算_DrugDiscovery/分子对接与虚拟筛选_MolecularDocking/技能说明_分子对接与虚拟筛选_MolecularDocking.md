---
name: bioinfo-molecular-docking
description: >-
  分子对接与虚拟筛选 / MolecularDocking：验证靶点结合、虚筛排序；山水 M16。工具：bio3d, ggplot2, AutoDock Vina, Open Babel。
  触发：分子对接, Vina, 虚拟筛选。
---

# 分子对接与虚拟筛选 / MolecularDocking

## 1. 数据来源

PDB/AlphaFold 结构；配体 3D

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 验证靶点结合、虚筛排序；山水 M16
- 山水用途层标签：药物-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

受体/配体准备→对接→打分排序→姿态分析→出图

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `bio3d` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `AutoDock Vina` | CLI 工具 | 非 R |
| 上游/主分析 | `Open Babel` | CLI 工具 | 非 R |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

结合能条图、2D 相互作用图；**DPI≥600；SVG+PNG；图面 English；防遮挡**。

**对齐高分期刊范式：** 遵循 [期刊范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) + [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)；近邻水平柱/点图。**网络药理学视觉轨已 FROZEN，本技能不得改网药样例图。**

## 7. 数据结果解读

打分近似；勿单凭对接定药效

## 8. 能否结合其它生信

网络药理、蛋白结构、MD、ADMET；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 9. 外部软件操作 SOP（BLOCKED 样例）

样例 `STATUS=BLOCKED`。受体 PDBQT + Open Babel 配体 → AutoDock Vina → bio3d/ggplot 结合能条形图。

## 样例验证

样例：`01_样例_sample/`
