---
name: bioinfo-mr
description: >-
  孟德尔随机化 / MendelianRandomization：因果推断工具变量。工具：TwoSampleMR, MendelianRandomization。
  触发：孟德尔随机化, MR, TwoSampleMR。
---

# 孟德尔随机化 / MendelianRandomization

## 1. 数据来源

暴露/结局 GWAS summary

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 因果推断工具变量
- 山水用途层标签：预测

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

选 IV→协调→MR 方法→敏感性

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `TwoSampleMR` | 核心 R 包 | |
| 分析 | `MendelianRandomization` | 核心 R 包 | |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

散点/森林；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

水平多效性

## 8. 能否结合其它生信

GWAS、coloc；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`
