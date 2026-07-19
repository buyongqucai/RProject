# 样例 — DiagnosticROC REAL GSE17536 FCGR3A vs OS event (山水嵌入)
# analysis_kind=diagnostic_roc  seed=30698
# data_provenance=REAL — skill-local real_GSE17536_FCGR3A_OS_for_ROC.csv
options(stringsAsFactors = FALSE)
set.seed(30698)

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

skill_en <- "DiagnosticROC"
skill_folder <- "诊断效能ROC_DiagnosticROC"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- if (length(sk_files)) {
  for (sf in sk_files) try(source(sf, encoding = "UTF-8"), silent = TRUE)
  paste0("sourced: ", paste(basename(sk_files), collapse = ", "))
} else "no skill scripts"
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
library(ggplot2)

accession <- "GSE17536"
cache <- file.path(data_dir, "real_GSE17536_FCGR3A_OS_for_ROC.csv")
stopifnot(file.exists(cache))
dat <- read.csv(cache, check.names = FALSE, stringsAsFactors = FALSE)
dat <- dat[!is.na(dat$FCGR3A) & !is.na(dat$event), , drop = FALSE]
score <- as.numeric(dat$FCGR3A)
label <- as.integer(dat$event)

# Empirical ROC (no pROC required)
ord <- order(score, decreasing = TRUE)
y <- label[ord]
n_pos <- sum(y == 1L); n_neg <- sum(y == 0L)
stopifnot(n_pos > 0L, n_neg > 0L)
tpr <- cumsum(y == 1L) / n_pos
fpr <- cumsum(y == 0L) / n_neg
# add origin
roc <- data.frame(FPR = c(0, fpr), TPR = c(0, tpr))
# trapezoid AUC
auc <- sum(diff(roc$FPR) * (head(roc$TPR, -1) + tail(roc$TPR, -1)) / 2)
write.csv(roc, file.path(tab_dir, delivery_table_name(skill_en, "ROC", "FCGR3A_OS")), row.names = FALSE)
write.csv(
  data.frame(marker = "FCGR3A", outcome = "os_event", n = nrow(dat), n_event = n_pos, AUC = auc),
  file.path(tab_dir, delivery_table_name(skill_en, "AUC", "summary")),
  row.names = FALSE
)

write_delivery_audit(
  skill_en, "post", nrow(dat), 2, n_pos,
  paste0(accession, " FCGR3A vs OS event ROC"),
  FALSE, accession, sourced_note,
  paste0("AUC=", signif(auc, 3), "; data_provenance=REAL"),
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "REAL"
)

p <- ggplot(roc, aes(FPR, TPR)) +
  geom_ribbon(aes(ymin = 0, ymax = TPR), fill = bioinfo_palette[2], alpha = 0.18) +
  geom_line(color = bioinfo_palette[2], linewidth = 1.1) +
  geom_abline(slope = 1, intercept = 0, linetype = 2, color = "grey50") +
  annotate("text", x = 0.65, y = 0.15, label = paste0("AUC = ", signif(auc, 3)), size = 4) +
  labs(
    title = paste0("FCGR3A ROC — ", accession),
    x = "FPR", y = "TPR"
  ) +
  theme_journal() +
  coord_equal()
delivery_save_plot(p, skill_en, "ROC", "Diagnostic", 5.5, 5.2, fig_dir, bio_root, order = 1)

fig_map <- c("诊断 ROC" = paste0("../图片文件/", delivery_stem(skill_en, "ROC", "Diagnostic", order = 1), ".png"))
interp <- paste0(
  "REAL ", accession, "：FCGR3A 连续分 vs OS event 的经验 ROC（AUC=", signif(auc, 3),
  "）。样例为预后关联演示，非临床诊断声明。data_provenance=REAL。"
)
status <- "PASS"
data_html <- paste0(
  "<p><b>data_provenance: REAL</b> — <code>", accession, "</code> ",
  "<code>real_GSE17536_FCGR3A_OS_for_ROC.csv</code>（山水临床嵌入）。</p>"
)
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- if (file.exists(audit_path)) {
  paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")
} else "<p>none</p>"
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(skill_en, skill_folder, status, data_html, audit_html, sourced_note, fig_map, interp, rep_file, blocked_reason = "")
writeLines(c(status, "data_provenance=REAL", paste0("accession=", accession), paste0("AUC=", signif(auc, 4))), file.path(rep_dir, "STATUS.txt"))
message("DONE ", status, " — ", skill_folder, " REAL ", accession, " AUC=", signif(auc, 3))
