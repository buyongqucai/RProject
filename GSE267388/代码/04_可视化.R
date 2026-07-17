source("配置.R", encoding = "UTF-8")
setup_script_env()
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA可视化.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA细胞注释.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_bulk可视化.R"), encoding = "UTF-8")

suppressPackageStartupMessages(library(tidyverse))

mat <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_expr_matrix.rds")))
sample_info <- as.data.frame(readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_sample_info.rds"))))
save_all_bulk_figures(mat, sample_info, DATASET, PATHS, cfg)
message("完成: 04_可视化.R (", DATASET, ")")
