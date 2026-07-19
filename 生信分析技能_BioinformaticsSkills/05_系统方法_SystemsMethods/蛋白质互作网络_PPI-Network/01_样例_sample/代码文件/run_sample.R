# 样例 — PPI-Network REAL GSE207177 Hub ligand-target (书清嵌入)
# analysis_kind=ppi  seed=14771
# data_provenance=REAL — skill-local real_GSE207177_Hub_LR_network.csv
options(stringsAsFactors = FALSE)
set.seed(14771)

sample_root <- normalizePath("..", winslash = "/", mustWork = TRUE)
skill_root <- normalizePath("../..", winslash = "/", mustWork = TRUE)
bio_root <- normalizePath("../../..", winslash = "/", mustWork = TRUE)
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath("../../../..", winslash = "/", mustWork = TRUE)
}
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath(file.path(skill_root, "..", ".."), winslash = "/", mustWork = TRUE)
}

viz_script <- file.path(
  bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
  "脚本_scripts", "出版级出图_PublicationPlot.R"
)
if (file.exists(viz_script)) source(viz_script, encoding = "UTF-8")

delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
paths <- delivery_sample_paths(sample_root)
data_dir <- paths$raw_dir; fig_dir <- paths$fig_dir; tab_dir <- paths$tab_dir; rep_dir <- paths$rep_dir
for (d in c(data_dir, fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)
source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")

skill_en <- "PPI-Network"
skill_folder <- "蛋白质互作网络_PPI-Network"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- if (length(sk_files)) {
  for (sf in sk_files) try(source(sf, encoding = "UTF-8"), silent = TRUE)
  paste0("sourced: ", paste(basename(sk_files), collapse = ", "))
} else "no skill scripts"
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
library(ggplot2)

accession <- "GSE207177"
edge_path <- file.path(data_dir, "real_GSE207177_Hub_LR_network.csv")
stopifnot(file.exists(edge_path))
edges <- read.csv(edge_path, check.names = FALSE, stringsAsFactors = FALSE)
# ligand -> target edges
edges <- edges[!is.na(edges$ligand) & !is.na(edges$target), , drop = FALSE]
edges <- unique(edges[, c("ligand", "target"), drop = FALSE])
names(edges) <- c("from", "to")
# degree of hubs (ligand side + target side)
all_nodes <- unique(c(edges$from, edges$to))
deg <- table(c(edges$from, edges$to))
nodes <- data.frame(
  protein = names(deg),
  degree = as.integer(deg),
  stringsAsFactors = FALSE
)
nodes <- nodes[order(-nodes$degree), , drop = FALSE]
top_n <- nodes[seq_len(min(15L, nrow(nodes))), , drop = FALSE]
write.csv(nodes, file.path(tab_dir, delivery_table_name(skill_en, "degree", "hubs")), row.names = FALSE)
write.csv(edges, file.path(tab_dir, delivery_table_name(skill_en, "edges", "HubLR")), row.names = FALSE)

write_delivery_audit(
  skill_en, "post", nrow(nodes), 2, nrow(edges),
  paste0(accession, " hub ligand-target network"),
  FALSE, accession, sourced_note,
  "hub degree + network; data_provenance=REAL",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "REAL"
)

p <- ggplot(top_n, aes(reorder(protein, degree), degree, fill = degree)) +
  geom_col(width = 0.75, show.legend = FALSE) +
  scale_fill_gradient(low = "#56B4E9", high = "#D55E00") +
  coord_flip() +
  labs(title = paste0("Hub degree — ", accession), x = NULL, y = "Degree") +
  theme_journal()
delivery_save_plot(p, skill_en, "bar", "HubDegree", 5.2, 4.8, fig_dir, bio_root, order = 1)

# Keep top edges incident to top hubs for readable layout
keep <- unique(top_n$protein)
sub_e <- edges[edges$from %in% keep | edges$to %in% keep, , drop = FALSE]
sub_e <- head(sub_e, 80L)
if (requireNamespace("igraph", quietly = TRUE) && nrow(sub_e) > 0) {
  g <- igraph::graph_from_data_frame(sub_e, directed = TRUE)
  lay <- igraph::layout_with_fr(g)
  vdf <- data.frame(
    name = igraph::V(g)$name, x = lay[, 1], y = lay[, 2],
    degree = as.integer(deg[igraph::V(g)$name])
  )
  ed <- igraph::as_data_frame(g, "edges")
  ed <- merge(ed, vdf, by.x = "from", by.y = "name")
  ed <- merge(ed, vdf, by.x = "to", by.y = "name", suffixes = c("", "end"))
  p2 <- ggplot() +
    geom_segment(data = ed, aes(x = x, y = y, xend = xend, yend = yend),
                 color = "grey70", linewidth = 0.4, alpha = 0.8) +
    geom_point(data = vdf, aes(x, y, size = degree), color = bioinfo_palette[1], alpha = 0.9) +
    geom_text(data = vdf, aes(x, y, label = name), size = 2.6, vjust = -0.9) +
    scale_size_continuous(range = c(2.5, 8), name = "Degree") +
    labs(title = paste0("Hub LR network — ", accession)) +
    theme_void(base_size = 11) +
    theme(legend.position = "bottom", plot.title = element_text(hjust = 0.5, face = "bold"))
} else {
  p2 <- ggplot(top_n, aes(degree, reorder(protein, degree))) +
    geom_point(color = bioinfo_palette[1], size = 3) +
    labs(title = paste0("Hub degrees — ", accession), x = "Degree", y = NULL) +
    theme_journal()
}
delivery_save_plot(p2, skill_en, "network", "HubLayout", 5.8, 5.2, fig_dir, bio_root, order = 2)

fig_map <- c(
  "枢纽度" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "HubDegree", order = 1), ".png"),
  "网络布局" = paste0("../图片文件/", delivery_stem(skill_en, "network", "HubLayout", order = 2), ".png")
)
interp <- paste0("REAL ", accession, " Hub 配体–靶标网络（书清嵌入）。data_provenance=REAL。")
status <- "PASS"
data_html <- paste0(
  "<p><b>data_provenance: REAL</b> — <code>", accession, "</code> ",
  "<code>real_GSE207177_Hub_LR_network.csv</code>。</p>"
)
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- if (file.exists(audit_path)) {
  paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")
} else "<p>none</p>"
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(skill_en, skill_folder, status, data_html, audit_html, sourced_note, fig_map, interp, rep_file, blocked_reason = "")
writeLines(c(status, "data_provenance=REAL", paste0("accession=", accession)), file.path(rep_dir, "STATUS.txt"))
message("DONE ", status, " — ", skill_folder, " REAL ", accession)
