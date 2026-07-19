---
name: bioinfo-sv
description: >-
  结构变异分析 / StructuralVariant：大结构变异。工具：StructuralVariantAnnotation, Manta, lumpy。
  触发：结构变异, SV。
---

# 结构变异分析 / StructuralVariant

## 1. 数据来源

WGS BAM

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 大结构变异
- 山水用途层标签：病因-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

call SV→过滤→注释

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `StructuralVariantAnnotation` | 核心 R 包 | |
| 上游/主分析 | `Manta` | CLI 工具 | 非 R |
| 上游/主分析 | `lumpy` | CLI 工具 | 非 R |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

circos；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

短读长对 SV 敏感度有限

## 8. 能否结合其它生信

融合基因 RNA、长读长；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 9. 外部软件操作 SOP（BLOCKED 样例）

样例 `STATUS=BLOCKED`。Manta/Delly/Lumpy → SURVIVOR merge → AnnotSV；English SV 概览图。

## 样例验证

样例：`01_样例_sample/`
