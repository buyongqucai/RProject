---
name: bioinfo-wgcna
description: >-
  共表达网络WGCNA / WGCNA：共表达模块与性状关联。工具：WGCNA, ggplot2。
  触发：WGCNA, 共表达, 模块。
---

# 共表达网络WGCNA / WGCNA

## 1. 数据来源

bulk 表达样本足够

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 共表达模块与性状关联
- 山水用途层标签：解释

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

软阈值 → TOM → 动态剪枝模块 → 模块特征基因（ME）→ 与性状相关 → 可选 hub/富集。

样例流程（GSE10072）：方差 Top 基因 → `WGCNA::adjacency`（power=6）→ `TOMsimilarity` → `cutreeDynamic` → `moduleEigengenes` → 与吸烟性状 `cor`。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 共表达 | `WGCNA` | soft-threshold / TOM / ME | 需 `dynamicTreeCut` |
| 备用 | `stats::hclust` | 无 WGCNA 时层次模块 | 样例含 fallback |
| 出图 | `ggplot2` + PublicationPlot | 模块热图/趋势/样本树 | `plot_severity_trend_journal` / `plot_sample_dendrogram_journal` |

## 6. 数据可视化

树状图/模块性状；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

样本少不稳定

## 8. 能否结合其它生信

转录组、ML 标志物；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`（**data_provenance=REAL**，`GSE10072`）

- 缓存：`real_GSE10072_expr_topVar.csv` + `real_GSE10072_sample_meta.csv`
- 复跑：`代码文件/run_sample.R`
- 图：模块–性状热图、模块大小、ME 趋势、样本树状图
- 对齐期刊 Fig1-a/d 风格（树状 + 模块趋势）
