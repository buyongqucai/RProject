---
name: bioinfo-genome-assembly
description: >-
  基因组组装与注释 / GenomeAssembly：组装与基因注释。工具：rtracklayer, SPAdes, Flye, Prokka。
  触发：基因组组装, de novo, Prokka。
---

# 基因组组装与注释 / GenomeAssembly

## 1. 数据来源

测序 reads

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 组装与基因注释
- 山水用途层标签：—

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

质控→组装→评估→注释

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `rtracklayer` | 核心 R 包 | |
| 上游/主分析 | `SPAdes` | CLI 工具 | 非 R |
| 上游/主分析 | `Flye` | CLI 工具 | 非 R |
| 上游/主分析 | `Prokka` | CLI 工具 | 非 R |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

N50 等质控图；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

污染与杂合影响组装

## 8. 能否结合其它生信

变异检测、长读长；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 9. 外部软件操作 SOP（BLOCKED 样例）

样例 `STATUS=BLOCKED`。SPAdes/flye 组装 → QUAST/BUSCO → Prokka/MAKER 注释 → 英文 N50 图。

## 样例验证

样例：`01_样例_sample/`
