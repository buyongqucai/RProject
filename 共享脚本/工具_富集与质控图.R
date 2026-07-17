# 补充图：QC 箱线图/PCA、Top50 热图、GO/KEGG 富集（dotplot + barplot）
# 与 GSE79962 图集保持一致，适用于 bulk 与 scRNA（pseudobulk）数据

suppressPackageStartupMessages({
  library(ggplot2)
  library(tidyverse)
})

if (!exists("FIG_DPI")) {
  pr <- if (file.exists("RProject.Rproj")) normalizePath(".") else {
    p <- normalizePath(getwd(), winslash = "/")
    for (i in 1:6) { if (file.exists(file.path(p, "RProject.Rproj"))) break; p <- dirname(p) }
    p
  }
  source(file.path(pr, "共享脚本", "工具_统一出图.R"), encoding = "UTF-8")
}

`%||%` <- function(x, y) if (is.null(x)) y else x

# 从 Seurat 对象按样本聚合为 pseudobulk 表达矩阵（log2 CPM）
build_pseudobulk_matrix <- function(obj, sample_col = "sample", group_col = "group") {
  suppressPackageStartupMessages(library(Seurat))
  DefaultAssay(obj) <- "RNA"
  meta <- obj@meta.data
  # AggregateExpression 可稳健处理 v5 多层对象，按样本汇总原始 counts
  agg <- AggregateExpression(obj, assays = "RNA", group.by = sample_col,
                             slot = "counts", return.seurat = FALSE)
  pb <- as.matrix(agg$RNA)
  # AggregateExpression 会把样本名中的下划线替换为连字符，做一次对齐映射
  usam_raw <- unique(as.character(meta[[sample_col]]))
  map_clean <- setNames(usam_raw, make.names(gsub("_", "-", usam_raw)))
  cn_clean <- make.names(colnames(pb))
  colnames(pb) <- ifelse(cn_clean %in% names(map_clean), map_clean[cn_clean], colnames(pb))
  cpm <- t(t(pb) / colSums(pb)) * 1e6
  logcpm <- log2(cpm + 1)
  grp <- meta[[group_col]][match(colnames(pb), as.character(meta[[sample_col]]))]
  sample_info <- data.frame(sample = colnames(pb), group = grp,
                            row.names = colnames(pb))
  list(expr = logcpm, sample_info = sample_info)
}

# QC 箱线图 + 质控PCA + PCA（分组虚线框）
make_qc_and_pca_plots <- function(expr, sample_info, dataset, fig_dir) {
  fam <- ext_setup_font()
  expr <- as.matrix(expr)
  # 对齐分组与列（避免顺序错位导致每个样本出现两个箱体的历史 bug）
  rownames(sample_info) <- sample_info$sample
  sample_info <- sample_info[colnames(expr), , drop = FALSE]
  sample_info$group <- factor(sample_info$group)
  grp_vec <- sample_info$group

  # 箱线图：group 用 each 对齐每个样本（每样本仅一个箱体）
  box_df <- tibble(
    sample = factor(rep(colnames(expr), each = nrow(expr)), levels = colnames(expr)),
    expression = as.vector(expr),
    group = rep(grp_vec, each = nrow(expr))
  )
  p_box <- ggplot(box_df, aes(x = sample, y = expression, fill = group)) +
    geom_boxplot(outlier.size = 0.3) +
    theme(axis.text.x = element_text(angle = 90, hjust = 1, size = 7)) +
    labs(title = paste(dataset, "样本表达分布"), x = NULL, y = "log2 表达量", fill = "分组") +
    theme_no_overlap()
  safe_ggsave(file.path(fig_dir, paste0(dataset, "_质控箱线图.pdf")), p_box, width = 12, height = 7)

  vars <- apply(expr, 1, var)
  expr_pca <- expr[vars > 0, , drop = FALSE]
  n_smp <- ncol(expr_pca)
  pca_df <- NULL; var_pct <- c(NA, NA)
  if (n_smp >= 3) {
    pca <- prcomp(t(expr_pca), scale. = TRUE)
    var_pct <- round(100 * summary(pca)$importance[2, 1:2], 1)
    pca_df <- tibble(PC1 = pca$x[, 1], PC2 = pca$x[, 2],
                     sample = rownames(pca$x), group = grp_vec)
  }

  add_group_box <- function(p, df) {
    # 每组 ≥2 个样本时画虚线外框（bounding box）；单样本组不画（避免空框/Inf）
    keep_g <- df %>% count(group) %>% filter(n >= 2) %>% pull(group)
    box_g <- df %>% filter(group %in% keep_g) %>% group_by(group) %>%
      summarise(xmin = min(PC1), xmax = max(PC1), ymin = min(PC2), ymax = max(PC2),
                .groups = "drop")
    if (nrow(box_g) > 0) {
      pad_x <- diff(range(df$PC1)) * 0.05 + 1e-9
      pad_y <- diff(range(df$PC2)) * 0.05 + 1e-9
      p <- p + geom_rect(data = box_g, inherit.aes = FALSE,
                         aes(xmin = xmin - pad_x, xmax = xmax + pad_x,
                             ymin = ymin - pad_y, ymax = ymax + pad_y, color = group),
                         fill = NA, linetype = 2, linewidth = 0.5, show.legend = FALSE)
    }
    p
  }

  if (!is.null(pca_df)) {
    lab_geom <- if (requireNamespace("ggrepel", quietly = TRUE))
      ggrepel::geom_text_repel(aes(label = sample), size = 3.2,
                               max.overlaps = 40, min.segment.length = 0, segment.size = 0.25,
                               box.padding = 0.4, force = 2)
    else geom_text(aes(label = sample), vjust = -0.8, size = 2.8)

    p_qc_pca <- add_group_box(
      ggplot(pca_df, aes(PC1, PC2, color = group)) + geom_point(size = 4), pca_df) +
      lab_geom + theme_no_overlap() +
      labs(title = paste(dataset, "质控 PCA"), color = "分组",
           x = paste0("PC1 (", var_pct[1], "%)"), y = paste0("PC2 (", var_pct[2], "%)"))
    safe_ggsave(file.path(fig_dir, paste0(dataset, "_质控PCA.pdf")), p_qc_pca, width = 10, height = 8)

    p_pca <- add_group_box(
      ggplot(pca_df, aes(PC1, PC2, color = group)) + geom_point(size = 5), pca_df) +
      theme_no_overlap() +
      labs(title = paste(dataset, "PCA（分组虚线框）"), color = "分组",
           x = paste0("PC1 (", var_pct[1], "%)"), y = paste0("PC2 (", var_pct[2], "%)"))
    safe_ggsave(file.path(fig_dir, paste0(dataset, "_PCA.pdf")), p_pca, width = 10, height = 8)
  } else {
    message("样本数 < 3，PCA 无意义，跳过 PCA 图: ", dataset)
  }
}

# Top50 DEG 热图
make_top50_heatmap <- function(expr, sample_info, deg_sig, dataset, fig_dir) {
  suppressPackageStartupMessages({ library(pheatmap); library(RColorBrewer) })
  sample_info$group <- factor(sample_info$group)
  top_genes <- deg_sig %>% arrange(padj) %>% head(50) %>% pull(gene)
  top_genes <- top_genes[top_genes %in% rownames(expr)]
  if (length(top_genes) < 2) {
    message("显著 DEG 不足，跳过热图")
    return(invisible(NULL))
  }
  mat <- expr[top_genes, , drop = FALSE]
  mat_scaled <- t(scale(t(mat)))
  mat_scaled[is.na(mat_scaled)] <- 0
  annotation_col <- data.frame(Group = sample_info$group)
  rownames(annotation_col) <- rownames(sample_info)
  nlev <- length(levels(sample_info$group))
  ann_colors <- list(Group = setNames(
    brewer.pal(max(3, nlev), "Set1")[seq_len(nlev)], levels(sample_info$group)))
  safe_pdf(file.path(fig_dir, paste0(dataset, "_Top50热图.pdf")), width = 12, height = 14, {
    pheatmap(mat_scaled, annotation_col = annotation_col, annotation_colors = ann_colors,
             show_rownames = TRUE, fontsize_row = 8,
             main = paste(dataset, "Top 50 DEGs"),
             color = colorRampPalette(c("#4DBBD5", "white", "#E64B35"))(100))
  })
}

# GO/KEGG 富集：每类输出 dotplot（名字.pdf）+ barplot（名字图.pdf）+ 表（名字.csv）
run_enrichment_full <- function(deg_sig, dataset, tab_dir, fig_dir,
                                org_db = "org.Mm.eg.db", kegg_org = "mmu",
                                id_type = "SYMBOL") {
  suppressPackageStartupMessages({
    library(clusterProfiler)
    library(org.Mm.eg.db)
  })
  ext_setup_font()
  if (nrow(deg_sig) == 0) { message("无显著 DEG，跳过富集"); return(invisible(NULL)) }
  org_pkg <- get(org_db, envir = asNamespace(org_db))
  map_entrez <- function(ids) suppressMessages(
    tryCatch(bitr(ids, fromType = id_type, toType = "ENTREZID", OrgDb = org_pkg),
             error = function(e) data.frame(ENTREZID = character(0))))

  genes_all <- deg_sig$gene
  genes_up <- deg_sig %>% filter(log2FC > 0) %>% pull(gene)
  genes_down <- deg_sig %>% filter(log2FC < 0) %>% pull(gene)

  go_of <- function(ids) {
    e <- map_entrez(ids)
    if (nrow(e) < 3) return(NULL)
    enrichGO(e$ENTREZID, OrgDb = org_pkg, ont = "BP", pAdjustMethod = "BH",
             pvalueCutoff = 0.05, qvalueCutoff = 0.2, readable = TRUE)
  }
  kegg_of <- function(ids) {
    e <- map_entrez(ids)
    if (nrow(e) < 3) return(NULL)
    enrichKEGG(e$ENTREZID, organism = kegg_org, pAdjustMethod = "BH",
               pvalueCutoff = 0.05, qvalueCutoff = 0.2)
  }
  save_dot_bar <- function(res, base, title) {
    save_enrich_plots(res, base, title, tab_dir, fig_dir)
  }
  save_kegg_safe <- function(ids, base, title) {
    tryCatch(save_dot_bar(kegg_of(ids), base, title), error = function(e) {
      message("KEGG 跳过: ", title, " — ", conditionMessage(e))
    })
  }

  save_dot_bar(go_of(genes_all), paste0(dataset, "_GO生物过程"), paste(dataset, "GO BP"))
  save_kegg_safe(genes_all, paste0(dataset, "_KEGG通路"), paste(dataset, "KEGG"))
  save_dot_bar(go_of(genes_up), paste0(dataset, "_GO生物过程_上调"), paste(dataset, "GO BP Up"))
  save_dot_bar(go_of(genes_down), paste0(dataset, "_GO生物过程_下调"), paste(dataset, "GO BP Down"))
  save_kegg_safe(genes_up, paste0(dataset, "_KEGG通路_上调"), paste(dataset, "KEGG Up"))
  save_kegg_safe(genes_down, paste0(dataset, "_KEGG通路_下调"), paste(dataset, "KEGG Down"))
}
