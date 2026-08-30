# scRNA 标准图：UMAP / 比例环图 / 堆叠柱图 / 火山图（600 DPI）

if (!exists("FIG_DPI")) {
  pr <- if (file.exists("RProject.Rproj")) normalizePath(".") else {
    p <- normalizePath(getwd(), winslash = "/")
    for (i in 1:6) { if (file.exists(file.path(p, "RProject.Rproj"))) break; p <- dirname(p) }
    p
  }
  source(file.path(pr, "共享脚本", "工具_统一出图.R"), encoding = "UTF-8")
}

plot_umap_celltype <- function(obj, label_col = "celltype", title = "", out_path = NULL) {
  setup_plot_fonts()
  p <- Seurat::DimPlot(obj, group.by = label_col, label = TRUE, repel = TRUE, label.size = 4) +
    ggplot2::ggtitle(title) + theme_no_overlap()
  if (!is.null(out_path)) safe_ggsave(out_path, p, width = 10, height = 8)
  p
}

plot_umap_clusters <- function(obj, title = "", out_path = NULL) {
  setup_plot_fonts()
  p <- Seurat::DimPlot(obj, group.by = "seurat_clusters", label = TRUE, repel = TRUE, label.size = 4) +
    ggplot2::ggtitle(title) + theme_no_overlap()
  if (!is.null(out_path)) safe_ggsave(out_path, p, width = 10, height = 8)
  p
}

plot_umap_by_col <- function(obj, col, title = "", out_path = NULL) {
  setup_plot_fonts()
  p <- Seurat::DimPlot(obj, group.by = col, label = TRUE, repel = TRUE, label.size = 4) +
    ggplot2::ggtitle(title) + theme_no_overlap()
  if (!is.null(out_path)) safe_ggsave(out_path, p, width = 10, height = 8)
  p
}

plot_celltype_donut <- function(obj, label_col = "celltype", title = "", out_path = NULL) {
  setup_plot_fonts()
  df <- obj@meta.data %>%
    tibble::as_tibble() %>%
    dplyr::count(.data[[label_col]], name = "n") %>%
    dplyr::mutate(celltype = .data[[label_col]], prop = n / sum(n),
                  pct = scales::percent(prop, accuracy = 0.1))
  p <- ggplot2::ggplot(df, ggplot2::aes(x = 2, y = prop, fill = celltype)) +
    ggplot2::geom_col(width = 1, color = "white") +
    ggplot2::coord_polar(theta = "y") + ggplot2::xlim(0.5, 2.5) + ggplot2::theme_void() +
    ggplot2::geom_text(ggplot2::aes(label = pct), position = ggplot2::position_stack(vjust = 0.5), size = 3.5) +
    ggplot2::labs(title = title, fill = "Cell type") +
    ggplot2::theme(plot.title = ggplot2::element_text(hjust = 0.5, face = "bold"))
  if (!is.null(out_path)) safe_ggsave(out_path, p, width = 9, height = 8)
  p
}

plot_celltype_prop_bar <- function(obj, label_col = "celltype", group_col = "group",
                                   title = "", out_path = NULL) {
  setup_plot_fonts()
  df <- obj@meta.data %>%
    tibble::as_tibble() %>%
    dplyr::count(.data[[group_col]], .data[[label_col]], name = "n") %>%
    dplyr::group_by(.data[[group_col]]) %>%
    dplyr::mutate(prop = n / sum(n)) %>% dplyr::ungroup() %>%
    dplyr::rename(group = 1, celltype = 2)
  p <- ggplot2::ggplot(df, ggplot2::aes(x = group, y = prop, fill = celltype)) +
    ggplot2::geom_col(position = "fill", width = 0.65, color = "white", linewidth = 0.3) +
    ggplot2::scale_y_continuous(labels = scales::percent_format()) +
    ggplot2::labs(title = title, x = NULL, y = "Proportion", fill = "Cell type") +
    theme_no_overlap()
  if (!is.null(out_path)) safe_ggsave(out_path, p, width = 10, height = 7)
  p
}

plot_volcano <- function(deg, title = "", out_path = NULL, padj_cut = 0.05, lfc_cut = 1,
                         n_label = 15) {
  setup_plot_fonts()
  fam <- ""
  deg <- deg %>%
    dplyr::mutate(
      padj = pmax(padj, 1e-300),
      significance = dplyr::case_when(
        padj < padj_cut & log2FC > lfc_cut ~ "Up",
        padj < padj_cut & log2FC < -lfc_cut ~ "Down",
        TRUE ~ "NS"
      ))
  lab <- deg %>%
    dplyr::filter(significance != "NS") %>%
    dplyr::group_by(significance) %>%
    dplyr::arrange(padj, dplyr::desc(abs(log2FC)), .by_group = TRUE) %>%
    dplyr::slice_head(n = n_label) %>% dplyr::ungroup()
  n_up <- sum(deg$significance == "Up"); n_dn <- sum(deg$significance == "Down")
  p <- ggplot2::ggplot(deg, ggplot2::aes(x = log2FC, y = -log10(padj), color = significance)) +
    ggplot2::geom_point(alpha = 0.6, size = 1.4) +
    ggplot2::geom_vline(xintercept = c(-lfc_cut, lfc_cut), linetype = 2, color = "grey50", linewidth = 0.3) +
    ggplot2::geom_hline(yintercept = -log10(padj_cut), linetype = 2, color = "grey50", linewidth = 0.3) +
    ggplot2::scale_color_manual(
      values = c(Up = "#E64B35", Down = "#4DBBD5", NS = "grey70"),
      labels = c(Up = paste0("上调 (", n_up, ")"), Down = paste0("下调 (", n_dn, ")"), NS = "无差异"),
      name = NULL) +
    ggplot2::labs(title = title, x = "log2 fold change", y = "-log10(padj)") +
    theme_no_overlap()
  p <- add_ggrepel(p, lab, ggplot2::aes(label = gene), fam = fam, size = 3.2)
  if (!is.null(out_path)) safe_ggsave(out_path, p, width = 10, height = 8)
  p
}

save_all_scrna_figures <- function(obj, dataset, paths, cfg, immune_obj = NULL) {
  fig <- paths$图形
  # 全细胞 UMAP：优先用细胞名，避免数字簇标签
  if ("celltype" %in% colnames(obj@meta.data)) {
    plot_umap_celltype(obj, title = paste(dataset, "UMAP 细胞类型"),
                       out_path = file.path(fig, paste0(dataset, "_UMAP.pdf")))
  } else {
    plot_umap_clusters(obj, title = paste(dataset, "UMAP 聚类"),
                       out_path = file.path(fig, paste0(dataset, "_UMAP.pdf")))
  }
  plot_umap_celltype(obj, title = paste(dataset, "UMAP 细胞类型"),
                     out_path = file.path(fig, paste0(dataset, "_UMAP_细胞类型.pdf")))
  plot_celltype_donut(obj, title = paste(dataset, "细胞比例"),
                      out_path = file.path(fig, paste0(dataset, "_细胞比例环图.pdf")))
  plot_celltype_prop_bar(obj, title = paste(dataset, "分组细胞比例"),
                         out_path = file.path(fig, paste0(dataset, "_分组细胞比例堆叠图.pdf")))
  if (!is.null(immune_obj)) {
    # 免疫亚群：一律用细胞名（immune_lineage），不用数字簇
    plot_umap_by_col(immune_obj, "immune_lineage",
                     title = paste(dataset, "免疫亚群（细胞类型）"),
                     out_path = file.path(fig, paste0(dataset, "_UMAP_免疫聚类.pdf")))
    plot_umap_by_col(immune_obj, "immune_lineage",
                     title = paste(dataset, "免疫谱系（淋巴系+髓系）"),
                     out_path = file.path(fig, paste0(dataset, "_UMAP_免疫谱系.pdf")))
  }
  deg_rds <- file.path(paths$中间数据, paste0(dataset, "_deg.rds"))
  if (file.exists(deg_rds)) {
    deg <- readRDS(deg_rds)
    plot_volcano(deg, title = paste(dataset, "差异基因火山图"),
                 out_path = file.path(fig, paste0(dataset, "_火山图.pdf")),
                 padj_cut = cfg$deg_padj %||% 0.05,
                 lfc_cut = cfg$deg_logfc %||% 1)
  }
}
