# 样例分析脚本 — 免疫浸润与免疫治疗_ImmuneInfiltration
# 合规：统一交付规范_DeliveryStandards + 统一可视化规范_VizStandards
# analysis_kind=immune  seed=15496
# data_provenance=REAL — GSE207177 CIBERSORT-like fractions (书清)
options(stringsAsFactors = FALSE)
set.seed(15496)

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
data_dir <- paths$raw_dir
fig_dir <- paths$fig_dir
tab_dir <- paths$tab_dir
rep_dir <- paths$rep_dir
for (d in c(data_dir, fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)
source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")

skill_en <- "ImmuneInfiltration"
skill_folder <- "免疫浸润与免疫治疗_ImmuneInfiltration"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- "未找到可 source 的技能脚本"
if (length(sk_files)) {
  for (sf in sk_files) {
    try(source(sf, encoding = "UTF-8"), silent = TRUE)
  }
  sourced_note <- paste0("已 source 本技能 脚本_scripts/: ", paste(basename(sk_files), collapse = ", "))
}
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")

shuqing_root <- Sys.getenv("SHUQING_ROOT", "E:/RProject/书清项目")
accession <- "GSE207177"
cib_cache <- file.path(data_dir, "real_GSE207177_CIBERSORT_fractions.csv")
cib_live <- file.path(shuqing_root, "GSE207177", "结果", "表格", "GSE207177_CIBERSORT免疫浸润.csv")
cib_path <- if (file.exists(cib_cache)) cib_cache else if (file.exists(cib_live)) cib_live else NA_character_
if (is.na(cib_path)) stop("Missing REAL CIBERSORT table")

cib <- read.csv(cib_path, check.names = FALSE, stringsAsFactors = FALSE)
cell_cols <- setdiff(names(cib), c("sample", "method", "Sample", "Group"))
# Mean fraction across samples for bar plot
cells <- data.frame(
  cell = cell_cols,
  fraction = colMeans(as.matrix(cib[, cell_cols, drop = FALSE]), na.rm = TRUE),
  stringsAsFactors = FALSE
)
cells <- cells[order(-cells$fraction), ]
write.csv(cells, file.path(tab_dir, delivery_table_name(skill_en, "CIBERSORT", "fractions")), row.names = FALSE)

# Group from sample name: Control (n-) vs CLP
grp <- ifelse(grepl("clp|CLP", cib$sample, ignore.case = TRUE), "CLP", "Control")
# Bracket box: Macrophages (or first available) by group
score_col <- if ("Macrophages" %in% names(cib)) "Macrophages" else cell_cols[1]
score_df <- data.frame(
  group = factor(grp, levels = c("Control", "CLP")),
  value = as.numeric(cib[[score_col]]),
  stringsAsFactors = FALSE
)

write_delivery_audit(
  skill_en, "post", nrow(cib), length(cell_cols), nrow(cib),
  paste0(accession, " CIBERSORT-like fractions"),
  FALSE, NA, sourced_note,
  "immune frac + Macrophages score brackets; data_provenance=REAL",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "REAL"
)

library(ggplot2)
ncell <- nrow(cells)
p <- ggplot(cells, aes(reorder(cell, fraction), fraction, fill = cell)) +
  geom_col(show.legend = FALSE) + coord_flip() +
  scale_fill_manual(values = rep(bioinfo_palette, length.out = ncell)) +
  labs(title = paste0("Immune fractions — ", accession), x = NULL, y = "fraction")
delivery_save_plot(p, skill_en, "bar", "CellFractions", 6.5, 5, fig_dir, bio_root, order = 1)

p_box <- plot_box_bracket_journal(
  score_df, value_col = "value", group_col = "group",
  title = paste0(score_col, " by group — ", accession),
  ylab = paste0(score_col, " fraction")
)
delivery_save_plot(p_box, skill_en, "box", "ScoreBrackets", 4.5, 4.5, fig_dir, bio_root, order = 2)

fig_map <- c(
  "免疫细胞比例" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "CellFractions", order = 1), ".png"),
  "评分箱线括号" = paste0("../图片文件/", delivery_stem(skill_en, "box", "ScoreBrackets", order = 2), ".png")
)
interp <- paste0("REAL ", accession, "：书清 CIBERSORT 风格免疫分数均值柱 + ", score_col, " Control vs CLP 箱线括号。data_provenance=REAL。")
status <- "PASS"

data_html <- paste0(
  "<p><b>data_provenance: REAL</b> — <code>", accession, "</code> ",
  "<code>GSE207177_CIBERSORT免疫浸润.csv</code>（书清；method 字段见原表）。</p>",
  "<p>缓存：<code>数据文件/real_GSE207177_CIBERSORT_fractions.csv</code>。</p>"
)
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- if (file.exists(audit_path)) {
  paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")
} else {
  "<p>无 post 审计表</p>"
}
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(
  skill_en, skill_folder, status,
  data_html, audit_html, sourced_note, fig_map, interp, rep_file,
  blocked_reason = if (exists("blocked_reason")) blocked_reason else ""
)
writeLines(c(status, "data_provenance=REAL", paste0("accession=", accession)), file.path(rep_dir, "STATUS.txt"))
for (old in c("sample_pca.png", "sample_volcano.png", "样例报告.html")) {
  f1 <- file.path(fig_dir, old); if (file.exists(f1)) file.remove(f1)
  f2 <- file.path(rep_dir, old); if (file.exists(f2)) file.remove(f2)
}
message("DONE ", status, " — ", skill_folder, " REAL ", accession, " report=", basename(rep_file))
