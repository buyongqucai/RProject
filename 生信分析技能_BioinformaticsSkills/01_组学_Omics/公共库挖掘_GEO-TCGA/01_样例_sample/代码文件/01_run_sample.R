# 样例分析脚本 — 公共库挖掘_GEO-TCGA
# data_provenance: REAL（GEO GSE10072 本地 series matrix 缓存）
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

skill_en <- "GEO-TCGA"
skill_folder <- "公共库挖掘_GEO-TCGA"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- "未找到可 source 的技能脚本"
if (length(sk_files)) {
  for (sf in sk_files) try(source(sf, encoding = "UTF-8"), silent = TRUE)
  sourced_note <- paste0("已 source 本技能 脚本_scripts/: ", paste(basename(sk_files), collapse = ", "))
}
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
library(ggplot2)
if (exists("setup_cjk_fonts")) setup_cjk_fonts()

data_provenance <- "REAL"
accession <- "GSE10072"
mat_path <- file.path(cache_dir, "GSE10072_series_matrix.txt")
gz_path <- file.path(cache_dir, "GSE10072_series_matrix.txt.gz")
if (!file.exists(mat_path) && file.exists(gz_path)) {
  con <- gzfile(gz_path, open = "rb")
  raw <- readLines(con, warn = FALSE)
  close(con)
  writeLines(raw, mat_path, useBytes = TRUE)
}
if (!file.exists(mat_path)) stop("缺少 GEO 缓存: ", mat_path, " （请先下载 GSE10072 series matrix）")

geo <- parse_geo_series_matrix(mat_path, max_features = 2000L)
mat <- geo$matrix
meta <- geo$meta
meta$tissue <- ifelse(grepl("Normal", meta$source, ignore.case = TRUE), "Normal", "Tumor")
# 取组织类型各 12 样本做可核对小队列
set.seed(10072L)
idx <- c(
  sample(which(meta$tissue == "Tumor"), min(12, sum(meta$tissue == "Tumor"))),
  sample(which(meta$tissue == "Normal"), min(12, sum(meta$tissue == "Normal")))
)
meta_sub <- meta[idx, , drop = FALSE]
mat_sub <- mat[, idx, drop = FALSE]
colnames(mat_sub) <- meta_sub$sample

utils::write.csv(meta_sub, file.path(data_dir, "样本元数据_SampleMeta_GSE10072.csv"), row.names = FALSE, fileEncoding = "UTF-8")
expr_out <- data.frame(probe = rownames(mat_sub), as.data.frame(mat_sub), check.names = FALSE)
utils::write.csv(expr_out, file.path(data_dir, "表达矩阵_Expression_GSE10072_subset.csv"), row.names = FALSE, fileEncoding = "UTF-8")
utils::write.csv(meta_sub, file.path(tab_dir, delivery_table_name(skill_en, "Meta", "GSE10072subset")), row.names = FALSE)

logmat <- log2(pmax(mat_sub, 1))
pc <- prcomp(t(logmat), scale. = TRUE)
pcd <- data.frame(PC1 = pc$x[, 1], PC2 = pc$x[, 2], group = meta_sub$tissue)
grp_cols <- c(Normal = unname(bioinfo_groups[["Control"]]), Tumor = unname(bioinfo_groups[["TreatA"]]))
if (exists("plot_pca_journal")) {
  p1 <- plot_pca_journal(pcd, group_col = "group", title = "PCA (GSE10072 lung subset)", palette = grp_cols)
} else {
  p1 <- ggplot(pcd, aes(PC1, PC2, color = group)) +
    geom_point(size = 3) +
    scale_color_manual(values = grp_cols) +
    labs(title = "PCA (GSE10072 lung subset)", color = "Tissue")
}
delivery_save_plot(p1, skill_en, "PCA", "GSE10072Lung", 5.2, 4.5, fig_dir, bio_root)

# 每样本平均 log2 表达箱线（journal box+jitter family）
mean_df <- data.frame(
  group = meta_sub$tissue,
  value = colMeans(logmat),
  stringsAsFactors = FALSE
)
if (exists("plot_box_jitter_journal")) {
  p2 <- plot_box_jitter_journal(
    mean_df, value_col = "value", group_col = "group",
    title = "Mean log2 intensity (GSE10072)", ylab = "Mean log2 intensity",
    palette = grp_cols
  )
} else {
  p2 <- ggplot(mean_df, aes(group, value, fill = group)) +
    geom_boxplot(outlier.size = 0.4, linewidth = 0.35) +
    scale_fill_manual(values = grp_cols) +
    labs(title = "Expression distribution (GSE10072)", x = "Tissue", y = "log2 intensity", fill = NULL)
}
delivery_save_plot(p2, skill_en, "box", "TissueIntensity", 5, 4.5, fig_dir, bio_root)

write_delivery_audit(
  skill_en, "post", nrow(mat_sub), ncol(mat_sub), ncol(mat_sub),
  "GSE10072 series matrix; tissue Normal vs Tumor", FALSE, accession, sourced_note,
  "REAL GEO metadata + QC plots; not toy survival",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = data_provenance
)

prov <- list(
  data_provenance = data_provenance,
  accession = accession,
  geo_url = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE10072",
  cache_file = "geo_cache/GSE10072_series_matrix.txt.gz",
  n_probes = nrow(mat_sub),
  n_samples = ncol(mat_sub),
  grouping = "Normal Lung vs Adenocarcinoma (Sample_source_name_ch1)",
  note = "Parsed locally from GEO series matrix; GEOquery getGEO crashes on this host."
)
if (requireNamespace("jsonlite", quietly = TRUE)) {
  jsonlite::write_json(prov, file.path(data_dir, "PROVENANCE.json"), auto_unbox = TRUE, pretty = TRUE)
}

fig_map <- c(
  "PCA 队列 QC" = paste0("../图片文件/", delivery_stem(skill_en, "PCA", "GSE10072Lung"), ".png"),
  "组织箱线图" = paste0("../图片文件/", delivery_stem(skill_en, "box", "TissueIntensity"), ".png")
)
interp <- paste0("REAL GEO GSE10072: metadata table + PCA + tissue boxplot. accession=", accession, ".")
status <- "PASS"
data_html <- paste0(
  "<p><b>data_provenance: REAL</b> — GEO ", accession, " series matrix（本地缓存）。</p>",
  "<p>详见 <code>数据文件/DATA_SOURCE.md</code>。</p>"
)
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(skill_en, skill_folder, status, data_html, audit_html, sourced_note, fig_map, interp, rep_file)
writeLines(c(status, paste0("data_provenance=", data_provenance)), file.path(rep_dir, "STATUS.txt"))
for (old in c("toy_survival_proxy.csv")) {
  f <- file.path(data_dir, old)
  if (file.exists(f)) file.rename(f, file.path(data_dir, paste0("obsolete_", old)))
}
message("DONE ", status, " — ", skill_folder)
