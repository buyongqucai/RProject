source("配置.R", encoding = "UTF-8")
setup_script_env()
source(file.path(PROJECT_ROOT, "共享脚本", "工具_单细胞差异分析.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA细胞注释.R"), encoding = "UTF-8")

suppressPackageStartupMessages({
  library(Seurat)
  library(tidyverse)
})

seurat_rds <- file.path(PATHS$中间数据, paste0(DATASET, "_seurat.rds"))
if (file.exists(seurat_rds)) {
  obj <- readRDS(seurat_rds)
} else {
  raw <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_raw_sc.rds")))
  counts <- raw$counts
  meta <- raw$meta
  objs <- list()
  for (i in seq_along(counts)) {
    sid <- names(counts)[i]
    o <- build_seurat_from_10x(counts[[i]], project = sid)
    o$sample <- sid
    o$group <- as.character(meta$group[i])
    objs[[sid]] <- o
  }
  obj <- merge(objs[[1]], y = objs[-1], add.cell.ids = names(objs))
  obj <- run_seurat_qc_cluster(obj)
  if ("JoinLayers" %in% ls("package:Seurat")) obj <- JoinLayers(obj, assay = "RNA")
  saveRDS(obj, seurat_rds)
}
obj <- filter_seurat_by_groups(obj, cfg$keep_groups)
if ("JoinLayers" %in% ls("package:Seurat")) obj <- JoinLayers(obj, assay = "RNA")
saveRDS(obj, seurat_rds)
message("Seurat 细胞数: ", ncol(obj), " | 分组: ", paste(unique(obj$group), collapse = ", "))
message("完成: 02_单细胞预处理.R")
