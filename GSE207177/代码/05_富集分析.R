source("配置.R", encoding = "UTF-8")
setup_script_env()

if (!requireNamespace("clusterProfiler", quietly = TRUE)) {
  message("跳过富集：未安装 clusterProfiler")
} else {
  suppressPackageStartupMessages({
    library(clusterProfiler)
    library(org.Mm.eg.db)
    library(tidyverse)
  })
  deg <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_deg.rds")))
  deg_sig <- deg %>% filter(padj < DEG_PADJ, abs(log2FC) > DEG_LOGFC)
  saveRDS(deg_sig, file.path(PATHS$中间数据, paste0(DATASET, "_deg_sig.rds")))
  if (nrow(deg_sig) >= 5) {
    genes <- bitr(deg_sig$gene, fromType = "SYMBOL", toType = "ENTREZID", OrgDb = org.Mm.eg.db)
    ego <- enrichGO(genes$ENTREZID, OrgDb = org.Mm.eg.db, ont = "BP", pAdjustMethod = "BH", readable = TRUE)
    if (!is.null(ego) && nrow(as.data.frame(ego)) > 0) {
      write.csv(as.data.frame(ego), file.path(PATHS$表格, paste0(DATASET, "_GO生物过程.csv")), row.names = FALSE)
    }
  }
}
message("完成: 05_富集分析.R")
