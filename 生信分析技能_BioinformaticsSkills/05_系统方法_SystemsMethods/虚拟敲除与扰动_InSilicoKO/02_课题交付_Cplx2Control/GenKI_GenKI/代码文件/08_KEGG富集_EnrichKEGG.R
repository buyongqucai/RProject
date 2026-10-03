# KEGG ORA for GenKI response genes.
# Same rule as GO: the gene set is the genes that passed the KL filter,
# excluding the knocked-out gene. No pathway is chosen before the test.
options(stringsAsFactors = FALSE)
root <- "C:/Users/10540/Desktop/琪乐无穷/CPLX2虚拟敲除_Cplx2VirtualKO/GenKI_GenKI/结果文件"
suppressPackageStartupMessages({
  library(clusterProfiler)
  library(org.Mm.eg.db)
})

jobs <- list()
for (subtype in c("PEP", "NF1")) {
  base <- file.path(root, subtype, "GenKI")
  if (!dir.exists(base)) next
  for (gene in list.dirs(base, full.names = FALSE, recursive = FALSE)) {
    resp <- file.path(base, gene, "响应基因_Responsive.csv")
    if (file.exists(resp)) jobs[[length(jobs) + 1]] <- c(subtype, gene, resp)
  }
}

run_one <- function(subtype, gene, resp_path) {
  frame <- read.csv(resp_path, stringsAsFactors = FALSE)
  symbols <- unique(frame$gene)
  symbols <- symbols[!is.na(symbols) & nzchar(symbols) & symbols != gene]
  out_dir <- dirname(resp_path)
  note <- file.path(out_dir, "KEGG_EnrichNote.txt")
  if (length(symbols) < 5) {
    writeLines(c("too_few_genes", paste0("n=", length(symbols))), note)
    message(subtype, " ", gene, " too_few n=", length(symbols))
    return(NULL)
  }
  mapped <- bitr(symbols, fromType = "SYMBOL", toType = "ENTREZID", OrgDb = org.Mm.eg.db)
  if (nrow(mapped) < 5) {
    writeLines(c("too_few_mapped", paste0("n=", nrow(mapped))), note)
    message(subtype, " ", gene, " too_few_mapped n=", nrow(mapped))
    return(NULL)
  }
  ek <- enrichKEGG(
    gene = mapped$ENTREZID,
    organism = "mmu",
    keyType = "ncbi-geneid",
    pAdjustMethod = "BH",
    pvalueCutoff = 0.05,
    qvalueCutoff = 0.2
  )
  result <- as.data.frame(ek)
  if (nrow(result) && "geneID" %in% names(result)) {
    result$gene_symbol <- vapply(strsplit(result$geneID, "/"), function(ids) {
      hit <- mapped$SYMBOL[match(ids, mapped$ENTREZID)]
      paste(hit[!is.na(hit)], collapse = "/")
    }, character(1))
  }
  write.csv(result, file.path(out_dir, "富集_KEGG.csv"), row.names = FALSE)
  writeLines(c(
    paste0("input_symbols=", length(symbols)),
    paste0("mapped_entrez=", nrow(mapped)),
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
if (length(pieces)) {
  all_terms <- do.call(rbind, pieces)
  write.csv(all_terms, file.path(root, "富集_KEGG_全部.csv"), row.names = FALSE)
} else {
  write.csv(data.frame(), file.path(root, "富集_KEGG_全部.csv"), row.names = FALSE)
}
message("KEGG_DONE jobs=", length(jobs))
