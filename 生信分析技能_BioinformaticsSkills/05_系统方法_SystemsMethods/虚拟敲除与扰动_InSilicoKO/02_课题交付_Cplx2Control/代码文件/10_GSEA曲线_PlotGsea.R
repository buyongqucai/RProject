options(stringsAsFactors = FALSE)
vko <- "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除"
arch <- "C:/Users/10540/Desktop/琪乐无穷/五亚群留档"
tab <- file.path(arch, "结果文件", "_跨亚群", "scTenifoldKnk", "数据文件", "04_扰动基因_五亚群_Cplx2DrAll.csv")
fig <- file.path(arch, "结果文件", "_跨亚群", "scTenifoldKnk", "图片文件")
out <- file.path(arch, "结果文件", "_跨亚群", "scTenifoldKnk", "数据文件")
suppressPackageStartupMessages({
  library(clusterProfiler)
  library(org.Mm.eg.db)
  library(enrichplot)
  library(ggplot2)
})
dr <- read.csv(tab, check.names = FALSE)
subtypes <- c("cLTMR", "NF1", "NP", "PEP", "TRPM8")
want <- c("GO:0099504", "GO:0035493", "GO:0007269")
rows <- list()
for (s in subtypes) {
  d <- dr[dr$subtype == s & dr$gene != "Cplx2", ]
  d <- d[order(d$distance, decreasing = TRUE), ]
  ids <- bitr(d$gene, fromType = "SYMBOL", toType = "ENTREZID", OrgDb = org.Mm.eg.db)
  d <- d[d$gene %in% ids$SYMBOL, ]
  m <- match(d$gene, ids$SYMBOL)
  score <- setNames(d$distance, ids$ENTREZID[m])
  score <- score[!duplicated(names(score))]
  eg <- gseGO(
    geneList = sort(score, decreasing = TRUE),
    OrgDb = org.Mm.eg.db,
    ont = "BP",
    keyType = "ENTREZID",
    minGSSize = 10,
    maxGSSize = 500,
    pvalueCutoff = 1,
    verbose = FALSE,
    eps = 0
  )
  if (is.null(eg) || nrow(as.data.frame(eg)) == 0) next
  ed <- as.data.frame(eg)
  ed$subtype <- s
  rows[[s]] <- ed
  hit <- ed[ed$ID %in% want, , drop = FALSE]
  if (!nrow(hit)) next
  show_id <- hit$ID[which.min(hit$pvalue)]
  p <- gseaplot2(eg, geneSetID = show_id, title = paste0(s, ": ", hit$Description[hit$ID == show_id][1]))
  ggsave(file.path(fig, paste0("08_富集曲线_", s, "_GseaCurve.png")), p, width = 7, height = 5, dpi = 600, bg = "white")
  ggsave(file.path(fig, paste0("08_富集曲线_", s, "_GseaCurve.svg")), p, width = 7, height = 5, bg = "white")
}
if (length(rows)) {
  allr <- do.call(rbind, rows)
  keep <- allr[allr$ID %in% want, c("subtype","ID","Description","setSize","enrichmentScore","NES","pvalue","p.adjust")]
  write.csv(keep, file.path(out, "08_GSEA_突触条目_SynapseGsea.csv"), row.names = FALSE)
}
message("GSEA_DONE")
