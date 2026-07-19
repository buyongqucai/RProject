---
name: bioinfo-rna-editing
description: >-
  RNA编辑与修饰 / RNAEditing：A-to-I 或 m6A 峰。工具：exomePeak2, REDItools。
  触发：RNA编辑, m6A, MeRIP。
---

# RNA编辑与修饰 / RNAEditing

## 1. 数据来源

RNA-seq 或 MeRIP

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- A-to-I 或 m6A 峰
- 山水用途层标签：病因-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

call 位点/峰→差异→注释

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `exomePeak2` | 核心 R 包 | |
| 上游/主分析 | `REDItools` | CLI 工具 | 非 R |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

峰注释图；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

区分 SNV 与编辑

## 8. 能否结合其它生信

转录组、表观；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`
