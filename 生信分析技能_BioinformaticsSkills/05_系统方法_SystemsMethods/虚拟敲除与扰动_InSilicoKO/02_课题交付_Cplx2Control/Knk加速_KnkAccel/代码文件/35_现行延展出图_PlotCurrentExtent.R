# Current PEP/NF1 extent figures: Phase1 single-cell, DR ranks, enrichment if any.
# English plot text. Computational prediction. Not wet-lab DEG.
options(stringsAsFactors = FALSE)
set.seed(1)

vko <- "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除"
raw_dir <- file.path(vko, "数据文件")
res <- file.path(vko, "结果文件")
algo <- "scTenifoldKnk_1.4.3_GPU"
cross_fig <- file.path(res, "_跨亚群", algo, "图片文件")
cross_tab <- file.path(res, "_跨亚群", algo, "数据文件")
cross_rep <- file.path(res, "_跨亚群", algo, "报告文件")
for (d in c(cross_fig, cross_tab, cross_rep)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
np_plots <- "E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology/脚本_scripts/02_可视化_NetworkPharmPlots.R"
if (file.exists(viz)) source(viz, encoding = "UTF-8")
tryCatch({
  if (file.exists(np_plots)) source(np_plots, encoding = "UTF-8")
}, error = function(e) message("skip NetworkPharmPlots: ", conditionMessage(e)))
suppressPackageStartupMessages({
  library(ggplot2)
  library(Matrix)
  library(Seurat)
})
if (!exists("theme_journal")) theme_journal <- function(...) ggplot2::theme_bw()
fill1 <- if (exists("bioinfo_palette")) bioinfo_palette[1] else "#6B8F71"

save_plot <- function(p, dir, stem, w = 7, h = 5) {
  dir.create(dir, recursive = TRUE, showWarnings = FALSE)
  if (exists("save_plot_pub", mode = "function")) {
    save_plot_pub(p, stem = stem, width = w, height = h, dpi = 600, out_dir = dir)
  } else {
    ggplot2::ggsave(file.path(dir, paste0(stem, ".png")), p, width = w, height = h, dpi = 600, limitsize = FALSE)
    ggplot2::ggsave(file.path(dir, paste0(stem, ".svg")), p, width = w, height = h, limitsize = FALSE)
  }
}

subtypes <- c("PEP", "NF1")
targets <- c("Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21")
controls <- c(PEP = "Ret", NF1 = "Rdx")
ko_genes <- function(st) c(targets, unname(controls[[st]]))

arch01 <- "C:/Users/10540/Desktop/琪乐无穷/五亚群留档/结果文件/_跨亚群/scTenifoldKnk/图片文件"
for (nm in c("01_方法示意_scTenifoldKnkWorkflow.jpg", "01_部位示意_MouseTG_Cplx2Sites.jpg")) {
  src <- file.path(arch01, nm)
  if (file.exists(src)) file.copy(src, file.path(cross_fig, nm), overwrite = TRUE)
}

message("load counts")
meta <- read.csv(gzfile(file.path(raw_dir, "01_细胞注释_CellMeta_GSE197289.csv.gz")), check.names = FALSE)
counts <- readRDS(gzcon(gzfile(file.path(raw_dir, "02_表达矩阵_Counts_GSE197289.RDS.gz"), "rb")))
meta <- meta[match(colnames(counts), meta$V1), , drop = FALSE]
keep <- meta$model == "Control" & meta$subtype %in% subtypes
mat <- counts[, keep, drop = FALSE]
st_vec <- factor(meta$subtype[keep], levels = subtypes)

message("violin and detection")
long <- do.call(rbind, lapply(targets, function(g) {
  data.frame(gene = g, subtype = st_vec, log1p_count = log1p(as.numeric(mat[g, ])), stringsAsFactors = FALSE)
}))
p_vl <- ggplot(long, aes(subtype, log1p_count, fill = subtype)) +
  geom_violin(scale = "width", color = "grey20", linewidth = 0.2, trim = FALSE) +
  geom_boxplot(width = 0.12, outlier.shape = NA, fill = "white") +
  facet_wrap(~ gene, nrow = 2, scales = "free_y") +
  scale_fill_manual(values = c(PEP = fill1, NF1 = "#C17B7B")) +
  labs(title = "Target gene expression in control PEP and NF1", x = NULL, y = "log1p(count)", fill = NULL) +
  theme_journal() +
  theme(legend.position = "none")
save_plot(p_vl, cross_fig, "02_小提琴图_靶基因对照表达_TargetViolin", 9.5, 6.2)

det_parts <- lapply(subtypes, function(st) {
  pth <- file.path(res, st, algo, "_野生型", "数据文件", "检出_Detection.csv")
  d <- read.csv(pth, check.names = FALSE)
  d$subtype <- st
  d
})
det <- do.call(rbind, det_parts)
det$pct <- 100 * det$detected_cells / det$cells
det$gene <- factor(det$gene, levels = targets)
det$subtype <- factor(det$subtype, levels = subtypes)
p_det <- ggplot(det, aes(gene, pct, fill = subtype)) +
  geom_col(position = position_dodge(width = 0.8), width = 0.72) +
  scale_fill_manual(values = c(PEP = fill1, NF1 = "#C17B7B")) +
  labs(
    title = "Target gene detection in control TG",
    subtitle = "Denominator is Control cells before scQC",
    x = NULL, y = "Detected cells (%)", fill = NULL
  ) +
  theme_journal()
save_plot(p_det, cross_fig, "03_柱状图_靶基因检出率_TargetDetectionBar", 8.2, 4.6)
write.csv(det, file.path(cross_tab, "03_检出率_PEPNF1靶基因_TargetDetection.csv"), row.names = FALSE)

message("umap")
rownames(mat) <- make.unique(rownames(mat))
colnames(mat) <- make.unique(colnames(mat))
obj <- CreateSeuratObject(counts = mat, meta.data = data.frame(subtype = st_vec, row.names = colnames(mat)))
obj <- NormalizeData(obj, verbose = FALSE)
obj <- FindVariableFeatures(obj, nfeatures = 2000, verbose = FALSE)
obj <- ScaleData(obj, verbose = FALSE)
obj <- RunPCA(obj, npcs = 30, verbose = FALSE)
obj <- RunUMAP(obj, dims = 1:20, verbose = FALSE)
um <- as.data.frame(obj@reductions$umap@cell.embeddings)
um$subtype <- obj$subtype
um$Cplx2 <- as.numeric(GetAssayData(obj, layer = "data")["Cplx2", ])
p_u <- ggplot(um, aes(umap_1, umap_2, color = subtype)) +
  geom_point(size = 0.35, alpha = 0.85) +
  scale_color_manual(values = c(PEP = fill1, NF1 = "#C17B7B")) +
  labs(title = "Control TG PEP and NF1", x = "UMAP-1", y = "UMAP-2", color = NULL) +
  theme_journal() +
  coord_equal()
save_plot(p_u, cross_fig, "02_散点图_对照亚群UMAP_PepNf1Umap", 6.4, 5.4)
p_f <- ggplot(um, aes(umap_1, umap_2, color = Cplx2)) +
  geom_point(size = 0.35) +
  scale_color_gradient(low = "grey85", high = "#2166AC") +
  labs(title = "Cplx2 in control PEP and NF1", x = "UMAP-1", y = "UMAP-2", color = "log-normalized") +
  theme_journal() +
  coord_equal()
save_plot(p_f, cross_fig, "02_散点图_Cplx2表达UMAP_Cplx2Feature", 6.6, 5.4)

read_dr <- function(st, gene) {
  pth <- file.path(res, st, algo, gene, "数据文件", "扰动_Dr.csv")
  if (!file.exists(pth)) return(NULL)
  d <- read.csv(pth, check.names = FALSE)
  d$subtype <- st
  d$knockout <- gene
  d
}

all_dr <- list()
message("per-gene DR and enrichment")
for (st in subtypes) {
  for (gene in ko_genes(st)) {
    d <- read_dr(st, gene)
    if (is.null(d)) next
    all_dr[[paste(st, gene)]] <- d
    fig_dir <- file.path(res, st, algo, gene, "图片文件")
    rep_dir <- file.path(res, st, algo, gene, "报告文件")
    dir.create(rep_dir, recursive = TRUE, showWarnings = FALSE)
    d2 <- d[d$gene != gene, , drop = FALSE]
    d2 <- d2[order(d2$distance, decreasing = TRUE), , drop = FALSE]
    d2$rank <- seq_len(nrow(d2))
    d2$sig <- d2$p.adj < 0.05
    p_sc <- ggplot(d2, aes(rank, distance, color = sig)) +
      geom_point(size = 0.55, alpha = 0.7) +
      scale_color_manual(values = c("FALSE" = "grey70", "TRUE" = "#C17B7B")) +
      labs(
        title = paste0(st, " ", gene, " virtual KO"),
        subtitle = "scTenifoldKnk 1.4.3 GPU; computational prediction",
        x = "Rank (by distance)",
        y = "Distance",
        color = "FDR < 0.05"
      ) +
      theme_journal()
    save_plot(p_sc, fig_dir, paste0("04_散点图_扰动排名_", st, "_", gene, "RankScatter"), 6.4, 5)
    top <- d2[order(d2$distance, decreasing = TRUE), , drop = FALSE]
    top <- head(top, 15)
    top$gene <- factor(top$gene, levels = rev(top$gene))
    p_bar <- ggplot(top, aes(distance, gene, fill = p.adj < 0.05)) +
      geom_col(width = 0.72) +
      scale_fill_manual(values = c("FALSE" = fill1, "TRUE" = "#C17B7B")) +
      labs(
        title = paste0("Top 15 DR genes after ", gene, " KO (", st, ")"),
        x = "Distance", y = NULL, fill = "FDR < 0.05"
      ) +
      theme_journal()
    save_plot(p_bar, fig_dir, paste0("04_柱状图_扰动基因_", st, "_", gene, "DrBar"), 7.2, 5.2)

    go_path <- file.path(res, st, algo, gene, "数据文件", "富集_GO.csv")
    kegg_path <- file.path(res, st, algo, gene, "数据文件", "富集_KEGG.csv")
    go <- if (file.exists(go_path)) tryCatch(read.csv(go_path, check.names = FALSE), error = function(e) data.frame()) else data.frame()
    kegg <- if (file.exists(kegg_path)) tryCatch(read.csv(kegg_path, check.names = FALSE), error = function(e) data.frame()) else data.frame()
    n_go <- if (ncol(go) == 0 || nrow(go) == 0) 0L else nrow(go)
    n_kegg <- if (ncol(kegg) == 0 || nrow(kegg) == 0) 0L else nrow(kegg)
    if (n_go == 0L && n_kegg == 0L) {
      writeLines(
        "No GO or KEGG term passed BH p=0.05 and q=0.2 on FDR<0.05 response genes. No enrichment figure was drawn.",
        file.path(rep_dir, "05_富集_无通过条目.txt")
      )
    } else {
      if (n_go > 0L && exists("np_plot_go_bubble")) {
        if (!"term" %in% names(go) && "Description" %in% names(go)) go$term <- go$Description
        save_plot(np_plot_go_bubble(go, top_n = 10), fig_dir, paste0("05_气泡图_GO_", st, "_", gene), 8.5, 9)
        save_plot(np_plot_go_bar(go, top_n = 10), fig_dir, paste0("05_柱状图_GO_", st, "_", gene), 9, 7)
      }
      if (n_kegg > 0L && exists("np_plot_kegg_bar")) {
        if (!"term" %in% names(kegg) && "Description" %in% names(kegg)) kegg$term <- kegg$Description
        save_plot(np_plot_kegg_lollipop(kegg, top_n = 20), fig_dir, paste0("05_棒棒糖_KEGG_", st, "_", gene), 8, 7)
        save_plot(np_plot_kegg_bar(kegg, top_n = 20), fig_dir, paste0("05_柱状图_KEGG_", st, "_", gene), 8, 7)
      }
    }
  }
}

combo <- do.call(rbind, all_dr)
combo <- combo[combo$gene != combo$knockout, , drop = FALSE]
combo$sig <- combo$p.adj < 0.05
combo <- do.call(rbind, lapply(split(combo, list(combo$subtype, combo$knockout), drop = TRUE), function(x) {
  x <- x[order(x$distance, decreasing = TRUE), , drop = FALSE]
  x$rank <- seq_len(nrow(x))
  x
}))
p_all <- ggplot(combo, aes(rank, distance, color = sig)) +
  geom_point(size = 0.4, alpha = 0.65) +
  scale_color_manual(values = c("FALSE" = "grey70", "TRUE" = "#C17B7B")) +
  facet_grid(subtype ~ knockout, scales = "free") +
  labs(
    title = "Virtual KO rank statistic in PEP and NF1",
    subtitle = "scTenifoldKnk 1.4.3 GPU",
    x = "Rank (by distance)",
    y = "Distance",
    color = "FDR < 0.05"
  ) +
  theme_journal() +
  theme(strip.text = element_text(size = 8))
save_plot(p_all, cross_fig, "04_散点图_扰动排名_PepNf1RankScatter", 14, 6.5)
write.csv(combo[combo$sig, c("subtype", "knockout", "gene", "distance", "p.adj")], file.path(cross_tab, "04_显著扰动_PEPNF1_Fdr05.csv"), row.names = FALSE)

keep_ko <- names(all_dr)[vapply(names(all_dr), function(k) {
  parts <- strsplit(k, " ", fixed = TRUE)[[1]]
  !file.exists(file.path(res, parts[1], algo, parts[2], "报告文件", "说明_无出边.txt"))
}, logical(1))]
fdr_sets <- lapply(keep_ko, function(k) {
  d <- all_dr[[k]]
  ko <- unique(d$knockout)
  d$gene[d$gene != ko & d$p.adj < 0.05]
})
names(fdr_sets) <- keep_ko
labs <- names(fdr_sets)
jac <- matrix(NA_real_, length(labs), length(labs), dimnames = list(labs, labs))
for (i in labs) for (j in labs) {
  a <- fdr_sets[[i]]
  b <- fdr_sets[[j]]
  u <- length(union(a, b))
  jac[i, j] <- if (u == 0) 0 else length(intersect(a, b)) / u
}
write.csv(jac, file.path(cross_tab, "07_重叠_FDR基因Jaccard_PepNf1.csv"))
jac_df <- as.data.frame(as.table(jac))
names(jac_df) <- c("a", "b", "jaccard")
p_j <- ggplot(jac_df, aes(a, b, fill = jaccard)) +
  geom_tile(color = "white") +
  geom_text(aes(label = sprintf("%.2f", jaccard)), size = 2.2) +
  scale_fill_gradient(low = "white", high = fill1, limits = c(0, 1)) +
  labs(title = "Overlap of FDR < 0.05 response genes", x = NULL, y = NULL, fill = "Jaccard") +
  theme_journal() +
  theme(axis.text.x = element_text(angle = 50, hjust = 1, size = 7), axis.text.y = element_text(size = 7))
save_plot(p_j, cross_fig, "07_热图_亚群基因重叠_FdrJaccard", 8.8, 7.6)

writeLines(
  c(
    "Extent figures for current PEP/NF1 virtual KO (scTenifoldKnk 1.4.3 GPU).",
    "Phase1: violin, detection bar, UMAP of Control PEP+NF1. Method overview copied from the five-subtype archive with the same published schematic.",
    "Phase2: per-gene DR scatter and top-15 bar; combined rank scatter; Jaccard of FDR genes.",
    "Enrichment: no passing GO/KEGG on valid knockouts; 05_富集_无通过条目.txt written per gene. Discarded zero-edge GO plots stay under 图片文件/_未采用_无出边.",
    "Jaccard excludes PEP Mitf/Ppp1r26/Sh3d21 (zero outgoing edges after rounding). Those FDR lists are noise and stay under _未采用_无出边."
  ),
  file.path(cross_rep, "STATUS_延展出图.txt")
)
message("EXTENT_DONE")
