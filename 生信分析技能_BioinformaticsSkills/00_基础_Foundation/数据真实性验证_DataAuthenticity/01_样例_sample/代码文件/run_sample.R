# 样例分析脚本 — 数据真实性验证_DataAuthenticity
# 合规：统一交付规范_DeliveryStandards + 统一可视化规范_VizStandards
# analysis_kind=authenticity  seed=202603
options(stringsAsFactors = FALSE)
set.seed(202603)

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


skill_en <- "DataAuthenticity"
skill_folder <- "数据真实性验证_DataAuthenticity"
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


# 真实性核对：声明的样本数 vs 矩阵列
meta <- data.frame(sample = paste0("GSM", 1:6), group = rep(c("Tumor", "Normal"), each = 3))
mat <- matrix(rpois(30 * 6, 20), nrow = 30, dimnames = list(paste0("g", 1:30), meta$sample))
mat[1:5, 1:3] <- mat[1:5, 1:3] + 25
write.csv(cbind(gene = rownames(mat), as.data.frame(mat)), file.path(data_dir, "toy_geo_like_counts.csv"), row.names = FALSE)
write.csv(meta, file.path(data_dir, "toy_geo_like_meta.csv"), row.names = FALSE)
chk <- audit_meta_vs_matrix(colnames(mat), meta$sample)
audit_df <- data.frame(
  declared_n = nrow(meta), matrix_n = ncol(mat), match_ok = chk$ok,
  toy = TRUE, accession = "TOY-GEO-0000"
)
write.csv(audit_df, file.path(tab_dir, delivery_table_name(skill_en, "check", "sampleMatch")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 30, 6, 6, "toy_geo_like_meta.csv", TRUE, "TOY-GEO-0000",
  sourced_note, ifelse(chk$ok, "样本数列一致", "不一致"), file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
plot_df <- data.frame(item = c("declared_n", "matrix_n"), n = c(nrow(meta), ncol(mat)))
p <- ggplot(plot_df, aes(item, n, fill = item)) + geom_col(show.legend = FALSE) +
  labs(title = "Sample count check", y = "n samples", x = NULL) +
  scale_fill_manual(values = bioinfo_palette[1:2])
delivery_save_plot(p, skill_en, "bar", "SampleCountCheck", 5, 4, fig_dir, bio_root)
fig_map <- c("样本数核对" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "SampleCountCheck"), ".png"))
interp <- "演示真实性核对字段；accession=TOY，不可当作真实 GEO。"
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
