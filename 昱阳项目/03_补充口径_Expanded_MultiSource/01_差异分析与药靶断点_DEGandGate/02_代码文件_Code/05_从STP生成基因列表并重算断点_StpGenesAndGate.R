# 昱阳：以 SwissTargetPrediction 筛选后靶点为唯一药物基因来源，重算人鼠映射与断点
# 不用努力学习 CompoundTargets

suppressPackageStartupMessages({
  library(org.Mm.eg.db)
  library(AnnotationDbi)
})

root <- "E:/RProject/昱阳项目/02_差异分析与药靶断点_DEGandGate"
raw_q <- file.path(root, "01_数据文件_Data/01_初始数据_RawInitial/02_STP_槲皮素靶点_QuercetinTargets")
tab_dir <- file.path(root, "01_数据文件_Data/02_结果数据_ResultTables")
rep_dir <- file.path(root, "04_报告文件_Reports")
report_sum <- "E:/RProject/昱阳项目/01_分析报告_AnalysisReport/02_阶段汇总_StageSummaries"

stp_post <- file.path(raw_q, "Quercetin_Swiss预测靶点_筛选后.csv")
stopifnot(file.exists(stp_post))
stp <- read.csv(stp_post, stringsAsFactors = FALSE, check.names = FALSE, fileEncoding = "UTF-8")
# columns: Target, Common name, Uniprot ID, ...
gene_col <- if ("Common name" %in% names(stp)) "Common name" else names(stp)[2]
prob_col <- if ("Probability" %in% names(stp)) "Probability" else NA
if (!is.na(prob_col)) {
  prob <- as.numeric(gsub("\\*", "", stp[[prob_col]]))
  stopifnot(all(prob > 0, na.rm = TRUE))
}

genes_raw <- trimws(as.character(stp[[gene_col]]))
# drop empty common names (complexes) for gene list; keep detail in STP csv
genes_h <- unique(genes_raw[!is.na(genes_raw) & nzchar(genes_raw) & genes_raw != ""])
write.csv(
  data.frame(
    gene_human = genes_h,
    source = "SwissTargetPrediction",
    filter = "Probability>0",
    pubchem_cid = "5280343",
    data_provenance = "REAL",
    stringsAsFactors = FALSE
  ),
  file.path(raw_q, "02_槲皮素靶点基因列表_人源_QuercetinTargetGenes_Human_STP.csv"),
  row.names = FALSE, fileEncoding = "UTF-8"
)

# map human -> mouse
all_mm <- keys(org.Mm.eg.db, keytype = "SYMBOL")
all_mm_map <- setNames(all_mm, toupper(all_mm))
gene_mouse <- all_mm_map[toupper(genes_h)]
miss <- is.na(gene_mouse)
if (any(miss)) {
  gene_mouse[miss] <- vapply(genes_h[miss], function(h) {
    cand <- paste0(substring(h, 1, 1), tolower(substring(h, 2)))
    if (cand %in% all_mm) return(cand)
    hit <- match(tolower(h), tolower(all_mm))
    if (!is.na(hit)) return(all_mm[hit])
    NA_character_
  }, character(1))
}
map_df <- data.frame(
  gene_human = genes_h,
  gene_mouse = unname(gene_mouse),
  method = "symbol_casefold_orgMm",
  source = "STP_Probability_gt_0",
  stringsAsFactors = FALSE
)
map_ok <- map_df[!is.na(map_df$gene_mouse), , drop = FALSE]
write.csv(map_df, file.path(tab_dir, "08_人鼠同源映射_HumanMouseOrtholog.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")
write.csv(
  data.frame(gene_mouse = sort(unique(map_ok$gene_mouse))),
  file.path(raw_q, "03_槲皮素靶点基因列表_小鼠_QuercetinTargetGenes_Mouse_STP.csv"),
  row.names = FALSE, fileEncoding = "UTF-8"
)

deg <- read.csv(file.path(tab_dir, "05_差异基因_DEG_mainThreshold.csv"), stringsAsFactors = FALSE)
mouse_targets <- unique(map_ok$gene_mouse)
inter <- deg[toupper(deg$gene) %in% toupper(mouse_targets), , drop = FALSE]
inter$gene_human <- map_ok$gene_human[match(toupper(inter$gene), toupper(map_ok$gene_mouse))]
inter$target_source <- "SwissTargetPrediction_Prob_gt_0"
write.csv(inter, file.path(tab_dir, "09_药靶与DEG交集_QuercetinDegOverlap.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")
# direct toupper also
hit <- deg[toupper(deg$gene) %in% toupper(genes_h), , drop = FALSE]
write.csv(hit, file.path(tab_dir, "10_交集_直接符号匹配_DirectSymbolOverlap.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

n_human <- length(genes_h)
n_mapped <- length(mouse_targets)
n_deg <- nrow(deg)
n_up <- sum(deg$direction == "up")
n_down <- sum(deg$direction == "down")
n_overlap <- nrow(inter)
suggest <- if (n_overlap < 15) {
  "ORA_on_full_DEG (overlap<15)"
} else {
  "ORA_on_intersection"
}

gate <- data.frame(
  item = c(
    "Drug_target_source", "STP_rows_post_filter", "Quercetin_targets_human_nonempty_gene",
    "Quercetin_targets_mouse_mapped", "DEG_total", "DEG_up", "DEG_down",
    "Overlap_Quercetin_x_DEG", "Overlap_genes", "Suggest_enrichment_gene_set",
    "RigorPack_03_status", "Next_user_decision"
  ),
  value = c(
    "SwissTargetPrediction Homo_sapiens Probability>0 (NOT 努力学习 cache)",
    nrow(stp), n_human, n_mapped, n_deg, n_up, n_down, n_overlap,
    paste(inter$gene, collapse = ";"),
    suggest, "PLACEHOLDER_skip_by_default",
    "Decide rigor/threshold then stage C"
  ),
  stringsAsFactors = FALSE
)
write.csv(gate, file.path(tab_dir, "01_数量断点_GateCounts.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")
dir.create(report_sum, recursive = TRUE, showWarnings = FALSE)
write.csv(gate, file.path(report_sum, "01_数量断点_GateCounts.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

md <- c(
  "# 阶段 A 数量断点（药物靶点已改为 STP）",
  "",
  "- **药物基因来源**：SwissTargetPrediction（Homo sapiens），`Probability > 0` 筛选后",
  "- **不再使用**努力学习 `CompoundTargets` 缓存",
  sprintf("- PubChem CID：5280343；STP 筛选后行数：%s；非空基因符号：%s → 小鼠映射 %s", nrow(stp), n_human, n_mapped),
  sprintf("- DEG：%s（↑%s / ↓%s）", n_deg, n_up, n_down),
  sprintf("- 药靶 ∩ DEG：**%s**（%s）", n_overlap, paste(inter$gene, collapse = ", ")),
  sprintf("- 富集建议：`%s`", suggest),
  "",
  "文件：`Quercetin_Swiss预测靶点_筛选前/后.csv`",
  sprintf("更新：%s", format(Sys.time(), "%Y-%m-%d %H:%M"))
)
writeLines(md, file.path(report_sum, "01_数量断点结论_GateDecision.md"), useBytes = TRUE)

writeLines(sprintf(
  "STATUS: GATE_PAUSE\ndrug_targets: SwissTargetPrediction\nstp_post=%s human_genes=%s mouse=%s overlap=%s\nupdated: %s",
  nrow(stp), n_human, n_mapped, n_overlap, format(Sys.time(), "%Y-%m-%d")
), file.path(rep_dir, "01_STATUS.txt"))

message("STP human genes: ", n_human, " mapped: ", n_mapped, " overlap: ", n_overlap)
print(inter[, intersect(c("gene", "logFC", "direction", "gene_human"), names(inter)), drop = FALSE])
print(gate)
