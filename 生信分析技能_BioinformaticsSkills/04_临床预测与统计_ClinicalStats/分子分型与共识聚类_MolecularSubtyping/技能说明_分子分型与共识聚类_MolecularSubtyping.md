---
name: bioinfo-subtyping
description: >-
  分子分型与共识聚类 / MolecularSubtyping：无监督亚型。工具：ConsensusClusterPlus, ggplot2。
  触发：分子分型, 共识聚类, ConsensusClusterPlus。
---

# 分子分型与共识聚类 / MolecularSubtyping

## 1. 数据来源

肿瘤表达谱

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 无监督亚型
- 山水用途层标签：病因-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

一致性聚类→标志基因→临床关联

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `ConsensusClusterPlus` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

一致性热图；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

k 选择主观性

## 8. 能否结合其它生信

生存、免疫浸润；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`
