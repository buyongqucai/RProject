# 样例分析脚本 — 蛋白质互作网络_PPI-Network
# 合规：统一交付规范_DeliveryStandards + 统一可视化规范_VizStandards
# analysis_kind=ppi  seed=14771
options(stringsAsFactors = FALSE)
set.seed(14771)

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


skill_en <- "PPI-Network"
skill_folder <- "蛋白质互作网络_PPI-Network"
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


nodes <- data.frame(
  protein = c("TP53", "EGFR", "MYC", "AKT1", "MAPK1", "SRC", "JUN", "STAT3"),
  degree = c(22, 18, 15, 12, 11, 9, 8, 7),
  stringsAsFactors = FALSE
)
edges <- data.frame(
  from = c("TP53", "TP53", "EGFR", "EGFR", "MYC", "AKT1", "MAPK1", "SRC", "JUN", "STAT3", "AKT1", "MAPK1"),
  to   = c("EGFR", "MYC", "SRC", "STAT3", "JUN", "MAPK1", "JUN", "STAT3", "TP53", "EGFR", "SRC", "EGFR"),
  score = runif(12, 0.4, 0.98),
  stringsAsFactors = FALSE
)
write.csv(nodes, file.path(tab_dir, delivery_table_name(skill_en, "degree", "hubs")), row.names = FALSE)
write.csv(edges, file.path(tab_dir, "互作边_ToyEdges.csv"), row.names = FALSE)
write_delivery_audit(skill_en, "post", 8, 2, NA, "toy PPI", TRUE, NA, sourced_note, "hub+network; data_provenance=TOY",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")), data_provenance = "TOY")
library(ggplot2)
p <- ggplot(nodes, aes(reorder(protein, degree), degree, fill = degree)) +
  geom_col(width = 0.75, show.legend = FALSE) +
  scale_fill_gradient(low = "#56B4E9", high = "#D55E00") +
  coord_flip() +
  labs(title = "PPI hub degree (toy)", x = NULL, y = "Degree")
delivery_save_plot(p, skill_en, "bar", "HubDegree", 5.0, 4.2, fig_dir, bio_root)
if (requireNamespace("igraph", quietly = TRUE)) {
  g <- igraph::graph_from_data_frame(edges, directed = FALSE, vertices = nodes)
  lay <- igraph::layout_with_fr(g)
  vdf <- data.frame(name = igraph::V(g)$name, x = lay[, 1], y = lay[, 2],
                    degree = nodes$degree[match(igraph::V(g)$name, nodes$protein)])
  ed <- igraph::as_data_frame(g, "edges")
  ed <- merge(ed, vdf, by.x = "from", by.y = "name")
  ed <- merge(ed, vdf, by.x = "to", by.y = "name", suffixes = c("", "end"))
  p2 <- ggplot() +
    geom_segment(data = ed, aes(x = x, y = y, xend = xend, yend = yend),
                 color = "grey70", linewidth = 0.5) +
    geom_point(data = vdf, aes(x, y, size = degree), color = bioinfo_palette[1], alpha = 0.9) +
    geom_text(data = vdf, aes(x, y, label = name), size = 3, vjust = -0.9) +
    scale_size_continuous(range = c(3, 9), name = "Degree") +
    labs(title = "Toy PPI network layout") +
    theme_void(base_size = 11) +
    theme(legend.position = "bottom", plot.title = element_text(hjust = 0.5))
} else {
  p2 <- ggplot(nodes, aes(degree, protein)) + geom_point(color = bioinfo_palette[1], size = 3) +
    labs(title = "PPI degrees (igraph missing)")
}
delivery_save_plot(p2, skill_en, "network", "ToyLayout", 5.5, 5.0, fig_dir, bio_root)
fig_map <- c(
  "PPI 枢纽度" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "HubDegree"), ".png"),
  "PPI 网络布局" = paste0("../图片文件/", delivery_stem(skill_en, "network", "ToyLayout"), ".png")
)
interp <- "TOY PPI：枢纽度 + 网络布局。data_provenance=TOY。"
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
