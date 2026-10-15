# 补充口径：实验靶(ChEMBL+BindingDB) ∪ 预测靶(STP[+多站]) × 疾病(DEG∪CTD)
# 药靶主池=并集分层；双证据仅排序

suppressPackageStartupMessages({
  library(org.Mm.eg.db)
  library(org.Hs.eg.db)
  library(AnnotationDbi)
})

root <- "E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/01_差异分析与药靶断点_DEGandGate"
raw <- file.path(root, "01_数据文件_Data/01_初始数据_RawInitial")
tab <- file.path(root, "01_数据文件_Data/02_结果数据_ResultTables")
rep <- file.path(root, "04_报告文件_Reports")
sumdir <- "E:/RProject/昱阳项目/01_分析报告_AnalysisReport/02_阶段汇总_StageSummaries"
expd <- file.path(raw, "03_ChEMBL_BindingDB_Experimental")
pred <- file.path(raw, "04_STP_STITCH_PharmMapper_TargetNet_BATMAN_预测靶点")
ctdd <- file.path(raw, "05_CTD_Propofol")
dir.create(tab, recursive = TRUE, showWarnings = FALSE)

map_human_to_mouse <- function(genes_h) {
  genes_h <- unique(trimws(as.character(genes_h)))
  genes_h <- genes_h[!is.na(genes_h) & nzchar(genes_h)]
  all_mm <- keys(org.Mm.eg.db, keytype = "SYMBOL")
  all_mm_map <- setNames(all_mm, toupper(all_mm))
  gene_mouse <- unname(all_mm_map[toupper(genes_h)])
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
  data.frame(gene_human = genes_h, gene_mouse = gene_mouse, stringsAsFactors = FALSE)
}

# ---- 1) ChEMBL experimental ----
act <- read.csv(file.path(expd, "01_ChEMBL50_activities_raw.csv"), stringsAsFactors = FALSE)
tmap <- read.csv(file.path(expd, "02_ChEMBL_target_map.csv"), stringsAsFactors = FALSE)
act$standard_value <- as.numeric(act$standard_value)
keep_type <- toupper(act$standard_type) %in% c("IC50", "KI", "KD", "EC50", "POTENCY", "AC50")
# nM-like units or pchembl; keep <=10000 nM when numeric in nM
units <- toupper(trimws(as.character(act$standard_units)))
is_nm <- units %in% c("NM", "NANOMOLES")
is_um <- units %in% c("UM", "MICROMOLES")
ok_val <- (is_nm & !is.na(act$standard_value) & act$standard_value <= 10000) |
  (is_um & !is.na(act$standard_value) & act$standard_value <= 10) |
  (!is.na(act$pchembl_value) & as.numeric(act$pchembl_value) >= 5)
# organism human preferred via target map later
chembl_f <- act[keep_type & ok_val & !is.na(act$target_chembl_id), , drop = FALSE]
chembl_f <- merge(chembl_f, tmap, by = "target_chembl_id", all.x = TRUE)
chembl_f <- chembl_f[!is.na(chembl_f$gene_symbols) & nzchar(chembl_f$gene_symbols), , drop = FALSE]
# prefer Homo sapiens targets
chembl_f$org_ok <- grepl("Homo sapiens", chembl_f$organism, ignore.case = TRUE) | is.na(chembl_f$organism)
genes_chembl <- unique(unlist(strsplit(chembl_f$gene_symbols[chembl_f$org_ok | TRUE], "\\|")))
genes_chembl <- unique(trimws(genes_chembl))
genes_chembl <- genes_chembl[nzchar(genes_chembl)]
write.csv(chembl_f, file.path(expd, "14_ChEMBL_filtered_activities.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(data.frame(gene_human = sort(genes_chembl), source = "ChEMBL", evidence = "experimental",
                     filter = "IC50/Ki/Kd/EC50_le_10uM", molecule = "CHEMBL50", stringsAsFactors = FALSE),
          file.path(expd, "15_ChEMBL_genes_human.csv"), row.names = FALSE, fileEncoding = "UTF-8")

# ---- 2) BindingDB via hsa gene ids + HTML affinity text ----
hsa_file <- file.path(expd, "12_BindingDB_hsa_geneids.txt")
genes_bdb <- character(0)
if (file.exists(hsa_file)) {
  hsa <- unique(trimws(readLines(hsa_file, warn = FALSE)))
  hsa <- hsa[nzchar(hsa)]
  if (length(hsa)) {
    sym <- tryCatch(
      AnnotationDbi::select(org.Hs.eg.db, keys = hsa, keytype = "ENTREZID", columns = "SYMBOL"),
      error = function(e) NULL
    )
    if (!is.null(sym)) genes_bdb <- unique(na.omit(sym$SYMBOL))
  }
}
# parse monomer HTML for affinity <=10uM blocks (name only; gene via hsa list)
html_path <- file.path(expd, "07_BindingDB_monomer_7460.html")
if (file.exists(html_path)) {
  html <- paste(readLines(html_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n")
  aff <- gregexpr(">(IC50|Ki|Kd|EC50):&nbsp;([^<]+)<", html, perl = TRUE, ignore.case = TRUE)
  # keep provenance file
  writeLines(sprintf("BindingDB monomerid=7460; hsa_gene_ids=%d; human_symbols=%d",
                     length(if (file.exists(hsa_file)) readLines(hsa_file, warn = FALSE) else character(0)),
                     length(genes_bdb)),
             file.path(expd, "16_BindingDB_parse_note.txt"))
}
write.csv(data.frame(gene_human = sort(unique(genes_bdb)), source = "BindingDB", evidence = "experimental",
                     filter = "hsa_ids_from_monomer7460_page", monomerid = "7460", stringsAsFactors = FALSE),
          file.path(expd, "17_BindingDB_genes_human.csv"), row.names = FALSE, fileEncoding = "UTF-8")

exp_genes <- sort(unique(c(genes_chembl, genes_bdb)))
write.csv(data.frame(gene_human = exp_genes, evidence = "experimental",
                     in_chembl = exp_genes %in% genes_chembl,
                     in_bindingdb = exp_genes %in% genes_bdb,
                     stringsAsFactors = FALSE),
          file.path(tab, "11_实验靶点_人源_ExperimentalTargets_Human.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

# ---- 3) Predicted: STP (+ optional extra CSVs in MultiPredict) ----
stp <- read.csv(file.path(pred, "01_STP_Quercetin_筛选后.csv"), stringsAsFactors = FALSE, check.names = FALSE)
gcol <- if ("Common name" %in% names(stp)) "Common name" else names(stp)[grep("name|Name|gene", names(stp), ignore.case = TRUE)[1]]
genes_stp <- unique(trimws(as.character(stp[[gcol]])))
genes_stp <- genes_stp[!is.na(genes_stp) & nzchar(genes_stp)]
pred_list <- list(STP = genes_stp)

# auto-load any extra *genes*.csv in MultiPredict with column gene_human or gene
extra_files <- list.files(pred, pattern = "^(02|03|04|05|06)_.*\\.(csv|tsv)$", full.names = TRUE)
for (f in extra_files) {
  # skip probes / docs / PharmMapper audit copies (unfiltered & sensitivity)
  if (grepl("STITCH_resolve|sea_probe|DATA_SOURCE|_unfiltered|normFit|sensitivity|_audit", basename(f), ignore.case = TRUE)) next
  d <- tryCatch({
    if (grepl("\\.tsv$", f, ignore.case = TRUE)) read.delim(f, stringsAsFactors = FALSE, check.names = FALSE)
    else read.csv(f, stringsAsFactors = FALSE, check.names = FALSE)
  }, error = function(e) NULL)
  if (is.null(d) || !nrow(d)) next
  cn <- names(d)
  gc2 <- cn[tolower(cn) %in% c("gene_human", "gene", "symbol", "common name", "preferredname", "genesymbol")][1]
  if (is.na(gc2)) next
  gs <- unique(trimws(as.character(d[[gc2]])))
  gs <- gs[!is.na(gs) & nzchar(gs)]
  pred_list[[tools::file_path_sans_ext(basename(f))]] <- gs
}

pred_genes <- sort(unique(unlist(pred_list)))
pred_long <- do.call(rbind, lapply(names(pred_list), function(src) {
  data.frame(gene_human = pred_list[[src]], source = src, evidence = "predicted", stringsAsFactors = FALSE)
}))
write.csv(pred_long, file.path(tab, "12_预测靶点_人源_PredictedTargets_Human.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

# union drug pool
drug_h <- sort(unique(c(exp_genes, pred_genes)))
drug_ann <- data.frame(
  gene_human = drug_h,
  experimental = drug_h %in% exp_genes,
  predicted = drug_h %in% pred_genes,
  dual_evidence = drug_h %in% exp_genes & drug_h %in% pred_genes,
  stringsAsFactors = FALSE
)
write.csv(drug_ann, file.path(tab, "13_药靶并集分层_人源_DrugTargetUnion_Human.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

map_drug <- map_human_to_mouse(drug_h)
map_drug$experimental <- map_drug$gene_human %in% exp_genes
map_drug$predicted <- map_drug$gene_human %in% pred_genes
write.csv(map_drug, file.path(tab, "14_药靶人鼠映射_DrugOrtholog.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")
drug_m <- sort(unique(map_drug$gene_mouse[!is.na(map_drug$gene_mouse)]))
write.csv(data.frame(gene_mouse = drug_m), file.path(tab, "15_药靶小鼠_DrugTargets_Mouse.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

# ---- 4) Disease: DEG ∪ CTD ----
deg <- read.csv(file.path(tab, "05_差异基因_DEG_mainThreshold.csv"), stringsAsFactors = FALSE)
deg$gene <- as.character(deg$gene)
deg_genes <- unique(deg$gene)

ctd_path <- file.path(ctdd, "01_CTD_propofol_D015742_genes_curated.tsv")
# header line starts with "# Input\t..." — strip leading "# " then read
ctd_lines <- readLines(ctd_path, warn = FALSE)
hdr <- sub("^#\\s*", "", ctd_lines[1])
ctd <- read.delim(text = paste(c(hdr, ctd_lines[-1]), collapse = "\n"),
                  stringsAsFactors = FALSE, check.names = FALSE)
sym_col <- names(ctd)[tolower(names(ctd)) %in% c("genesymbol", "gene symbol")][1]
if (is.na(sym_col)) {
  # fallback positional (Input, ChemicalName, ChemicalId, CasRN, GeneSymbol, ...)
  sym_col <- names(ctd)[5]
}
ctd_h <- unique(trimws(as.character(ctd[[sym_col]])))
ctd_h <- ctd_h[!is.na(ctd_h) & nzchar(ctd_h)]
map_ctd <- map_human_to_mouse(ctd_h)
all_mm <- keys(org.Mm.eg.db, keytype = "SYMBOL")
direct_mm <- ctd_h[toupper(ctd_h) %in% toupper(all_mm)]
if (length(direct_mm)) {
  direct_mm <- all_mm[match(toupper(direct_mm), toupper(all_mm))]
} else {
  direct_mm <- character(0)
}
ctd_m <- sort(unique(c(map_ctd$gene_mouse[!is.na(map_ctd$gene_mouse)], direct_mm)))
write.csv(data.frame(gene_human_or_input = ctd_h, stringsAsFactors = FALSE),
          file.path(tab, "16_CTD_propofol_genes_input.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")
if (!length(ctd_m)) {
  write.csv(data.frame(gene_mouse = character(), source = character(), stringsAsFactors = FALSE),
            file.path(tab, "17_CTD_propofol_genes_mouse.csv"), row.names = FALSE, fileEncoding = "UTF-8")
} else {
  write.csv(data.frame(gene_mouse = ctd_m, source = "CTD_propofol_D015742", stringsAsFactors = FALSE),
            file.path(tab, "17_CTD_propofol_genes_mouse.csv"), row.names = FALSE, fileEncoding = "UTF-8")
}

disease_m <- sort(unique(c(deg_genes, ctd_m)))
dis_ann <- data.frame(
  gene_mouse = disease_m,
  in_DEG = disease_m %in% deg_genes,
  in_CTD = disease_m %in% ctd_m,
  stringsAsFactors = FALSE
)
write.csv(dis_ann, file.path(tab, "18_疾病基因并集_DEG_CTD_Mouse.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

# ---- 5) Overlaps ----
ov_all <- sort(intersect(drug_m, disease_m))
ov_deg <- sort(intersect(drug_m, deg_genes))
ov_ctd <- sort(intersect(drug_m, ctd_m))
ov_exp_dis <- sort(intersect(
  unique(map_drug$gene_mouse[map_drug$experimental & !is.na(map_drug$gene_mouse)]),
  disease_m
))
ov_dual_dis <- sort(intersect(
  unique(map_drug$gene_mouse[map_drug$experimental & map_drug$predicted & !is.na(map_drug$gene_mouse)]),
  disease_m
))

ov_df <- data.frame(gene_mouse = ov_all, stringsAsFactors = FALSE)
ov_df$in_DEG <- ov_df$gene_mouse %in% deg_genes
ov_df$in_CTD <- ov_df$gene_mouse %in% ctd_m
ov_df$experimental <- ov_df$gene_mouse %in% map_drug$gene_mouse[map_drug$experimental]
ov_df$predicted <- ov_df$gene_mouse %in% map_drug$gene_mouse[map_drug$predicted]
# attach DEG stats if any
if (nrow(deg)) {
  ov_df <- merge(ov_df, deg, by.x = "gene_mouse", by.y = "gene", all.x = TRUE)
}
write.csv(ov_df, file.path(tab, "19_药靶与疾病交集_DrugDiseaseOverlap.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

gate <- data.frame(
  item = c(
    "arm", "Drug_pool", "Experimental_human", "Predicted_human_STP", "Predicted_sources_loaded",
    "Drug_human_union", "Drug_mouse_mapped",
    "DEG", "CTD_mouse", "Disease_union_mouse",
    "Overlap_drug_x_disease", "Overlap_drug_x_DEG", "Overlap_drug_x_CTD",
    "Overlap_experimental_x_disease", "Overlap_dualEvidence_x_disease",
    "Suggest_enrichment_gene_set", "RigorPack", "BindingDB_status", "ExtraPredict_manual"
  ),
  value = c(
    "Expanded_MultiSource",
    "experimental_UNION_predicted",
    as.character(length(exp_genes)),
    as.character(length(genes_stp)),
    paste(names(pred_list), collapse = "+"),
    as.character(length(drug_h)),
    as.character(length(drug_m)),
    as.character(length(deg_genes)),
    as.character(length(ctd_m)),
    as.character(length(disease_m)),
    as.character(length(ov_all)),
    as.character(length(ov_deg)),
    as.character(length(ov_ctd)),
    as.character(length(ov_exp_dis)),
    as.character(length(ov_dual_dis)),
    if (length(ov_all) < 15) "ORA_on_DiseaseUnion_DEG_CTD" else "ORA_on_overlap",
    "DONE_EXPANDED_ONLY",
    "monomer7460_hsa_ids+chembl_primary",
    "SEA/SuperPred/PharmMapper/TargetNet slots MANUAL if not present"
  ),
  stringsAsFactors = FALSE
)
write.csv(gate, file.path(tab, "01_数量断点_GateCounts.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(gate, file.path(sumdir, "02_补充口径_数量断点_GateCounts_Expanded.csv"), row.names = FALSE, fileEncoding = "UTF-8")

writeLines(c(
  "STATUS: GATE_DONE_EXPANDED",
  "arm: 03_补充口径_Expanded_MultiSource",
  sprintf("drug_human_union=%d experimental=%d predicted=%d", length(drug_h), length(exp_genes), length(pred_genes)),
  sprintf("disease_union=%d DEG=%d CTD=%d", length(disease_m), length(deg_genes), length(ctd_m)),
  sprintf("overlap_drug_x_disease=%d genes=%s", length(ov_all), paste(head(ov_all, 30), collapse = ",")),
  "rigor: AWAITING_USER",
  sprintf("updated: %s", format(Sys.time(), "%Y-%m-%d %H:%M"))
), file.path(rep, "01_STATUS.txt"))

writeLines(c(
  "# 补充口径断点",
  sprintf("- 实验靶(人): %d (ChEMBL+BindingDB)", length(exp_genes)),
  sprintf("- 预测靶(人): %d (源: %s)", length(pred_genes), paste(names(pred_list), collapse = ", ")),
  sprintf("- 药靶并集小鼠: %d", length(drug_m)),
  sprintf("- 疾病并集小鼠: %d (DEG %d ∪ CTD %d)", length(disease_m), length(deg_genes), length(ctd_m)),
  sprintf("- 药∩病: %d", length(ov_all)),
  sprintf("- 实验∩病: %d; 双证据∩病: %d", length(ov_exp_dis), length(ov_dual_dis)),
  "- 严谨包: 等确认",
  sprintf("- 更新: %s", format(Sys.time(), "%Y-%m-%d"))
), file.path(sumdir, "02_补充口径断点结论_GateDecision_Expanded.md"))

message("DONE expand gate: overlap=", length(ov_all))
