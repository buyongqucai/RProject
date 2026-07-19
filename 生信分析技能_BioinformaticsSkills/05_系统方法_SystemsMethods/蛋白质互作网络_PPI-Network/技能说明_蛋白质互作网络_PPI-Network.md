---
name: bioinfo-ppi
description: >-
  蛋白质互作网络 / PPI-Network：疾病基因 PPI（不含成分网络药理）。工具：STRINGdb, igraph, ggplot2, Cytoscape。
  触发：PPI, STRING, 互作网络。
---

# 蛋白质互作网络 / PPI-Network

## 1. 数据来源

基因/蛋白列表

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 疾病基因 PPI（不含成分网络药理）
- 山水用途层标签：解释

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

STRING→过滤→拓扑→hub

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `STRINGdb` | 核心 R 包 | |
| 分析 | `igraph` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `Cytoscape` | CLI 工具 | 非 R |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

网络图；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

数据库偏倚

## 8. 能否结合其它生信

网络药理边界、GSEA；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`
