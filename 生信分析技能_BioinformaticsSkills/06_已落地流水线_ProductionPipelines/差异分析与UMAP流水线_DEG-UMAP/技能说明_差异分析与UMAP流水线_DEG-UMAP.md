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

下载校验 → 预处理（bulk QC 或 Seurat）→ 注释 → DEG（limma / edgeR-TMM pseudobulk / FindMarkers）→ 标准图 + GO/KEGG → 可选延展分析。细节见下文「工作流程」。

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

---

## 附录：核心原则与生产细节

- **只用官方真实数据**：从 GEO（`ftp.ncbi.nlm.nih.gov`）或 NGDC/OMIX 下载。
  **禁止** 模拟表达矩阵、禁止手工编造样本分组。
- **样本数必须 = GEO 官方**：GSM 命名缺口 = 漏样本信号；脚本 `书清项目/校验/数据真实性核对.R`。
- **可复现** / **诚实报告** / **图表规范统一**（见上 §2、§6）。

## 数据集目录结构

每个数据集位于 `书清项目/GSE*****/`（如 `书清项目/GSE267388/`）：

```
书清项目/GSE267388/
├── 代码/         # 配置.R, 01_下载数据.R, 02..., 06_补充图.R, 运行全部分析.R
├── 源数据/       # 原始下载 + 中间文件/（*.rds 中间产物）
├── 结果/
│   ├── 图形/     # SVG/PNG/PDF
│   └── 表格/     # 所有 CSV 表
└── 文档/         # 数据集选型说明.md
```

共享工具脚本在 `书清项目/共享脚本/`（用相对路径 `source`）：

| 脚本（均在 `书清项目/共享脚本/`） | 作用 |
|------|------|
| `工具_项目路径.R` | `init_dataset_paths()` / `setup_script_env()` 定位路径 |
| `工具_NCBI接口.R` / `工具_GEO元数据.R` | GEO 下载、校验、SOFT 元数据解析 |
| `工具_RNA定量.R` | 10x 读取（`parse_10x_from_dir`）、矩阵解析 |
| `工具_scRNA细胞注释.R` | canonical markers + 细胞注释 + 免疫亚群重聚类 |
| `工具_scRNA可视化.R` | UMAP / 比例环图 / 堆叠柱图 / 火山图 |
| `工具_富集与质控图.R` | pseudobulk 聚合、QC 箱线图/PCA、Top50 热图、GO/KEGG |
| `工具_统一出图.R` | DPI=600；`save_plot_pub` 输出 SVG+PNG |

## 配置模板（代码/配置.R）

```r
DATASET <- "GSE267388"
PROJECT_ROOT <- if (file.exists("RProject.Rproj")) normalizePath(".") else normalizePath("../..")
source(file.path(PROJECT_ROOT, "书清项目", "共享脚本", "工具_项目路径.R"), encoding = "UTF-8")
# init_dataset_paths 需指向书清项目下数据集目录，或 PROJECT_ROOT 设为书清项目根
PATHS <- init_dataset_paths(file.path(PROJECT_ROOT, "书清项目"), DATASET)
DEG_PADJ <- 0.05; DEG_LOGFC <- 1.0
cfg <- list(
  type = "scrna",          # 或 "bulk_rnaseq" / "microarray"
  organism = "mouse", org_db = "org.Mm.eg.db", kegg_org = "mmu", id_type = "SYMBOL",
  gse_id = "GSE267388",
  contrast = c("CLP", "Steady"),   # c(实验组, 对照组)；方向 = 组1 vs 组2
  run_immune_subset = TRUE, deg_padj = 0.05, deg_logfc = 1.0
)
set.seed(42)
```

## 工作流程

复制以下清单并跟踪进度：

```
- [ ] 1. 确认物种/对比/分组（GEO 官方元数据）
- [ ] 2. 下载官方数据并校验体积（01_下载数据.R）
- [ ] 3. 预处理：bulk 走 QC/归一化；scRNA 走 Seurat QC+聚类+UMAP
- [ ] 4. 细胞注释（scRNA）+ 免疫亚群重聚类
- [ ] 5. 差异分析（按重复数选方法，见下）
- [ ] 6. 标准可视化 + 补充图 + GO/KEGG 富集
- [ ] 7. 核对图集完整；更新数据集文档
```

### 差异分析方法选择（关键）

| 场景 | 方法 | 说明 |
|------|------|------|
| bulk / microarray | `limma-voom`（count）或 `lmFit`（log 强度） | 见 `02_差异分析.R` |
| scRNA，每组 ≥3 生物学重复 | 样本级 pseudobulk + **edgeR-TMM + voom** | 必须 TMM 组成归一化，否则出现全基因单向偏移伪影 |
| scRNA，每组 <3 重复或 pseudobulk 无显著 | Seurat `FindMarkers`（Wilcoxon，细胞级） | 与低重复数据集一致；注意伪重复局限 |

DEG 结果统一列名：`gene, log2FC, pvalue, padj`；保存 `_deg.rds` 与 `_deg_sig.rds`
（`deg_sig = padj<DEG_PADJ & |log2FC|>DEG_LOGFC`）。

### UMAP 与单细胞图（scRNA）

预处理→注释后调用 `save_all_scrna_figures(obj, DATASET, PATHS, cfg, immune_obj)`：
UMAP 细胞类型 / 免疫聚类 / 免疫谱系、细胞比例环图、分组堆叠柱图、火山图。
细胞注释用 `annotate_clusters_by_markers()` + `CARDIAC_MARKERS`；免疫亚群用
`subset_immune_recluster()`。

### 标准补充图（对齐 GSE79962 图集）

`06_补充图.R` 调用 `工具_富集与质控图.R`，对 bulk 用表达矩阵、对 scRNA 用
`build_pseudobulk_matrix()`（AggregateExpression 按样本聚合 → log2CPM）产出：

- `_质控箱线图.pdf`、`_质控PCA.pdf`、`_PCA.pdf`（`make_qc_and_pca_plots`）
  —— **QC/PCA 用全部样本**（数据质量总览）；每组 ≥2 样本时 PCA 画**分组虚线框**；
  样本数 <3 时 PCA 无意义会自动跳过。
- `_Top50热图.pdf`（`make_top50_heatmap`，仅用对比组样本）
- GO/KEGG：`_GO生物过程(.pdf/图.pdf/.csv)`、`_..._上调`、`_..._下调`、
  `_KEGG通路(.pdf/图.pdf/.csv)`（`run_enrichment_full`，每类 dotplot + barplot，标签自动折行）

`_火山图.pdf` 由 `plot_volcano` 产出：ggrepel 标注 Top 上/下调基因、阈值虚线、中文标题。
所有图表样式细节与交付前自检见 [图表规范_PlotStandards.md](图表规范_PlotStandards.md)。

## 运行

```r
# 单数据集
setwd("GSE267388/代码"); source("运行全部分析.R", encoding = "UTF-8")
# 补充图（复用已算好的 DEG）
setwd("GSE267388/代码"); source("06_补充图.R", encoding = "UTF-8")
```

Windows 下用 `E:\R-4.6.0\bin\Rscript.exe --vanilla 06_补充图.R`。

## 常见坑（已踩，见 参考_Reference.md 详解）

- v5 Seurat 多 layer 对象聚合用 `AggregateExpression`，不要直接对未 `JoinLayers` 的
  counts 做 `rowSums`（列数不匹配会报 subscript 错误）。
- `AggregateExpression` 会把样本名的 `_` 换成 `-`，需做名称对齐映射。
- pseudobulk **必须 TMM 归一化**：`median(log2FC)≈15`、全基因单向即归一化缺失的信号。
- GEO `_RAW.tar` 可能是嵌套 tar.gz（每样本一个），需递归解包。
- `.xls.gz` 表达矩阵注意编码与列名（fpkm/count 列、gene_symbol 列）。
- 富集 `scale_y_continuous` 用 `ggplot2::`，百分比用 `scales::percent_format()`。

详细模板、marker 列表、排错见 [参考_Reference.md](参考_Reference.md)。

## 延展生信分析（差异分析/UMAP 之后的深入分析）

在 DEG/UMAP 基础上，围绕一条生物学主线做延展分析。方法正文已**独立成技能**（一方法一技能），本流水线负责调度书清脚本与调用下列技能说明：

| # | 分析 | 独立技能 | 书清/延展代码 |
|---|------|----------|----------------|
| 1 | 跨物种保守基因 | [跨物种基因映射_CrossSpecies](../../05_系统方法_SystemsMethods/跨物种基因映射_CrossSpecies/技能说明_跨物种基因映射_CrossSpecies.md) | 延展 `01` |
| 2 | GSEA / 通路 | [基因集富集与通路_GSEA-Pathway](../../05_系统方法_SystemsMethods/基因集富集与通路_GSEA-Pathway/技能说明_基因集富集与通路_GSEA-Pathway.md) | 延展 `02` |
| 3 | 代谢重编程评分 | GSEA-Pathway（GSVA）± 代谢组技能 | 延展 `03` |
| 4 | WGCNA | [共表达网络WGCNA_WGCNA](../../05_系统方法_SystemsMethods/共表达网络WGCNA_WGCNA/技能说明_共表达网络WGCNA_WGCNA.md) | 延展 `04` |
| 5 | TF/通路活性 | [转录因子与调控网络_TF-Network](../../05_系统方法_SystemsMethods/转录因子与调控网络_TF-Network/技能说明_转录因子与调控网络_TF-Network.md) | 延展 `05` |
| 6 | 虚拟敲除 | [虚拟敲除与扰动_InSilicoKO](../../05_系统方法_SystemsMethods/虚拟敲除与扰动_InSilicoKO/技能说明_虚拟敲除与扰动_InSilicoKO.md) | 延展 `06` |
| 7 | 细胞通讯 | [细胞通讯分析_CellCommunication](../../05_系统方法_SystemsMethods/细胞通讯分析_CellCommunication/技能说明_细胞通讯分析_CellCommunication.md) | 延展 `07` |

全部复用中间产物（`_deg.rds` / `_expr_matrix.rds` / `_seurat.rds`）。代码骨架在 `延展分析/代码/`（`00_公共函数.R` + `01–07` + `运行全部延展分析.R`）。

关键约定：
- **GSEA 用 `clusterProfiler::gseGO/gseKEGG`**（不要依赖 `msigdbr`——其数据包 `msigdbdf`
  在较新 R 上常无二进制）。
- **中文图注**：`00_公共函数.R` 用 `showtext + SimHei`，PDF 才能正确显示中文
  （否则 `mbcsToSbcs conversion failure`）。图内文字若嫌麻烦也可改英文。
- **虚拟敲除**默认是透明的 regulon 传播式 in silico KO（假设生成）；更严谨可用
  CellOracle/scTenifoldKnk 的 GRN 扰动。
- **细胞通讯**默认 curated L-R + CellPhoneDB 式均值乘积；更全面可接 CellChat/CellPhoneDB。
- 报告须逐部分写：**数据来源 / 处理 / 数据的生物学意义 / 结果的生物学意义 /
  与其它部分的关联 / 解读**，最后给"整合机制链"。范例见项目
  `延展分析/报告/脓毒症心肌病_延展生信分析报告.md`。

完整代码模板、包 API 兼容写法与排错见 [延展分析_ExtendedAnalysis.md](延展分析_ExtendedAnalysis.md)。

## 样例验证

样例：`01_样例_sample/`
