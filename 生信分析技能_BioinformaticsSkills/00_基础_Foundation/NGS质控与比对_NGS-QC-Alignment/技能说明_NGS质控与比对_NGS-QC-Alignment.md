---
name: bioinfo-ngs-qc
description: >-
  NGS质控与比对 / NGS-QC-Alignment：各测序技能公共前置。工具：FastQC, MultiQC, BWA, STAR, samtools。
  触发：FastQC, MultiQC, 比对, BAM。
---

# NGS质控与比对 / NGS-QC-Alignment

## 1. 数据来源

原始 FASTQ

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 各测序技能公共前置
- 山水用途层标签：基础

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

FastQC→修剪→比对→BAM 统计

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| （本技能以 CLI/网页为主） | — | 见 CLI 列 | |
| 上游/主分析 | `FastQC` | CLI 工具 | 非 R |
| 上游/主分析 | `MultiQC` | CLI 工具 | 非 R |
| 上游/主分析 | `BWA` | CLI 工具 | 非 R |
| 上游/主分析 | `STAR` | CLI 工具 | 非 R |
| 上游/主分析 | `samtools` | CLI 工具 | 非 R |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

MultiQC 报告；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

质量阈值依实验

## 8. 能否结合其它生信

几乎所有测序技能；出图强制 [统一可视化规范](../统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`
