# 阶段C：一轮 GO/KEGG ORA + STRING PPI（补充口径）
# 若 overlap<15 → ORA 用疾病并集；PPI 优先 overlap，其次实验∩病，再疾病并集 top by |logFC|
# 富集出图：网药 FROZEN（BPCCMF 气泡/柱 + KEGG 棒棒糖/柱/圈图）

suppressPackageStartupMessages({
  library(clusterProfiler)
  library(org.Mm.eg.db)
  library(ggplot2)
})
source(
  "E:/RProject/昱阳项目/_shared_scripts/enrich_plot_netpharm.R",
  encoding = "UTF-8"
)

arm <- "E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource"
gate_tab <- file.path(arm, "01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/02_结果数据_ResultTables")
out_tab <- file.path(arm, "03_富集与PPI_EnrichPPI/01_数据文件_Data/02_结果数据_ResultTables")
out_fig <- file.path(arm, "03_富集与PPI_EnrichPPI/03_图片文件_Figures")
out_rep <- file.path(arm, "03_富集与PPI_EnrichPPI/04_报告文件_Reports")
dir.create(out_tab, recursive = TRUE, showWarnings = FALSE)
dir.create(out_fig, recursive = TRUE, showWarnings = FALSE)
dir.create(out_rep, recursive = TRUE, showWarnings = FALSE)

ov <- read.csv(file.path(gate_tab, "19_药靶与疾病交集_DrugDiseaseOverlap.csv"), stringsAsFactors = FALSE)
dis <- read.csv(file.path(gate_tab, "18_疾病基因并集_DEG_CTD_Mouse.csv"), stringsAsFactors = FALSE)
deg <- read.csv(file.path(gate_tab, "05_差异基因_DEG_mainThreshold.csv"), stringsAsFactors = FALSE)
gate <- read.csv(file.path(gate_tab, "01_数量断点_GateCounts.csv"), stringsAsFactors = FALSE)

n_ov <- nrow(ov)
ora_genes <- if (n_ov < 15) dis$gene_mouse else ov$gene_mouse
ora_mode <- if (n_ov < 15) "DiseaseUnion_DEG_CTD" else "Overlap"

sym2entrez <- function(syms) {
  s <- unique(trimws(as.character(syms)))
  s <- s[nzchar(s)]
  m <- AnnotationDbi::select(org.Mm.eg.db, keys = s, keytype = "SYMBOL", columns = "ENTREZID")
  unique(na.omit(m$ENTREZID))
}

eg <- sym2entrez(ora_genes)
write.csv(data.frame(gene_mouse = ora_genes, ora_mode = ora_mode),
          file.path(out_tab, "01_ORA输入基因_OraInputGenes.csv"), row.names = FALSE, fileEncoding = "UTF-8")

ego_bp <- tryCatch(enrichGO(gene = eg, OrgDb = org.Mm.eg.db, keyType = "ENTREZID",
                            ont = "BP", pAdjustMethod = "BH", pvalueCutoff = 0.05, qvalueCutoff = 0.2,
                            readable = TRUE), error = function(e) NULL)
ego_cc <- tryCatch(enrichGO(gene = eg, OrgDb = org.Mm.eg.db, keyType = "ENTREZID",
                            ont = "CC", pAdjustMethod = "BH", pvalueCutoff = 0.05, qvalueCutoff = 0.2,
                            readable = TRUE), error = function(e) NULL)
ego_mf <- tryCatch(enrichGO(gene = eg, OrgDb = org.Mm.eg.db, keyType = "ENTREZID",
                            ont = "MF", pAdjustMethod = "BH", pvalueCutoff = 0.05, qvalueCutoff = 0.2,
                            readable = TRUE), error = function(e) NULL)
ekegg <- tryCatch(enrichKEGG(gene = eg, organism = "mmu", keyType = "ncbi-geneid",
                             pAdjustMethod = "BH", pvalueCutoff = 0.05, qvalueCutoff = 0.2),
                  error = function(e) NULL)
if (!is.null(ekegg) && nrow(as.data.frame(ekegg)) > 0) {
  ekegg <- setReadable(ekegg, OrgDb = org.Mm.eg.db, keyType = "ENTREZID")
}

save_enrich <- function(obj, path) {
  if (is.null(obj) || nrow(as.data.frame(obj)) == 0) {
    write.csv(data.frame(note = "no_significant_terms"), path, row.names = FALSE)
  } else {
    write.csv(as.data.frame(obj), path, row.names = FALSE, fileEncoding = "UTF-8")
  }
}
save_enrich(ego_bp, file.path(out_tab, "02_GO_BP.csv"))
save_enrich(ego_cc, file.path(out_tab, "02c_GO_CC.csv"))
save_enrich(ego_mf, file.path(out_tab, "03_GO_MF.csv"))
save_enrich(ekegg, file.path(out_tab, "04_KEGG.csv"))

go_df <- yy_bind_go_df(ego_bp, ego_cc, ego_mf)
kegg_df <- yy_kegg_from_enrich(ekegg)
enrich_figs <- yy_plot_enrich_netpharm(go_df, kegg_df, out_fig, out_tab)

# PPI gene set for STRING
ppi_genes <- if (n_ov >= 3) ov$gene_mouse else if (sum(ov$experimental %in% TRUE, na.rm = TRUE) >= 3) {
  ov$gene_mouse[ov$experimental %in% TRUE]
} else {
  # top DEG by |logFC| within disease union that are also drug targets if any; else top DEG
  d2 <- deg[order(-abs(deg$logFC)), , drop = FALSE]
  head(d2$gene, 50)
}
ppi_genes <- unique(as.character(ppi_genes))
write.csv(data.frame(gene_mouse = ppi_genes), file.path(out_tab, "05_PPI输入基因_PpiInputGenes.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

# STRING API
string_map <- tryCatch({
  url <- paste0(
    "https://string-db.org/api/json/get_string_ids?identifiers=",
    utils::URLencode(paste(ppi_genes, collapse = "\r")),
    "&species=10090&limit=1"
  )
  jsonlite::fromJSON(url)
}, error = function(e) NULL)

edges <- data.frame()
hubs <- data.frame(gene = character(), degree = integer())
if (!is.null(string_map) && nrow(string_map) > 0) {
  ids <- string_map$stringId
  url2 <- paste0(
    "https://string-db.org/api/json/network?identifiers=",
    utils::URLencode(paste(ids, collapse = "%0d")),
    "&species=10090&required_score=400"
  )
  net <- tryCatch(jsonlite::fromJSON(url2), error = function(e) NULL)
  if (!is.null(net) && length(net)) {
    edges <- as.data.frame(net, stringsAsFactors = FALSE)
    write.csv(edges, file.path(out_tab, "06_STRING_edges.csv"), row.names = FALSE, fileEncoding = "UTF-8")
    # degree from preferredName
    if (all(c("preferredName_A", "preferredName_B") %in% names(edges))) {
      alln <- c(edges$preferredName_A, edges$preferredName_B)
      deg_tbl <- sort(table(alln), decreasing = TRUE)
      hubs <- data.frame(gene = names(deg_tbl), degree = as.integer(deg_tbl), stringsAsFactors = FALSE)
      write.csv(hubs, file.path(out_tab, "07_PPI_hub_degree.csv"), row.names = FALSE, fileEncoding = "UTF-8")
      write.csv(head(hubs, 10), file.path(out_tab, "08_PPI_TopHubs.csv"), row.names = FALSE, fileEncoding = "UTF-8")
    }
  }
}
if (!nrow(edges)) {
  write.csv(data.frame(note = "STRING_network_empty_or_blocked"), file.path(out_tab, "06_STRING_edges.csv"),
            row.names = FALSE)
  # fallback hubs = overlap genes with DEG |logFC|
  if (n_ov > 0 && "logFC" %in% names(ov)) {
    hubs <- ov[!is.na(ov$logFC), c("gene_mouse", "logFC")]
    hubs <- hubs[order(-abs(hubs$logFC)), , drop = FALSE]
    names(hubs)[1] <- "gene"
    hubs$degree <- NA_integer_
    write.csv(head(hubs, 10), file.path(out_tab, "08_PPI_TopHubs.csv"), row.names = FALSE, fileEncoding = "UTF-8")
  }
}

# PPI 网络图（网药同心 Degree）
source("E:/RProject/昱阳项目/_shared_scripts/plot_ppi_netpharm.R", encoding = "UTF-8")
ppi_fig_ok <- isTRUE(yy_plot_ppi_arm(arm))

writeLines(c(
  "STATUS: DONE",
  "step: 03_EnrichPPI",
  "phase: C",
  "enrich_viz: NetworkPharm FROZEN (BPCCMF bubble/bar + KEGG lollipop/bar/circos; GO bubble sort_by=count)",
  "ppi_viz: NetworkPharm FROZEN np_plot_string_ppi concentric",
  "venn_viz: NetworkPharm FROZEN §G weishengxin",
  sprintf("ora_mode=%s n_ora=%d n_overlap=%d", ora_mode, length(ora_genes), n_ov),
  sprintf("enrich_figs=%s", paste(enrich_figs, collapse = ",")),
  sprintf("ppi_fig=%s ppi_genes=%d string_edges=%d hubs=%d",
          ppi_fig_ok, length(ppi_genes), nrow(edges), nrow(hubs)),
  sprintf("updated: %s", format(Sys.time(), "%Y-%m-%d %H:%M"))
), file.path(out_rep, "01_STATUS.txt"))

message("Enrich+PPI done ora_mode=", ora_mode, " overlap=", n_ov,
        " figs=", paste(enrich_figs, collapse = ","), " ppi=", ppi_fig_ok)
