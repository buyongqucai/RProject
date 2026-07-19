---
name: bioinfo-methylation
description: >-
  DNA甲基化分析 / WGBS-RRBS：CpG 差异甲基化（含 EPIC）。工具：bsseq, minfi, DSS, ggplot2。
  触发：甲基化, WGBS, RRBS, EPIC, 450K。
---

# DNA甲基化分析 / WGBS-RRBS

## 1. 数据来源

WGBS/RRBS 或 Illumina 芯片

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- CpG 差异甲基化（含 EPIC）
- 山水用途层标签：病因-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

导入→QC→DMP/DMR→注释富集

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `bsseq` | 核心 R 包 | |
| 分析 | `minfi` | 核心 R 包 | |
| 分析 | `DSS` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

曼哈顿/火山；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

细胞组成混杂

## 8. 能否结合其它生信

转录组、液体活检；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`
