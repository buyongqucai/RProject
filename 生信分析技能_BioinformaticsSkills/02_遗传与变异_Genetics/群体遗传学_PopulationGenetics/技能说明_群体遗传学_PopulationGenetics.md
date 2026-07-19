---
name: bioinfo-popgen
description: >-
  群体遗传学 / PopulationGenetics：GWAS 上游结构。工具：PLINK, ADMIXTURE。
  触发：群体遗传, Fst, admixture。
---

# 群体遗传学 / PopulationGenetics

## 1. 数据来源

群体基因型

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- GWAS 上游结构
- 山水用途层标签：基础

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

QC→PCA→Fst/admixture

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| （本技能以 CLI/网页为主） | — | 见 CLI 列 | |
| 上游/主分析 | `PLINK` | CLI 工具 | 非 R |
| 上游/主分析 | `ADMIXTURE` | CLI 工具 | 非 R |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

PCA 图；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

采样偏差

## 8. 能否结合其它生信

GWAS；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`
