---
name: bioinfo-splicing
description: >-
  剪接与异构体分析 / AlternativeSplicing：差异剪接/异构体。工具：ggplot2, rMATS, LeafCutter。
  触发：剪接, rMATS, 异构体。
---

# 剪接与异构体分析 / AlternativeSplicing

## 1. 数据来源

RNA-seq BAM

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 差异剪接/异构体
- 山水用途层标签：病因-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

定量→差异剪接→功能注释

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `rMATS` | CLI 工具 | 非 R |
| 上游/主分析 | `LeafCutter` | CLI 工具 | 非 R |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

火山/sashimi；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

深度不足假阴性

## 8. 能否结合其它生信

转录组、ncRNA；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`
