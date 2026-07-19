# 样例分析脚本 — 系统发育分析_Phylogenetics
# 合规：统一交付规范_DeliveryStandards + 统一可视化规范_VizStandards
# analysis_kind=phylo  seed=15126
options(stringsAsFactors = FALSE)
set.seed(15126)

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


skill_en <- "Phylogenetics"
skill_folder <- "系统发育分析_Phylogenetics"
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


dist <- data.frame(
  pair = paste0("sp", 1:10, "-ref"),
  distance = sort(runif(10, 0.02, 0.45), decreasing = TRUE)
)
write.csv(dist, file.path(tab_dir, delivery_table_name(skill_en, "dist", "species")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 10, 2, NA, "toy phylogeny", TRUE, NA, sourced_note, "distances + dendrogram",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(dist, aes(reorder(pair, distance), distance)) + geom_col(fill = bioinfo_palette[6]) +
  coord_flip() + labs(title = "Phylogenetics pairwise distance (toy)", x = NULL, y = "distance")
delivery_save_plot(p, skill_en, "bar", "SpeciesDistance", 6.5, 5, fig_dir, bio_root, order = 1)

# Sample / species dendrogram from existing toy_counts.csv (genes × samples)
counts_path <- file.path(data_dir, "toy_counts.csv")
meta_path <- file.path(data_dir, "toy_meta.csv")
if (file.exists(counts_path)) {
  ct <- utils::read.csv(counts_path, check.names = FALSE, stringsAsFactors = FALSE)
  mat <- as.matrix(ct[, -1, drop = FALSE])
  storage.mode(mat) <- "numeric"
  rownames(mat) <- ct[[1]]
  grp <- NULL
  if (file.exists(meta_path)) {
    meta <- utils::read.csv(meta_path, stringsAsFactors = FALSE)
    grp <- meta[, c(1, 2)]
  }
  p_den <- plot_sample_dendrogram_journal(
    mat, group = grp, title = "Sample dendrogram from toy_counts",
    hclust_method = "average"
  )
  delivery_save_plot(p_den, skill_en, "dendrogram", "SampleTree", 6.5, 4.5, fig_dir, bio_root, order = 2)
  fig_map <- c(
    "种间距离" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "SpeciesDistance", order = 1), ".png"),
    "样本树状图" = paste0("../图片文件/", delivery_stem(skill_en, "dendrogram", "SampleTree", order = 2), ".png")
  )
} else {
  fig_map <- c("种间距离" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "SpeciesDistance", order = 1), ".png"))
}
interp <- "系统发育距离玩具条形图 + 基于 toy_counts 的样本层次聚类树。"
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
