# 差异分析和UMAP — 参考细节

## 1. 数据下载（GEO）

用 `工具_NCBI接口.R` / `工具_GEO元数据.R`：

```r
source(file.path(PROJECT_ROOT, "共享脚本", "工具_NCBI接口.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_GEO元数据.R"), encoding = "UTF-8")
gse <- cfg$gse_id
fname <- paste0(gse, "_RAW.tar")
tar_path <- file.path(PATHS$源数据, fname)
if (!file.exists(tar_path)) geo_download_file(gse, fname, PATHS$源数据)
geo_verify_download(tar_path, min_bytes = 500e6)          # 校验体积，防截断
geo_save_manifest(gse, url, tar_path, PATHS)              # 记录下载清单
```

嵌套 tar.gz（每个 GSM 一个）递归解包：

```r
extract_dir <- file.path(PATHS$源数据, paste0(gse, "_RAW"))
untar(tar_path, exdir = extract_dir)
nested <- list.files(extract_dir, pattern = "GSM.*\\.tar\\.gz$", full.names = TRUE)
for (nt in nested) {
  subdir <- file.path(extract_dir, tools::file_path_sans_ext(basename(nt)))
  if (!dir.exists(subdir) || length(list.files(subdir)) == 0) untar(nt, exdir = subdir)
}
tenx_dirs <- find_10x_dirs(extract_dir)
counts_list <- setNames(lapply(tenx_dirs, parse_10x_from_dir), basename(tenx_dirs))
```

**分组来自官方元数据**（GEO SOFT / series matrix 的 characteristics），
落库为 `sample_meta.csv`（列：`sample, geo_accession, group, ...`）。禁止手工编造。

大文件下载可能被安全策略拦截，需在工具调用里带 `request_smart_mode_approval`。

## 2. bulk 预处理与差异（02_预处理与质控.R / 02_差异分析.R）

- 若 `max(expr) > 100` 做 `log2(x+1)`；microarray 用 `normalizeBetweenArrays(method="quantile")`。
- 重复基因符号用 `limma::avereps()` 合并（取均值）。
- QC 箱线图 + 质控PCA（`prcomp(t(expr), scale.=TRUE)`）。
- DEG：

```r
group <- factor(sample_info$group, levels = cfg$contrast)
design <- model.matrix(~ 0 + group); colnames(design) <- levels(group)
cm <- makeContrasts(contrasts = paste0(cfg$contrast[1], "-", cfg$contrast[2]), levels = design)
if (max(mat) > 50) { v <- voom(mat, design); fit <- lmFit(v, design) } else fit <- lmFit(log2(mat+1), design)
fit2 <- eBayes(contrasts.fit(fit, cm))
deg <- topTable(fit2, number = Inf, adjust.method = "BH")
```

## 3. scRNA 预处理（02_单细胞预处理.R）

```r
obj <- merge(objs[[1]], y = objs[-1], add.cell.ids = names(objs))
obj <- run_seurat_qc_cluster(obj)     # NormalizeData→FindVariableFeatures→ScaleData→PCA→Neighbors→Clusters→UMAP
if ("JoinLayers" %in% ls("package:Seurat")) obj <- JoinLayers(obj, assay = "RNA")
saveRDS(obj, file.path(PATHS$中间数据, paste0(DATASET, "_seurat.rds")))
```

meta.data 必含 `sample` 与 `group` 两列（后续聚合/分组依赖）。

## 4. 细胞注释（工具_scRNA细胞注释.R）

`CARDIAC_MARKERS`（小鼠心肌）：

- Cardiomyocytes `Myh6,Tnnt2,Rbm20`；Endothelial `Pecam1,Cdh5,Kdr`
- Fibroblasts `Col1a1,Dcn,Pdgfra`；Fibroblasts_activated `Postn,Acta2,Cthrc1`
- Macrophages `Adgre1,Cd68,Csf1r`；Monocytes `Ly6c2,Ccr2`；Granulocytes `S100a8,Ly6g`
- T_cells `Cd3d,Trbc2`；NK_cells `Nkg7,Klrb1c`；B_cells `Cd79a,Ms4a1`
- Smooth_muscle `Myh11,Tagln`；Pericytes `Rgs5,Pdgfrb`

用法：`obj <- annotate_clusters_by_markers(obj, CARDIAC_MARKERS, "celltype")`。
免疫亚群：`immune_obj <- subset_immune_recluster(obj)`（按 Ptprc/免疫评分取子集并重聚类）。

## 5. scRNA 差异分析

### 5a. pseudobulk（edgeR-TMM + voom，每组 ≥3 重复推荐）

```r
agg <- AggregateExpression(obj, assays = "RNA", group.by = "sample",
                           slot = "counts", return.seurat = FALSE)
pb <- as.matrix(agg$RNA)
# 列名对齐：AggregateExpression 把 '_' 换成 '-'
usam <- unique(as.character(obj$sample))
map_clean <- setNames(usam, make.names(gsub("_", "-", usam)))
cn <- make.names(colnames(pb)); colnames(pb) <- ifelse(cn %in% names(map_clean), map_clean[cn], colnames(pb))
grp <- factor(obj$group[match(colnames(pb), as.character(obj$sample))], levels = cfg$contrast)
keep <- grp %in% cfg$contrast; pb <- pb[, keep]; grp <- droplevels(grp[keep])

library(edgeR); library(limma)
dge <- DGEList(pb, group = grp)
dge <- dge[filterByExpr(dge, group = grp), , keep.lib.sizes = FALSE]
dge <- calcNormFactors(dge, method = "TMM")             # 关键：组成归一化
design <- model.matrix(~ 0 + grp); colnames(design) <- levels(grp)
cm <- makeContrasts(contrasts = paste0(cfg$contrast[1], "-", cfg$contrast[2]), levels = design)
fit2 <- eBayes(contrasts.fit(lmFit(voom(dge, design), design), cm))
deg <- topTable(fit2, number = Inf, adjust.method = "BH")
```

**校验**：`median(deg$log2FC)` 应接近 0，且 up/down 双向。若中位数很大且全部单向，
说明归一化缺失或样本聚合错误（cell→sample 匹配问题）。

### 5b. FindMarkers（细胞级 Wilcoxon，低重复回退）

```r
obj <- JoinLayers(obj, assay = "RNA"); Idents(obj) <- obj$group
obj_sub <- subset(obj, cells = WhichCells(obj, expression = group %in% cfg$contrast))
deg <- FindMarkers(obj_sub, ident.1 = cfg$contrast[1], ident.2 = cfg$contrast[2],
                   logfc.threshold = 0, min.pct = 0.1)
deg <- deg %>% mutate(gene = rownames(.)) %>%
  rename(log2FC = avg_log2FC, padj = p_val_adj, pvalue = p_val)
```

未装 `presto` 时 FindMarkers 用基础 Wilcoxon，几万细胞可能耗时 10–20 分钟；
可选装 presto 加速。

## 6. 补充图与富集（工具_富集与质控图.R）

关键函数：

- `build_pseudobulk_matrix(obj, "sample", "group")` → `list(expr=log2CPM, sample_info)`
- `make_qc_and_pca_plots(expr, sample_info, DATASET, PATHS$图形)`
- `make_top50_heatmap(expr, sample_info, deg_sig, DATASET, PATHS$图形)`
- `run_enrichment_full(deg_sig, DATASET, PATHS$表格, PATHS$图形, org_db, kegg_org, id_type)`

`run_enrichment_full` 每类输出 dotplot（`名字.pdf`）+ barplot（`名字图.pdf`）+ 表
（`名字.csv`）；类别 = 全部/上调/下调 GO-BP + 全部 KEGG。样本数 <3 时不画置信椭圆。

`06_补充图.R` 通用模板（bulk 用表达矩阵，scRNA 用 pseudobulk）：

```r
source("配置.R", encoding = "UTF-8"); setup_script_env()
source(file.path(PROJECT_ROOT, "共享脚本", "工具_富集与质控图.R"), encoding = "UTF-8")
deg <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_deg.rds")))
deg_sig <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_deg_sig.rds")))
if (cfg$type %in% c("bulk_rnaseq","microarray")) {
  expr <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_expr_matrix.rds")))
  sample_info <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_sample_info.rds")))
  # 取 contrast 组、必要时 log2
} else {
  obj <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_seurat.rds")))
  obj <- subset(obj, cells = WhichCells(obj, expression = group %in% cfg$contrast))
  pb <- build_pseudobulk_matrix(obj); expr <- pb$expr; sample_info <- pb$sample_info
}
make_qc_and_pca_plots(expr, sample_info, DATASET, PATHS$图形)
make_top50_heatmap(expr, sample_info, deg_sig, DATASET, PATHS$图形)
run_enrichment_full(deg_sig, DATASET, PATHS$表格, PATHS$图形, cfg$org_db, cfg$kegg_org, cfg$id_type)
```

## 7. 标准图集清单（每个数据集应齐备）

| 文件后缀 | 来源 |
|----------|------|
| `_火山图.pdf` | scRNA 可视化 / bulk 04 |
| `_质控箱线图.pdf` `_质控PCA.pdf` `_PCA.pdf` | `make_qc_and_pca_plots` |
| `_Top50热图.pdf` | `make_top50_heatmap` |
| `_GO生物过程(.pdf/图.pdf)` `_..._上调(.pdf/图.pdf)` `_..._下调(.pdf/图.pdf)` | `run_enrichment_full` |
| `_KEGG通路(.pdf/图.pdf)` | `run_enrichment_full` |
| `_UMAP_细胞类型.pdf` `_UMAP_免疫聚类.pdf` `_UMAP_免疫谱系.pdf` | scRNA：`save_all_scrna_figures`；bulk：`save_all_bulk_figures`（样本级 marker 签名 UMAP） |
| `_细胞比例环图.pdf` `_分组细胞比例堆叠图.pdf` | scRNA only |

下调 GO 缺失是合理的：当无显著下调基因或无富集结果时不产图，如实说明。

## 8. 排错速查

| 症状 | 原因 / 处理 |
|------|-------------|
| `subscript ... logical subscript too long` | v5 多 layer 未合并；改用 `AggregateExpression` |
| `data layers are not joined` | `FindMarkers` 前先 `JoinLayers(obj, assay="RNA")` |
| DEG 全部单向、`median(log2FC)`≈15 | pseudobulk 缺 TMM，加 `calcNormFactors` |
| `DESeqDataSet ... single variable` | 每组样本数不足；改 limma-voom 或 FindMarkers |
| `Barcode file missing` | `_RAW.tar` 为嵌套 tar.gz，需递归解包 |
| `scale_y_continuous not exported from scales` | 用 `ggplot2::scale_y_continuous` + `scales::percent_format()` |
| Rscript 段错误(-1073741819) | 复杂 `-e` 内联导致，改写成脚本文件运行 |

## 9. Windows / R 环境

- R 位置：`E:\R-4.6.0\bin\Rscript.exe`，需在 PATH。
- 运行：`E:\R-4.6.0\bin\Rscript.exe --vanilla 脚本.R`（在数据集 `代码/` 目录下）。
- 依赖：Seurat, tidyverse, limma, edgeR, DESeq2, clusterProfiler, org.Mm.eg.db,
  pheatmap, RColorBrewer, ggrepel, enrichplot（见 `共享脚本/安装依赖.R`）。
