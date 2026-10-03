# GO biological process enrichment for one subtype's GenKI response genes.
options(stringsAsFactors = FALSE)
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) stop("need gene csv and output csv")
genes <- unique(read.csv(args[[1]], stringsAsFactors = FALSE)$gene)
genes <- genes[genes != "Cplx2" & !is.na(genes) & nzchar(genes)]
note <- file.path(dirname(args[[2]]), "焦点通路_EnrichNote.txt")
if (length(genes) < 5) {
  writeLines(c("too_few_genes", paste0("n=", length(genes))), note)
  message("too_few_genes n=", length(genes))
  quit(save = "no", status = 0)
}
suppressPackageStartupMessages({
  library(clusterProfiler)
  library(org.Mm.eg.db)
})
ego <- enrichGO(
  gene = genes,
  OrgDb = org.Mm.eg.db,
  keyType = "SYMBOL",
  ont = "BP",
  pAdjustMethod = "BH",
  pvalueCutoff = 0.05,
  qvalueCutoff = 0.2,
  readable = FALSE
)
frame <- as.data.frame(ego)
write.csv(frame, args[[2]], row.names = FALSE)
focus <- c("GO:0099504", "GO:0007269", "GO:0035493")
hit <- if (nrow(frame)) paste(intersect(focus, frame$ID), collapse = ",") else ""
writeLines(c(
  paste0("genes=", length(genes)),
  paste0("terms=", nrow(frame)),
  paste0("focus_hit=", hit)
), note)
message("terms=", nrow(frame), " focus_hit=", hit)
