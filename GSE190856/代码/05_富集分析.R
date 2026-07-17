source("配置.R", encoding = "UTF-8")
setup_script_env()

suppressPackageStartupMessages({
  library(clusterProfiler)
  library(org.Mm.eg.db)
  library(ggplot2)
  library(tidyverse)
})

deg_sig <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_deg_sig.rds")))
if (nrow(deg_sig) == 0) stop("无显著差异基因")

entrez <- bitr(deg_sig$gene, fromType = cfg$id_type, toType = "ENTREZID", OrgDb = org.Mm.eg.db)
ego <- enrichGO(entrez$ENTREZID, OrgDb = org.Mm.eg.db, ont = "BP", readable = TRUE)
if (!is.null(ego) && nrow(as.data.frame(ego)) > 0) {
  write.csv(as.data.frame(ego), file.path(PATHS$表格, paste0(DATASET, "_GO生物过程.csv")), row.names = FALSE)
  ggsave(file.path(PATHS$图形, paste0(DATASET, "_GO生物过程图.pdf")),
         dotplot(ego, showCategory = 15) + ggtitle("GO BP"), width = 10, height = 6)
}
message("完成: 05_富集分析.R")
