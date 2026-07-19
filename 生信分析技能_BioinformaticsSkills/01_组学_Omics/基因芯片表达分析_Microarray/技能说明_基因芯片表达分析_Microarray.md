---
name: bioinfo-microarray
description: >-
  基因芯片表达分析 / Microarray：芯片归一化 DEG（并列 RNA-seq）。工具：affy, limma, ggplot2。
  触发：芯片, Affymetrix, microarray。
---

# 基因芯片表达分析 / Microarray

## 1. 数据来源

GEO 芯片

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 芯片归一化 DEG（并列 RNA-seq）
- 山水用途层标签：病因-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

读入→RMA→limma→富集

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `affy` | 核心 R 包 | |
| 分析 | `limma` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

对齐 [高分期刊出图范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) **Fig2-A/B**：MA/火山、可选 Top 热图；`plot_volcano_journal`；分组色一致。

**强制：** REAL GEO（如 GSE10072）；DPI≥600；SVG+PNG；图面 English；每图 [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)。

## 7. 数据结果解读

探针注释版本

## 8. 能否结合其它生信

GEO、GSEA；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`
