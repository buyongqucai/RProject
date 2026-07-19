---
name: bioinfo-longread
description: >-
  长读长测序分析 / LongRead：组装/校正/甲基化。工具：NanoMethViz, minimap2, Medaka。
  触发：长读长, ONT, PacBio。
---

# 长读长测序分析 / LongRead

## 1. 数据来源

ONT/PacBio

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 组装/校正/甲基化
- 山水用途层标签：—

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

比对→校正→组装或甲基化

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `NanoMethViz` | 核心 R 包 | |
| 上游/主分析 | `minimap2` | CLI 工具 | 非 R |
| 上游/主分析 | `Medaka` | CLI 工具 | 非 R |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

质量图；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

错误率模型依赖版本

## 8. 能否结合其它生信

组装、SV；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 9. 外部软件操作 SOP（BLOCKED 样例）

样例 `STATUS=BLOCKED`。NanoPlot → minimap2 → Clair3/Sniffles2；English QC 图。

## 样例验证

样例：`01_样例_sample/`
