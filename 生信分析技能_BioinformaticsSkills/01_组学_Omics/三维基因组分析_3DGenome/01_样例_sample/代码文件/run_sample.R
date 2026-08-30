# 样例分析脚本 — 三维基因组分析_3DGenome
# 合规：统一可视化规范_VizStandards + 统一交付规范_DeliveryStandards
# analysis_kind=blocked_3d  seed=16153
#
# 1) source 统一可视化规范 出版级出图
# 2) source 统一交付规范 出图命名/审计/报告
# 3) source 本技能 脚本_scripts
options(stringsAsFactors = FALSE)
set.seed(16153)

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
viz_script <- file.path(
  bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
  "脚本_scripts", "出版级出图_PublicationPlot.R"
)
source(viz_script, encoding = "UTF-8")

# 2) DeliveryStandards
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

# 3) 本技能脚本
skill_en <- "3DGenome"
skill_folder <- "三维基因组分析_3DGenome"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- "未找到可 source 的技能脚本"
if (length(sk_files)) {
  for (sf in sk_files) {
    try(source(sf, encoding = "UTF-8"), silent = TRUE)
  }
  sourced_note <- paste0(
    "已 source VizStandards + DeliveryStandards + 本技能: ",
    paste(basename(sk_files), collapse = ", ")
  )
} else {
  sourced_note <- "已 source VizStandards + DeliveryStandards；本技能无额外 .R 骨架"
}
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
library(ggplot2)

# ---- BLOCKED：三维基因组契约 + 接触矩阵示意（禁止无关 DEG）----
blocked_reason <- "需 Hi-C 原始或 .hic/.cool 全库与 juicer/cooler 栈"
stub <- data.frame(
  item = c("juicer_cooler_CLI", "hic_or_cool_input", "contact_matrix_pipeline", "delivery_contract"),
  ok = c(0, 0, 0, 1),
  note = c("missing", "missing", "blocked", "DeliveryStandards OK"),
  stringsAsFactors = FALSE
)
write.csv(stub, file.path(tab_dir, delivery_table_name(skill_en, "contract", "blockedStub")), row.names = FALSE)

# 玩具接触矩阵（示意，不可外推）
nbin <- 12
cm <- outer(seq_len(nbin), seq_len(nbin), function(i, j) {
  exp(-abs(i - j) / 3) + rnorm(1, 0, 0.03)
})
cm <- pmax(cm, 0)
colnames(cm) <- paste0("bin", seq_len(nbin))
rownames(cm) <- paste0("bin", seq_len(nbin))
bin_levels <- paste0("bin", seq_len(nbin))
contact_long <- data.frame(
  bin_i = factor(rep(rownames(cm), times = nbin), levels = bin_levels),
  bin_j = factor(rep(colnames(cm), each = nbin), levels = bin_levels),
  contact = as.vector(cm),
  stringsAsFactors = FALSE
)
write.csv(contact_long, file.path(tab_dir, delivery_table_name(skill_en, "contact", "ToyMatrix")), row.names = FALSE)

write_delivery_audit(
  skill_en, "post", nrow(stub), ncol(stub), 0L, "n/a BLOCKED Hi-C",
  FALSE, NA_character_, sourced_note,
  paste("BLOCKED:", blocked_reason),
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "BLOCKED"
)

p <- ggplot(contact_long, aes(bin_i, bin_j, fill = contact)) +
  geom_tile() +
  scale_fill_gradient(low = bioinfo_continuous[2], high = bioinfo_continuous[1], name = "Contact frequency") +
  coord_fixed() +
  labs(
    title = "Contact matrix (schematic · BLOCKED)",
    subtitle = "Toy schematic · not real Hi-C",
    x = "Bin i", y = "Bin j"
  ) +
  theme(
    axis.text.x = element_text(angle = 90, vjust = 0.5, hjust = 1, size = 7),
    axis.text.y = element_text(size = 7),
    plot.title = element_text(size = 10),
    plot.subtitle = element_text(size = 8)
  )

delivery_save_plot(p, skill_en, "heatmap", "ContactMatrixStub", width = 4.2, height = 3.8, out_dir = fig_dir, start = bio_root)
fig_map <- c(
  "接触矩阵示意（BLOCKED）" = paste0("../图片文件/", delivery_stem(skill_en, "heatmap", "ContactMatrixStub"), ".png")
)
interp <- paste0(
  "客观 BLOCKED：", blocked_reason,
  "。已产出契约阻塞桩、审计后检与主题相关接触矩阵示意；不得标 PASS。禁止无关 DEG 玩具表。"
)
status <- "BLOCKED"

data_html <- paste0(
  "<p><b>BLOCKED</b>：本样例为契约桩（无真实 Hi-C 数据）；接触矩阵仅为示意，<b>不可外推</b>为真实三维基因组结论。</p>",
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
  blocked_reason = blocked_reason
)
writeLines(status, file.path(rep_dir, "STATUS.txt"))

# 清理旧违规/无关文件名
old_junk <- c(
  "sample_pca.png", "sample_volcano.png", "样例报告.html",
  "sample_summary.csv", "toy_deg_results.csv",
  "3DGenome_audit_post.csv", "3DGenome_contract_blockedStub.csv",
  "3DGenome_bar_BlockedContract.png", "3DGenome_bar_BlockedContract.svg",
  "3DGenome_样例报告_v1.html"
)
for (old in old_junk) {
  for (d in c(fig_dir, tab_dir, rep_dir)) {
    f <- file.path(d, old)
    if (file.exists(f)) file.remove(f)
  }
}
message("DONE ", status, " — ", skill_folder, " report=", basename(rep_file))
