# 议题 08 E2E：PBMC3k（10x Genomics 真实数据）跑通骨架四参数主链
# QC_MIN_FEATURE_FLOOR=200 → RES_GRID=0.1–1.2 聚类网格 → DE_LOGFC=1 / DE_FDR=0.05 marker 过滤
# data_provenance=REAL（10x 官方 pbmc3k_filtered_gene_bc_matrices，hg19）
options(stringsAsFactors = FALSE)
set.seed(202)

sample_root <- normalizePath("..", winslash = "/", mustWork = TRUE)
skill_root <- normalizePath("../..", winslash = "/", mustWork = TRUE)
bio_root <- normalizePath("../../..", winslash = "/", mustWork = TRUE)
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath("../../../..", winslash = "/", mustWork = TRUE)
}

viz_script <- file.path(
  bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
  "脚本_scripts", "出版级出图_PublicationPlot.R"
)
if (file.exists(viz_script)) source(viz_script, encoding = "UTF-8")

delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")

paths <- delivery_sample_paths(sample_root)
fig_dir <- paths$fig_dir
tab_dir <- paths$tab_dir
for (d in c(fig_dir, tab_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

source(file.path(skill_root, "脚本_scripts", "运行单细胞空转骨架_runScrnaSkeleton.R"), encoding = "UTF-8")

library(Seurat)
library(ggplot2)

skill_en <- "scRNA-Spatial"

# ---- 四参数（技能说明 §4 默认值） ----
qc_min_feature_floor <- 200
pb_min_samples <- 2
de_logfc <- 1
de_fdr <- 0.05
res_grid <- seq(0.1, 1.2, by = 0.1)

# ---- 01 载入 + 原始计数校验 ----
mtx_dir <- file.path(paths$raw_dir, "pbmc3k", "filtered_gene_bc_matrices", "hg19")
stopifnot("缺 PBMC3k 矩阵（见 数据文件/DATA_SOURCE.md）" = dir.exists(mtx_dir))
counts <- Read10X(mtx_dir)
chk <- validate_raw_counts_stub(counts)
message("【原始计数校验】", chk$reason)
stopifnot(chk$ok)

obj <- CreateSeuratObject(counts = counts, project = "pbmc3k", min.cells = 0, min.features = 0)
n_raw <- ncol(obj)

# ---- 02 QC（QC_MIN_FEATURE_FLOOR） ----
obj <- scrna_qc_filter(obj, min_feature_floor = qc_min_feature_floor)
message(sprintf("【QC】%d → %d 细胞（nFeature_RNA >= %d）", n_raw, ncol(obj), qc_min_feature_floor))

# ---- 03 分辨率网格（RES_GRID） ----
obj <- scrna_resolution_grid(obj, res_grid = res_grid, verbose = FALSE)
res_cols <- paste0("RNA_snn_res.", res_grid)
res_cols <- res_cols[res_cols %in% colnames(obj[[]])]
cluster_counts <- data.frame(
  resolution = res_grid[match(res_cols, paste0("RNA_snn_res.", res_grid))],
  n_clusters = vapply(res_cols, function(cl) length(unique(obj[[]][[cl]])), integer(1))
)
write.csv(cluster_counts, file.path(tab_dir, delivery_table_name(skill_en, "ResGrid", "PBMC3k")), row.names = FALSE)
message("【RES_GRID】", paste(sprintf("%s=%d簇", cluster_counts$resolution, cluster_counts$n_clusters), collapse = " "))

# 网格中位分辨率作为本演示的最终聚类（正式项目应结合 clustree/生物学判断）
res_pick <- cluster_counts$resolution[ceiling(nrow(cluster_counts) / 2)]
pick_col <- paste0("RNA_snn_res.", res_pick)
obj$cluster <- paste0("Cluster ", obj[[]][[pick_col]])
Idents(obj) <- obj[[]][[pick_col]]
message("【聚类】选用 res=", res_pick, "（", length(unique(obj$cluster)), " 簇；注释待 SingleR，簇号非最终细胞类型）")

# ---- 04 UMAP ----
obj <- RunUMAP(obj, dims = 1:30, verbose = FALSE)
emb <- as.data.frame(Embeddings(obj, "umap"))
names(emb) <- c("umap_1", "umap_2")
umap_df <- cbind(emb, cluster = obj$cluster)

# ---- 05 marker（DE_LOGFC / DE_FDR；单样本 → 探索性） ----
de_method <- choose_de_method(1, 1, pb_min = pb_min_samples)
message("【DE 方法】", de_method$method, "（每组样本数 < ", pb_min_samples, "，探索性）")
markers <- scrna_find_markers(obj, logfc = de_logfc, fdr = de_fdr, verbose = FALSE)
markers$gene <- rownames(markers)
write.csv(markers, file.path(tab_dir, delivery_table_name(skill_en, "Markers", "PBMC3k")), row.names = FALSE)
writeLines(
  paste0("DEG_method_note: 单样本 PBMC3k，细胞级 Wilcoxon 探索性（DE_LOGFC=", de_logfc, ", DE_FDR=", de_fdr, "）；非 pseudobulk"),
  file.path(tab_dir, "DEG_method_note.txt")
)
message("【marker】", nrow(markers), " 行通过 |log2FC|>=", de_logfc, " 且 FDR<=", de_fdr)

# ---- 06 出图（VizStandards：PNG+SVG，DPI>=600，标签黑色） ----
p <- plot_umap_discrete_journal(
  umap_df, x_col = "umap_1", y_col = "umap_2", label_col = "cluster",
  title = "PBMC3k cluster UMAP (10x Genomics, hg19)",
  point_size = 0.4, label_on_plot = TRUE, show_legend = FALSE, label_size = 3.0
)
delivery_save_plot(p, skill_en, "UMAP", "PBMC3kClusters", 6.8, 5.8, fig_dir, bio_root, order = 4)

# ---- 07 审计（REAL；独立文件，不覆盖 run_sample.R 的官方 AuditPost） ----
write_delivery_audit(
  skill_en, "post", nrow(counts), n_raw, 1,
  "10x PBMC3k filtered_gene_bc_matrices (hg19)",
  FALSE, "10x-pbmc3k", "运行单细胞空转骨架_runScrnaSkeleton.R 四参数主链",
  sprintf("QC floor=%d: %d→%d cells; RES_GRID 0.1-1.2; pick res=%.1f; markers=%d rows (log2FC>=%s, FDR<=%s); %s",
          qc_min_feature_floor, n_raw, ncol(obj), res_pick, nrow(markers), de_logfc, de_fdr, de_method$method),
  file.path(tab_dir, "审计后检_AuditPost_PBMC3k.csv"),
  data_provenance = "REAL"
)

message("DONE PBMC3k pipeline E2E — REAL")
