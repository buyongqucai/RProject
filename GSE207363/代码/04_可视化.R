source("配置.R", encoding = "UTF-8")
setup_script_env()
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA可视化.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA细胞注释.R"), encoding = "UTF-8")

suppressPackageStartupMessages({
  library(Seurat)
  library(ggplot2)
  library(tidyverse)
})

obj <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_seurat.rds")))
immune_obj <- NULL
if (isTRUE(cfg$run_immune_subset)) {
  immune_obj <- subset_immune_recluster(obj)
  if (!is.null(immune_obj)) {
    saveRDS(immune_obj, file.path(PATHS$中间数据, paste0(DATASET, "_immune.rds")))
  }
}
save_all_scrna_figures(obj, DATASET, PATHS, cfg, immune_obj)
message("完成: 04_可视化.R")
