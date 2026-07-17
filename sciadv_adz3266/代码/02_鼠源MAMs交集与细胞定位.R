source("配置.R", encoding = "UTF-8")
setup_script_env()

suppressPackageStartupMessages({
  library(tidyverse)
  library(clusterProfiler)
  library(org.Mm.eg.db)
})

deg <- read.csv(PATHS$mouse_deg, stringsAsFactors = FALSE)
mams <- read.csv(PATHS$mams_mouse, stringsAsFactors = FALSE)
table_s1 <- read.csv(PATHS$table_s1, stringsAsFactors = FALSE)

intersect_mouse <- deg %>%
  inner_join(mams, by = c("gene" = "gene")) %>%
  arrange(desc(abs(log2FC)))

write.csv(intersect_mouse,
          file.path(PATHS$表格, "鼠源_MAMs交集.csv"),
          row.names = FALSE)

message("鼠源 DEG: ", nrow(deg), " | MAMs: ", nrow(mams), " | 交集: ", nrow(intersect_mouse))

if (nrow(intersect_mouse) >= 3) {
  entrez <- bitr(intersect_mouse$gene, fromType = "SYMBOL", toType = "ENTREZID", OrgDb = org.Mm.eg.db)
  ego <- enrichGO(gene = entrez$ENTREZID, OrgDb = org.Mm.eg.db, ont = "BP", pAdjustMethod = "BH", readable = TRUE)
  if (!is.null(ego) && nrow(as.data.frame(ego)) > 0) {
    write.csv(as.data.frame(ego), file.path(PATHS$表格, "鼠源_MAMs交集_GO.csv"), row.names = FALSE)
  }
}

genes <- intersect_mouse$gene
map_tbl <- table_s1 %>%
  filter(gene %in% genes) %>%
  group_by(gene) %>%
  arrange(desc(avg_log2FC), .by_group = TRUE) %>%
  mutate(rank = row_number()) %>%
  ungroup()

primary <- map_tbl %>% filter(rank == 1) %>% select(gene, primary_celltype = cluster, max_log2FC = avg_log2FC, pct.1, pct.2, p_val_adj)
cell_loc <- intersect_mouse %>%
  left_join(primary, by = "gene") %>%
  left_join(map_tbl %>% count(gene, name = "n_clusters"), by = "gene")

write.csv(cell_loc, file.path(PATHS$表格, "鼠源_MAMs交集_细胞定位.csv"), row.names = FALSE)
write.csv(map_tbl, file.path(PATHS$表格, "鼠源_MAMs交集_TableS1明细.csv"), row.names = FALSE)

write.csv(deg, file.path(PATHS$export, "mouse_deg_significant.csv"), row.names = FALSE)
write.csv(intersect_mouse, file.path(PATHS$export, "mouse_mams_intersection.csv"), row.names = FALSE)
write.csv(cell_loc, file.path(PATHS$export, "mouse_celltype_mapping.csv"), row.names = FALSE)
write.csv(mams, file.path(PATHS$export, "mouse_mams_geneset.csv"), row.names = FALSE)

expr_rds <- file.path(PROJECT_ROOT, "GSE171546", "源数据", "中间文件", "GSE171546_expr_matrix.rds")
if (file.exists(expr_rds)) {
  expr <- readRDS(expr_rds)
  sample_info <- readRDS(file.path(PROJECT_ROOT, "GSE171546", "源数据", "中间文件", "GSE171546_sample_info_final.rds"))
  write.csv(cbind(gene = rownames(expr), as.data.frame(expr)), file.path(PATHS$export, "mouse_expr_matrix.csv"), row.names = FALSE)
  write.csv(sample_info, file.path(PATHS$export, "mouse_sample_meta.csv"), row.names = FALSE)
} else {
  message("未找到 GSE171546 表达矩阵 RDS，跳过 mouse_expr_matrix 导出")
}

if (nrow(intersect_mouse) > 0) {
  p <- ggplot(cell_loc, aes(x = reorder(primary_celltype, max_log2FC, FUN = median, na.rm = TRUE), y = abs(log2FC), fill = category)) +
    geom_boxplot(outlier.shape = NA) +
    geom_jitter(width = 0.15, alpha = 0.8) +
    coord_flip() +
    theme_bw() +
    labs(title = "鼠源 MAMs 交集基因 |log2FC| 按细胞类型", x = NULL, y = "|log2FC|")
  ggsave(file.path(PATHS$图形, "鼠源_MAMs交集_细胞类型分布.pdf"), p, width = 8, height = 5)
}

message("完成: 02_鼠源MAMs交集与细胞定位.R")
