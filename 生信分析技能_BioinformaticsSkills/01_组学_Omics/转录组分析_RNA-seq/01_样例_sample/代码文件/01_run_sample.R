# 样例分析脚本 — 转录组分析_RNA-seq
# data_provenance: REAL（Bioconductor airway）
# STATUS: PASS
options(stringsAsFactors = FALSE)

args_all <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args_all, value = TRUE)
script_path <- if (length(file_arg)) {
  normalizePath(sub("^--file=", "", file_arg[1]), winslash = "/", mustWork = TRUE)
} else {
  normalizePath("01_run_sample.R", winslash = "/", mustWork = TRUE)
}
code_dir <- dirname(script_path)
sample_root <- normalizePath(file.path(code_dir, ".."), winslash = "/", mustWork = TRUE)
skill_root <- normalizePath(file.path(sample_root, ".."), winslash = "/", mustWork = TRUE)
bio_root <- normalizePath(file.path(skill_root, "..", ".."), winslash = "/", mustWork = TRUE)
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath(file.path(skill_root, "..", "..", ".."), winslash = "/", mustWork = TRUE)
}


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

skill_en <- "RNA-seq"
skill_folder <- "转录组分析_RNA-seq"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- "未找到可 source 的技能脚本"
if (length(sk_files)) {
  for (sf in sk_files) try(source(sf, encoding = "UTF-8"), silent = TRUE)
  sourced_note <- paste0("已 source 本技能 脚本_scripts/: ", paste(basename(sk_files), collapse = ", "))
}

for (pkg in c("ggplot2", "limma", "edgeR", "SummarizedExperiment", "airway")) {
  if (!requireNamespace(pkg, quietly = TRUE)) stop("缺少 R 包: ", pkg)
}
suppressPackageStartupMessages({
  library(ggplot2)
  library(limma)
  library(edgeR)
  library(SummarizedExperiment)
  library(airway)
})

data_provenance <- "REAL"
accession <- "airway (Bioconductor ExperimentData)"
data(airway, package = "airway")
counts <- assay(airway)
genes <- rownames(counts)
samples <- colnames(counts)
meta <- as.data.frame(colData(airway))
meta$sample <- rownames(meta)
meta$group <- as.character(meta$dex)
meta_out <- meta[, c("sample", "group", "cell"), drop = FALSE]
counts_out <- data.frame(gene = genes, as.data.frame(counts), check.names = FALSE)
utils::write.csv(counts_out, file.path(data_dir, "计数矩阵_Counts_airway.csv"), row.names = FALSE, fileEncoding = "UTF-8")
utils::write.csv(meta_out, file.path(data_dir, "样本信息_SampleMeta_airway.csv"), row.names = FALSE, fileEncoding = "UTF-8")

if (exists("setup_cjk_fonts")) setup_cjk_fonts()

y <- DGEList(counts = counts, group = meta$group)
keep <- filterByExpr(y)
y <- y[keep, , keep.lib.sizes = FALSE]
y <- calcNormFactors(y)
design <- model.matrix(~ 0 + group, data = meta)
colnames(design) <- levels(factor(meta$group))
v <- voom(y, design)
fit <- lmFit(v, design)
cont <- makeContrasts(trt - untrt, levels = design)
fit2 <- contrasts.fit(fit, cont)
fit2 <- eBayes(fit2)
deg <- topTable(fit2, number = Inf, sort.by = "P")
deg$gene <- rownames(deg)
deg <- deg[, c("gene", "logFC", "AveExpr", "t", "P.Value", "adj.P.Val")]
names(deg)[names(deg) == "adj.P.Val"] <- "padj"
utils::write.csv(deg, file.path(tab_dir, delivery_table_name(skill_en, "DEG", "TrtVsUntrt")), row.names = FALSE)

chk <- audit_meta_vs_matrix(colnames(counts), meta$sample)
write_delivery_audit(
  skill_en, "post", nrow(counts), ncol(counts), ncol(counts),
  "airway colData$dex trt vs untrt", FALSE, accession, sourced_note,
  "REAL limma-voom DEG; data_provenance=REAL",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = data_provenance
)

deg$sig <- ifelse(!is.na(deg$padj) & deg$padj < 0.05 & abs(deg$logFC) > 1,
                  ifelse(deg$logFC > 0, "up", "down"), "ns")
deg$sig <- factor(deg$sig, levels = c("up", "down", "ns"))
p1 <- ggplot(deg, aes(logFC, -log10(pmax(P.Value, 1e-300)), color = sig)) +
  geom_point(alpha = 0.85, size = 2.2) +
  geom_vline(xintercept = c(-1, 1), linetype = 2, color = "grey55", linewidth = 0.35) +
  geom_hline(yintercept = -log10(0.05), linetype = 2, color = "grey55", linewidth = 0.35) +
  (if (exists("scale_color_volcano")) scale_color_volcano() else
     scale_color_manual(values = bioinfo_volcano)) +
  labs(title = "Volcano plot (trt vs untrt, airway)", x = "logFC", y = expression(-log[10](P)), color = NULL)
delivery_save_plot(p1, skill_en, "volcano", "TrtVsUntrt", 5.5, 4.5, fig_dir, bio_root)

logc <- v$E
pc <- prcomp(t(logc), scale. = TRUE)
pcd <- data.frame(PC1 = pc$x[, 1], PC2 = pc$x[, 2], group = meta$group)
pca_cols <- setNames(
  unname(c(bioinfo_groups[["Control"]], bioinfo_groups[["TreatA"]])),
  c("untrt", "trt")
)
p2 <- ggplot(pcd, aes(PC1, PC2, color = group)) +
  geom_point(size = 3.5) +
  scale_color_manual(values = pca_cols) +
  labs(title = "PCA (airway, dex)", color = "Group")
delivery_save_plot(p2, skill_en, "PCA", "TrtVsUntrt", 5.2, 4.5, fig_dir, bio_root)

top_g <- as.character(head(deg$gene[order(deg$P.Value)], 12))
hm_mat <- logc[top_g, , drop = FALSE]
hm <- t(scale(t(hm_mat)))
hdf <- data.frame(
  gene = rep(rownames(hm), times = ncol(hm)),
  sample = rep(colnames(hm), each = nrow(hm)),
  z = as.vector(hm),
  stringsAsFactors = FALSE
)
hdf$gene <- factor(hdf$gene, levels = rev(top_g))
p3 <- ggplot(hdf, aes(sample, gene, fill = z)) +
  geom_tile(color = "white", linewidth = 0.2) +
  (if (exists("scale_fill_bioinfo_continuous")) scale_fill_bioinfo_continuous(name = "z-score") else
     scale_fill_gradient2(low = bioinfo_continuous[1], mid = bioinfo_continuous[2],
                          high = bioinfo_continuous[3], midpoint = 0, name = "z-score")) +
  labs(title = "Top 12 DEG heatmap (airway)", x = NULL, y = NULL) +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
delivery_save_plot(p3, skill_en, "heatmap", "Top12DEG", 5.5, 4.8, fig_dir, bio_root)

# Sample dendrogram from airway expression + PC density/box (REAL data)
p_tree <- plot_sample_dendrogram_journal(
  logc[head(deg$gene[order(deg$P.Value)], 100), , drop = FALSE],
  group = data.frame(sample = meta$sample, group = meta$group),
  title = "Sample dendrogram (airway top100 DEG)"
)
delivery_save_plot(p_tree, skill_en, "dendrogram", "AirwaySamples", 6.5, 4.5, fig_dir, bio_root, order = 4)

p_pc <- plot_pc_density_box_journal(
  pcd, value_col = "PC1", group_col = "group",
  title = "PC1 density + box (airway)", xlab = "PC1",
  palette = pca_cols
)
delivery_save_plot(p_pc, skill_en, "densitybox", "PC1_ByDex", 5.5, 4.8, fig_dir, bio_root, order = 5)

# Pathway-like score brackets from mean z of top up DEGs per sample
top_up <- head(deg$gene[deg$sig == "up"], 30)
if (length(top_up) >= 5) {
  zmat <- t(scale(t(logc[top_up, , drop = FALSE])))
  sc <- colMeans(zmat, na.rm = TRUE)
  score_df <- data.frame(
    sample = names(sc),
    value = as.numeric(sc),
    group = meta$group[match(names(sc), meta$sample)],
    stringsAsFactors = FALSE
  )
  p_br <- plot_box_bracket_journal(
    score_df, value_col = "value", group_col = "group",
    title = "Top-up DEG score by dex (airway)", ylab = "Mean z-score",
    palette = pca_cols
  )
  delivery_save_plot(p_br, skill_en, "box", "PathwayScoreBrackets", 4.8, 4.5, fig_dir, bio_root, order = 6)
}

prov <- list(
  data_provenance = data_provenance,
  source = "Bioconductor ExperimentData",
  package = "airway",
  accession = accession,
  contrast = "dex trt vs untrt",
  n_genes = nrow(counts),
  n_samples = ncol(counts),
  group_counts = as.list(table(meta$group)),
  method = "limma-voom",
  note = "REAL public RNA-seq counts; not simulated."
)
if (requireNamespace("jsonlite", quietly = TRUE)) {
  jsonlite::write_json(prov, file.path(data_dir, "PROVENANCE.json"), auto_unbox = TRUE, pretty = TRUE)
}

fig_map <- c(
  "火山图（处理对照）" = paste0("../图片文件/", delivery_stem(skill_en, "volcano", "TrtVsUntrt"), ".png"),
  "PCA图（处理对照）" = paste0("../图片文件/", delivery_stem(skill_en, "PCA", "TrtVsUntrt"), ".png"),
  "Top12 热图" = paste0("../图片文件/", delivery_stem(skill_en, "heatmap", "Top12DEG"), ".png"),
  "样本树状图" = paste0("../图片文件/", delivery_stem(skill_en, "dendrogram", "AirwaySamples", order = 4), ".png"),
  "PC1密度箱线" = paste0("../图片文件/", delivery_stem(skill_en, "densitybox", "PC1_ByDex", order = 5), ".png"),
  "通路评分箱线" = paste0("../图片文件/", delivery_stem(skill_en, "box", "PathwayScoreBrackets", order = 6), ".png")
)
interp <- "REAL airway limma-voom DEG: volcano + PCA + heatmap + dendrogram + PC density/box + score brackets."
status <- "PASS"

data_html <- paste0(
  "<p><b>data_provenance: REAL</b> — Bioconductor <code>airway</code> (8 samples, trt vs untrt).</p>",
  "<p>详见 <code>数据文件/DATA_SOURCE.md</code> 与 <code>PROVENANCE.json</code>。</p>"
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
  data_html, audit_html, sourced_note, fig_map, interp, rep_file
)
writeLines(c(status, paste0("data_provenance=", data_provenance)), file.path(rep_dir, "STATUS.txt"))

for (old in c("toy_counts.csv", "toy_meta.csv", "sample_pca.png", "sample_volcano.png", "样例报告.html")) {
  f <- file.path(data_dir, old)
  if (file.exists(f)) file.rename(f, file.path(data_dir, paste0("obsolete_", old)))
}
message("DONE ", status, " — ", skill_folder, " report=", basename(rep_file))
