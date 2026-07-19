# 样例分析脚本 — 基因芯片表达分析_Microarray
# data_provenance: REAL（GEO GSE10072 Affymetrix 子集）
# STATUS: PASS
options(stringsAsFactors = FALSE)

args_all <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args_all, value = TRUE)
script_path <- if (length(file_arg)) {
  normalizePath(sub("^--file=", "", file_arg[1]), winslash = "/", mustWork = TRUE)
} else {
  normalizePath("01_run_sample.R", winslash = "/", mustWork = TRUE)
}
code_dir <- dirname(script_path)
sample_root <- normalizePath(file.path(code_dir, ".."), winslash = "/", mustWork = TRUE)
skill_root <- normalizePath(file.path(sample_root, ".."), winslash = "/", mustWork = TRUE)
bio_root <- normalizePath(file.path(skill_root, "..", ".."), winslash = "/", mustWork = TRUE)
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath(file.path(skill_root, "..", "..", ".."), winslash = "/", mustWork = TRUE)
}

viz_script <- file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards", "脚本_scripts", "出版级出图_PublicationPlot.R")
if (file.exists(viz_script)) source(viz_script, encoding = "UTF-8")
delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")

paths <- delivery_sample_paths(sample_root)
data_dir <- paths$raw_dir
cache_dir <- file.path(data_dir, "geo_cache")
fig_dir <- paths$fig_dir
tab_dir <- paths$tab_dir
rep_dir <- paths$rep_dir
for (d in c(data_dir, cache_dir, fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

skill_en <- "Microarray"
skill_folder <- "基因芯片表达分析_Microarray"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- "未找到可 source 的技能脚本"
if (length(sk_files)) {
  for (sf in sk_files) try(source(sf, encoding = "UTF-8"), silent = TRUE)
  sourced_note <- paste0("已 source 本技能 脚本_scripts/: ", paste(basename(sk_files), collapse = ", "))
}
for (pkg in c("ggplot2", "limma")) {
  if (!requireNamespace(pkg, quietly = TRUE)) stop("缺少 R 包: ", pkg)
}
suppressPackageStartupMessages({ library(ggplot2); library(limma) })
if (exists("setup_cjk_fonts")) setup_cjk_fonts()

data_provenance <- "REAL"
accession <- "GSE10072"
mat_path <- file.path(cache_dir, "GSE10072_series_matrix.txt")
if (!file.exists(mat_path)) stop("缺少 GEO 缓存: ", mat_path)
geo <- parse_geo_series_matrix(mat_path, max_features = 3000L)
mat <- geo$matrix
meta <- geo$meta
meta$group <- ifelse(grepl("Normal", meta$source, ignore.case = TRUE), "Normal", "Tumor")
set.seed(10072L)
idx <- c(
  sample(which(meta$group == "Tumor"), min(10, sum(meta$group == "Tumor"))),
  sample(which(meta$group == "Normal"), min(10, sum(meta$group == "Normal")))
)
meta_sub <- meta[idx, , drop = FALSE]
mat_sub <- mat[, idx, drop = FALSE]
colnames(mat_sub) <- meta_sub$sample

design <- model.matrix(~ 0 + group, data = meta_sub)
colnames(design) <- levels(factor(meta_sub$group))
fit <- lmFit(mat_sub, design)
cont <- makeContrasts(Tumor - Normal, levels = design)
fit2 <- contrasts.fit(fit, cont)
fit2 <- eBayes(fit2)
tt <- topTable(fit2, number = nrow(mat_sub), sort.by = "P")
tt$probe <- rownames(tt)
ma_df <- data.frame(
  probe = rownames(tt),
  A = tt$AveExpr,
  M = tt$logFC,
  pvalue = tt$P.Value,
  padj = tt$adj.P.Val
)
utils::write.csv(ma_df, file.path(tab_dir, delivery_table_name(skill_en, "MA", "TumorVsNormal")), row.names = FALSE)
utils::write.csv(meta_sub, file.path(data_dir, "样本元数据_SampleMeta_GSE10072.csv"), row.names = FALSE, fileEncoding = "UTF-8")

write_delivery_audit(
  skill_en, "post", nrow(mat_sub), ncol(mat_sub), ncol(mat_sub),
  "GSE10072 Affymetrix; Tumor vs Normal", FALSE, accession, sourced_note,
  "REAL microarray limma; MA plot",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = data_provenance
)

ma_df$sig <- ifelse(!is.na(ma_df$padj) & ma_df$padj < 0.05 & abs(ma_df$M) > 0.5, "sig", "ns")
p <- ggplot(ma_df, aes(A, M, color = sig)) +
  geom_point(alpha = 0.75, size = 1.6) +
  geom_hline(yintercept = c(-0.5, 0.5), linetype = 2, color = "grey50") +
  scale_color_manual(values = c(ns = unname(bioinfo_volcano[["ns"]]), sig = unname(bioinfo_volcano[["up"]]))) +
  labs(title = "MA plot (GSE10072 Tumor vs Normal)", x = "Average log2 intensity", y = "logFC") +
  (if (exists("theme_journal")) theme_journal() else theme_bw())
delivery_save_plot(p, skill_en, "MA", "TumorVsNormal", 6.5, 5, fig_dir, bio_root)

# Journal volcano (Fig2-B recipe) from same REAL limma table
vol_df <- data.frame(
  gene = ma_df$probe,
  logFC = ma_df$M,
  adj.P.Val = ma_df$padj,
  stringsAsFactors = FALSE
)
if (exists("plot_volcano_journal")) {
  p_vol <- plot_volcano_journal(
    vol_df, gene_col = "gene", logfc_col = "logFC", p_col = "adj.P.Val",
    logfc_cut = 0.5, p_cut = 0.05, label_n = 10,
    title = "Volcano (GSE10072 Tumor vs Normal)"
  )
} else {
  p_vol <- ggplot(vol_df, aes(logFC, -log10(pmax(adj.P.Val, 1e-300)))) +
    geom_point(alpha = 0.7, size = 1.2) +
    labs(title = "Volcano (GSE10072)", y = "-log10 adj.P")
}
delivery_save_plot(p_vol, skill_en, "volcano", "TumorVsNormal", 5.5, 5, fig_dir, bio_root)

# Authenticity snapshot: full series n vs analysis subset
n_series <- nrow(meta)
n_tumor_all <- sum(meta$group == "Tumor")
n_normal_all <- sum(meta$group == "Normal")
auth <- data.frame(
  accession = accession,
  n_series_samples_parsed = n_series,
  n_tumor_in_series = n_tumor_all,
  n_normal_in_series = n_normal_all,
  n_analysis_subset = ncol(mat_sub),
  n_tumor_subset = sum(meta_sub$group == "Tumor"),
  n_normal_subset = sum(meta_sub$group == "Normal"),
  grouping_field = "Sample_source_name_ch1 (Normal vs non-Normal->Tumor)",
  geo_url = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE10072",
  stringsAsFactors = FALSE
)
utils::write.csv(auth, file.path(tab_dir, delivery_table_name(skill_en, "Authenticity", "GSE10072")), row.names = FALSE)

prov <- list(
  data_provenance = data_provenance,
  accession = accession,
  platform = "Affymetrix HG-U133A (GSE10072)",
  contrast = "Tumor vs Normal lung",
  method = "limma",
  n_series = n_series,
  n_subset = ncol(mat_sub),
  figures = c("MA", "volcano"),
  note = "REAL GEO microarray; journal volcano via plot_volcano_journal; not fabricated."
)
if (requireNamespace("jsonlite", quietly = TRUE)) {
  jsonlite::write_json(prov, file.path(data_dir, "PROVENANCE.json"), auto_unbox = TRUE, pretty = TRUE)
}

fig_map <- c(
  "芯片 MA 图" = paste0("../图片文件/", delivery_stem(skill_en, "MA", "TumorVsNormal"), ".png"),
  "期刊火山图" = paste0("../图片文件/", delivery_stem(skill_en, "volcano", "TumorVsNormal"), ".png")
)
interp <- paste0(
  "REAL GSE10072 microarray limma MA + journal volcano. accession=", accession,
  "; series_n=", n_series, "; subset_n=", ncol(mat_sub), "."
)
status <- "PASS"
data_html <- paste0(
  "<p><b>data_provenance: REAL</b> — GEO ", accession, " Affymetrix 子集。</p>",
  "<p>series n=", n_series, " (Tumor=", n_tumor_all, ", Normal=", n_normal_all,
  "); analysis subset n=", ncol(mat_sub), ".</p>"
)
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(skill_en, skill_folder, status, data_html, audit_html, sourced_note, fig_map, interp, rep_file)
writeLines(c(status, paste0("data_provenance=", data_provenance)), file.path(rep_dir, "STATUS.txt"))
message("DONE ", status, " — ", skill_folder)
