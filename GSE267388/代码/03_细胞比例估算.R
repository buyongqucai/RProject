# bulk：marker 基因集估算细胞比例（输出表格，绘图见 04_可视化.R）

source("配置.R", encoding = "UTF-8")
setup_script_env()
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA细胞注释.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_bulk可视化.R"), encoding = "UTF-8")

suppressPackageStartupMessages(library(tidyverse))

mat <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_expr_matrix.rds")))
sample_info <- as.data.frame(readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_sample_info.rds"))))
rownames(sample_info) <- sample_info$sample

ct_scores <- bulk_marker_scores(mat, CARDIAC_MARKERS)
prop_df <- bind_rows(lapply(rownames(ct_scores), function(sid) {
  sc <- ct_scores[sid, , drop = TRUE]
  if (sum(sc) == 0) sc <- rep(1 / length(sc), length(sc))
  tibble(sample = sid, group = sample_info$group[sid],
         celltype = names(sc), score = sc, proportion = sc / sum(sc))
}))
write.csv(prop_df, file.path(PATHS$表格, paste0(DATASET, "_估算细胞比例.csv")), row.names = FALSE)
message("完成: 03_细胞比例估算.R (", nrow(sample_info), " 样本, ", length(CARDIAC_MARKERS), " 细胞类型)")
