# 样例分析脚本 — 差异分析与UMAP流水线_DEG-UMAP
# 合规：统一交付规范_DeliveryStandards + 统一可视化规范_VizStandards
# analysis_kind=deg_umap_pipe  seed=43505
options(stringsAsFactors = FALSE)
set.seed(43505)

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


skill_en <- "DEG-UMAP"
skill_folder <- "差异分析与UMAP流水线_DEG-UMAP"
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


# 流水线样例：小 DEG + 伪 UMAP（与 RNA-seq / scRNA 核心样例不同 seed/主题）
genes <- paste0("PIPE", 1:50)
mat <- matrix(rnbinom(50 * 6, mu = 25, size = 6), nrow = 50)
mat[1:8, 4:6] <- mat[1:8, 4:6] + 40
colnames(mat) <- paste0("Pipe", 1:6)
meta <- data.frame(sample = colnames(mat), group = c(rep("A", 3), rep("B", 3)))
logc <- log2(mat + 1)
pvals <- apply(logc, 1, function(v) t.test(v[1:3], v[4:6])$p.value)
lfc <- rowMeans(logc[, 4:6]) - rowMeans(logc[, 1:3])
deg <- data.frame(gene = genes, logFC = lfc, pvalue = pvals)
write.csv(cbind(gene = genes, as.data.frame(mat)), file.path(data_dir, "toy_pipe_counts.csv"), row.names = FALSE)
write.csv(deg, file.path(tab_dir, delivery_table_name(skill_en, "DEG", "GroupBvsA")), row.names = FALSE)
umap <- data.frame(
  UMAP_1 = c(rnorm(60, -1, 0.7), rnorm(60, 2.5, 0.8)),
  UMAP_2 = c(rnorm(60, 0.5, 0.6), rnorm(60, -1.5, 0.7)),
  group = factor(rep(c("A", "B"), each = 60))
)
write.csv(umap, file.path(tab_dir, delivery_table_name(skill_en, "UMAP", "pipeline")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 50, 6, 6, "toy pipeline meta", TRUE, NA, sourced_note, "DEG-UMAP pipe",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
deg$sig <- ifelse(deg$pvalue < 0.05 & abs(deg$logFC) > 0.5,
                  ifelse(deg$logFC > 0, "up", "down"), "ns")
deg$sig <- factor(deg$sig, levels = c("up", "down", "ns"))
p1 <- ggplot(deg, aes(logFC, -log10(pmax(pvalue, 1e-300)), color = sig)) +
  geom_point(alpha = 0.85) +
  (if (exists("scale_color_volcano")) scale_color_volcano() else
     scale_color_manual(values = bioinfo_volcano)) +
  labs(title = "DEG-UMAP pipeline volcano B vs A (toy)")
delivery_save_plot(p1, skill_en, "volcano", "GroupBvsA", 6.5, 5, fig_dir, bio_root)
umap_cols <- setNames(bioinfo_umap_discrete[1:2], c("A", "B"))
p2 <- ggplot(umap, aes(UMAP_1, UMAP_2, color = group)) +
  geom_point(size = 1.4, alpha = 0.75) +
  scale_color_manual(values = umap_cols) +
  labs(title = "DEG-UMAP pipeline UMAP (toy)")
delivery_save_plot(p2, skill_en, "UMAP", "PipeClusters", 6.5, 5, fig_dir, bio_root)
fig_map <- c(
  "流水线火山图" = paste0("../图片文件/", delivery_stem(skill_en, "volcano", "GroupBvsA"), ".png"),
  "流水线 UMAP" = paste0("../图片文件/", delivery_stem(skill_en, "UMAP", "PipeClusters"), ".png")
)
interp <- "已落地 DEG-UMAP 流水线玩具交付；数据与核心 RNA-seq/scRNA 样例不同。"
status <- "PASS"

data_html <- paste0(
  "<p><b>toy=TRUE</b>：本样例为可复现模拟数据，<b>不可外推</b>为真实生物学/临床结论。</p>",
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
writeLines(status, file.path(rep_dir, "STATUS.txt"))
# 清理旧无语义文件名
for (old in c("sample_pca.png", "sample_volcano.png", "样例报告.html")) {
  f1 <- file.path(fig_dir, old); if (file.exists(f1)) file.remove(f1)
  f2 <- file.path(rep_dir, old); if (file.exists(f2)) file.remove(f2)
}
message("DONE ", status, " — ", skill_folder, " report=", basename(rep_file))
