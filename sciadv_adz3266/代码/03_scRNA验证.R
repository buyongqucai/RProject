source("配置.R", encoding = "UTF-8")
setup_script_env()

suppressPackageStartupMessages({
  library(tidyverse)
})

intersect_path <- file.path(PATHS$表格, "鼠源_MAMs交集.csv")
if (!file.exists(intersect_path)) stop("请先运行 02_鼠源MAMs交集与细胞定位.R")

intersect_mouse <- read.csv(intersect_path, stringsAsFactors = FALSE)
genes <- unique(intersect_mouse$gene)
if (length(genes) == 0) {
  message("鼠源交集为空，跳过 scRNA 验证")
  quit(save = "no", status = 0)
}

seurat_rds <- file.path(PROJECT_ROOT, "GSE207363", "源数据", "中间文件", "GSE207363_seurat.rds")
if (!file.exists(seurat_rds)) {
  message("未找到 GSE207363 Seurat 对象 (", seurat_rds, ")，跳过 scRNA 验证")
  quit(save = "no", status = 0)
}

source(file.path(PROJECT_ROOT, "共享脚本", "工具_单细胞差异分析.R"), encoding = "UTF-8")
check_scrna_dependencies()

obj <- readRDS(seurat_rds)
if (!requireNamespace("Seurat", quietly = TRUE)) stop("需要 Seurat")

plot_genes <- head(genes, min(20, length(genes)))
p <- Seurat::DotPlot(obj, features = plot_genes, group.by = "seurat_clusters") + RotatedAxis()
ggplot2::ggsave(file.path(PATHS$图形, "鼠源_MAMs交集_DotPlot.pdf"), p, width = 12, height = 6)

mams <- read.csv(PATHS$mams_mouse, stringsAsFactors = FALSE)
mams_present <- intersect(mams$gene, rownames(obj))
if (length(mams_present) >= 5) {
  obj <- Seurat::AddModuleScore(obj, features = list(mams_present), name = "MAMs_score")
  score_col <- grep("^MAMs_score", colnames(obj@meta.data), value = TRUE)[1]
  meta <- obj@meta.data
  if ("group" %in% colnames(meta)) {
    score_summary <- meta %>% group_by(seurat_clusters, group) %>% summarise(mean_score = mean(.data[[score_col]], na.rm = TRUE), .groups = "drop")
    write.csv(score_summary, file.path(PATHS$表格, "GSE207363_MAMs_ModuleScore.csv"), row.names = FALSE)
  }
}

message("完成: 03_scRNA验证.R")
