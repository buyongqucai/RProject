---
name: bioinfo-spatial-advanced
description: >-
  空间转录组进阶 / SpatialAdvanced：高分辨空间与反卷积。工具：Seurat, Giotto。
  触发：空间转录组, Visium, Xenium, MERFISH。
---

# 空间转录组进阶 / SpatialAdvanced

## 1. 数据来源

Visium/Xenium 等

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 高分辨空间与反卷积
- 山水用途层标签：病因-细胞

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

QC→聚类→反卷积→共定位

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `Seurat` | 核心 R 包 | |
| 分析 | `Giotto` | 核心 R 包 | |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

空间着色图；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

分辨率平台差异大

## 8. 能否结合其它生信

scRNA、细胞通讯；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`
