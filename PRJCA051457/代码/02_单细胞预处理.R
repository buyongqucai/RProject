source("配置.R", encoding = "UTF-8")
setup_script_env()
source(file.path(PROJECT_ROOT, "共享脚本", "工具_NGDC下载.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_单细胞差异分析.R"), encoding = "UTF-8")

suppressPackageStartupMessages({
  library(Seurat)
  library(tidyverse)
})

`%||%` <- function(x, y) if (is.null(x)) y else x

seurat_rds <- file.path(PATHS$中间数据, paste0(DATASET, "_seurat.rds"))
if (file.exists(seurat_rds)) {
  message("加载已有 Seurat 对象")
} else {
  paths <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_omix_paths.rds")))
  parsed <- parse_omix_count_matrix(paths$count, paths$metadata)
  obj <- CreateSeuratObject(counts = parsed$counts, project = DATASET)
  meta <- parsed$meta
  if ("group" %in% colnames(meta)) {
    grp_col <- meta$group
    names(grp_col) <- meta[[intersect(c("sample", "Sample", "cell", "barcode"), colnames(meta))[1]]]
    obj$group <- grp_col[colnames(obj)]
  }
  obj$sample <- obj$orig.ident
  obj <- run_seurat_qc_cluster(obj)
  saveRDS(obj, seurat_rds)
}
message("完成: 02_单细胞预处理.R")
