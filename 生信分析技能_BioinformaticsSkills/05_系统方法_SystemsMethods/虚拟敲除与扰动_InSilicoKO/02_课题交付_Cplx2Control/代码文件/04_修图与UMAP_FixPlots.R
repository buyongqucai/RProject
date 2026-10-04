# Fix crowded enrichment bars, draw full violins, add control-cell UMAP.
options(stringsAsFactors = FALSE)
vko <- "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除"
arch <- "C:/Users/10540/Desktop/琪乐无穷/五亚群留档"
raw_dir <- file.path(vko, "数据文件")
tab_dir <- file.path(arch, "结果文件", "_跨亚群", "scTenifoldKnk", "数据文件")
fig_dir <- file.path(arch, "结果文件", "_跨亚群", "scTenifoldKnk", "图片文件")
viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
if (file.exists(viz)) source(viz, encoding = "UTF-8")
suppressPackageStartupMessages({
  library(ggplot2)
  library(Matrix)
})
if (!exists("theme_journal")) theme_journal <- function(...) theme_bw()
fill1 <- if (exists("bioinfo_palette")) bioinfo_palette[1] else "#4C78A8"
subtypes <- c("cLTMR", "NF1", "NP", "PEP", "TRPM8")

save_plot <- function(p, stem, w, h) {
  ggplot2::ggsave(file.path(fig_dir, paste0(stem, ".png")), p, width = w, height = h, dpi = 600, limitsize = FALSE)
  ggplot2::ggsave(file.path(fig_dir, paste0(stem, ".svg")), p, width = w, height = h, limitsize = FALSE)
}

wrap_term <- function(x) {
  vapply(x, function(s) paste(strwrap(s, width = 42), collapse = "\n"), character(1))
}

# --- enrichment: one subtype per row, focus terms only ---
enr <- read.csv(file.path(tab_dir, "05_富集_Top50_Cplx2Enrich.csv"), check.names = FALSE)
focus <- grepl("synaptic vesicle|SNARE|neurotransmitter", enr$Term, ignore.case = TRUE)
enr <- enr[focus, , drop = FALSE]
enr$neglog <- -log10(as.numeric(enr$Adjusted.P.value) + 1e-300)
enr <- enr[order(enr$subtype, -enr$neglog), ]
enr <- do.call(rbind, lapply(split(enr, enr$subtype), function(d) head(d, 6)))
enr$label <- wrap_term(enr$Term)
enr$label <- factor(enr$label, levels = unique(enr$label[order(enr$subtype, enr$neglog)]))
p5 <- ggplot(enr, aes(neglog, label)) +
  geom_col(fill = fill1, width = 0.72) +
  facet_wrap(~ subtype, ncol = 1, scales = "free_y") +
  labs(
    title = "Synaptic GO terms among top 50 ranked genes",
    subtitle = "Not an FDR-significant gene set",
    x = "-log10(adjusted P)", y = NULL
  ) +
  theme_journal() +
  theme(strip.text = element_text(face = "bold"))
save_plot(p5, "05_柱状图_突触富集_Cplx2SynapticGO", w = 8, h = 14)

# --- full violin ---
message("load counts")
meta <- read.csv(gzfile(file.path(raw_dir, "01_细胞注释_CellMeta_GSE197289.csv.gz")), check.names = FALSE)
counts <- readRDS(gzcon(gzfile(file.path(raw_dir, "02_表达矩阵_Counts_GSE197289.RDS.gz"), "rb")))
meta <- meta[match(colnames(counts), meta$V1), , drop = FALSE]
keep <- meta$model == "Control" & meta$subtype %in% subtypes
expr <- data.frame(
  subtype = factor(meta$subtype[keep], levels = subtypes),
  log1p_count = log1p(as.numeric(counts["Cplx2", keep])),
  stringsAsFactors = FALSE
)
violin_args <- list(trim = FALSE, scale = "width", width = 0.85, fill = fill1, color = "grey20", linewidth = 0.2)
if ("side" %in% names(formals(geom_violin))) violin_args$side <- "both"
p2 <- ggplot(expr, aes(subtype, log1p_count)) +
  do.call(geom_violin, violin_args) +
  geom_boxplot(width = 0.12, outlier.shape = NA, fill = "white") +
  scale_y_continuous(expand = expansion(mult = c(0.02, 0.08))) +
  labs(title = "Cplx2 expression in control TG subtypes", x = NULL, y = "log1p(count)") +
  theme_journal() +
  coord_cartesian(clip = "off")
save_plot(p2, "02_小提琴图_对照亚群表达_Cplx2Violin", w = 7.2, h = 5.2)

# --- single-cell UMAP of the same control cells ---
message("umap")
suppressPackageStartupMessages(library(Seurat))
mat <- counts[, keep, drop = FALSE]
rownames(mat) <- make.unique(rownames(mat))
colnames(mat) <- make.unique(colnames(mat))
meta_use <- data.frame(subtype = expr$subtype, row.names = colnames(mat))
obj <- CreateSeuratObject(counts = mat, meta.data = meta_use)
obj <- NormalizeData(obj, verbose = FALSE)
obj <- FindVariableFeatures(obj, nfeatures = 2000, verbose = FALSE)
obj <- ScaleData(obj, verbose = FALSE)
obj <- RunPCA(obj, npcs = 20, verbose = FALSE)
obj <- RunUMAP(obj, dims = 1:15, verbose = FALSE)
emb <- as.data.frame(Embeddings(obj, "umap"))
emb$subtype <- obj$subtype
cplx2_vec <- expr$log1p_count
names(cplx2_vec) <- colnames(mat)
emb$Cplx2 <- cplx2_vec[rownames(emb)]
p_umap <- ggplot(emb, aes(umap_1, umap_2, color = subtype)) +
  geom_point(size = 0.35, alpha = 0.8) +
  labs(title = "Control TG sensory subtypes", x = "UMAP 1", y = "UMAP 2", color = NULL) +
  theme_journal() +
  guides(color = guide_legend(override.aes = list(size = 2.5, alpha = 1)))
save_plot(p_umap, "02_散点图_对照亚群UMAP_SubtypeUmap", w = 7.2, h = 5.6)
p_feat <- ggplot(emb, aes(umap_1, umap_2, color = Cplx2)) +
  geom_point(size = 0.35) +
  scale_color_gradient(low = "grey85", high = "#B33A3A") +
  labs(title = "Cplx2 expression", x = "UMAP 1", y = "UMAP 2", color = "log1p") +
  theme_journal()
save_plot(p_feat, "02_散点图_Cplx2表达UMAP_Cplx2Feature", w = 7.2, h = 5.6)
message("FIX_DONE")
