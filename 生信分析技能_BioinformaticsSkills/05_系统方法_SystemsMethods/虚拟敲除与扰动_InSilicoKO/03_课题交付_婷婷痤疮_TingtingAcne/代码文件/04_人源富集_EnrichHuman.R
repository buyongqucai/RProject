# Human GO BP/CC/MF + KEGG for response gene table.
# Usage: Rscript 04_...R <响应基因_Responsive.csv> <out_dir> [knockout]
options(stringsAsFactors = FALSE)
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) stop("need gene csv and out dir")
gene_csv <- args[[1]]
out_dir <- args[[2]]
ko <- if (length(args) >= 3) args[[3]] else "AHR"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
note_dir <- file.path(dirname(out_dir), "报告文件")
dir.create(note_dir, recursive = TRUE, showWarnings = FALSE)

genes <- unique(read.csv(gene_csv, stringsAsFactors = FALSE)$gene)
genes <- genes[!is.na(genes) & nzchar(genes) & genes != ko]
empty <- data.frame()
write_empty <- function(msg) {
  write.csv(empty, file.path(out_dir, "富集_GO.csv"), row.names = FALSE)
  write.csv(empty, file.path(out_dir, "富集_KEGG.csv"), row.names = FALSE)
  writeLines(msg, file.path(note_dir, "富集_EnrichNote.txt"))
  message(msg[[1]])
}
if (length(genes) < 2) {
  write_empty(c("too_few_genes", paste0("n=", length(genes))))
  quit(save = "no", status = 0)
}

suppressPackageStartupMessages({
  library(clusterProfiler)
  library(org.Hs.eg.db)
})
gene_ratio <- function(text) {
  parts <- strsplit(as.character(text), "/", fixed = TRUE)
  vapply(parts, function(x) as.numeric(x[[1]]) / as.numeric(x[[2]]), numeric(1))
}
parts <- list()
for (ont in c("BP", "CC", "MF")) {
  ego <- tryCatch(
    enrichGO(genes, OrgDb = org.Hs.eg.db, keyType = "SYMBOL", ont = ont,
             pAdjustMethod = "BH", pvalueCutoff = 0.05, qvalueCutoff = 0.2, readable = FALSE),
    error = function(e) NULL
  )
  if (is.null(ego) || nrow(as.data.frame(ego)) == 0) next
  frame <- as.data.frame(ego)
  frame$ontology <- ont
  frame$term <- frame$Description
  frame$enrichment <- gene_ratio(frame$GeneRatio)
  parts[[ont]] <- frame
}
go_df <- if (length(parts)) do.call(rbind, parts) else empty
write.csv(go_df, file.path(out_dir, "富集_GO.csv"), row.names = FALSE)

mapped <- tryCatch(
  bitr(genes, fromType = "SYMBOL", toType = "ENTREZID", OrgDb = org.Hs.eg.db),
  error = function(e) NULL
)
kegg_df <- empty
if (!is.null(mapped) && nrow(mapped) >= 2) {
  kegg <- tryCatch(
    enrichKEGG(unique(mapped$ENTREZID), organism = "hsa",
               pAdjustMethod = "BH", pvalueCutoff = 0.05, qvalueCutoff = 0.2),
    error = function(e) NULL
  )
  if (!is.null(kegg) && nrow(as.data.frame(kegg))) {
    kegg_df <- as.data.frame(kegg)
    kegg_df$term <- kegg_df$Description
  }
}
write.csv(kegg_df, file.path(out_dir, "富集_KEGG.csv"), row.names = FALSE)
writeLines(
  sprintf("genes=%d\ngo_terms=%d\nkegg_terms=%d", length(genes), nrow(go_df), nrow(kegg_df)),
  file.path(note_dir, "富集_EnrichNote.txt")
)
message("ENRICH_DONE genes=", length(genes), " go=", nrow(go_df), " kegg=", nrow(kegg_df))
