---
name: bioinfo-gsea-pathway
description: >-
  基因集富集与通路 / GSEA-Pathway：ORA/GSEA/GSVA（供任意组学调用）。工具：clusterProfiler, GSVA, enrichplot, ggplot2。
  触发：GSEA, GO, KEGG, GSVA, 富集。
---

# 基因集富集与通路 / GSEA-Pathway

## 1. 数据来源

DEG 或有序 logFC

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- ORA/GSEA/GSVA（供任意组学调用）
- 山水用途层标签：解释

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

ID 映射→ORA/GSEA→作图

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `clusterProfiler` | 核心 R 包 | |
| 分析 | `GSVA` | 核心 R 包 | |
| 分析 | `enrichplot` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

对齐 [高分期刊出图范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) **Fig1-f / Fig2-E·F / Fig3-C·D**：

| 分析 | 必出图种 | recipe |
|------|----------|--------|
| ORA | **水平柱**（按 ontology 分色）或气泡点图 | `plot_enrich_hbar_facet` / `plot_enrich_dot_journal` |
| GSEA | enrichment 曲线 + NES/p 上图 | enrichplot 或等价；禁止仅用棒棒糖顶替 |
| GSVA | 通路活性热图或箱线+jitter | `scale_fill_diverging_rb` / `plot_box_jitter_journal` |

**强制：** 输入 DEG/有序统计量可溯源（禁止编造基因集结果）；DPI≥600；SVG+PNG；图面 English；每图 [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)。**棒棒糖不作默认。**

## 7. 数据结果解读

基因集选择影响结果

## 8. 能否结合其它生信

全部组学下游；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`
