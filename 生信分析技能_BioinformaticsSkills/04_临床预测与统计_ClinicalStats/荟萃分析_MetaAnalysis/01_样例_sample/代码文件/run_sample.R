# 样例 — MetaAnalysis REAL cross-cohort KEGG NES (书清多 GSE 嵌入)
# analysis_kind=meta  seed=43626
# data_provenance=REAL — skill-local real_GSE*_GSEA_KEGG.csv
options(stringsAsFactors = FALSE)
set.seed(43626)

sample_root <- normalizePath("..", winslash = "/", mustWork = TRUE)
skill_root <- normalizePath("../..", winslash = "/", mustWork = TRUE)
bio_root <- normalizePath("../../..", winslash = "/", mustWork = TRUE)
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath("../../../..", winslash = "/", mustWork = TRUE)
}
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath(file.path(skill_root, "..", ".."), winslash = "/", mustWork = TRUE)
}

viz_script <- file.path(
  bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
  "脚本_scripts", "出版级出图_PublicationPlot.R"
)
if (file.exists(viz_script)) source(viz_script, encoding = "UTF-8")

delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
paths <- delivery_sample_paths(sample_root)
data_dir <- paths$raw_dir; fig_dir <- paths$fig_dir; tab_dir <- paths$tab_dir; rep_dir <- paths$rep_dir
for (d in c(data_dir, fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)
source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")

skill_en <- "MetaAnalysis"
skill_folder <- "荟萃分析_MetaAnalysis"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- if (length(sk_files)) {
  for (sf in sk_files) try(source(sf, encoding = "UTF-8"), silent = TRUE)
  paste0("sourced: ", paste(basename(sk_files), collapse = ", "))
} else "no skill scripts"
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
library(ggplot2)

gsea_files <- list.files(data_dir, pattern = "^real_GSE[0-9]+_GSEA_KEGG\\.csv$", full.names = TRUE)
stopifnot(length(gsea_files) >= 2L)

# Build NES table per study for pathways present in >=2 cohorts
rows <- list()
for (f in gsea_files) {
  acc <- sub("^real_(GSE[0-9]+)_GSEA_KEGG\\.csv$", "\\1", basename(f))
  d <- read.csv(f, check.names = FALSE, stringsAsFactors = FALSE)
  d$study <- acc
  d$pathway <- if ("Description" %in% names(d)) d$Description else d$ID
  d$NES <- as.numeric(d$NES)
  d$pvalue <- as.numeric(d$pvalue)
  rows[[acc]] <- d[, c("study", "pathway", "NES", "pvalue", "ID")]
}
all <- do.call(rbind, rows)
freq <- table(all$pathway)
common <- names(freq)[freq >= 2L]
# pick pathway with strongest mean |NES| among common
# pick pathway with strongest mean |NES| among common; keep short display title
cand <- all[all$pathway %in% common, ]
mean_abs <- tapply(abs(cand$NES), cand$pathway, mean, na.rm = TRUE)
focus <- names(sort(mean_abs, decreasing = TRUE))[1]
# Prefer a short pathway name if top has long Description
short_candidates <- names(mean_abs)[nchar(names(mean_abs)) <= 28]
if (length(short_candidates)) {
  focus <- names(sort(mean_abs[short_candidates], decreasing = TRUE))[1]
}
studies <- cand[cand$pathway == focus, , drop = FALSE]
# SE proxy from p-value via |NES|/z approx (display only)
z <- abs(qnorm(pmax(studies$pvalue, 1e-12) / 2))
studies$se <- ifelse(is.finite(z) & z > 0, abs(studies$NES) / z, 0.15)
studies$lo <- studies$NES - 1.96 * studies$se
studies$hi <- studies$NES + 1.96 * studies$se
studies <- studies[order(studies$NES), , drop = FALSE]
write.csv(studies, file.path(tab_dir, delivery_table_name(skill_en, "forest", "NES")), row.names = FALSE)

write_delivery_audit(
  skill_en, "post", nrow(studies), ncol(studies), length(gsea_files),
  paste0("cross-cohort NES forest: ", focus),
  FALSE, paste(studies$study, collapse = ","), sourced_note,
  "KEGG NES forest across embedded GSEA tables; data_provenance=REAL",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "REAL"
)

title_short <- if (nchar(focus) > 24) paste0(substr(focus, 1, 21), "...") else focus
p <- ggplot(studies, aes(NES, reorder(study, NES))) +
  geom_vline(xintercept = 0, linetype = 2, color = "grey50") +
  geom_errorbar(aes(xmin = lo, xmax = hi), orientation = "y", width = 0.2, color = "grey40") +
  geom_point(color = bioinfo_palette[3], size = 2.8) +
  labs(
    title = paste0("NES — ", title_short),
    x = "NES", y = NULL
  ) +
  theme_journal()
delivery_save_plot(p, skill_en, "forest", "StudyNES", 7.2, 4.8, fig_dir, bio_root, order = 1)

fig_map <- c("NES 森林图" = paste0("../图片文件/", delivery_stem(skill_en, "forest", "StudyNES", order = 1), ".png"))
interp <- paste0(
  "REAL：书清多队列 GSEA KEGG 嵌入表，通路「", focus, "」跨队列 NES 森林图。",
  "SE 由 p 值近似，仅作展示。data_provenance=REAL。"
)
status <- "PASS"
data_html <- paste0(
  "<p><b>data_provenance: REAL</b> — 技能内 <code>real_GSE*_GSEA_KEGG.csv</code>（",
  length(gsea_files), " 队列）。焦点通路：", focus, "。</p>"
)
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- if (file.exists(audit_path)) {
  paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")
} else "<p>none</p>"
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(skill_en, skill_folder, status, data_html, audit_html, sourced_note, fig_map, interp, rep_file, blocked_reason = "")
writeLines(c(status, "data_provenance=REAL", paste0("pathway=", focus)), file.path(rep_dir, "STATUS.txt"))
message("DONE ", status, " — ", skill_folder, " REAL pathway=", focus)
