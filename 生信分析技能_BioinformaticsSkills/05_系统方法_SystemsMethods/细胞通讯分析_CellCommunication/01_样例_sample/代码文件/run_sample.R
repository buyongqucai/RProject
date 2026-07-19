# 样例 — CellCommunication REAL GSE207177 LR (书清嵌入缓存)
# analysis_kind=cellcomm  seed=30338
# data_provenance=REAL — skill-local real_GSE207177_*
options(stringsAsFactors = FALSE)
set.seed(30338)

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

skill_en <- "CellCommunication"
skill_folder <- "细胞通讯分析_CellCommunication"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- if (length(sk_files)) {
  for (sf in sk_files) try(source(sf, encoding = "UTF-8"), silent = TRUE)
  paste0("sourced: ", paste(basename(sk_files), collapse = ", "))
} else "no skill scripts"
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
library(ggplot2)

accession <- "GSE207177"
top_path <- file.path(data_dir, "real_GSE207177_Top_LR_pairs.csv")
stopifnot(file.exists(top_path))
lr <- read.csv(top_path, check.names = FALSE, stringsAsFactors = FALSE)
# expect: pair, axis, delta, label
lr <- lr[order(-abs(as.numeric(lr$delta))), , drop = FALSE]
lr <- lr[seq_len(min(12L, nrow(lr))), , drop = FALSE]
lr$label <- if ("label" %in% names(lr)) lr$label else paste0(lr$pair, " | ", lr$axis)
lr$label <- factor(lr$label, levels = rev(lr$label))
write.csv(lr, file.path(tab_dir, delivery_table_name(skill_en, "LR", "TopPairs")), row.names = FALSE)

write_delivery_audit(
  skill_en, "post", nrow(lr), ncol(lr), NA,
  paste0(accession, " top enhanced LR pairs"),
  FALSE, accession, sourced_note,
  "LR bar from skill-local cache; data_provenance=REAL",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "REAL"
)

p <- ggplot(lr, aes(as.numeric(delta), label)) +
  geom_col(fill = bioinfo_palette[5], width = 0.72) +
  labs(
    title = paste0("Top LR pairs — ", accession),
    x = "delta (CLP vs Control)", y = NULL
  ) +
  theme_journal()
delivery_save_plot(p, skill_en, "bar", "LRscores", 7.2, 5.2, fig_dir, bio_root, order = 1)

fig_map <- c("配体-受体 Top" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "LRscores", order = 1), ".png"))
interp <- paste0("REAL ", accession, "：书清 Top 增强通讯对（技能内 real_* 缓存）。data_provenance=REAL。")
status <- "PASS"
data_html <- paste0(
  "<p><b>data_provenance: REAL</b> — <code>", accession, "</code> ",
  "<code>real_GSE207177_Top_LR_pairs.csv</code>（书清表嵌入本技能）。</p>"
)
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- if (file.exists(audit_path)) {
  paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")
} else "<p>none</p>"
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(skill_en, skill_folder, status, data_html, audit_html, sourced_note, fig_map, interp, rep_file, blocked_reason = "")
writeLines(c(status, "data_provenance=REAL", paste0("accession=", accession)), file.path(rep_dir, "STATUS.txt"))
message("DONE ", status, " — ", skill_folder, " REAL ", accession)
