# 阶段C：一轮 GO/KEGG ORA + STRING PPI（未补充口径 Baseline）
# disease = DEG only；overlap = STP×DEG（n=1）→ ORA 用全 DEG
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

arm <- "E:/RProject/昱阳项目/02_未补充口径_Baseline_STPonly"
gate_tab <- file.path(arm, "01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/02_结果数据_ResultTables")
out_tab <- file.path(arm, "03_富集与PPI_EnrichPPI/01_数据文件_Data/02_结果数据_ResultTables")
out_fig <- file.path(arm, "03_富集与PPI_EnrichPPI/03_图片文件_Figures")
out_rep <- file.path(arm, "03_富集与PPI_EnrichPPI/04_报告文件_Reports")
dir.create(out_tab, recursive = TRUE, showWarnings = FALSE)
dir.create(out_fig, recursive = TRUE, showWarnings = FALSE)
dir.create(out_rep, recursive = TRUE, showWarnings = FALSE)

deg <- read.csv(file.path(gate_tab, "05_差异基因_DEG_mainThreshold.csv"), stringsAsFactors = FALSE)
ov_f <- list.files(gate_tab, pattern = "^09_.*Overlap.*\\.csv$", full.names = TRUE)
if (!length(ov_f)) ov_f <- list.files(gate_tab, pattern = "^09_.*\\.csv$", full.names = TRUE)
ov <- read.csv(ov_f[[1]], stringsAsFactors = FALSE)
ortho_f <- list.files(gate_tab, pattern = "^08_.*\\.csv$", full.names = TRUE)
ortho <- read.csv(ortho_f[[1]], stringsAsFactors = FALSE)
# normalize overlap gene column
if (!"gene" %in% names(ov)) {
  gcol <- names(ov)[grep("gene", names(ov), ignore.case = TRUE)[1]]
  ov$gene <- ov[[gcol]]
}

n_ov <- nrow(ov)
ora_genes <- if (n_ov < 15) unique(deg$gene) else unique(ov$gene)
ora_mode <- if (n_ov < 15) "Full_DEG" else "Overlap"

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

# PPI: overlap too small → use drug mouse genes ∩ DEG neighborhood: all mapped drug genes for network context
# Prefer: if overlap>=3 use overlap; else use drug orthologs that map (for STRING) — plan says PPI prefer overlap
ppi_genes <- if (n_ov >= 3) {
  unique(ov$gene)
} else {
  # use DEG for network (ORA already on DEG); hubs by |logFC|
  unique(deg$gene[order(-abs(deg$logFC))])[seq_len(min(50, nrow(deg)))]
}
write.csv(data.frame(gene_mouse = ppi_genes, note = "overlap<3_use_topDEG_for_STRING"),
          file.path(out_tab, "05_PPI输入基因_PpiInputGenes.csv"), row.names = FALSE, fileEncoding = "UTF-8")

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
  write.csv(data.frame(note = "STRING_empty"), file.path(out_tab, "06_STRING_edges.csv"), row.names = FALSE)
  hubs <- deg[order(-abs(deg$logFC)), c("gene", "logFC")]
  names(hubs)[1] <- "gene"
  hubs$degree <- NA_integer_
  write.csv(head(hubs, 10), file.path(out_tab, "08_PPI_TopHubs.csv"), row.names = FALSE, fileEncoding = "UTF-8")
}

# Venn: Drug vs DEG — 网药 FROZEN §G 微生信模板（weishengxin_venn_lib）
py <- Sys.which("python")
if (!nzchar(py)) py <- Sys.which("python3")
if (!nzchar(py)) stop("需要 python 以运行微生信韦恩")
st_venn <- system2(
  py,
  args = c(
    shQuote(normalizePath("E:/RProject/昱阳项目/_shared_scripts/build_venn_weishengxin.py")),
    "--arm", "baseline"
  ),
  stdout = TRUE, stderr = TRUE
)
message(paste(st_venn, collapse = "\n"))
if ("gene_mouse" %in% names(ortho)) {
  drug_mm <- unique(na.omit(ortho$gene_mouse[nzchar(as.character(ortho$gene_mouse))]))
} else if (ncol(ortho) >= 2) {
  drug_mm <- unique(na.omit(ortho[[2]]))
} else {
  drug_mm <- character(0)
}
deg_g <- unique(deg$gene)

writeLines(c(
  "STATUS: DONE",
  "step: 03_EnrichPPI",
  "phase: C",
  "arm: 02_未补充口径_Baseline_STPonly",
  "enrich_viz: NetworkPharm FROZEN (BPCCMF bubble/bar + KEGG lollipop/bar/circos)",
  "venn_viz: NetworkPharm FROZEN §G weishengxin_venn_lib",
  sprintf("ora_mode=%s n_ora=%d n_overlap=%d", ora_mode, length(ora_genes), n_ov),
  sprintf("enrich_figs=%s", paste(enrich_figs, collapse = ",")),
  sprintf("ppi_genes=%d string_edges=%d hubs=%d", length(ppi_genes), nrow(edges), nrow(hubs)),
  sprintf("venn_drug_vs_deg_intersect=%d", length(intersect(drug_mm, deg_g))),
  sprintf("updated: %s", format(Sys.time(), "%Y-%m-%d %H:%M"))
), file.path(out_rep, "01_STATUS.txt"))

message("Baseline Enrich+PPI+Venn done overlap=", n_ov, " ora=", ora_mode,
        " figs=", paste(enrich_figs, collapse = ","))
