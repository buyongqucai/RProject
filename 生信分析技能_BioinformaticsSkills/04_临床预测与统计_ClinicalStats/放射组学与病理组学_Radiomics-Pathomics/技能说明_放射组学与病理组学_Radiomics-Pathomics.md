---
name: bioinfo-radiomics
description: >-
  放射组学与病理组学 / Radiomics-Pathomics：组学特征与预后。工具：ggplot2。
  触发：放射组学, 病理组学。
---

# 放射组学与病理组学 / Radiomics-Pathomics

## 1. 数据来源

影像/病理特征表

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 组学特征与预后
- 山水用途层标签：临床

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

特征提取→筛选→模型

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `ggplot2` | 核心 R 包 | |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

同 ML 图；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

中心效应

## 8. 能否结合其它生信

生存、ROC；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 9. 外部软件操作 SOP（BLOCKED 样例）

样例 `STATUS=BLOCKED`。3D Slicer 分割 → PyRadiomics 特征 → ML 筛选 → English ROC/importance 图。

## 样例验证

样例：`01_样例_sample/`
