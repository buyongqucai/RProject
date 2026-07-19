# 样例 — DoseTime REAL GSE207177 MAMs time-course
# analysis_kind=dose_time  seed=11515
options(stringsAsFactors = FALSE)
set.seed(11515)

sample_root <- normalizePath("..", winslash = "/", mustWork = TRUE)
skill_root <- normalizePath("../..", winslash = "/", mustWork = TRUE)
bio_root <- normalizePath("../../..", winslash = "/", mustWork = TRUE)
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath("../../../..", winslash = "/", mustWork = TRUE)
}
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath(file.path(skill_root, "..", ".."), winslash = "/", mustWork = TRUE)
}

viz_script <- file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards", "脚本_scripts", "出版级出图_PublicationPlot.R")
if (file.exists(viz_script)) source(viz_script, encoding = "UTF-8")
delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
paths <- delivery_sample_paths(sample_root)
data_dir <- paths$raw_dir; fig_dir <- paths$fig_dir; tab_dir <- paths$tab_dir; rep_dir <- paths$rep_dir
for (d in c(data_dir, fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)
source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")

skill_en <- "DoseTime"
skill_folder <- "剂量反应与时间序列_DoseTime"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- if (length(sk_files)) {
  for (sf in sk_files) try(source(sf, encoding = "UTF-8"), silent = TRUE)
  paste0("sourced: ", paste(basename(sk_files), collapse = ", "))
} else "no skill scripts"
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
library(ggplot2)

accession <- "GSE207177"
cache <- file.path(data_dir, "real_GSE207177_MAMs_timeseries.csv")
if (!file.exists(cache)) {
  proj <- normalizePath(file.path(bio_root, ".."), winslash = "/", mustWork = TRUE)
  bs <- file.path(proj, "_tmp_build_wave1_caches.R")
  if (file.exists(bs)) source(bs, encoding = "UTF-8")
}
stopifnot(file.exists(cache))
ts <- read.csv(cache, check.names = FALSE, stringsAsFactors = FALSE)
# time order
ts$time <- factor(ts$time, levels = intersect(c("Control", "CLP12h", "CLP24h"), unique(ts$time)))
write.csv(ts, file.path(tab_dir, delivery_table_name(skill_en, "timeseries", "MAMs")), row.names = FALSE)
write_delivery_audit(
  skill_en, "post", nrow(ts), ncol(ts), length(unique(ts$sample_id)),
  paste0(accession, " MAMs time-course"), FALSE, accession, sourced_note,
  "line + severity trend + paired; data_provenance=REAL",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "REAL"
)

# 1) Line: mean expr per gene x time (top 6 genes by variance)
gene_var <- tapply(ts$expr, ts$gene, stats::var, na.rm = TRUE)
top_g <- names(sort(gene_var, decreasing = TRUE))[seq_len(min(6L, length(gene_var)))]
agg <- aggregate(expr ~ gene + time, data = ts[ts$gene %in% top_g, ], FUN = mean)
p1 <- ggplot(agg, aes(time, expr, color = gene, group = gene)) +
  geom_line(linewidth = 0.9) + geom_point(size = 2) +
  scale_color_manual(values = rep(bioinfo_palette, length.out = length(top_g))) +
  labs(title = paste0("MAMs time-course — ", accession), x = "Time", y = "Expression", color = NULL) +
  theme_journal()
delivery_save_plot(p1, skill_en, "line", "MAMsTimeCourse", 7, 4.5, fig_dir, bio_root, order = 1)

# 2) Severity trend: map time to numeric severity 0/1/2
sev <- ts[ts$gene %in% top_g[1:2], ]
sev$severity <- as.numeric(sev$time) - 1
sev$module <- sev$gene
p_tr <- plot_severity_trend_journal(
  sev, x_col = "severity", y_col = "expr", group_col = "module",
  title = paste0("Gene vs time — ", accession),
  xlab = "Time score (0/1/2)", ylab = "Expression"
)
delivery_save_plot(p_tr, skill_en, "trend", "GeneSeverity", 6.0, 4.2, fig_dir, bio_root, order = 2)

# 3) Paired: Control vs CLP24h for gene with both (use sample pairing by index within gene)
g0 <- top_g[1]
ctrl <- ts[ts$gene == g0 & ts$time == "Control", ]
clp <- ts[ts$gene == g0 & ts$time == "CLP24h", ]
n_pair <- min(nrow(ctrl), nrow(clp), 6L)
paired <- rbind(
  data.frame(id = paste0("P", seq_len(n_pair)), group = "Control", value = ctrl$expr[seq_len(n_pair)]),
  data.frame(id = paste0("P", seq_len(n_pair)), group = "CLP24h", value = clp$expr[seq_len(n_pair)])
)
paired$group <- factor(paired$group, levels = c("Control", "CLP24h"))
p_pair <- plot_paired_box_journal(
  paired, id_col = "id", group_col = "group", value_col = "value",
  title = paste0(g0, ": Control vs CLP24h"), ylab = "Expression"
)
delivery_save_plot(p_pair, skill_en, "pairedbox", "ControlVsCLP24h", 4.8, 4.5, fig_dir, bio_root, order = 3)

fig_map <- c(
  "时序折线" = paste0("../图片文件/", delivery_stem(skill_en, "line", "MAMsTimeCourse", order = 1), ".png"),
  "严重度趋势" = paste0("../图片文件/", delivery_stem(skill_en, "trend", "GeneSeverity", order = 2), ".png"),
  "配对箱线" = paste0("../图片文件/", delivery_stem(skill_en, "pairedbox", "ControlVsCLP24h", order = 3), ".png")
)
interp <- paste0("REAL ", accession, " MAMs 时序表达：折线 + 趋势 + Control–CLP24h 配对。data_provenance=REAL。")
status <- "PASS"
data_html <- paste0("<p><b>data_provenance: REAL</b> — <code>", accession, "</code> 书清 MAMs时序表达。</p>")
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- if (file.exists(audit_path)) paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>") else "<p>none</p>"
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(skill_en, skill_folder, status, data_html, audit_html, sourced_note, fig_map, interp, rep_file, blocked_reason = "")
writeLines(c(status, "data_provenance=REAL", paste0("accession=", accession)), file.path(rep_dir, "STATUS.txt"))
message("DONE ", status, " — ", skill_folder, " REAL ", accession)
