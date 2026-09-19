---
name: differential-analysis-and-umap
description: >-
  差异分析和UMAP：从 GEO/NGDC 搜集官方 bulk 或 scRNA-seq 数据集，完成下载、质控、
  差异表达分析（limma-voom / edgeR-TMM pseudobulk / Seurat FindMarkers）、
  UMAP 单细胞可视化与 GO/KEGG 富集，并产出标准图集（火山图、质控箱线图、质控PCA、
  Top50 热图、UMAP、细胞比例图、GO/KEGG dotplot+barplot）；还包含延展生信分析
  （跨物种保守基因整合、GSEA、代谢重编程 GSVA/AUCell、WGCNA 共表达模块、
  转录因子/通路活性 decoupleR、虚拟敲除 in silico KO、细胞通讯配体-受体）与综合报告。
  内置统一图表规范（中文字体、火山图标签防遮挡、QC 全样本、PCA 分组虚线框、富集标签折行）
  与数据真实性核对（样本数对齐 GEO、剔除汇总列、防编造分组）。
  当用户要求搜集/分析 GEO 或 NGDC 数据集、做差异分析、绘制 UMAP、pseudobulk、细胞注释、
  富集分析，或做多组学/代谢/虚拟敲除/细胞通讯/WGCNA/TF 活性等延展分析并出报告时使用。
---

# 差异分析与UMAP流水线 / DEG-UMAP

生产级流水线：从 GEO/NGDC 搜集 bulk/scRNA，完成 DEG、UMAP、富集与延展分析。主战场：脓毒症心肌病（SCM/SIC）四数据集，物种以小鼠为主。  
本组：`生信分析技能_BioinformaticsSkills/06_已落地流水线_ProductionPipelines/差异分析与UMAP流水线_DEG-UMAP/`。

## 1. 数据来源

GEO / NGDC 官方下载；本地目录 `书清项目/GSE*****/`；共享工具 `书清项目/共享脚本/`。

## 2. 数据规范（判断是否可用）

- **只用官方真实数据**：分组来自 GEO SOFT / series matrix；禁止模拟矩阵与编造分组  
- **样本数 = GEO 官方**；剔除 `average/汇总` 列；先过 [数据真实性验证](../../00_基础_Foundation/数据真实性验证_DataAuthenticity/技能说明_数据真实性验证_DataAuthenticity.md)  
- 可复现：独立数据集目录 + `set.seed`；诚实报告（无显著不放宽阈值凑数）

## 3. 何时选用本技能

- 用户要跑**已落地**的四数据集/同类 GEO bulk+scRNA 全流程（含标准图集与延展分析）  
- 编排表中「脓毒症心肌病四数据集主线」  

不适用：全新组学类型（代谢/ChIP/GWAS）应走对应组学技能，而非本流水线。

## 4. 数据处理方法

下载校验 → 预处理（bulk QC 或 Seurat）→ 注释 → DEG（limma / edgeR-TMM pseudobulk / FindMarkers）→ 标准图 + GO/KEGG → 可选延展分析。细节见 [`文档_docs/生产流水线SOP_ProductionPipeline.md`](文档_docs/生产流水线SOP_ProductionPipeline.md)。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| GEO | `GEOquery` + 书清 `工具_GEO元数据.R` | 下载/元数据 | |
| bulk 差异 | `limma` | voom/lmFit | |
| scRNA | `Seurat`, `harmony`（可选） | 聚类/UMAP | |
| pseudobulk | `edgeR` | TMM+voom | 每组≥3 重复 |
| 富集 | `clusterProfiler`, `org.Mm.eg.db` | GO/KEGG | |
| 延展 | `GSVA`/`AUCell`, `WGCNA`, `decoupleR` 等 | 见延展表 | |
| 出图 | 书清 `工具_统一出图.R` / 出版级出图 | DPI≥600 | 可视化技能 |

## 6. 数据可视化

标准图集对齐 [高分期刊出图范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md)：

| 流水线图 | 范式面板 | 备注 |
|----------|----------|------|
| QC 箱线 / PCA | Fig1-b/c | `plot_pca_journal` |
| 火山 / Top50 热图 | Fig2-A/B | `plot_volcano_journal`；BWR 热图 |
| GO/KEGG bar+dot | Fig1-f / Fig3-C | 水平柱或气泡；**勿默认棒棒糖** |
| UMAP + 比例 | Fig3-A/B/G | `bioinfo_umap_discrete` |
| 延展 GSEA/GSVA/AUCell/KM | Fig2-E·F / Fig3-D–H | 签名与生存须真实临床 |

**强制：** 官方 GEO/NGDC；真实性门禁；DPI≥600；SVG+PNG；图面 English；每图 [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)。详见 [图表规范_PlotStandards.md](图表规范_PlotStandards.md) 与 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。NetPharm 视觉轨不在本流水线覆盖范围。

## 7. 数据结果解读

报告上/下调与通路；pseudobulk 全基因单向偏移优先查 TMM；细胞类型图例禁纯数字簇号。

## 8. 能否结合其它生信

编排入口；转录组/单细胞方法论技能；真实性与可视化强制依赖；延展分析接多组学叙事。

## 样例验证

样例：`01_样例_sample/`（**data_provenance=REAL**）

| 臂 | 数据 | 图 |
|----|------|-----|
| bulk DEG | Bioconductor `airway` → limma/edgeR | 火山 / PCA / TopDEG 热图 |
| sc UMAP | 山水 `GSE164522` subsample | 细胞类型 UMAP |

复跑：`代码文件/01_run_sample.R`。

生产细节 → [`文档_docs/生产流水线SOP_ProductionPipeline.md`](文档_docs/生产流水线SOP_ProductionPipeline.md)。  
图表：[`图表规范_PlotStandards.md`](图表规范_PlotStandards.md)；排错：[`参考_Reference.md`](参考_Reference.md)；延展：[`延展分析_ExtendedAnalysis.md`](延展分析_ExtendedAnalysis.md)。

