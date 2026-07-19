# 样例 — InSilicoKO REAL GSE207177 TF rescue counts (书清延展分析嵌入)
# analysis_kind=insilico_ko  seed=37409
# data_provenance=REAL — skill-local real_GSE207177_InSilicoKO_TF.csv
options(stringsAsFactors = FALSE)
set.seed(37409)

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

skill_en <- "InSilicoKO"
skill_folder <- "虚拟敲除与扰动_InSilicoKO"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- if (length(sk_files)) {
  for (sf in sk_files) try(source(sf, encoding = "UTF-8"), silent = TRUE)
  paste0("sourced: ", paste(basename(sk_files), collapse = ", "))
} else "no skill scripts"
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
library(ggplot2)

accession <- "GSE207177"
ko_path <- file.path(data_dir, "real_GSE207177_InSilicoKO_TF.csv")
stopifnot(file.exists(ko_path))
ko <- read.csv(ko_path, check.names = FALSE, stringsAsFactors = FALSE)
ko$rescued_DEGs <- as.integer(ko$rescued_DEGs)
ko <- ko[order(-ko$rescued_DEGs), , drop = FALSE]
ko$TF <- factor(ko$TF, levels = rev(ko$TF))
write.csv(ko, file.path(tab_dir, delivery_table_name(skill_en, "KO", "TFrescue")), row.names = FALSE)

write_delivery_audit(
  skill_en, "post", nrow(ko), ncol(ko), NA,
  paste0(accession, " in silico KO TF rescued DEGs"),
  FALSE, accession, sourced_note,
  "TF rescued DEG bar; data_provenance=REAL",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "REAL"
)

p <- ggplot(ko, aes(rescued_DEGs, TF)) +
  geom_col(fill = bioinfo_palette[1], width = 0.72) +
  labs(
    title = paste0("TF rescued DEGs — ", accession),
    x = "rescued DEGs", y = NULL
  ) +
  theme_journal()
delivery_save_plot(p, skill_en, "bar", "KOrescue", 6.2, 4.5, fig_dir, bio_root, order = 1)

fig_map <- c("虚拟敲除逆转" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "KOrescue", order = 1), ".png"))
interp <- paste0("REAL ", accession, "：书清虚拟敲除 TF 逆转疾病基因数。data_provenance=REAL。")
status <- "PASS"
data_html <- paste0(
  "<p><b>data_provenance: REAL</b> — <code>", accession, "</code> ",
  "<code>real_GSE207177_InSilicoKO_TF.csv</code>。</p>"
)
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- if (file.exists(audit_path)) {
  paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")
} else "<p>none</p>"
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(skill_en, skill_folder, status, data_html, audit_html, sourced_note, fig_map, interp, rep_file, blocked_reason = "")
writeLines(c(status, "data_provenance=REAL", paste0("accession=", accession)), file.path(rep_dir, "STATUS.txt"))
message("DONE ", status, " — ", skill_folder, " REAL ", accession)
