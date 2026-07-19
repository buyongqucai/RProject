# 样例分析脚本 — 蛋白质组分析_Proteomics
# 合规：统一交付规范_DeliveryStandards + 统一可视化规范_VizStandards
# analysis_kind=proteomics  seed=101
options(stringsAsFactors = FALSE)
set.seed(101)

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


skill_en <- "Proteomics"
skill_folder <- "蛋白质组分析_Proteomics"
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


proteins <- paste0("PROT", 1:50)
mat <- matrix(rnorm(50 * 6, mean = 20, sd = 2), nrow = 50)
mat[1:8, 1:3] <- mat[1:8, 1:3] + 4
colnames(mat) <- paste0("P", 1:6)
meta <- data.frame(sample = colnames(mat), group = c(rep("Disease", 3), rep("Healthy", 3)))
write.csv(cbind(protein = proteins, as.data.frame(mat)), file.path(data_dir, "toy_protein_intensity.csv"), row.names = FALSE)
write.csv(meta, file.path(data_dir, "toy_meta.csv"), row.names = FALSE)
group <- meta$group
pvals <- apply(mat, 1, function(v) t.test(v[group == "Disease"], v[group == "Healthy"])$p.value)
lfc <- rowMeans(mat[, group == "Disease", drop = FALSE]) - rowMeans(mat[, group == "Healthy", drop = FALSE])
res <- data.frame(protein = proteins, logFC = lfc, pvalue = pvals)
write.csv(res, file.path(tab_dir, delivery_table_name(skill_en, "DEP", "DiseaseVsHealthy")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 50, 6, 6, "toy_meta.csv", TRUE, NA, sourced_note, "LFQ-like; data_provenance=TOY",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")), data_provenance = "TOY")
library(ggplot2)
res$sig <- ifelse(res$pvalue < 0.05 & abs(res$logFC) > 1, ifelse(res$logFC > 0, "Up", "Down"), "NS")
p0 <- ggplot(res, aes(logFC, -log10(pmax(pvalue, 1e-300)), color = sig)) +
  geom_point(alpha = 0.85, size = 2) +
  scale_color_manual(values = c(NS = "grey75", Up = bioinfo_palette[6], Down = bioinfo_palette[1])) +
  labs(title = "Proteomics volcano (Disease vs Healthy)", x = "logFC", y = expression(-log[10](p)), color = NULL)
delivery_save_plot(p0, skill_en, "volcano", "DiseaseVsHealthy", 5.5, 4.5, fig_dir, bio_root)
top <- res[order(res$pvalue), ][1:15, ]
top$protein <- factor(top$protein, levels = rev(top$protein))
p <- ggplot(top, aes(logFC, protein, fill = logFC > 0)) + geom_col(width = 0.75) +
  scale_fill_manual(values = c("FALSE" = bioinfo_palette[1], "TRUE" = bioinfo_palette[6]), guide = "none") +
  labs(title = "Top 15 differential proteins", x = "logFC (disease − healthy)")
delivery_save_plot(p, skill_en, "bar", "Top15DEP", 5.5, 5.2, fig_dir, bio_root)
pc <- prcomp(t(mat), scale. = TRUE)
pcd <- data.frame(PC1 = pc$x[, 1], PC2 = pc$x[, 2], group = group)
p2 <- ggplot(pcd, aes(PC1, PC2, color = group)) +
  geom_point(size = 3.2) +
  scale_color_manual(values = bioinfo_palette[c(3, 2)]) +
  labs(title = "PCA of protein intensities", color = "Group")
delivery_save_plot(p2, skill_en, "PCA", "DiseaseVsHealthy", 5.0, 4.4, fig_dir, bio_root)
fig_map <- c(
  "差异蛋白火山图" = paste0("../图片文件/", delivery_stem(skill_en, "volcano", "DiseaseVsHealthy"), ".png"),
  "Top15 差异蛋白" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "Top15DEP"), ".png"),
  "PCA" = paste0("../图片文件/", delivery_stem(skill_en, "PCA", "DiseaseVsHealthy"), ".png")
)
interp <- "TOY 蛋白强度：火山 + Top 柱状 + PCA。data_provenance=TOY。"
status <- "PASS"

data_html <- paste0(
  "<p><b>data_provenance: TOY</b>：可复现模拟数据，<b>不可外推</b>。</p>",
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
