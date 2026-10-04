# KEGG ORA for GenKI response genes (mouse mmu).
# Same rule as GO / 网药口径对齐课题 SSOT：BH, p=0.05, q=0.2.
# Gene set = response genes excluding the knocked-out gene.
# Writes into DeliveryStandards leaves: 数据文件/富集_KEGG.csv, 报告文件/KEGG_EnrichNote.txt
options(stringsAsFactors = FALSE)
root <- "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除/结果文件"
suppressPackageStartupMessages({
  library(clusterProfiler)
  library(org.Mm.eg.db)
})

jobs <- list()
for (subtype in c("PEP", "NF1")) {
  base <- file.path(root, subtype, "GenKI")
  if (!dir.exists(base)) next
  for (gene in list.dirs(base, full.names = FALSE, recursive = FALSE)) {
    if (startsWith(gene, "_") || grepl("烟测|未采用", gene)) next
    resp <- file.path(base, gene, "数据文件", "响应基因_Responsive.csv")
    if (file.exists(resp)) jobs[[length(jobs) + 1]] <- c(subtype, gene, resp)
  }
}

run_one <- function(subtype, gene, resp_path) {
  frame <- read.csv(resp_path, stringsAsFactors = FALSE)
  symbols <- unique(frame$gene)
  symbols <- symbols[!is.na(symbols) & nzchar(symbols) & symbols != gene]
  tab_dir <- dirname(resp_path)
  note_dir <- file.path(dirname(tab_dir), "报告文件")
  dir.create(note_dir, recursive = TRUE, showWarnings = FALSE)
  note <- file.path(note_dir, "KEGG_EnrichNote.txt")
  out_csv <- file.path(tab_dir, "富集_KEGG.csv")
  if (length(symbols) < 5) {
    write.csv(data.frame(), out_csv, row.names = FALSE)
    writeLines(c("too_few_genes", paste0("n=", length(symbols))), note)
    message(subtype, " ", gene, " too_few n=", length(symbols))
    return(NULL)
  }
  mapped <- tryCatch(
    bitr(symbols, fromType = "SYMBOL", toType = "ENTREZID", OrgDb = org.Mm.eg.db),
    error = function(e) data.frame()
  )
  if (!nrow(mapped) || nrow(mapped) < 5) {
    write.csv(data.frame(), out_csv, row.names = FALSE)
    writeLines(c("too_few_mapped", paste0("n=", nrow(mapped))), note)
    message(subtype, " ", gene, " too_few_mapped n=", nrow(mapped))
    return(NULL)
  }
  ek <- tryCatch(
    enrichKEGG(
      gene = unique(mapped$ENTREZID),
      organism = "mmu",
      keyType = "ncbi-geneid",
      pAdjustMethod = "BH",
      pvalueCutoff = 0.05,
      qvalueCutoff = 0.2
    ),
    error = function(e) {
      writeLines(c("enrichKEGG_error", conditionMessage(e)), note)
      message(subtype, " ", gene, " ERROR ", conditionMessage(e))
      NULL
    }
  )
  result <- if (is.null(ek)) data.frame() else as.data.frame(ek)
  if (nrow(result) && "geneID" %in% names(result)) {
    result$gene_symbol <- vapply(strsplit(result$geneID, "/"), function(ids) {
      hit <- mapped$SYMBOL[match(ids, mapped$ENTREZID)]
      paste(hit[!is.na(hit)], collapse = "/")
    }, character(1))
  }
  write.csv(result, out_csv, row.names = FALSE)
  writeLines(c(
    paste0("input_symbols=", length(symbols)),
    paste0("mapped_entrez=", length(unique(mapped$ENTREZID))),
    paste0("unmapped=", paste(setdiff(symbols, mapped$SYMBOL), collapse = ",")),
    paste0("terms=", nrow(result)),
    "rule=response genes excluding knockout; BH; p=0.05; q=0.2; organism=mmu"
  ), note)
  message(subtype, " ", gene, " terms=", nrow(result))
  if (!nrow(result)) return(NULL)
  result$subtype <- subtype
  result$knockout_gene <- gene
  result
}

pieces <- lapply(jobs, function(job) run_one(job[[1]], job[[2]], job[[3]]))
pieces <- pieces[!vapply(pieces, is.null, logical(1))]
cross_tab <- file.path(root, "_跨亚群", "GenKI", "数据文件")
dir.create(cross_tab, recursive = TRUE, showWarnings = FALSE)
if (length(pieces)) {
  all_terms <- do.call(rbind, pieces)
  write.csv(all_terms, file.path(cross_tab, "富集_KEGG_全部.csv"), row.names = FALSE)
} else {
  write.csv(data.frame(), file.path(cross_tab, "富集_KEGG_全部.csv"), row.names = FALSE)
}
message("KEGG_DONE jobs=", length(jobs), " with_terms=", length(pieces))
