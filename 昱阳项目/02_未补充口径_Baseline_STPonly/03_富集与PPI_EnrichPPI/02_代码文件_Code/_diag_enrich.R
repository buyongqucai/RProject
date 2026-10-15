# 基线富集诊断：区分「真无富集」与「报错被吞」+ 映射率 + 真实 error
suppressPackageStartupMessages({
  ok <- TRUE
  for (p in c("clusterProfiler", "org.Mm.eg.db", "AnnotationDbi")) {
    if (!requireNamespace(p, quietly = TRUE)) { cat("MISSING_PKG:", p, "\n"); ok <- FALSE }
  }
  if (!ok) quit(status = 2)
  library(clusterProfiler); library(org.Mm.eg.db); library(AnnotationDbi)
})
gate <- "E:/RProject/昱阳项目/02_未补充口径_Baseline_STPonly/01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/02_结果数据_ResultTables"
deg <- read.csv(file.path(gate, "05_差异基因_DEG_mainThreshold.csv"), stringsAsFactors = FALSE)
cat("DEG rows:", nrow(deg), " cols:", paste(names(deg), collapse = ","), "\n")
syms <- unique(trimws(as.character(deg$gene)))
syms <- syms[nzchar(syms)]
cat("unique symbols:", length(syms), "\n")
m <- suppressMessages(AnnotationDbi::select(org.Mm.eg.db, keys = syms, keytype = "SYMBOL", columns = "ENTREZID"))
eg <- unique(na.omit(m$ENTREZID))
cat("mapped ENTREZID:", length(eg), " (", round(100 * length(eg) / length(syms), 1), "% )\n")
unmapped <- syms[!syms %in% m$SYMBOL[!is.na(m$ENTREZID)]]
cat("unmapped example:", paste(head(unmapped, 10), collapse = ", "), "\n\n")

run_one <- function(label, expr) {
  r <- tryCatch(expr, error = function(e) { cat(label, "ERROR:", conditionMessage(e), "\n"); NULL })
  if (is.null(r)) { cat(label, "-> NULL\n"); return(invisible(NULL)) }
  d <- as.data.frame(r)
  cat(label, "-> rows:", nrow(d), "\n")
  if (nrow(d) > 0) print(utils::head(d[, intersect(c("ID", "Description", "pvalue", "p.adjust", "Count"), names(d))], 5))
  invisible(r)
}
cat("== enrichGO BP (cutoff .05) ==\n")
bp <- run_one("BP", enrichGO(gene = eg, OrgDb = org.Mm.eg.db, keyType = "ENTREZID", ont = "BP",
                             pAdjustMethod = "BH", pvalueCutoff = 0.05, qvalueCutoff = 0.2, readable = TRUE))
cat("\n== enrichGO BP (cutoff .2 放宽看是否有信号) ==\n")
bp2 <- run_one("BP2", enrichGO(gene = eg, OrgDb = org.Mm.eg.db, keyType = "ENTREZID", ont = "BP",
                               pAdjustMethod = "BH", pvalueCutoff = 0.2, qvalueCutoff = 0.5, readable = TRUE))
cat("\n== enrichKEGG mmu ==\n")
kk <- run_one("KEGG", enrichKEGG(gene = eg, organism = "mmu", keyType = "ncbi-geneid",
                                 pAdjustMethod = "BH", pvalueCutoff = 0.05, qvalueCutoff = 0.2))
cat("\nDONE_DIAG\n")
