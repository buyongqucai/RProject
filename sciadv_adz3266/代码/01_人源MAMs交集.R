source("配置.R", encoding = "UTF-8")
setup_script_env()

suppressPackageStartupMessages({
  library(tidyverse)
  library(clusterProfiler)
  library(org.Hs.eg.db)
})

deg <- read.csv(PATHS$human_deg, stringsAsFactors = FALSE)
mams <- read.csv(PATHS$mams_human, stringsAsFactors = FALSE)

intersect_human <- deg %>%
  inner_join(mams, by = c("gene" = "gene")) %>%
  arrange(desc(abs(log2FC)))

write.csv(intersect_human,
          file.path(PATHS$表格, "人源_MAMs交集.csv"),
          row.names = FALSE)

message("人源 DEG: ", nrow(deg), " | MAMs: ", nrow(mams), " | 交集: ", nrow(intersect_human))

if (nrow(intersect_human) >= 3) {
  entrez <- bitr(intersect_human$gene, fromType = "SYMBOL", toType = "ENTREZID", OrgDb = org.Hs.eg.db)
  ego <- enrichGO(gene = entrez$ENTREZID, OrgDb = org.Hs.eg.db, ont = "BP", pAdjustMethod = "BH", readable = TRUE)
  if (!is.null(ego) && nrow(as.data.frame(ego)) > 0) {
    write.csv(as.data.frame(ego), file.path(PATHS$表格, "人源_MAMs交集_GO.csv"), row.names = FALSE)
  }
}

write.csv(deg, file.path(PATHS$export, "human_deg_significant.csv"), row.names = FALSE)
write.csv(intersect_human, file.path(PATHS$export, "human_mams_intersection.csv"), row.names = FALSE)
write.csv(mams, file.path(PATHS$export, "human_mams_geneset.csv"), row.names = FALSE)

if (file.exists(file.path(PROJECT_ROOT, "GSE79962", "源数据", "中间文件", "GSE79962_expr_matrix.rds"))) {
  expr <- readRDS(file.path(PROJECT_ROOT, "GSE79962", "源数据", "中间文件", "GSE79962_expr_matrix.rds"))
  sample_info <- readRDS(file.path(PROJECT_ROOT, "GSE79962", "源数据", "中间文件", "GSE79962_sample_info_final.rds"))
  write.csv(cbind(gene = rownames(expr), as.data.frame(expr)), file.path(PATHS$export, "human_expr_matrix.csv"), row.names = FALSE)
  write.csv(sample_info, file.path(PATHS$export, "human_sample_meta.csv"), row.names = FALSE)
} else {
  message("未找到 GSE79962 表达矩阵 RDS，跳过 human_expr_matrix 导出（可重跑 GSE79962 02-03 脚本）")
}

message("完成: 01_人源MAMs交集.R")
