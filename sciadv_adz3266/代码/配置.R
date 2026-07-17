DATASET <- "sciadv_adz3266"
PROJECT_ROOT <- if (file.exists("RProject.Rproj")) normalizePath(".") else normalizePath("../..")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_项目路径.R"), encoding = "UTF-8")
PATHS <- init_dataset_paths(PROJECT_ROOT, DATASET)
PATHS$human_deg <- file.path(PROJECT_ROOT, "GSE79962", "结果", "表格", "GSE79962_显著差异基因.csv")
PATHS$mouse_deg <- file.path(PROJECT_ROOT, "GSE171546", "结果", "表格", "GSE171546_显著差异基因.csv")
PATHS$mams_human <- file.path(PATHS$源数据, "MAMs_基因集_人.csv")
PATHS$mams_mouse <- file.path(PATHS$源数据, "MAMs_基因集_鼠.csv")
PATHS$table_s1 <- file.path(PATHS$源数据, "adz3266_table_s1.csv")
PATHS$export <- file.path(PATHS$结果, "导出")
dir.create(PATHS$export, recursive = TRUE, showWarnings = FALSE)
DEG_PADJ <- 0.05
DEG_LOGFC <- 1.0
set.seed(42)
