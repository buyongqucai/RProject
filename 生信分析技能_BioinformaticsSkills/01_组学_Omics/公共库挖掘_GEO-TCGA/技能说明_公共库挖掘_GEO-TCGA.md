---
name: bioinfo-geo-tcga
description: >-
  公共库挖掘 GEO-TCGA：下载、元数据、队列整理与真实性门禁。
  生存/荟萃/ROC 请分别调用独立技能。R包：GEOquery、TCGAbiolinks。书清 GEO 工具可对接。
---

# 公共库挖掘 / GEO-TCGA

## 1. 数据来源

GEO series matrix / SOFT；TCGA/GDC 表达与临床；书清：`工具_GEO元数据.R`、`工具_NCBI接口.R`。

## 2. 数据规范（判断是否可用）

**强制**先读 [数据真实性验证](../../00_基础_Foundation/数据真实性验证_DataAuthenticity/技能说明_数据真实性验证_DataAuthenticity.md)：样本数=官网；分组官方可溯源；TCGA 随访定义清楚。

## 3. 何时选用本技能

- 需要从 GEO/TCGA **下载与整理队列**（公共数据挖掘入口）  
- 编排：临床预后主线的数据层（随后接生存/ROC 独立技能）  

不适用：无公共登录号；已有干净矩阵只需做 KM/Cox（直接用生存技能）。

## 4. 数据处理方法

下载与元数据整理 → 真实性核对 →（可选）交给转录组做 DEG → **生存 / 荟萃 / ROC 分别调用独立技能**（本技能不替代它们）。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| GEO | `GEOquery` | 矩阵/临床 | 书清工具封装 |
| TCGA | `TCGAbiolinks` | GDC 下载 | |
| 差异（可选） | `limma`/`edgeR`/`DESeq2` | DEG | 接转录组技能 |
| 出图 | `ggplot2` + 出版级出图 | 队列 QC 图 | DPI≥600 |
| 真实性 | 书清 `数据真实性核对.R` | 门禁 | 强制 |

生存/荟萃/ROC 包表见：`生存分析与预后模型_Survival`、`荟萃分析_MetaAnalysis`、`诊断效能ROC_DiagnosticROC`。

## 6. 数据可视化

对齐 [高分期刊出图范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) **Fig1-b/c（队列 QC）与 Fig2 临床层入口**：

| 步骤 | 图种 | 说明 |
|------|------|------|
| 队列 QC | PCA、组织/分组箱线 | `plot_pca_journal`；分组色=`bioinfo_groups` |
| DEG（可选，接转录组/芯片） | 火山、热图 | 勿在本技能编造矩阵 |
| 预后（下游 Survival） | KM + risk table | `bioinfo_survival` |

**强制：** accession 与 n 经真实性验证；DPI≥600；SVG+PNG；每图 [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)。样例：GSE10072 肺腺癌 vs 正常。

## 7. 数据结果解读

公共数据混杂多，用「关联」表述；样本数必须对齐官网。

## 8. 能否结合其它生信

强制下游可接：`生存分析与预后模型_Survival`、`荟萃分析_MetaAnalysis`、`诊断效能ROC_DiagnosticROC`、转录组/单细胞；多组学验证层。

## 样例验证

样例：`01_样例_sample/`
