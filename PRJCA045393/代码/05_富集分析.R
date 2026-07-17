source("配置.R", encoding = "UTF-8")
setup_script_env()

suppressPackageStartupMessages({
  library(clusterProfiler)
  library(tidyverse)
  library(ggplot2)
  library(org.Mm.eg.db)
})

prefix <- file.path(PATHS$中间数据, DATASET)
deg_sig <- readRDS(paste0(prefix, "_deg_sig.rds"))
if (nrow(deg_sig) == 0) stop("无显著差异基因")

genes_up <- deg_sig %>% filter(log2FC > 0) %>% pull(gene)
genes_down <- deg_sig %>% filter(log2FC < 0) %>% pull(gene)
genes_all <- deg_sig$gene

map_to_entrez <- function(ids) {
  suppressMessages(bitr(ids, fromType = cfg$id_type, toType = "ENTREZID", OrgDb = org.Mm.eg.db))
}

entrez_all <- map_to_entrez(genes_all)
entrez_up <- map_to_entrez(genes_up)
entrez_down <- map_to_entrez(genes_down)

run_go <- function(entrez_ids) {
  if (nrow(entrez_ids) < 3) return(NULL)
  enrichGO(gene = entrez_ids$ENTREZID, OrgDb = org.Mm.eg.db, ont = "BP",
           pAdjustMethod = "BH", pvalueCutoff = 0.05, qvalueCutoff = 0.2, readable = TRUE)
}
run_kegg <- function(entrez_ids) {
  if (nrow(entrez_ids) < 3) return(NULL)
  enrichKEGG(gene = entrez_ids$ENTREZID, organism = "mmu",
             pAdjustMethod = "BH", pvalueCutoff = 0.05, qvalueCutoff = 0.2)
}

save_and_plot <- function(res, csv_name, pdf_name, title) {
  if (is.null(res) || nrow(as.data.frame(res)) == 0) return(invisible(NULL))
  write.csv(as.data.frame(res), file.path(PATHS$表格, csv_name), row.names = FALSE)
  p <- dotplot(res, showCategory = min(15, nrow(as.data.frame(res)))) + ggtitle(title)
  ggsave(file.path(PATHS$图形, pdf_name), p, width = 10, height = 6)
}

save_and_plot(run_go(entrez_all), paste0(DATASET, "_GO生物过程.csv"), paste0(DATASET, "_GO生物过程图.pdf"), "GO BP")
save_and_plot(run_kegg(entrez_all), paste0(DATASET, "_KEGG通路.csv"), paste0(DATASET, "_KEGG通路图.pdf"), "KEGG")
save_and_plot(run_go(entrez_up), paste0(DATASET, "_GO生物过程_上调.csv"), paste0(DATASET, "_GO生物过程_上调图.pdf"), "GO BP Up")
save_and_plot(run_go(entrez_down), paste0(DATASET, "_GO生物过程_下调.csv"), paste0(DATASET, "_GO生物过程_下调图.pdf"), "GO BP Down")
message("完成: 05_富集分析.R")
