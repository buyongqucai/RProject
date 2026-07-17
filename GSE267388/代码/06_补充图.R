source("配置.R", encoding = "UTF-8")
setup_script_env()
source(file.path(PROJECT_ROOT, "共享脚本", "工具_富集与质控图.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA可视化.R"), encoding = "UTF-8")

suppressPackageStartupMessages({
  library(tidyverse)
})

deg <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_deg.rds")))
deg_sig <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_deg_sig.rds")))

plot_volcano(deg, title = paste(DATASET, "差异基因火山图"),
             out_path = file.path(PATHS$图形, paste0(DATASET, "_火山图.pdf")),
             padj_cut = DEG_PADJ, lfc_cut = DEG_LOGFC)

# 全部样本表达矩阵（QC/PCA 用）：bulk 直接用矩阵；scRNA 聚合为 pseudobulk
if (identical(cfg$type, "bulk_rnaseq") || identical(cfg$type, "microarray")) {
  expr_all <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_expr_matrix.rds")))
  info_all <- as.data.frame(readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_sample_info.rds"))))
  rownames(info_all) <- info_all$sample
  expr_all <- as.matrix(expr_all[, info_all$sample, drop = FALSE])
  if (max(expr_all, na.rm = TRUE) > 50) expr_all <- log2(expr_all + 1)
} else {
  suppressPackageStartupMessages(library(Seurat))
  obj <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_seurat.rds")))
  pb <- build_pseudobulk_matrix(obj)
  expr_all <- pb$expr
  info_all <- pb$sample_info
}

# QC 箱线图 + 质控PCA + PCA（分组虚线框）：使用全部样本，反映数据整体质量
make_qc_and_pca_plots(expr_all, info_all, DATASET, PATHS$图形)

# Top50 热图：仅对比组样本
keep <- info_all$group %in% cfg$contrast
expr_c <- expr_all[, info_all$sample[keep], drop = FALSE]
info_c <- info_all[keep, , drop = FALSE]
info_c$group <- factor(info_c$group, levels = cfg$contrast)
make_top50_heatmap(expr_c, info_c, deg_sig, DATASET, PATHS$图形)

run_enrichment_full(deg_sig, DATASET, PATHS$表格, PATHS$图形,
                    org_db = cfg$org_db, kegg_org = cfg$kegg_org,
                    id_type = cfg$id_type)

message("完成: 06_补充图.R (", DATASET, ")")
