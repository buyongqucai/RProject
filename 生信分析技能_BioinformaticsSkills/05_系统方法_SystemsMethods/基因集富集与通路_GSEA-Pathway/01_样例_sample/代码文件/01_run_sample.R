# 样例分析脚本 — 基因集富集与通路_GSEA-Pathway
# 合规：统一交付规范_DeliveryStandards + 统一可视化规范_VizStandards
# analysis_kind=gsea  seed=19537
options(stringsAsFactors = FALSE)
set.seed(19537)

sample_root <- normalizePath("..", winslash = "/", mustWork = TRUE)
skill_root <- normalizePath("../..", winslash = "/", mustWork = TRUE)
bio_root <- normalizePath("../../..", winslash = "/", mustWork = TRUE)
# 若技能在 00/01/... 下，bio_root 可能需再上一级
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath("../../../..", winslash = "/", mustWork = TRUE)
}
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  # DeliveryStandards 自身：skill 在 00 下，上两级即 bio root
  bio_root <- normalizePath(file.path(skill_root, "..", ".."), winslash = "/", mustWork = TRUE)
}


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


skill_en <- "GSEA-Pathway"
skill_folder <- "基因集富集与通路_GSEA-Pathway"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- "未找到可 source 的技能脚本"
if (length(sk_files)) {
  # source 全部非说明 R 脚本（骨架为函数定义，安全）
  for (sf in sk_files) {
    try(source(sf, encoding = "UTF-8"), silent = TRUE)
  }
  sourced_note <- paste0("已 source 本技能 脚本_scripts/: ", paste(basename(sk_files), collapse = ", "))
}
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")


pathways <- data.frame(
  pathway = c("OXPHOS", "Glycolysis", "TNF", "IFN-g", "Wnt", "Notch", "p53", "Hypoxia"),
  NES = c(1.8, 1.5, -1.6, -1.3, 1.1, -0.9, 1.4, 1.2) + rnorm(8, 0, 0.05),
  size = c(80, 60, 70, 55, 90, 40, 65, 75),
  stringsAsFactors = FALSE
)
pathways$padj <- pmin(0.2, 10^(-abs(pathways$NES)))
write.csv(pathways, file.path(tab_dir, delivery_table_name(skill_en, "GSEA", "NES")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 8, 4, NA, "toy gene sets", TRUE, NA, sourced_note, "GSEA NES; data_provenance=TOY",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")), data_provenance = "TOY")
library(ggplot2)
pathways$pathway <- factor(pathways$pathway, levels = pathways$pathway[order(pathways$NES)])
# Bar + bubble (not lollipop); muted up/down + sequential -log10(padj)
nes_fill <- c("FALSE" = unname(bioinfo_volcano[["down"]]), "TRUE" = unname(bioinfo_volcano[["up"]]))
p <- ggplot(pathways, aes(NES, pathway, fill = NES > 0)) +
  geom_col(width = 0.7) +
  geom_vline(xintercept = 0, linewidth = 0.4, color = "grey40") +
  scale_fill_manual(values = nes_fill, guide = "none") +
  labs(title = "GSEA NES by pathway (toy)", x = "NES", y = NULL)
delivery_save_plot(p, skill_en, "bar", "NES_Pathways", 5.5, 4.5, fig_dir, bio_root)
pb <- ggplot(pathways, aes(NES, pathway, size = size, color = -log10(pmax(padj, 1e-300)))) +
  geom_point(alpha = 0.9) +
  (if (exists("scale_color_bioinfo_sequential")) {
    scale_color_bioinfo_sequential(name = expression(-log[10](padj)))
  } else {
    scale_color_gradientn(colours = bioinfo_sequential, name = expression(-log[10](padj)))
  }) +
  scale_size_continuous(range = c(3, 9), name = "Set size") +
  labs(title = "GSEA bubble (NES vs pathway)", x = "NES", y = NULL)
delivery_save_plot(pb, skill_en, "bubble", "NES_Bubble", 6.2, 4.8, fig_dir, bio_root)
fig_map <- c(
  "通路 NES" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "NES_Pathways"), ".png"),
  "NES 气泡图" = paste0("../图片文件/", delivery_stem(skill_en, "bubble", "NES_Bubble"), ".png")
)
interp <- "TOY GSEA：NES 条形 + 气泡。data_provenance=TOY。"
status <- "PASS"

data_html <- paste0(
  "<p><b>data_provenance: TOY</b>：可复现模拟，<b>不可外推</b>。</p>",
  "<p>详见 <code>数据文件/DATA_SOURCE.md</code>。</p>"
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
writeLines(c(status, "data_provenance=TOY"), file.path(rep_dir, "STATUS.txt"))
for (old in c("sample_pca.png", "sample_volcano.png", "样例报告.html")) {
  f1 <- file.path(fig_dir, old); if (file.exists(f1)) file.remove(f1)
  f2 <- file.path(rep_dir, old); if (file.exists(f2)) file.remove(f2)
}
message("DONE ", status, " — ", skill_folder, " report=", basename(rep_file))
