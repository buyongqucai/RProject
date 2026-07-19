# 样例分析脚本 — 统一交付规范_DeliveryStandards
# 合规：统一可视化规范_VizStandards + 统一交付规范_DeliveryStandards
# analysis_kind=delivery_demo  seed=202601
#
# 1) source 统一可视化规范 出版级出图
# 2) source 统一交付规范 出图命名/审计/报告
# 3) source 本技能 脚本_scripts
options(stringsAsFactors = FALSE)
set.seed(202601)

sample_root <- normalizePath("..", winslash = "/", mustWork = TRUE)
skill_root <- normalizePath("../..", winslash = "/", mustWork = TRUE)
bio_root <- normalizePath("../../..", winslash = "/", mustWork = TRUE)
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath("../../../..", winslash = "/", mustWork = TRUE)
}
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath(file.path(skill_root, "..", ".."), winslash = "/", mustWork = TRUE)
}


# 1) VizStandards
source(file.path(
  bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
  "脚本_scripts", "出版级出图_PublicationPlot.R"
), encoding = "UTF-8")

# 2) DeliveryStandards
# 1) source 统一可视化规范 出版级出图
# 2) source 统一交付规范 出图命名/审计/报告
# 3) source 本技能 脚本_scripts
viz_script <- file.path(
  bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
  "脚本_scripts", "出版级出图_PublicationPlot.R"
)
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


# 3) 本技能脚本（规范脚本即本技能）
skill_en <- "DeliveryStandards"
skill_folder <- "统一交付规范_DeliveryStandards"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- paste0("已 source VizStandards + DeliveryStandards: ", paste(basename(sk_files), collapse = ", "))
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
library(ggplot2)

df <- data.frame(
  rule = c("命名", "审计", "报告", "DPI600", "SVG+PNG"),
  score = c(5, 4, 5, 5, 5)
)
write.csv(df, file.path(tab_dir, delivery_table_name(skill_en, "rules", "checklist")), row.names = FALSE)
write_delivery_audit(
  skill_en, "pre", n_rows = nrow(df), n_cols = 2, n_samples = 0,
  group_source = "n/a", toy = TRUE, sourced_skill_scripts = sourced_note,
  notes = "规范自证样例", out_path = file.path(tab_dir, delivery_audit_name(skill_en, "pre"))
)
p <- ggplot(df, aes(rule, score, fill = rule)) +
  geom_col(show.legend = FALSE) +
  scale_fill_manual(values = bioinfo_palette[seq_len(nrow(df))]) +
  labs(title = "Delivery rule coverage", x = NULL, y = "Score")
paths <- delivery_save_plot(
  p, skill_en, "bar", "RuleCoverage",
  width = FIG_WIDTH_DOUBLE_IN, height = 3.2, out_dir = fig_dir, start = bio_root
)
write_delivery_audit(
  skill_en, "post", n_rows = nrow(df), n_cols = 2, n_samples = 0,
  group_source = "n/a", toy = TRUE, sourced_skill_scripts = sourced_note,
  notes = paste("图:", basename(paths$png)),
  out_path = file.path(tab_dir, delivery_audit_name(skill_en, "post"))
)
fig_map <- c("规则覆盖柱状图" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "RuleCoverage"), ".png"))
interp <- "自证中英对照命名与 save_plot_pub；非生物学结论。"
status <- "PASS"

data_html <- paste0(
  "<p><b>toy=TRUE</b>：本样例为可复现模拟数据，<b>不可外推</b>。</p>",
  "<p>详见 <code>数据文件/DATA_SOURCE.md</code>。</p>"
)
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(
  skill_en, skill_folder, status,
  data_html, audit_html, sourced_note, fig_map, interp, rep_file
)
writeLines(status, file.path(rep_dir, "STATUS.txt"))

# 清理旧英文前缀产物
for (old in list.files(c(fig_dir, tab_dir, rep_dir), full.names = TRUE)) {
  bn <- basename(old)
  if (grepl("^(DeliveryStandards_|sample_|toy_)", bn) || bn %in% c("样例报告.html")) {
    try(file.remove(old), silent = TRUE)
  }
}
message("DONE ", status, " — ", skill_folder, " report=", basename(rep_file))
