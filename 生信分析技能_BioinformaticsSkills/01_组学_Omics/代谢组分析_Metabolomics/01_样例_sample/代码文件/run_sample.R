# 样例分析脚本 — 代谢组分析_Metabolomics
# 合规：统一交付规范_DeliveryStandards + 统一可视化规范_VizStandards
# analysis_kind=metabolomics  seed=303
options(stringsAsFactors = FALSE)
set.seed(303)

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


skill_en <- "Metabolomics"
skill_folder <- "代谢组分析_Metabolomics"
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


mets <- paste0("M", 1:40)
mat <- matrix(abs(rnorm(40 * 8, 10, 3)), nrow = 40)
mat[1:6, 1:4] <- mat[1:6, 1:4] * 2.2
colnames(mat) <- paste0("S", 1:8)
meta <- data.frame(sample = colnames(mat), group = c(rep("Herb", 4), rep("Vehicle", 4)))
write.csv(cbind(metabolite = mets, as.data.frame(mat)), file.path(data_dir, "toy_metabolites.csv"), row.names = FALSE)
write.csv(meta, file.path(data_dir, "toy_meta.csv"), row.names = FALSE)
# 简易 VIP 代理：组间 |Δmean|
vip <- abs(rowMeans(mat[, 1:4]) - rowMeans(mat[, 5:8]))
res <- data.frame(metabolite = mets, delta = vip)[order(-vip), ]
write.csv(res, file.path(tab_dir, delivery_table_name(skill_en, "VIP", "HerbVsVehicle")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 40, 8, 8, "toy_meta Herb/Vehicle", TRUE, NA, sourced_note, "OPLS-like; data_provenance=TOY",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")), data_provenance = "TOY")
library(ggplot2)
top <- head(res, 12)
top$metabolite <- factor(top$metabolite, levels = rev(top$metabolite))
p <- ggplot(top, aes(delta, metabolite, fill = delta)) +
  geom_col(width = 0.75, show.legend = FALSE) +
  scale_fill_gradient(low = "#56B4E9", high = "#009E73") +
  labs(title = "Top 12 |Δmean| (VIP proxy)", x = "|Δmean| Herb − Vehicle", y = NULL)
delivery_save_plot(p, skill_en, "bar", "VIP_HerbVsVehicle", 5.2, 5.0, fig_dir, bio_root)
pc <- prcomp(t(log1p(mat)), scale. = TRUE)
pcd <- data.frame(PC1 = pc$x[, 1], PC2 = pc$x[, 2], group = meta$group)
p2 <- ggplot(pcd, aes(PC1, PC2, color = group)) +
  geom_point(size = 3.2) +
  scale_color_manual(values = bioinfo_palette[c(3, 8)]) +
  labs(title = "PCA of metabolite intensities", color = "Group")
delivery_save_plot(p2, skill_en, "PCA", "HerbVsVehicle", 5.0, 4.2, fig_dir, bio_root)
fig_map <- c(
  "差异代谢物条形图" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "VIP_HerbVsVehicle"), ".png"),
  "PCA" = paste0("../图片文件/", delivery_stem(skill_en, "PCA", "HerbVsVehicle"), ".png")
)
interp <- "TOY 代谢组：VIP 代理柱状 + PCA（非真实 OPLS-DA）。data_provenance=TOY。"
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
