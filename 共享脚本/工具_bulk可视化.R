# bulk RNA-seq 可视化：与 scRNA 图集品类对齐（600 DPI）

suppressPackageStartupMessages({ library(ggplot2); library(tidyverse) })

if (!exists("FIG_DPI")) {
  pr <- if (file.exists("RProject.Rproj")) normalizePath(".") else {
    p <- normalizePath(getwd(), winslash = "/")
    for (i in 1:6) { if (file.exists(file.path(p, "RProject.Rproj"))) break; p <- dirname(p) }
    p
  }
  source(file.path(pr, "共享脚本", "工具_统一出图.R"), encoding = "UTF-8")
}

`%||%` <- function(x, y) if (is.null(x)) y else x

bulk_marker_scores <- function(mat, marker_list) {
  score_one <- function(vec, genes) {
    g <- genes[genes %in% names(vec)]
    if (length(g) == 0) return(0)
    mean(vec[g], na.rm = TRUE)
  }
  samples <- colnames(mat)
  out <- matrix(0, nrow = length(samples), ncol = length(marker_list),
                dimnames = list(samples, names(marker_list)))
  for (i in seq_along(samples)) {
    vec <- mat[, samples[i]]; names(vec) <- rownames(mat)
    out[i, ] <- vapply(marker_list, score_one, numeric(1), vec = vec)
  }
  out[out < 0] <- 0
  out
}

dominant_label <- function(score_mat) {
  apply(score_mat, 1, function(x) {
    if (all(x <= 0)) return("Unknown")
    colnames(score_mat)[which.max(x)]
  })
}

bulk_umap_plot <- function(score_mat, meta, color, title = "", out_path = NULL,
                           label_col = "sample", show_labels = TRUE) {
  setup_plot_fonts()
  fam <- ""
  n <- nrow(score_mat)
  if (n < 3) { message("样本数 < 3，跳过 UMAP: ", title); return(invisible(NULL)) }
  set.seed(42)
  emb <- if (requireNamespace("uwot", quietly = TRUE)) {
    uwot::umap(scale(score_mat), n_neighbors = min(5, n - 1), min_dist = 0.3)
  } else {
    prcomp(scale(score_mat), rank. = min(2, ncol(score_mat) - 1))$x[, 1:2, drop = FALSE]
  }
  df <- tibble(UMAP_1 = emb[, 1], UMAP_2 = emb[, 2],
               sample = rownames(score_mat), color = color,
               group = meta$group[match(rownames(score_mat), meta$sample)])
  p <- ggplot(df, aes(UMAP_1, UMAP_2, color = color)) +
    geom_point(size = 5) +
    labs(title = title, color = NULL, subtitle = "bulk marker 签名 UMAP（样本级）") +
    theme_no_overlap()
  if (show_labels && requireNamespace("ggrepel", quietly = TRUE)) {
    p <- add_ggrepel(p, df, aes(label = .data[[label_col]]), fam = fam, size = 3.2)
  }
  if (!is.null(out_path)) safe_ggsave(out_path, p, width = 10, height = 8)
  p
}

plot_bulk_donut <- function(prop_df, title = "", out_path = NULL) {
  setup_plot_fonts()
  df <- prop_df %>% group_by(celltype) %>%
    summarise(prop = mean(proportion), .groups = "drop") %>%
    mutate(pct = scales::percent(prop, accuracy = 0.1))
  p <- ggplot(df, aes(x = 2, y = prop, fill = celltype)) +
    geom_col(width = 1, color = "white") + coord_polar(theta = "y") +
    xlim(0.5, 2.5) + theme_void() +
    geom_text(aes(label = pct), position = position_stack(vjust = 0.5), size = 3.5) +
    labs(title = title, fill = "Cell type") +
    theme(plot.title = element_text(hjust = 0.5, face = "bold"))
  if (!is.null(out_path)) safe_ggsave(out_path, p, width = 9, height = 8)
  p
}

plot_bulk_prop_bar <- function(prop_df, title = "", out_path = NULL) {
  setup_plot_fonts()
  df <- prop_df %>% group_by(group, celltype) %>%
    summarise(prop = mean(proportion), .groups = "drop")
  p <- ggplot(df, aes(group, prop, fill = celltype)) +
    geom_col(position = "fill", width = 0.65, color = "white", linewidth = 0.3) +
    scale_y_continuous(labels = scales::percent_format()) +
    labs(title = title, x = NULL, y = "Proportion", fill = "Cell type") +
    theme_no_overlap()
  if (!is.null(out_path)) safe_ggsave(out_path, p, width = 10, height = 7)
  p
}

save_all_bulk_figures <- function(mat, sample_info, dataset, paths, cfg) {
  fig <- paths$图形
  sample_info <- as.data.frame(sample_info)
  rownames(sample_info) <- sample_info$sample
  sample_info <- sample_info[colnames(mat), , drop = FALSE]

  ct_scores <- bulk_marker_scores(mat, CARDIAC_MARKERS)
  prop_list <- lapply(rownames(ct_scores), function(sid) {
    sc <- ct_scores[sid, , drop = TRUE]
    if (sum(sc) == 0) sc <- rep(1 / length(sc), length(sc))
    tibble(sample = sid, group = sample_info$group[sid],
           celltype = names(sc), score = sc, proportion = sc / sum(sc))
  })
  prop_df <- bind_rows(prop_list)
  write.csv(prop_df, file.path(paths$表格, paste0(dataset, "_估算细胞比例.csv")), row.names = FALSE)

  dom_ct <- dominant_label(ct_scores)
  bulk_umap_plot(ct_scores, sample_info, dom_ct,
                 title = paste(dataset, "UMAP 聚类"),
                 out_path = file.path(fig, paste0(dataset, "_UMAP.pdf")))
  bulk_umap_plot(ct_scores, sample_info, dom_ct,
                 title = paste(dataset, "UMAP 细胞类型"),
                 out_path = file.path(fig, paste0(dataset, "_UMAP_细胞类型.pdf")))

  imm_scores <- bulk_marker_scores(mat, IMMUNE_LINEAGE)
  imm_scores <- imm_scores[, colSums(imm_scores) > 0, drop = FALSE]
  if (ncol(imm_scores) >= 2 && nrow(imm_scores) >= 3) {
    dom_imm <- dominant_label(imm_scores)
    k <- min(4, max(2, nrow(imm_scores) - 1))
    imm_cl <- as.character(kmeans(scale(imm_scores), centers = k, nstart = 10)$cluster)
    bulk_umap_plot(imm_scores, sample_info, imm_cl,
                   title = paste(dataset, "免疫亚群聚类"),
                   out_path = file.path(fig, paste0(dataset, "_UMAP_免疫聚类.pdf")))
    bulk_umap_plot(imm_scores, sample_info, dom_imm,
                   title = paste(dataset, "免疫谱系"),
                   out_path = file.path(fig, paste0(dataset, "_UMAP_免疫谱系.pdf")))
  }

  plot_bulk_donut(prop_df, title = paste(dataset, "细胞比例"),
                  out_path = file.path(fig, paste0(dataset, "_细胞比例环图.pdf")))
  plot_bulk_prop_bar(prop_df, title = paste(dataset, "分组细胞比例"),
                     out_path = file.path(fig, paste0(dataset, "_分组细胞比例堆叠图.pdf")))

  deg_rds <- file.path(paths$中间数据, paste0(dataset, "_deg.rds"))
  if (file.exists(deg_rds)) {
    plot_volcano(readRDS(deg_rds), title = paste(dataset, "差异基因火山图"),
                 out_path = file.path(fig, paste0(dataset, "_火山图.pdf")),
                 padj_cut = cfg$deg_padj %||% 0.05,
                 lfc_cut = cfg$deg_logfc %||% 1)
  }
  invisible(prop_df)
}
