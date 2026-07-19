---
name: bioinfo-cmap
description: >-
  药物重定位与连通图 / CMap-L1000：表达逆转药签、重定位假说。工具：PharmacoGx, ggplot2。
  触发：CMap, L1000, 药物重定位。
---

# 药物重定位与连通图 / CMap-L1000

## 1. 数据来源

上调/下调基因签名

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 表达逆转药签、重定位假说
- 山水用途层标签：药物-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

签名→查询 CMap/L1000→药物列表→解读

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `PharmacoGx` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

连通性条图；**DPI≥600；SVG+PNG；图面 English；防遮挡**。

**对齐高分期刊范式：** 遵循 [期刊范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) + [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)；近邻水平柱（Fig1-f）。

## 7. 数据结果解读

细胞系≠组织；假说级

## 8. 能否结合其它生信

转录组、药物敏感性 GDSC；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`
