# 样例分析脚本 — DNA甲基化分析_WGBS-RRBS
# data_provenance: REAL（Bioconductor minfiData 450k beta 子集；非完整 WGBS 上游）
# STATUS: PARTIAL
options(stringsAsFactors = FALSE)

args_all <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args_all, value = TRUE)
script_path <- if (length(file_arg)) {
  normalizePath(sub("^--file=", "", file_arg[1]), winslash = "/", mustWork = TRUE)
} else {
  normalizePath("run_sample.R", winslash = "/", mustWork = TRUE)
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

paths <- delivery_sample_paths(sample_root)
data_dir <- paths$raw_dir
fig_dir <- paths$fig_dir
tab_dir <- paths$tab_dir
rep_dir <- paths$rep_dir
for (d in c(data_dir, fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)
source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")

skill_en <- "WGBS-RRBS"
skill_folder <- "DNA甲基化分析_WGBS-RRBS"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- "未找到可 source 的技能脚本"
if (length(sk_files)) {
  for (sf in sk_files) try(source(sf, encoding = "UTF-8"), silent = TRUE)
  sourced_note <- paste0("已 source 本技能 脚本_scripts/: ", paste(basename(sk_files), collapse = ", "))
}
for (pkg in c("ggplot2", "minfi", "FlowSorted.Blood.450k")) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    stop("缺少 R 包: ", pkg, " — 请 BiocManager::install('FlowSorted.Blood.450k')")
  }
}
suppressPackageStartupMessages({
  library(ggplot2)
  library(minfi)
  library(FlowSorted.Blood.450k)
})
if (exists("setup_cjk_fonts")) setup_cjk_fonts()

data_provenance <- "REAL"
accession <- "FlowSorted.Blood.450k (Bioconductor ExperimentData, 450k)"
data(FlowSorted.Blood.450k)
rgset <- FlowSorted.Blood.450k
beta <- getBeta(rgset)
pd <- as.data.frame(pData(rgset))
pd$sample <- rownames(pd)
if (!"CellType" %in% colnames(pd)) stop("FlowSorted.Blood.450k 缺少 CellType 列")
# 取两种细胞类型各 4 样本、5000 CpG
set.seed(505L)
types <- intersect(c("CD8T", "CD4T"), unique(pd$CellType))
if (length(types) < 2L) types <- head(unique(pd$CellType), 2)
idx <- unlist(lapply(types, function(t) sample(which(pd$CellType == t), min(4, sum(pd$CellType == t)))))
pd_sub <- pd[idx, , drop = FALSE]
beta_sub <- beta[sample(nrow(beta), min(5000L, nrow(beta))), idx, drop = FALSE]
colnames(beta_sub) <- pd_sub$sample

beta_out <- data.frame(cpg = rownames(beta_sub), as.data.frame(beta_sub), check.names = FALSE)
utils::write.csv(beta_out, file.path(data_dir, "Beta矩阵_BetaMatrix_FlowSorted450k_subset.csv"), row.names = FALSE, fileEncoding = "UTF-8")
meta_out <- data.frame(sample = pd_sub$sample, group = pd_sub$CellType, stringsAsFactors = FALSE)
utils::write.csv(meta_out, file.path(data_dir, "样本信息_SampleMeta_FlowSorted450k.csv"), row.names = FALSE, fileEncoding = "UTF-8")

g1 <- types[1]; g2 <- types[2]
cols1 <- which(meta_out$group == g1)
cols2 <- which(meta_out$group == g2)
delta <- rowMeans(beta_sub[, cols1, drop = FALSE]) - rowMeans(beta_sub[, cols2, drop = FALSE])
dm <- data.frame(cpg = rownames(beta_sub), deltaBeta = delta)
utils::write.csv(dm, file.path(tab_dir, delivery_table_name(skill_en, "DMP", "deltaBeta")), row.names = FALSE)

write_delivery_audit(
  skill_en, "post", nrow(beta_sub), ncol(beta_sub), ncol(beta_sub),
  paste0("FlowSorted.Blood.450k CellType ", g1, " vs ", g2), FALSE, accession, sourced_note,
  "REAL beta subset; upstream Bismark/MethylKit BLOCKED_EXTERNAL",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = data_provenance
)

p <- ggplot(dm, aes(deltaBeta)) +
  geom_histogram(bins = 30, fill = bioinfo_palette[4], color = "white") +
  labs(title = paste0("deltaBeta (", g1, " vs ", g2, ", FlowSorted450k)"), x = "deltaBeta", y = "count")
delivery_save_plot(p, skill_en, "hist", "deltaBeta", 6, 4.5, fig_dir, bio_root)

prov <- list(
  data_provenance = data_provenance,
  source = "Bioconductor FlowSorted.Blood.450k",
  accession = accession,
  scope = "450k/850k beta matrix downstream only",
  blocked_upstream = c("Bismark", "MethylKit", "WGBS FASTQ alignment"),
  contrast = paste(g1, "vs", g2),
  status_note = "PARTIAL: REAL beta QC/DMP demo; full WGBS pipeline not run in sample."
)
if (requireNamespace("jsonlite", quietly = TRUE)) {
  jsonlite::write_json(prov, file.path(data_dir, "PROVENANCE.json"), auto_unbox = TRUE, pretty = TRUE)
}

fig_map <- c("deltaBeta 分布" = paste0("../图片文件/", delivery_stem(skill_en, "hist", "deltaBeta"), ".png"))
interp <- paste0("REAL FlowSorted.Blood.450k beta subset; PARTIAL (no WGBS FASTQ). accession=", accession, ".")
status <- "PARTIAL"
blocked_reason <- "Upstream WGBS/RRBS alignment (Bismark/MethylKit) BLOCKED_EXTERNAL; sample uses REAL public beta matrix only."
data_html <- paste0(
  "<p><b>data_provenance: REAL</b> — FlowSorted.Blood.450k 公开 beta 子集（", g1, " vs ", g2, "）。</p>",
  "<p><b>STATUS: PARTIAL</b> — 未跑 WGBS/RRBS 比对；见技能说明 SOP。</p>"
)
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(skill_en, skill_folder, status, data_html, audit_html, sourced_note, fig_map, interp, rep_file, blocked_reason = blocked_reason)
writeLines(c(status, paste0("data_provenance=", data_provenance), blocked_reason), file.path(rep_dir, "STATUS.txt"))
for (old in c("toy_beta.csv")) {
  f <- file.path(data_dir, old)
  if (file.exists(f)) file.rename(f, file.path(data_dir, paste0("obsolete_", old)))
}
message("DONE ", status, " — ", skill_folder)
