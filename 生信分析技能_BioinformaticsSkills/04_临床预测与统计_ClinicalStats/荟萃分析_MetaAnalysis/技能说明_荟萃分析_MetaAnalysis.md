---
name: bioinfo-meta-analysis
description: >-
  荟萃分析 / MetaAnalysis：从 GEO-TCGA 拆出的荟萃方法。工具：meta, metafor, ggplot2。
  触发：荟萃, meta, 森林图, 异质性。
---

# 荟萃分析 / MetaAnalysis

## 1. 数据来源

多队列效应量或 DEG 方向

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 从 GEO-TCGA 拆出的荟萃方法
- 山水用途层标签：比较

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

效应量→固定/随机→异质性→森林图

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `meta` | 核心 R 包 | |
| 分析 | `metafor` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

森林图；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

异质性须报告

## 8. 能否结合其它生信

GEO-TCGA、生存；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`
