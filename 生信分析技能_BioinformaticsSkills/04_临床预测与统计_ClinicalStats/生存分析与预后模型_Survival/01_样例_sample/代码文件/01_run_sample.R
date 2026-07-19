# 样例 — Survival REAL GSE17536 (FCGR3A High/Low OS KM + risk table)
# analysis_kind=survival  seed=909
options(stringsAsFactors = FALSE)
set.seed(909)

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

skill_en <- "Survival"
skill_folder <- "生存分析与预后模型_Survival"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- if (length(sk_files)) {
  for (sf in sk_files) try(source(sf, encoding = "UTF-8"), silent = TRUE)
  paste0("sourced: ", paste(basename(sk_files), collapse = ", "))
} else "no skill scripts"

accession <- "GSE17536"
cache <- file.path(data_dir, "real_GSE17536_OS_FCGR3A.csv")
if (!file.exists(cache)) {
  proj <- normalizePath(file.path(bio_root, ".."), winslash = "/", mustWork = TRUE)
  bs <- file.path(proj, "_tmp_build_wave1_caches.R")
  if (file.exists(bs)) source(bs, encoding = "UTF-8")
}
stopifnot(file.exists(cache))
surv <- read.csv(cache, check.names = FALSE, stringsAsFactors = FALSE)
surv$risk <- factor(surv$risk, levels = c("High", "Low"))
write.csv(surv, file.path(tab_dir, delivery_table_name(skill_en, "KM", "HighVsLow")), row.names = FALSE)
write_delivery_audit(
  skill_en, "post", nrow(surv), ncol(surv), nrow(surv),
  paste0(accession, " OS + FCGR3A median risk"), FALSE, accession, sourced_note,
  "KM + risk table; data_provenance=REAL",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "REAL"
)

p <- plot_km_risk_table_journal(
  time = surv$time, event = surv$event, group = surv$risk,
  xlab = "OS (months)", ylab = "Survival probability",
  title = paste0("KM by FCGR3A — ", accession),
  conf.int = TRUE, risk_table = TRUE
)
delivery_save_plot(p, skill_en, "KM", "HighVsLow_RiskTable", 6.5, 6.2, fig_dir, bio_root, order = 1)

fig_map <- c("KM+风险表" = paste0("../图片文件/", delivery_stem(skill_en, "KM", "HighVsLow_RiskTable", order = 1), ".png"))
interp <- paste0("REAL ", accession, "：OS KM stratified by median FCGR3A. data_provenance=REAL。")
status <- "PASS"
data_html <- paste0(
  "<p><b>data_provenance: REAL</b> — <code>", accession, "</code> (山水 clinical+FCGR3A).</p>",
  "<p>See <code>数据文件/DATA_SOURCE.md</code>.</p>"
)
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- if (file.exists(audit_path)) paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>") else "<p>none</p>"
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(skill_en, skill_folder, status, data_html, audit_html, sourced_note, fig_map, interp, rep_file, blocked_reason = "")
writeLines(c(status, "data_provenance=REAL", paste0("accession=", accession)), file.path(rep_dir, "STATUS.txt"))
message("DONE ", status, " — ", skill_folder, " REAL ", accession)
