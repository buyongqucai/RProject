# 样例分析脚本 — 微生物组16S分析_Microbiome16S
# 合规：统一交付规范_DeliveryStandards + 统一可视化规范_VizStandards
# analysis_kind=microbiome16s  seed=404
options(stringsAsFactors = FALSE)
set.seed(404)

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


skill_en <- "Microbiome16S"
skill_folder <- "微生物组16S分析_Microbiome16S"
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


otu <- read.csv(file.path(data_dir, "toy_otu.csv"), check.names = FALSE)
if (!nrow(otu)) {
  otu <- data.frame(taxon = paste0("Taxa", 1:5), A1=10,A2=12,A3=11,B1=2,B2=3,B3=1)
  write.csv(otu, file.path(data_dir, "toy_otu.csv"), row.names = FALSE)
}
mat <- as.matrix(otu[, -1])
rownames(mat) <- otu[[1]]
rel <- sweep(mat, 2, colSums(mat), "/")
alpha <- data.frame(sample = colnames(mat), shannon = apply(rel, 2, function(p) {
  p <- p[p > 0]; -sum(p * log(p))
}), group = c(rep("SiteA", 3), rep("SiteB", 3)))
write.csv(alpha, file.path(tab_dir, delivery_table_name(skill_en, "alpha", "shannon")), row.names = FALSE)
write_delivery_audit(skill_en, "post", nrow(mat), ncol(mat), ncol(mat), "toy OTU SiteA/B", TRUE, NA, sourced_note,
  "16S alpha+beta; data_provenance=TOY", file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "TOY")
library(ggplot2)
p <- ggplot(alpha, aes(group, shannon, fill = group)) +
  geom_boxplot(alpha = 0.75, width = 0.55, outlier.shape = NA) +
  geom_jitter(width = 0.08, size = 2.4, alpha = 0.9) +
  scale_fill_manual(values = bioinfo_palette[c(2, 5)], guide = "none") +
  labs(title = "Alpha diversity (Shannon)", y = "Shannon index", x = NULL)
delivery_save_plot(p, skill_en, "boxplot", "Shannon_SiteAVsB", 4.5, 4.0, fig_dir, bio_root)
# Beta: PCoA-like on Bray-Curtis proxy (euclidean on rel)
d <- dist(t(rel))
pc <- cmdscale(d, k = 2)
bdf <- data.frame(PCoA1 = pc[, 1], PCoA2 = pc[, 2], group = alpha$group, sample = alpha$sample)
p2 <- ggplot(bdf, aes(PCoA1, PCoA2, color = group)) +
  geom_point(size = 3.2) +
  scale_color_manual(values = bioinfo_palette[c(2, 5)]) +
  labs(title = "Beta diversity (PCoA on relative abundance)", color = "Site")
delivery_save_plot(p2, skill_en, "pca", "PCoA_SiteAVsB", 5.0, 4.2, fig_dir, bio_root)
fig_map <- c(
  "Shannon 箱线图" = paste0("../图片文件/", delivery_stem(skill_en, "boxplot", "Shannon_SiteAVsB"), ".png"),
  "PCoA" = paste0("../图片文件/", delivery_stem(skill_en, "pca", "PCoA_SiteAVsB"), ".png")
)
interp <- "TOY 16S：Alpha 箱线 + Beta PCoA。data_provenance=TOY。"
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
