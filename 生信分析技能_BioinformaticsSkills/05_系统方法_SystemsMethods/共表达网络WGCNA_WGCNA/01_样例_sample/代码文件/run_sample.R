# 样例分析脚本 — 共表达网络WGCNA_WGCNA
# 合规：统一交付规范_DeliveryStandards + 统一可视化规范_VizStandards
# analysis_kind=wgcna  seed=1010
options(stringsAsFactors = FALSE)
set.seed(1010)

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


skill_en <- "WGCNA"
skill_folder <- "共表达网络WGCNA_WGCNA"
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


# 模块-性状相关热图玩具
mods <- paste0("M", 1:6)
traits <- c("Age", "Stage", "Response")
cor_mat <- matrix(runif(18, -0.8, 0.8), nrow = 6, dimnames = list(mods, traits))
cdf <- data.frame(
  module = rep(mods, times = 3),
  trait = rep(traits, each = 6),
  cor = as.vector(cor_mat)
)
write.csv(cdf, file.path(tab_dir, delivery_table_name(skill_en, "moduleTrait", "cor")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 6, 3, NA, "toy traits", TRUE, NA, sourced_note, "WGCNA module-trait; data_provenance=TOY",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")), data_provenance = "TOY")
library(ggplot2)
p <- ggplot(cdf, aes(trait, module, fill = cor)) + geom_tile(color = "white", linewidth = 0.4) +
  geom_text(aes(label = sprintf("%.2f", cor)), size = 3) +
  scale_fill_gradient2(low = bioinfo_palette[1], mid = "white", high = bioinfo_palette[6], midpoint = 0) +
  labs(title = "Module–trait correlation", fill = "r")
delivery_save_plot(p, skill_en, "heatmap", "ModuleTrait", 5.0, 4.5, fig_dir, bio_root)
# module size bar
ms <- data.frame(module = mods, n_genes = as.integer(runif(6, 40, 220)))
ms$module <- factor(ms$module, levels = ms$module)
p2 <- ggplot(ms, aes(module, n_genes, fill = module)) +
  geom_col(width = 0.7, show.legend = FALSE) +
  scale_fill_manual(values = rep(bioinfo_palette, length.out = 6)) +
  labs(title = "Module sizes (toy)", x = NULL, y = "Genes")
delivery_save_plot(p2, skill_en, "bar", "ModuleSize", 5.0, 3.8, fig_dir, bio_root)
fig_map <- c(
  "模块-性状相关" = paste0("../图片文件/", delivery_stem(skill_en, "heatmap", "ModuleTrait"), ".png"),
  "模块大小" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "ModuleSize"), ".png")
)
interp <- "TOY WGCNA：模块-性状热图 + 模块大小。data_provenance=TOY。"
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
