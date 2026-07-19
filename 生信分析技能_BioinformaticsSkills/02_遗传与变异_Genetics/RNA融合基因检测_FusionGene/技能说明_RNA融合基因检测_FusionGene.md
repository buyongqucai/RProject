---
name: bioinfo-fusion
description: >-
  RNA融合基因检测 / FusionGene：融合检出（勿并入普通 DEG）。工具：ggplot2, STAR-Fusion, Arriba。
  触发：融合基因, STAR-Fusion, Arriba。
---

# RNA融合基因检测 / FusionGene

## 1. 数据来源

肿瘤 RNA-seq

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 融合检出（勿并入普通 DEG）
- 山水用途层标签：病因-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

比对→融合 call→过滤注释

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `STAR-Fusion` | CLI 工具 | 非 R |
| 上游/主分析 | `Arriba` | CLI 工具 | 非 R |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

融合示意图；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

假阳性过滤关键

## 8. 能否结合其它生信

SV、肿瘤；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 9. 外部软件操作 SOP（BLOCKED 样例）

样例 `STATUS=BLOCKED`。STAR chimeric → STAR-Fusion / Arriba → 过滤 → `fusions.tsv` + 英文 QC 图。

## 样例验证

样例：`01_样例_sample/`
