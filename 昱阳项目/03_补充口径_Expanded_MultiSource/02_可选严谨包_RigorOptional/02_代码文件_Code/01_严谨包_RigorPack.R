# Optional rigor pack — Expanded arm ONLY (does NOT alter main overlap list)
# Contents (plan B–E): threshold sensitivity | hypergeometric | GSEA | multi-source consensus
# Baseline arm remains SKIPPED_CONFIRMED_DONE (no run)

suppressPackageStartupMessages({
  library(org.Mm.eg.db)
  library(clusterProfiler)
  library(enrichplot)
  library(ggplot2)
})

arm <- "E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource"
gate_tab <- file.path(arm, "01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/02_结果数据_ResultTables")
pred_dir <- file.path(arm, "01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/01_初始数据_RawInitial/04_STP_STITCH_PharmMapper_TargetNet_BATMAN_预测靶点")
rigor_root <- file.path(arm, "02_可选严谨包_RigorOptional")
out_tab <- file.path(rigor_root, "01_数据文件_Data/02_结果数据_ResultTables")
out_fig <- file.path(rigor_root, "03_图片文件_Figures")
out_rep <- file.path(rigor_root, "04_报告文件_Reports")
dir.create(out_tab, recursive = TRUE, showWarnings = FALSE)
dir.create(out_fig, recursive = TRUE, showWarnings = FALSE)
dir.create(out_rep, recursive = TRUE, showWarnings = FALSE)

allg_files <- list.files(gate_tab, pattern = "^04_.*AllGenes_limma\\.csv$", full.names = TRUE)
if (!length(allg_files)) stop("missing 04_*AllGenes_limma.csv in gate tables")
allg <- read.csv(allg_files[[1]], stringsAsFactors = FALSE)
deg_main <- read.csv(file.path(gate_tab, "05_差异基因_DEG_mainThreshold.csv"), stringsAsFactors = FALSE)
dis <- read.csv(file.path(gate_tab, "18_疾病基因并集_DEG_CTD_Mouse.csv"), stringsAsFactors = FALSE)
ov <- read.csv(file.path(gate_tab, "19_药靶与疾病交集_DrugDiseaseOverlap.csv"), stringsAsFactors = FALSE)
drug_map <- read.csv(file.path(gate_tab, "14_药靶人鼠映射_DrugOrtholog.csv"), stringsAsFactors = FALSE)
pred_long <- read.csv(file.path(gate_tab, "12_预测靶点_人源_PredictedTargets_Human.csv"), stringsAsFactors = FALSE)

# ---- 1) DEG threshold sensitivity (side tables; main list unchanged) ----
mk_deg <- function(df, logfc = 1, pcol = "P.Value", pcut = 0.05, use_adj = FALSE) {
  p <- if (use_adj) df$adj.P.Val else df[[pcol]]
  keep <- !is.na(df$logFC) & abs(df$logFC) >= logfc & !is.na(p) & p < pcut
  unique(df$gene[keep])
}
sens <- data.frame(
  rule = c(
    "main_|logFC|>=1_P<0.05",
    "strict_adjP<0.05_|logFC|>=1",
    "strict_adjP<0.05_|logFC|>=0.58",
    "loose_|logFC|>=0.58_P<0.05"
  ),
  n_DEG = c(
    length(mk_deg(allg, 1, "P.Value", 0.05, FALSE)),
    length(mk_deg(allg, 1, "P.Value", 0.05, TRUE)),
    length(mk_deg(allg, 0.58, "P.Value", 0.05, TRUE)),
    length(mk_deg(allg, 0.58, "P.Value", 0.05, FALSE))
  ),
  stringsAsFactors = FALSE
)
drug_mm <- unique(na.omit(drug_map$gene_mouse))
ctd <- unique(dis$gene_mouse[dis$in_CTD %in% TRUE])
overlap_under <- function(deg_genes) {
  disease <- unique(c(deg_genes, ctd))
  length(intersect(drug_mm, disease))
}
sens$n_disease_union <- c(
  length(unique(c(mk_deg(allg, 1, "P.Value", 0.05, FALSE), ctd))),
  length(unique(c(mk_deg(allg, 1, "P.Value", 0.05, TRUE), ctd))),
  length(unique(c(mk_deg(allg, 0.58, "P.Value", 0.05, TRUE), ctd))),
  length(unique(c(mk_deg(allg, 0.58, "P.Value", 0.05, FALSE), ctd)))
)
sens$n_overlap_drug_x_disease <- c(
  overlap_under(mk_deg(allg, 1, "P.Value", 0.05, FALSE)),
  overlap_under(mk_deg(allg, 1, "P.Value", 0.05, TRUE)),
  overlap_under(mk_deg(allg, 0.58, "P.Value", 0.05, TRUE)),
  overlap_under(mk_deg(allg, 0.58, "P.Value", 0.05, FALSE))
)
sens$adopted_main <- sens$rule == "main_|logFC|>=1_P<0.05"
write.csv(sens, file.path(out_tab, "01_DEG阈值敏感性_ThresholdSensitivity.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

# ---- 2) Hypergeometric: drug∩disease enrichment ----
# universe = all measured genes with symbols
U <- length(unique(allg$gene))
K <- length(unique(dis$gene_mouse))          # disease union size
n <- length(drug_mm)                        # drug mapped
k <- nrow(ov)                               # overlap
# P(X >= k)
p_hyper <- phyper(k - 1, K, U - K, n, lower.tail = FALSE)
hyper <- data.frame(
  universe_measured_genes = U,
  disease_union = K,
  drug_mouse = n,
  overlap = k,
  hypergeometric_P_ge_k = p_hyper,
  note = "Enrichment of drug targets among disease genes; does not remove genes",
  stringsAsFactors = FALSE
)
write.csv(hyper, file.path(out_tab, "02_超几何重叠检验_Hypergeometric.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

# ---- 3) Multi-source consensus (≥2 prediction sources) ----
# pred_long source may be STP / file basenames
cons <- as.data.frame(table(pred_long$gene_human), stringsAsFactors = FALSE)
names(cons) <- c("gene_human", "n_sources")
cons <- cons[order(-cons$n_sources, cons$gene_human), ]
cons$consensus_ge2 <- cons$n_sources >= 2
write.csv(cons, file.path(out_tab, "03_预测多站出现次数_PredictedSourceCounts.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")
# map consensus to mouse and intersect disease
cons_h <- cons$gene_human[cons$consensus_ge2]
cons_mm <- unique(na.omit(drug_map$gene_mouse[drug_map$gene_human %in% cons_h]))
cons_ov <- intersect(cons_mm, unique(dis$gene_mouse))
write.csv(
  data.frame(
    gene_mouse = cons_ov,
    rule = "predicted_in_ge2_sources_AND_disease_union",
    stringsAsFactors = FALSE
  ),
  file.path(out_tab, "04_多站共识与疾病交集_ConsensusDiseaseOverlap.csv"),
  row.names = FALSE, fileEncoding = "UTF-8"
)

# ---- 4) GSEA on full ranked list (t-statistic); GO BP ----
rank_df <- allg[!is.na(allg$t) & !is.na(allg$gene) & nzchar(allg$gene), ]
# collapse duplicate symbols by max |t|
rank_df <- rank_df[order(-abs(rank_df$t)), ]
rank_df <- rank_df[!duplicated(rank_df$gene), ]
eg <- AnnotationDbi::select(org.Mm.eg.db, keys = rank_df$gene, keytype = "SYMBOL", columns = "ENTREZID")
eg <- eg[!is.na(eg$ENTREZID) & !duplicated(eg$ENTREZID), ]
rank_df <- merge(rank_df, eg, by.x = "gene", by.y = "SYMBOL")
gene_list <- rank_df$t
names(gene_list) <- as.character(rank_df$ENTREZID)
gene_list <- sort(gene_list, decreasing = TRUE)

gsea_bp <- tryCatch(
  gseGO(
    geneList = gene_list, OrgDb = org.Mm.eg.db, ont = "BP",
    keyType = "ENTREZID", minGSSize = 15, maxGSSize = 500,
    pvalueCutoff = 0.05, verbose = FALSE, eps = 0
  ),
  error = function(e) NULL
)
if (!is.null(gsea_bp) && nrow(as.data.frame(gsea_bp)) > 0) {
  gsea_bp <- setReadable(gsea_bp, OrgDb = org.Mm.eg.db, keyType = "ENTREZID")
  write.csv(as.data.frame(gsea_bp), file.path(out_tab, "05_GSEA_GO_BP.csv"),
            row.names = FALSE, fileEncoding = "UTF-8")
  p <- tryCatch(
    dotplot(gsea_bp, showCategory = 15) + ggtitle("GSEA GO BP (ranked t-stat)") + theme_bw(base_size = 11),
    error = function(e) NULL
  )
  if (!is.null(p)) {
    ggsave(file.path(out_fig, "01_GSEA_GO_BP_dot.png"), p, width = 8, height = 6, dpi = 600)
    ggsave(file.path(out_fig, "01_GSEA_GO_BP_dot.svg"), p, width = 8, height = 6)
  }
} else {
  write.csv(data.frame(note = "no_significant_GSEA_GO_BP_or_failed"),
            file.path(out_tab, "05_GSEA_GO_BP.csv"), row.names = FALSE)
}

gsea_kegg <- tryCatch(
  gseKEGG(
    geneList = gene_list, organism = "mmu", keyType = "ncbi-geneid",
    minGSSize = 10, maxGSSize = 500, pvalueCutoff = 0.05, verbose = FALSE, eps = 0
  ),
  error = function(e) NULL
)
if (!is.null(gsea_kegg) && nrow(as.data.frame(gsea_kegg)) > 0) {
  write.csv(as.data.frame(gsea_kegg), file.path(out_tab, "06_GSEA_KEGG.csv"),
            row.names = FALSE, fileEncoding = "UTF-8")
  p2 <- tryCatch(
    dotplot(gsea_kegg, showCategory = 15) + ggtitle("GSEA KEGG (ranked t-stat)") + theme_bw(base_size = 11),
    error = function(e) NULL
  )
  if (!is.null(p2)) {
    ggsave(file.path(out_fig, "02_GSEA_KEGG_dot.png"), p2, width = 8, height = 6, dpi = 600)
    ggsave(file.path(out_fig, "02_GSEA_KEGG_dot.svg"), p2, width = 8, height = 6)
  }
} else {
  write.csv(data.frame(note = "no_significant_GSEA_KEGG_or_failed"),
            file.path(out_tab, "06_GSEA_KEGG.csv"), row.names = FALSE)
}

# ---- 5) PharmMapper strict audit pointer (already in MultiPredict/_audit) ----
write.csv(
  data.frame(
    item = c("PharmMapper_main", "PharmMapper_strict_audit"),
    rule = c("studySpecies_mouseORhuman_normFit>=0.6", "studySpecies_mouseORhuman_normFit>=0.8"),
    path = c(
      "01_.../04_STP_STITCH_PharmMapper_TargetNet_BATMAN_预测靶点/04_PharmMapper_Quercetin_genes.csv",
      "01_.../04_STP_STITCH_PharmMapper_TargetNet_BATMAN_预测靶点/_audit/04_PharmMapper_Quercetin_genes_studySpecies_normFit0.8.csv"
    ),
    stringsAsFactors = FALSE
  ),
  file.path(out_tab, "07_PharmMapper阈值审计指针_FilterAuditPointer.csv"),
  row.names = FALSE, fileEncoding = "UTF-8"
)

# ---- summary STATUS ----
writeLines(
  c(
    "STATUS: DONE",
    "step: 02_RigorOptional",
    "phase: B",
    "arm: 03_补充口径_Expanded_MultiSource",
    "notes: Rigor pack run as side analyses; main overlap list NOT altered.",
    sprintf("hypergeometric_P=%.4g overlap=%d", p_hyper, k),
    sprintf("consensus_ge2_x_disease=%d", length(cons_ov)),
    sprintf("main_overlap_unchanged=%d", nrow(ov)),
    "baseline_arm: SKIPPED_CONFIRMED_DONE (not run)",
    sprintf("updated: %s", format(Sys.time(), "%Y-%m-%d %H:%M"))
  ),
  file.path(out_rep, "01_STATUS.txt")
)

write.csv(
  data.frame(
    deliverable = c(
      "01_DEG阈值敏感性_ThresholdSensitivity.csv",
      "02_超几何重叠检验_Hypergeometric.csv",
      "03_预测多站出现次数_PredictedSourceCounts.csv",
      "04_多站共识与疾病交集_ConsensusDiseaseOverlap.csv",
      "05_GSEA_GO_BP.csv",
      "06_GSEA_KEGG.csv",
      "07_PharmMapper阈值审计指针_FilterAuditPointer.csv"
    ),
    alters_main_gene_list = FALSE,
    stringsAsFactors = FALSE
  ),
  file.path(out_tab, "00_严谨包清单_Manifest.csv"),
  row.names = FALSE, fileEncoding = "UTF-8"
)

message("Rigor pack DONE; main overlap still ", nrow(ov))
