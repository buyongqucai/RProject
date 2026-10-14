# 清风项目：药病交集基因 GO/KEGG 功能富集（clusterProfiler）
# 输入: 药物疾病交集_DrugDiseaseOverlap.csv (Gene 列)
# 口径: Bioconductor 通用背景（org.Hs.eg.db / KEGG 全库）; padj(BH)<0.05 为主阈值
suppressMessages({
  library(clusterProfiler)
  library(org.Hs.eg.db)
})
options(timeout = 300)  # KEGG REST 下载（本机 10s/文件，R 默认 60s 不够稳）
args <- commandArgs(trailingOnly = TRUE)
in_csv <- args[1]
outdir <- args[2]
dir.create(outdir, recursive = TRUE, showWarnings = FALSE)

ov <- read.csv(in_csv, fileEncoding = "UTF-8-BOM", stringsAsFactors = FALSE)
genes <- unique(ov$Gene)
cat(sprintf("[in] %d genes\n", length(genes)))

# ---- ID 映射 ----
map <- bitr(genes, fromType = "SYMBOL", toType = c("ENTREZID", "ENSEMBL"), OrgDb = org.Hs.eg.db)
write.csv(map, file.path(outdir, "ID映射_SYMBOL2ENTREZ.csv"), row.names = FALSE, fileEncoding = "UTF-8")
cat(sprintf("[map] %d/%d mapped\n", nrow(map), length(genes)))

run_go <- function(ont, tag) {
  e <- enrichGO(gene = map$ENTREZID, OrgDb = org.Hs.eg.db, ont = ont,
                pvalueCutoff = 0.05, qvalueCutoff = 0.2, readable = TRUE)
  df <- as.data.frame(e)
  df <- df[df$p.adjust < 0.05, , drop = FALSE]
  write.csv(df, file.path(outdir, sprintf("交集功能富集_GO_%s_EnrichGO%s.csv", tag, tag)),
            row.names = FALSE, fileEncoding = "UTF-8")
  cat(sprintf("[GO %s] %d terms (padj<0.05)\n", tag, nrow(df)))
  df
}
go_bp <- run_go("BP", "BP")
go_cc <- run_go("CC", "CC")
go_mf <- run_go("MF", "MF")

# ---- KEGG ----
kk <- tryCatch(
  enrichKEGG(gene = map$ENTREZID, organism = "hsa",
             pvalueCutoff = 0.05, qvalueCutoff = 0.2),
  error = function(e) { cat("[KEGG] ERROR:", conditionMessage(e), "\n"); NULL }
)
if (!is.null(kk)) {
  kk <- setReadable(kk, OrgDb = org.Hs.eg.db, keyType = "ENTREZID")
  df <- as.data.frame(kk)
  df <- df[df$p.adjust < 0.05, , drop = FALSE]
  write.csv(df, file.path(outdir, "KEGG通路富集_EnrichKEGG.csv"), row.names = FALSE, fileEncoding = "UTF-8")
  cat(sprintf("[KEGG] %d pathways (padj<0.05)\n", nrow(df)))
  # 靶点-通路长表（network.csv D 层用）
  if (nrow(df) > 0) {
    long <- do.call(rbind, lapply(seq_len(nrow(df)), function(i) {
      gl <- strsplit(as.character(df$geneID[i]), "/")[[1]]
      data.frame(Pathway = df$ID[i], PathwayName = df$Description[i],
                 Gene = gl, padj = df$p.adjust[i], stringsAsFactors = FALSE)
    }))
    write.csv(long, file.path(outdir, "KEGG靶点通路长表_KEGGGenePathway.csv"),
              row.names = FALSE, fileEncoding = "UTF-8")
    cat(sprintf("[KEGG-long] %d gene-pathway rows\n", nrow(long)))
  }
}
cat("[done]\n")
