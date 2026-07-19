---
name: bioinfo-rnaseq
description: >-
  转录组 RNA-seq：质检、定量、limma/edgeR/DESeq2 DEG、GO/KEGG、火山/热图。
  R包：GEOquery、edgeR、DESeq2、limma、clusterProfiler。书清共享脚本可对接。
---

# 转录组分析 / RNA-seq

## 1. 数据来源

GEO/SRA/NGDC counts 或 FASTQ；自测 Illumina RNA-seq。书清：`工具_GEO元数据.R`、`工具_RNA定量.R`、`工具_富集与质控图.R`。

## 2. 数据规范（判断是否可用）

每组建议 ≥3；分组官方可溯源；剔除汇总列；库型与比对参数匹配。

## 3. 何时选用本技能

- bulk 差异表达、通路富集、组织水平机制  
- 编排主线为「转录组」或单细胞后的 bulk 验证  

不适用：必须分辨细胞类型时（应先/并行单细胞技能）。

## 4. 数据处理方法

FastQC → 定量（或作者 counts）→ TMM/sizeFactor/voom → DEG → GO/KEGG → 重复性 PCA。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 质检 | FastQC, MultiQC | 原始质量 | CLI |
| 比对定量 | HISAT2/STAR + featureCounts | 或跳过用 counts | CLI |
| GEO | `GEOquery` | 矩阵/临床 | 公共数据 |
| 差异 | `edgeR` / `DESeq2` / `limma` | DEG | count→edgeR/DESeq2；voom→limma |
| 注释库 | `org.Hs.eg.db` / `org.Mm.eg.db` | ID 映射 | 按物种 |
| 富集 | `clusterProfiler`, `enrichplot` | GO/KEGG | |
| 出图 | `ggplot2`, `ggrepel`, `pheatmap` + 出版级出图 | DPI≥600 | 可视化技能 |
| 书清 | `工具_富集与质控图.R` 等 | 生产实现 | `书清项目/共享脚本` |

## 6. 数据可视化

对齐 [高分期刊出图范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) **Fig1/Fig2**：

| 步骤 | 必出/推荐图种 | recipe |
|------|---------------|--------|
| QC | PCA、表达箱线/密度 | `plot_pca_journal` |
| DEG | 火山、Top 热图（蓝白红） | `plot_volcano_journal` / `scale_fill_diverging_rb` |
| 富集 | GO/KEGG **水平柱或气泡点** | `plot_enrich_hbar_facet` / `plot_enrich_dot_journal` |
| 可选 | 模块/基因趋势、通路评分箱线+jitter | Fig1 d/e/g–j |

**强制：** 官方 GEO/NGDC/自测 counts（禁止编造）；DPI≥600；SVG+PNG；图面 English；每图后 [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)。

## 7. 数据结果解读

报告上/下调与 Top 通路；无显著勿放宽阈值凑数；全基因组单向偏移查归一化。

## 8. 能否结合其它生信

单细胞验证亚群；蛋白/代谢同通路；GEO-TCGA 生存；ChIP 调控；多组学联合。  
生产流水线：[差异分析与UMAP流水线_DEG-UMAP](../../06_已落地流水线_ProductionPipelines/差异分析与UMAP流水线_DEG-UMAP/技能说明_差异分析与UMAP流水线_DEG-UMAP.md)

## 样例验证

样例：`01_样例_sample/`
