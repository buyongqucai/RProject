---
name: bioinfo-scrna-spatial
description: >-
  单细胞与空间转录组：QC、聚类、注释、UMAP、FindMarkers/pseudobulk、比例图。
  R包：Seurat、SingleR、harmony、edgeR（pseudobulk）。书清工具可对接。
---

# 单细胞与空间转录组分析 / scRNA-Spatial

## 1. 数据来源

10x 矩阵、h5ad、GEO scRNA；空间 Visium/Xenium。书清：`工具_单细胞对象.R`、`工具_富集与质控图.R`。

## 2. 数据规范（判断是否可用）

细胞数与官网一致；双细胞/线粒体阈值有据；注释有 marker 证据；**禁止用汇总列当细胞**。

## 3. 何时选用本技能

- 细胞类型定位、亚群 DEG、免疫微环境、空间定位  
- 编排：机制假说 + 细胞分辨率  

不适用：只需组织平均表达且无细胞需求（可用 bulk 转录组）。

## 4. 数据处理方法

CreateSeuratObject → QC → Normalize/Scale → PCA → 整合(harmony) → 聚类 → 注释 → UMAP → FindMarkers 或 pseudobulk DEG → 比例图。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 主框架 | `Seurat` | 对象与聚类 | 主流 |
| 注释 | `SingleR`, `celldex` | 参考注释 | 可人工校对 |
| 整合 | `harmony` 或 Seurat Integrate | 批次 | 按设计 |
| 差异(细胞) | Seurat `FindMarkers` | 簇间 | Wilcoxon 等 |
| 差异(样本) | `edgeR` / `DESeq2` | pseudobulk | 推荐有生物学重复时 |
| 富集 | `clusterProfiler` | GO/KEGG | |
| 出图 | `ggplot2`, `DimPlot` + 出版级出图 | UMAP/比例 | 可视化技能 |
| 空间 | `Seurat` / `Giotto` / `BayesSpace` | 空间 | 按平台选 |
| 书清 | `工具_单细胞对象.R` | 生产封装 | |

## 6. 数据可视化

对齐 [高分期刊出图范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) **Fig3**：

| 面板映射 | 图种 | recipe |
|----------|------|--------|
| A | UMAP 细胞类型 | `plot_umap_discrete_journal` / `bioinfo_umap_discrete` |
| B | UMAP 条件/样本/亚簇 | 同上，换着色列 |
| C | 富集气泡点图 | `plot_enrich_dot_journal` |
| E–F | AUC 直方图阈值 + feature plot | 阈值竖线；连续色 `bioinfo_feature_blue` |
| G | 堆叠比例（临床组×状态） | 与 UMAP 分组色一致 |
| 可选 | 亚群火山、QC violin | `plot_volcano_journal` |

**强制：** 细胞数/元数据可溯源（禁止编造）；DPI≥600；SVG+PNG；图例禁纯数字簇号当最终类型；每图 [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)。

## 7. 数据结果解读

报告亚群变化与 marker；cluster 编号≠生物学名称；批次与生物学混淆须声明。

## 8. 能否结合其它生信

bulk 转录组验证；细胞通讯；ChIP 调控；空间+病理；流水线 DEG-UMAP。

## 样例验证

样例：`01_样例_sample/`
