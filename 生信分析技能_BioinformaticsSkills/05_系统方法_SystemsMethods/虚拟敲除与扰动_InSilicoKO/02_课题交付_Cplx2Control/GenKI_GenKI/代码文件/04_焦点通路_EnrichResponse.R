# GO enrichment for GenKI response genes: BP + CC + MF (each ORA separately).
# Usage: Rscript 04_...R <响应基因_Responsive.csv> <富集_GO.csv> [knockout_gene]
# Also writes 富集_GOBP.csv (BP-only mirror) for backward compatibility.
# Cutoffs align with project SSOT / 网药: BH, p=0.05, q=0.2.
# Does not force terms: empty tables when nothing passes.
options(stringsAsFactors = FALSE)
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) stop("need gene csv and output csv")
gene_csv <- args[[1]]
out_csv <- args[[2]]
# Accept legacy out name 富集_GOBP.csv → still write full GO next to it
if (grepl("GOBP", basename(out_csv), fixed = TRUE)) {
  out_csv <- file.path(dirname(out_csv), "富集_GO.csv")
}
ko_gene <- if (length(args) >= 3) {
  args[[3]]
} else {
  basename(dirname(dirname(normalizePath(gene_csv, winslash = "/", mustWork = FALSE))))
}
genes <- unique(read.csv(gene_csv, stringsAsFactors = FALSE)$gene)
genes <- genes[!is.na(genes) & nzchar(genes) & genes != ko_gene]
tab_dir <- dirname(out_csv)
note_dir <- file.path(dirname(tab_dir), "报告文件")
dir.create(tab_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(note_dir, recursive = TRUE, showWarnings = FALSE)
note <- file.path(note_dir, "焦点通路_EnrichNote.txt")
empty <- data.frame()
if (length(genes) < 5) {
  write.csv(empty, out_csv, row.names = FALSE)
  write.csv(empty, file.path(tab_dir, "富集_GOBP.csv"), row.names = FALSE)
  writeLines(c("too_few_genes", paste0("n=", length(genes)), paste0("ko=", ko_gene)), note)
  message("too_few_genes n=", length(genes))
  quit(save = "no", status = 0)
}
suppressPackageStartupMessages({
  library(clusterProfiler)
  library(org.Mm.eg.db)
})
parts <- list()
counts <- c(BP = 0L, CC = 0L, MF = 0L)
for (ont in c("BP", "CC", "MF")) {
  ego <- tryCatch(
    enrichGO(
      gene = genes,
      OrgDb = org.Mm.eg.db,
      keyType = "SYMBOL",
      ont = ont,
      pAdjustMethod = "BH",
      pvalueCutoff = 0.05,
      qvalueCutoff = 0.2,
      readable = FALSE
    ),
    error = function(e) NULL
  )
  frame <- if (is.null(ego)) empty else as.data.frame(ego)
  counts[[ont]] <- nrow(frame)
  if (nrow(frame)) {
    frame$ontology <- ont
    frame$term <- frame$Description
    parts[[ont]] <- frame
  }
}
go_df <- if (length(parts)) do.call(rbind, parts) else empty
write.csv(go_df, out_csv, row.names = FALSE)
bp_only <- if ("BP" %in% names(parts)) parts[["BP"]] else empty
write.csv(bp_only, file.path(tab_dir, "富集_GOBP.csv"), row.names = FALSE)
focus <- c("GO:0099504", "GO:0007269", "GO:0035493")
hit <- if (nrow(go_df) && "ID" %in% names(go_df)) paste(intersect(focus, go_df$ID), collapse = ",") else ""
writeLines(c(
  paste0("genes=", length(genes)),
  paste0("ko=", ko_gene),
  paste0("go_terms=", nrow(go_df)),
  paste0("BP=", counts[["BP"]], ";CC=", counts[["CC"]], ";MF=", counts[["MF"]]),
  paste0("focus_hit=", hit),
  "rule=response genes excluding knockout; GO BP+CC+MF; BH; p=0.05; q=0.2"
), note)
message(
  "go_terms=", nrow(go_df),
  " BP=", counts[["BP"]], " CC=", counts[["CC"]], " MF=", counts[["MF"]],
  " focus_hit=", hit
)
