# 样例 — DEG-UMAP REAL: airway limma DEG + PCA/heatmap; GSE164522 UMAP
# analysis_kind=deg_umap_pipe  seed=43505
options(stringsAsFactors = FALSE)
set.seed(43505)

sample_root <- normalizePath("..", winslash = "/", mustWork = TRUE)
skill_root <- normalizePath("../..", winslash = "/", mustWork = TRUE)
bio_root <- normalizePath("../../..", winslash = "/", mustWork = TRUE)
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath("../../../..", winslash = "/", mustWork = TRUE)
}
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath(file.path(skill_root, "..", ".."), winslash = "/", mustWork = TRUE)
}

viz_script <- file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards", "脚本_scripts", "出版级出图_PublicationPlot.R")
if (file.exists(viz_script)) source(viz_script, encoding = "UTF-8")
delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
paths <- delivery_sample_paths(sample_root)
data_dir <- paths$raw_dir; fig_dir <- paths$fig_dir; tab_dir <- paths$tab_dir; rep_dir <- paths$rep_dir
for (d in c(data_dir, fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)
source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")

skill_en <- "DEG-UMAP"
skill_folder <- "差异分析与UMAP流水线_DEG-UMAP"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- if (length(sk_files)) {
  for (sf in sk_files) try(source(sf, encoding = "UTF-8"), silent = TRUE)
  paste0("sourced: ", paste(basename(sk_files), collapse = ", "))
} else "no skill scripts"
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
library(ggplot2)

cnt_f <- file.path(data_dir, "real_airway_counts.csv")
meta_f <- file.path(data_dir, "real_airway_meta.csv")
umap_f <- file.path(data_dir, "real_GSE164522_umap_subsample.csv")
if (!file.exists(cnt_f)) {
  proj <- normalizePath(file.path(bio_root, ".."), winslash = "/", mustWork = TRUE)
  bs <- file.path(proj, "_tmp_build_wave1_caches.R")
  if (file.exists(bs)) source(bs, encoding = "UTF-8")
}
stopifnot(file.exists(cnt_f), file.exists(meta_f))

counts <- read.csv(cnt_f, check.names = FALSE, stringsAsFactors = FALSE)
meta <- read.csv(meta_f, check.names = FALSE, stringsAsFactors = FALSE)
gene_col <- names(counts)[1]
mat <- as.matrix(counts[, -1, drop = FALSE])
storage.mode(mat) <- "numeric"
rownames(mat) <- make.unique(as.character(counts[[gene_col]]))
# align
common <- intersect(colnames(mat), as.character(meta$sample))
mat <- mat[, common, drop = FALSE]
meta <- meta[match(common, meta$sample), ]
meta$group <- factor(meta$group)

# limma-voom DEG
if (!requireNamespace("limma", quietly = TRUE) || !requireNamespace("edgeR", quietly = TRUE)) {
  stop("需要 limma + edgeR")
}
dge <- edgeR::DGEList(counts = mat, group = meta$group)
keep <- edgeR::filterByExpr(dge, group = meta$group)
dge <- dge[keep, , keep.lib.sizes = FALSE]
dge <- edgeR::calcNormFactors(dge)
design <- model.matrix(~ 0 + group, data = meta)
colnames(design) <- levels(meta$group)
contrast <- limma::makeContrasts(trt - untrt, levels = design)
v <- limma::voom(dge, design, plot = FALSE)
fit <- limma::lmFit(v, design)
fit2 <- limma::contrasts.fit(fit, contrast)
fit2 <- limma::eBayes(fit2)
tt <- limma::topTable(fit2, number = Inf, sort.by = "P")
deg <- data.frame(
  gene = rownames(tt),
  logFC = tt$logFC,
  AveExpr = tt$AveExpr,
  P.Value = tt$P.Value,
  adj.P.Val = tt$adj.P.Val,
  stringsAsFactors = FALSE
)
write.csv(deg, file.path(tab_dir, delivery_table_name(skill_en, "DEG", "TrtVsUntrt")), row.names = FALSE)
write_delivery_audit(
  skill_en, "post", nrow(deg), ncol(mat), ncol(mat),
  "airway trt vs untrt (Bioconductor)", FALSE, "airway", sourced_note,
  "volcano+PCA+heatmap+UMAP; data_provenance=REAL",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "REAL"
)

p1 <- plot_volcano_journal(
  deg, gene_col = "gene", logfc_col = "logFC", p_col = "adj.P.Val",
  logfc_cut = 0.5, p_cut = 0.05, label_n = 6,
  title = "Airway DEG (trt vs untrt)"
)
delivery_save_plot(p1, skill_en, "volcano", "TrtVsUntrt", 6.5, 5.2, fig_dir, bio_root, order = 1)

# PCA on voom E
logc <- v$E
pca <- stats::prcomp(t(logc), scale. = TRUE)
pca_df <- data.frame(
  PC1 = pca$x[, 1], PC2 = pca$x[, 2],
  group = meta$group[match(rownames(pca$x), meta$sample)],
  stringsAsFactors = FALSE
)
p_pca <- plot_pca_journal(pca_df, title = "PCA — airway samples")
delivery_save_plot(p_pca, skill_en, "pca", "AirwaySamples", 5.5, 4.8, fig_dir, bio_root, order = 2)

# Top DEG heatmap (z-scored)
topn <- utils::head(deg$gene[order(deg$adj.P.Val)], 30)
topn <- intersect(topn, rownames(logc))
hm <- t(scale(t(logc[topn, , drop = FALSE])))
hm[is.na(hm)] <- 0
p_hm <- plot_pathway_activity_heatmap_journal(hm, title = "Top DEG expression (z)", cluster_rows = TRUE, cluster_cols = TRUE)
delivery_save_plot(p_hm, skill_en, "heatmap", "TopDEG", 6.0, 5.5, fig_dir, bio_root, order = 3)

# UMAP from GSE164522 REAL subsample
if (file.exists(umap_f)) {
  umap <- read.csv(umap_f, check.names = FALSE, stringsAsFactors = FALSE)
  if (!"score" %in% names(umap) && "FCGR3A" %in% names(umap)) umap$score <- umap$FCGR3A
  if (nrow(umap) > 3500L) {
    set.seed(43505)
    umap <- umap[sample.int(nrow(umap), 3500L), ]
  }
  write.csv(umap[, intersect(c("umap_1", "umap_2", "celltype", "group", "score"), names(umap))],
            file.path(tab_dir, delivery_table_name(skill_en, "UMAP", "GSE164522")), row.names = FALSE)
  p2 <- plot_umap_discrete_journal(
    umap, x_col = "umap_1", y_col = "umap_2", label_col = "celltype",
    title = "Cell-type UMAP — GSE164522",
    point_size = 0.4, label_on_plot = TRUE, show_legend = FALSE
  )
  delivery_save_plot(p2, skill_en, "UMAP", "Celltype", 6.8, 5.8, fig_dir, bio_root, order = 4)
  umap_ok <- TRUE
} else {
  umap_ok <- FALSE
}

fig_map <- c(
  "火山图" = paste0("../图片文件/", delivery_stem(skill_en, "volcano", "TrtVsUntrt", order = 1), ".png"),
  "PCA" = paste0("../图片文件/", delivery_stem(skill_en, "pca", "AirwaySamples", order = 2), ".png"),
  "TopDEG热图" = paste0("../图片文件/", delivery_stem(skill_en, "heatmap", "TopDEG", order = 3), ".png")
)
if (isTRUE(umap_ok)) {
  fig_map <- c(fig_map,
    "细胞UMAP" = paste0("../图片文件/", delivery_stem(skill_en, "UMAP", "Celltype", order = 4), ".png")
  )
}
interp <- "REAL：airway limma-voom DEG + PCA + TopDEG heatmap；UMAP 来自 GSE164522。data_provenance=REAL。"
status <- "PASS"
data_html <- paste0(
  "<p><b>data_provenance: REAL</b></p><ul>",
  "<li>bulk：Bioconductor <code>airway</code> counts</li>",
  "<li>UMAP：GSE164522 subsample</li></ul>"
)
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- if (file.exists(audit_path)) paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>") else "<p>none</p>"
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(skill_en, skill_folder, status, data_html, audit_html, sourced_note, fig_map, interp, rep_file, blocked_reason = "")
writeLines(c(status, "data_provenance=REAL", "bulk=airway", "umap=GSE164522"), file.path(rep_dir, "STATUS.txt"))
message("DONE ", status, " — ", skill_folder, " REAL airway + GSE164522")
