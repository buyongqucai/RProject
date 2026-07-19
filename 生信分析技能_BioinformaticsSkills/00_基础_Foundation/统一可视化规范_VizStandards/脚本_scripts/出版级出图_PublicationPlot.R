# 出版级出图：高分期刊多面板风格（journal muted palette）
# 规范源：统一可视化规范_VizStandards
#
# 强制：
# - DPI≥600；同名 SVG+PNG；图面 English only
# - theme_journal()：白底、细轴线、浅灰主网格、无次网格、干净图例
# - 配色：分组 muted 绿/红/紫；发散蓝-白-红；火山 up红/down青绿；富集 ontology 分色
# - 富集默认：水平柱状图 / 气泡点图；Fig3-C 允许棒棒糖 `plot_enrich_lollipop_journal`
# - UMAP 注释：簇心白底标签（Fig3-A）；Feature：灰→深蓝（Fig3-F）
# - GSEA：绿 ES + 红蓝 rank bar + 嵌字 NES/p（Fig2 E–F / Fig3-D）
# - 禁止彩虹、无主题灰糊、用假图顶替外部软件图

FIG_DPI <- 600L
FIG_WIDTH_SINGLE_IN <- 3.5
FIG_WIDTH_DOUBLE_IN <- 7.1
FIG_HEIGHT_DEFAULT_IN <- 3.2

# ---- Palettes (journal muted / reference panel mapping) ----
# Categorical groups (Control / ConditionA / ConditionB / Other…) — soft but distinct
bioinfo_groups <- c(
  Control = "#6B8F71",
  TreatA  = "#C17B7B",
  TreatB  = "#8B7BA8",
  Other   = "#A0A0A0",
  Accent1 = "#D4A574",
  Accent2 = "#5B8FA8"
)
bioinfo_palette <- unname(c(
  bioinfo_groups["Control"], bioinfo_groups["TreatA"], bioinfo_groups["TreatB"],
  bioinfo_groups["Accent1"], bioinfo_groups["Accent2"],
  bioinfo_groups["Other"], "#7A9E9F", "#B8956B"
))

# Legacy NPG-like accents (optional; prefer bioinfo_groups / bioinfo_enrich_facet for new figures)
bioinfo_npg <- c("#E64B35", "#4DBBD5", "#00A087", "#3C5488", "#F39B7F", "#8491B4", "#91D1C2", "#DC0000", "#7E6148", "#B09C85")

# Diverging blue–white–red (heatmap / pathway activity) — keep BWR
bioinfo_diverging_rb <- c("#2166AC", "#67A9CF", "#D1E5F0", "#F7F7F7", "#FDDBC7", "#EF8A62", "#B2182B")
bioinfo_continuous <- c("#2166AC", "#F7F7F7", "#B2182B")

# Sequential (enrichment -log10p, counts)
bioinfo_sequential <- c("#FFF7BC", "#FEC44F", "#D95F0E", "#7F2704")
bioinfo_sequential_blue <- c("#F7FBFF", "#C6DBEF", "#6BAED6", "#2171B5", "#08306B")
# Feature UMAP continuous (Fig3-F): light gray (low) → deep navy (high)
bioinfo_feature_blue <- c("#E8E8E8", "#DEEBF7", "#C6DBEF", "#9ECAE1", "#6BAED6", "#4292C6", "#2171B5", "#08306B")
# GSEA ranking colorbar (Fig2 E–F / Fig3-D): red (high) → blue (low)
bioinfo_gsea_rankbar <- c("#B2182B", "#EF8A62", "#F7F7F7", "#67A9CF", "#2166AC")
# Enrichment lollipop padj gradient (Fig3-C): purple → yellow
bioinfo_enrich_lollipop <- c("#440154", "#3B528B", "#21918C", "#5DC863", "#FDE725")

# Enrichment ontology / database facet colors (GO BP/CC/MF + KEGG)
bioinfo_enrich_facet <- c(
  BP   = "#6B8F71",
  CC   = "#8B7BA8",
  MF   = "#D4A574",
  KEGG = "#5B8FA8"
)

# UMAP / discrete cluster annotation — muted ~8 colors (avoid rainbow)
bioinfo_umap_discrete <- c(
  "#6B8F71", "#C17B7B", "#8B7BA8", "#5B8FA8",
  "#D4A574", "#7A9E9F", "#B8956B", "#A0A0A0",
  "#8B6B5B", "#5B9E8A", "#A87B9E", "#6B9EB8",
  "#C4A35A", "#7B8B6B", "#9E7B6B", "#6B8BA0"
)

# Volcano
bioinfo_volcano <- c(up = "#C0392B", down = "#1A7A6D", ns = "#BDBDBD")

# Survival / risk high-low
bioinfo_survival <- c(high = "#C0392B", low = "#2166AC")

# Network nodes (muted alignment with groups / enrich facet)
bioinfo_network_nodes <- c(
  herb = "#6B8F71", compound = "#C17B7B",
  target = "#5B8FA8", pathway = "#D4A574", other = "#BDBDBD"
)

# Soft pastels for Venn
bioinfo_venn <- c("#8DD3C7", "#FFFFB3", "#BEBADA", "#FB8072", "#80B1D3", "#FDB462", "#B3DE69", "#FCCDE5")

#' Journal panel theme (white, thin axes, light major grid only; soft border)
theme_journal <- function(base_size = 11, base_family = "sans") {
  ggplot2::theme_bw(base_size = base_size, base_family = base_family) +
    ggplot2::theme(
      plot.title = ggplot2::element_text(face = "bold", size = base_size + 1, hjust = 0, margin = ggplot2::margin(b = 6)),
      plot.subtitle = ggplot2::element_text(size = base_size - 1, color = "grey35", hjust = 0, margin = ggplot2::margin(b = 8)),
      axis.title = ggplot2::element_text(size = base_size),
      axis.text = ggplot2::element_text(size = base_size - 1, color = "grey20"),
      panel.grid.major = ggplot2::element_line(color = "grey92", linewidth = 0.25),
      panel.grid.minor = ggplot2::element_blank(),
      panel.border = ggplot2::element_rect(color = "grey82", fill = NA, linewidth = 0.35),
      legend.title = ggplot2::element_text(size = base_size - 1, face = "bold"),
      legend.text = ggplot2::element_text(size = base_size - 2),
      legend.key = ggplot2::element_rect(fill = "white", color = NA),
      legend.background = ggplot2::element_blank(),
      strip.background = ggplot2::element_rect(fill = "grey96", color = "grey85"),
      strip.text = ggplot2::element_text(face = "bold", size = base_size - 1),
      plot.margin = ggplot2::margin(6, 8, 6, 6)
    )
}

setup_cjk_fonts <- function(base_size = 11) {
  # Prefer journal English sans; SimHei only if explicitly needed for CJK in non-figure text contexts
  ggplot2::theme_set(theme_journal(base_size = base_size, base_family = "sans"))
  font_path <- "C:/Windows/Fonts/arial.ttf"
  if (file.exists(font_path) && requireNamespace("sysfonts", quietly = TRUE) &&
      requireNamespace("showtext", quietly = TRUE)) {
    try({
      sysfonts::font_add("ArialPub", font_path)
      showtext::showtext_auto()
      showtext::showtext_opts(dpi = FIG_DPI)
      ggplot2::theme_set(theme_journal(base_size = base_size, base_family = "ArialPub"))
      return("ArialPub")
    }, silent = TRUE)
  }
  "sans"
}

save_plot_pub <- function(plot, stem, width = FIG_WIDTH_SINGLE_IN,
                          height = FIG_HEIGHT_DEFAULT_IN,
                          dpi = FIG_DPI, out_dir = ".", also_pdf = FALSE) {
  setup_cjk_fonts()
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  stem <- sub("\\.(png|svg|pdf)$", "", stem, ignore.case = TRUE)
  fpng <- file.path(out_dir, paste0(stem, ".png"))
  fsvg <- file.path(out_dir, paste0(stem, ".svg"))
  ggplot2::ggsave(fpng, plot, width = width, height = height, dpi = dpi, device = "png", bg = "white")
  ok_svg <- FALSE
  if (requireNamespace("svglite", quietly = TRUE)) {
    try({
      ggplot2::ggsave(fsvg, plot, width = width, height = height, device = svglite::svglite, bg = "white")
      ok_svg <- TRUE
    }, silent = TRUE)
  }
  if (!ok_svg) {
    try({
      grDevices::svg(fsvg, width = width, height = height)
      print(plot)
      grDevices::dev.off()
      ok_svg <- TRUE
    }, silent = TRUE)
  }
  if (also_pdf) {
    ggplot2::ggsave(file.path(out_dir, paste0(stem, ".pdf")), plot, width = width, height = height, device = "pdf")
  }
  invisible(list(png = fpng, svg = if (ok_svg) fsvg else NA_character_))
}

scale_color_bioinfo <- function(...) ggplot2::scale_color_manual(values = bioinfo_palette, ...)
scale_fill_bioinfo <- function(...) ggplot2::scale_fill_manual(values = bioinfo_palette, ...)
scale_color_npg <- function(...) ggplot2::scale_color_manual(values = bioinfo_npg, ...)
scale_fill_npg <- function(...) ggplot2::scale_fill_manual(values = bioinfo_npg, ...)
scale_fill_enrich_facet <- function(...) {
  ggplot2::scale_fill_manual(values = bioinfo_enrich_facet, ...)
}
scale_color_enrich_facet <- function(...) {
  ggplot2::scale_color_manual(values = bioinfo_enrich_facet, ...)
}
scale_color_umap_discrete <- function(...) {
  # Named recycled values avoid ggplot2 "insufficient values" when n_levels > length(palette)
  vals <- setNames(
    rep(bioinfo_umap_discrete, length.out = max(64L, length(bioinfo_umap_discrete))),
    as.character(seq_len(max(64L, length(bioinfo_umap_discrete))))
  )
  ggplot2::scale_color_manual(values = vals, ...)
}
scale_fill_umap_discrete <- function(...) {
  vals <- setNames(
    rep(bioinfo_umap_discrete, length.out = max(64L, length(bioinfo_umap_discrete))),
    as.character(seq_len(max(64L, length(bioinfo_umap_discrete))))
  )
  ggplot2::scale_fill_manual(values = vals, ...)
}

scale_fill_bioinfo_continuous <- function(...) {
  ggplot2::scale_fill_gradient2(
    low = bioinfo_continuous[1], mid = bioinfo_continuous[2], high = bioinfo_continuous[3],
    midpoint = 0, ...
  )
}
scale_color_bioinfo_continuous <- function(...) {
  ggplot2::scale_color_gradient2(
    low = bioinfo_continuous[1], mid = bioinfo_continuous[2], high = bioinfo_continuous[3],
    midpoint = 0, ...
  )
}
scale_fill_bioinfo_sequential <- function(...) {
  ggplot2::scale_fill_gradientn(colours = bioinfo_sequential, ...)
}
scale_color_bioinfo_sequential <- function(...) {
  ggplot2::scale_color_gradientn(colours = bioinfo_sequential, ...)
}
scale_fill_feature_blue <- function(...) {
  ggplot2::scale_fill_gradientn(colours = bioinfo_feature_blue, ...)
}
scale_color_feature_blue <- function(...) {
  ggplot2::scale_color_gradientn(colours = bioinfo_feature_blue, ...)
}
scale_fill_diverging_rb <- function(...) {
  ggplot2::scale_fill_gradientn(colours = bioinfo_diverging_rb, ...)
}

#' Standard volcano colors
scale_color_volcano <- function(...) {
  ggplot2::scale_color_manual(values = bioinfo_volcano, ...)
}

# ---- Thin recipe helpers (enrichment bar/dot first; lollipop not default) ----

#' Horizontal enrichment bar by ontology facet (default enrichment recipe).
#' Expects columns: Description (or term), Count (or gene_count), pvalue/p.adjust, ONTOLOGY/facet.
#' Lollipop is deprecated as default — use this or a bubble/dot plot instead.
plot_enrich_hbar_facet <- function(df,
                                   term_col = "Description",
                                   count_col = "Count",
                                   p_col = "p.adjust",
                                   facet_col = "ONTOLOGY",
                                   top_n = 10,
                                   title = NULL) {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  need <- c(term_col, count_col, p_col, facet_col)
  miss <- setdiff(need, names(df))
  if (length(miss)) stop("Missing columns: ", paste(miss, collapse = ", "))
  d <- as.data.frame(df)
  d$.term <- as.character(d[[term_col]])
  d$.count <- as.numeric(d[[count_col]])
  d$.neglog10 <- -log10(pmax(as.numeric(d[[p_col]]), .Machine$double.xmin))
  d$.facet <- as.character(d[[facet_col]])
  # Top-N per facet
  split_d <- split(d, d$.facet)
  d <- do.call(rbind, lapply(split_d, function(x) {
    x <- x[order(x$.neglog10, decreasing = TRUE), , drop = FALSE]
    utils::head(x, top_n)
  }))
  d$.term <- factor(d$.term, levels = rev(unique(d$.term)))
  fill_vals <- bioinfo_enrich_facet
  # Map common aliases
  facet_map <- c(BP = "BP", `biological_process` = "BP", `Biological Process` = "BP",
                 CC = "CC", `cellular_component` = "CC", `Cellular Component` = "CC",
                 MF = "MF", `molecular_function` = "MF", `Molecular Function` = "MF",
                 KEGG = "KEGG")
  d$.fill_key <- ifelse(d$.facet %in% names(facet_map), facet_map[d$.facet], d$.facet)
  ggplot2::ggplot(d, ggplot2::aes(x = .neglog10, y = .term, fill = .fill_key)) +
    ggplot2::geom_col(width = 0.72, color = NA) +
    ggplot2::facet_wrap(~ .facet, scales = "free_y", ncol = 1) +
    ggplot2::scale_fill_manual(values = fill_vals, guide = "none", na.value = bioinfo_groups[["Other"]]) +
    ggplot2::labs(
      x = expression(-log[10](adjusted~italic(P))),
      y = NULL,
      title = title
    ) +
    theme_journal()
}

#' Journal volcano: expects columns gene, logFC, pvalue (or padj); optional label_genes.
plot_volcano_journal <- function(df,
                                 gene_col = "gene",
                                 logfc_col = "logFC",
                                 p_col = "adj.P.Val",
                                 logfc_cut = 1,
                                 p_cut = 0.05,
                                 label_n = 12,
                                 title = "Volcano") {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  need <- c(gene_col, logfc_col, p_col)
  miss <- setdiff(need, names(df))
  if (length(miss)) stop("Missing columns: ", paste(miss, collapse = ", "))
  d <- as.data.frame(df)
  d$.gene <- as.character(d[[gene_col]])
  d$.logfc <- as.numeric(d[[logfc_col]])
  d$.p <- pmax(as.numeric(d[[p_col]]), .Machine$double.xmin)
  d$.neglog10 <- -log10(d$.p)
  d$.class <- ifelse(d$.p < p_cut & d$.logfc >= logfc_cut, "up",
                     ifelse(d$.p < p_cut & d$.logfc <= -logfc_cut, "down", "ns"))
  d$.class <- factor(d$.class, levels = c("up", "down", "ns"))
  # Top labels by significance among DE
  de <- d[d$.class %in% c("up", "down"), , drop = FALSE]
  de <- de[order(de$.neglog10, decreasing = TRUE), , drop = FALSE]
  label_set <- utils::head(de$.gene, label_n)
  d$.lab <- ifelse(d$.gene %in% label_set, d$.gene, NA_character_)
  p <- ggplot2::ggplot(d, ggplot2::aes(x = .logfc, y = .neglog10, color = .class)) +
    ggplot2::geom_point(size = 1.1, alpha = 0.75) +
    ggplot2::scale_color_manual(values = bioinfo_volcano, name = NULL) +
    ggplot2::geom_vline(xintercept = c(-logfc_cut, logfc_cut), linetype = 2, color = "grey55", linewidth = 0.3) +
    ggplot2::geom_hline(yintercept = -log10(p_cut), linetype = 2, color = "grey55", linewidth = 0.3) +
    ggplot2::labs(x = expression(log[2]~fold~change), y = expression(-log[10]~adjusted~italic(P)), title = title) +
    theme_journal()
  if (requireNamespace("ggrepel", quietly = TRUE) && any(!is.na(d$.lab))) {
    p <- p + ggrepel::geom_text_repel(
      data = d[!is.na(d$.lab), , drop = FALSE],
      ggplot2::aes(label = .lab),
      size = 2.8, max.overlaps = 20, segment.size = 0.2, show.legend = FALSE
    )
  }
  p
}

#' Multi-panel letter (Fig1 a–j / Fig2 A–J style). Place with annotation_custom or cowplot.
annotate_panel_letter <- function(letter = "A", size = 14, face = "bold") {
  ggplot2::annotate(
    "text", x = -Inf, y = Inf, label = as.character(letter),
    hjust = -0.2, vjust = 1.4, size = size / ggplot2::.pt, fontface = face
  )
}

#' PCA scatter with journal group colors (Fig1-b / GEO QC).
#' Expects columns: PC1, PC2, group (or pass group_col).
plot_pca_journal <- function(df,
                             pc1_col = "PC1",
                             pc2_col = "PC2",
                             group_col = "group",
                             title = "PCA",
                             palette = NULL) {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  need <- c(pc1_col, pc2_col, group_col)
  miss <- setdiff(need, names(df))
  if (length(miss)) stop("Missing columns: ", paste(miss, collapse = ", "))
  d <- as.data.frame(df)
  d$.pc1 <- as.numeric(d[[pc1_col]])
  d$.pc2 <- as.numeric(d[[pc2_col]])
  d$.grp <- as.factor(d[[group_col]])
  nlev <- nlevels(d$.grp)
  cols <- palette
  if (is.null(cols)) {
    base_cols <- unname(c(
      bioinfo_groups["Control"], bioinfo_groups["TreatA"], bioinfo_groups["TreatB"],
      bioinfo_groups["Accent1"], bioinfo_groups["Accent2"], bioinfo_groups["Other"]
    ))
    cols <- setNames(rep(base_cols, length.out = nlev), levels(d$.grp))
  }
  ggplot2::ggplot(d, ggplot2::aes(x = .pc1, y = .pc2, color = .grp)) +
    ggplot2::geom_point(size = 2.4, alpha = 0.9) +
    ggplot2::scale_color_manual(values = cols, name = NULL) +
    ggplot2::labs(x = pc1_col, y = pc2_col, title = title) +
    theme_journal()
}

#' Enrichment bubble/dot (Fig3-C / Fig2 enrichment family). Prefer over lollipop.
plot_enrich_dot_journal <- function(df,
                                    term_col = "Description",
                                    count_col = "Count",
                                    p_col = "p.adjust",
                                    top_n = 15,
                                    title = NULL) {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  need <- c(term_col, count_col, p_col)
  miss <- setdiff(need, names(df))
  if (length(miss)) stop("Missing columns: ", paste(miss, collapse = ", "))
  d <- as.data.frame(df)
  d$.term <- as.character(d[[term_col]])
  d$.count <- as.numeric(d[[count_col]])
  d$.neglog10 <- -log10(pmax(as.numeric(d[[p_col]]), .Machine$double.xmin))
  d <- d[order(d$.neglog10, decreasing = TRUE), , drop = FALSE]
  d <- utils::head(d, top_n)
  d$.term <- factor(d$.term, levels = rev(unique(d$.term)))
  ggplot2::ggplot(d, ggplot2::aes(x = .neglog10, y = .term, size = .count, color = .neglog10)) +
    ggplot2::geom_point(alpha = 0.9) +
    ggplot2::scale_color_gradientn(colours = bioinfo_sequential_blue, name = expression(-log[10]~italic(P)[adj])) +
    ggplot2::scale_size_continuous(name = "Count", range = c(2.5, 8)) +
    ggplot2::labs(
      x = expression(-log[10]~adjusted~italic(P)),
      y = NULL,
      title = title
    ) +
    theme_journal()
}

#' Box + jitter + optional pairwise p labels (Fig1 g–j / Fig2-D style).
#' df: value_col, group_col; optional pairwise_p data.frame(group1, group2, p.label).
plot_box_jitter_journal <- function(df,
                                    value_col = "value",
                                    group_col = "group",
                                    title = NULL,
                                    ylab = "Score",
                                    palette = NULL,
                                    seed = 1L) {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  need <- c(value_col, group_col)
  miss <- setdiff(need, names(df))
  if (length(miss)) stop("Missing columns: ", paste(miss, collapse = ", "))
  d <- as.data.frame(df)
  d$.val <- as.numeric(d[[value_col]])
  d$.grp <- as.factor(d[[group_col]])
  nlev <- nlevels(d$.grp)
  cols <- palette
  if (is.null(cols)) {
    base_cols <- unname(c(
      bioinfo_groups["Control"], bioinfo_groups["TreatA"], bioinfo_groups["TreatB"],
      bioinfo_groups["Other"], bioinfo_groups["Accent1"], bioinfo_groups["Accent2"]
    ))
    cols <- setNames(rep(base_cols, length.out = nlev), levels(d$.grp))
  }
  set.seed(seed)
  ggplot2::ggplot(d, ggplot2::aes(x = .grp, y = .val, fill = .grp)) +
    ggplot2::geom_boxplot(width = 0.55, outlier.shape = NA, alpha = 0.55, color = "grey35") +
    ggplot2::geom_jitter(width = 0.12, height = 0, size = 1.4, alpha = 0.75, color = "grey25") +
    ggplot2::scale_fill_manual(values = cols, guide = "none") +
    ggplot2::labs(x = NULL, y = ylab, title = title) +
    theme_journal()
}

#' Kaplan–Meier with number-at-risk when survminer available (Fig2 G–J / Fig3-H).
#' Returns a ggsurvplot object if survminer+survival present; else a simple step ggplot.
plot_km_journal <- function(time,
                            event,
                            group,
                            xlab = "Time",
                            ylab = "Survival probability",
                            title = NULL,
                            conf.int = TRUE) {
  g <- as.factor(group)
  cols <- c(
    unname(bioinfo_survival["high"]),
    unname(bioinfo_survival["low"]),
    unname(bioinfo_groups["Other"])
  )
  cols <- setNames(rep(cols, length.out = nlevels(g)), levels(g))
  if (requireNamespace("survival", quietly = TRUE) && requireNamespace("survminer", quietly = TRUE)) {
    df <- data.frame(time = as.numeric(time), event = as.numeric(event), group = g)
    fit <- survival::survfit(survival::Surv(time, event) ~ group, data = df)
    return(survminer::ggsurvplot(
      fit, data = df, palette = unname(cols[levels(g)]),
      conf.int = conf.int, pval = TRUE, risk.table = TRUE,
      legend.title = "", xlab = xlab, ylab = ylab, title = title,
      ggtheme = theme_journal()
    ))
  }
  # Fallback: no risk table (caller should prefer survminer for journal KM)
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  ord <- order(as.numeric(time))
  d <- data.frame(
    time = as.numeric(time)[ord],
    event = as.numeric(event)[ord],
    group = g[ord]
  )
  ggplot2::ggplot(d, ggplot2::aes(x = time, color = group)) +
    ggplot2::geom_step(ggplot2::aes(y = 1 - (cumsum(event) / seq_along(event))), linewidth = 0.8) +
    ggplot2::scale_color_manual(values = cols, name = NULL) +
    ggplot2::labs(x = xlab, y = ylab, title = title,
                  subtitle = "Install survival+survminer for KM + risk table") +
    theme_journal()
}

#' Discrete UMAP (Fig3-A/B). Expects umap_1, umap_2, label columns.
#' Fig3-A style: white-backed cluster labels on centroids; legend optional.
plot_umap_discrete_journal <- function(df,
                                       x_col = "umap_1",
                                       y_col = "umap_2",
                                       label_col = "celltype",
                                       title = "UMAP",
                                       point_size = 0.35,
                                       palette = NULL,
                                       label_on_plot = TRUE,
                                       show_legend = NULL,
                                       label_size = 3.2,
                                       label_max = 20L) {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  need <- c(x_col, y_col, label_col)
  miss <- setdiff(need, names(df))
  if (length(miss)) stop("Missing columns: ", paste(miss, collapse = ", "))
  d <- as.data.frame(df)
  d$.x <- as.numeric(d[[x_col]])
  d$.y <- as.numeric(d[[y_col]])
  d$.lab <- as.factor(d[[label_col]])
  nlev <- nlevels(d$.lab)
  cols <- palette
  if (is.null(cols)) {
    cols <- setNames(rep(bioinfo_umap_discrete, length.out = nlev), levels(d$.lab))
  } else if (is.null(names(cols))) {
    cols <- setNames(rep(cols, length.out = nlev), levels(d$.lab))
  }
  if (is.null(show_legend)) show_legend <- !isTRUE(label_on_plot)
  p <- ggplot2::ggplot(d, ggplot2::aes(x = .x, y = .y, color = .lab)) +
    ggplot2::geom_point(size = point_size, alpha = 0.85) +
    ggplot2::scale_color_manual(values = cols, name = NULL, guide = if (show_legend) "legend" else "none") +
    ggplot2::coord_fixed() +
    ggplot2::labs(x = "UMAP_1", y = "UMAP_2", title = title) +
    theme_journal() +
    ggplot2::theme(panel.grid = ggplot2::element_blank())
  if (isTRUE(label_on_plot) && nlev >= 1L && nlev <= as.integer(label_max)) {
    cent <- stats::aggregate(cbind(.x, .y) ~ .lab, data = d, FUN = stats::median)
    names(cent)[1] <- "lab"
    if (requireNamespace("ggrepel", quietly = TRUE)) {
      p <- p + ggrepel::geom_label_repel(
        data = cent,
        ggplot2::aes(x = .x, y = .y, label = lab),
        inherit.aes = FALSE,
        size = label_size,
        fill = "white",
        color = "grey15",
        label.size = 0.15,
        label.padding = ggplot2::unit(0.15, "lines"),
        box.padding = 0.35,
        point.padding = 0.2,
        min.segment.length = 0,
        segment.color = "grey60",
        segment.size = 0.25,
        max.overlaps = Inf,
        seed = 1L
      )
    } else {
      p <- p + ggplot2::geom_label(
        data = cent,
        ggplot2::aes(x = .x, y = .y, label = lab),
        inherit.aes = FALSE,
        size = label_size,
        fill = "white",
        color = "grey15",
        label.size = 0.15,
        label.padding = ggplot2::unit(0.15, "lines")
      )
    }
  }
  p
}

# =============================================================================
# Journal supplement recipes (Fig1–3 gaps): GSEA classic, feature UMAP, stacked
# proportions, KM+risk table, box brackets, paired boxes, severity trend,
# sample dendrogram, pathway activity heatmap, PC density+box.
# NetworkPharmacology visuals remain FROZEN — do not restyle here for NetPharm.
# =============================================================================

#' Running enrichment score (classic GSEA) from ranked metric + hit genes.
#' @param ranked_metric named numeric (names = genes), high→low preferred
#' @param gene_set character gene IDs intersecting names(ranked_metric)
#' @return list(es_df, hits_df, metric_df, nes_proxy, peak_es)
compute_gsea_running_es <- function(ranked_metric, gene_set) {
  stopifnot(length(ranked_metric) > 1L, !is.null(names(ranked_metric)))
  ord <- order(as.numeric(ranked_metric), decreasing = TRUE, na.last = TRUE)
  metric <- as.numeric(ranked_metric)[ord]
  genes <- names(ranked_metric)[ord]
  hit <- genes %in% unique(as.character(gene_set))
  N <- length(genes)
  Nh <- sum(hit)
  Nm <- N - Nh
  if (Nh < 1L || Nm < 1L) {
    stop("gene_set must overlap ranked list with both hits and misses", call. = FALSE)
  }
  abs_m <- abs(metric)
  hit_w <- ifelse(hit, abs_m, 0)
  sum_hit <- sum(hit_w)
  if (sum_hit <= 0) hit_w <- ifelse(hit, 1, 0)
  sum_hit <- sum(hit_w)
  step_hit <- hit_w / sum_hit
  step_miss <- ifelse(hit, 0, 1 / Nm)
  running <- cumsum(step_hit - step_miss)
  peak_es <- running[which.max(abs(running))]
  list(
    es_df = data.frame(rank = seq_len(N), ES = running, stringsAsFactors = FALSE),
    hits_df = data.frame(rank = which(hit), stringsAsFactors = FALSE),
    metric_df = data.frame(rank = seq_len(N), metric = metric, stringsAsFactors = FALSE),
    peak_es = peak_es,
    n_hit = Nh,
    n_total = N
  )
}

#' Classic GSEA panel (Fig2 E–F / Fig3-D): ES + barcode + red–blue rank bar + metric.
#' Optional inset stats (NES / pvalue / p.adjust) like journal enrichplot panels.
plot_gsea_classic_journal <- function(ranked_metric = NULL,
                                      gene_set = NULL,
                                      es_df = NULL,
                                      hits_df = NULL,
                                      metric_df = NULL,
                                      title = NULL,
                                      subtitle = NULL,
                                      es_color = "#1B7A4A",
                                      nes = NULL,
                                      pvalue = NULL,
                                      p.adjust = NULL,
                                      show_rankbar = TRUE) {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  peak_es <- NA_real_
  n_hit <- NA_integer_
  n_total <- NA_integer_
  if (is.null(es_df)) {
    g <- compute_gsea_running_es(ranked_metric, gene_set)
    es_df <- g$es_df
    hits_df <- g$hits_df
    metric_df <- g$metric_df
    peak_es <- g$peak_es
    n_hit <- g$n_hit
    n_total <- g$n_total
    if (is.null(subtitle)) {
      subtitle <- sprintf("Peak ES = %.3f; hits = %d / %d", peak_es, n_hit, n_total)
    }
  }
  es_df <- as.data.frame(es_df)
  hits_df <- as.data.frame(hits_df)
  metric_df <- as.data.frame(metric_df)
  n_rank <- max(es_df$rank, na.rm = TRUE)

  # Inset stats table (Fig3-D)
  stats_lines <- character(0)
  if (!is.null(nes) && is.finite(as.numeric(nes)[1])) {
    stats_lines <- c(stats_lines, sprintf("NES = %.3f", as.numeric(nes)[1]))
  } else if (is.finite(peak_es)) {
    stats_lines <- c(stats_lines, sprintf("ES = %.3f", peak_es))
  }
  if (!is.null(pvalue) && is.finite(as.numeric(pvalue)[1])) {
    stats_lines <- c(stats_lines, sprintf("pvalue = %.4g", as.numeric(pvalue)[1]))
  }
  if (!is.null(p.adjust) && is.finite(as.numeric(p.adjust)[1])) {
    stats_lines <- c(stats_lines, sprintf("p.adjust = %.4g", as.numeric(p.adjust)[1]))
  }

  p_es <- ggplot2::ggplot(es_df, ggplot2::aes(x = rank, y = ES)) +
    ggplot2::geom_hline(yintercept = 0, color = "grey55", linewidth = 0.3) +
    ggplot2::geom_line(color = es_color, linewidth = 0.85) +
    ggplot2::labs(x = NULL, y = "Enrichment score", title = title, subtitle = subtitle) +
    theme_journal() +
    ggplot2::theme(
      axis.text.x = ggplot2::element_blank(),
      axis.ticks.x = ggplot2::element_blank(),
      panel.grid.minor = ggplot2::element_blank()
    )
  if (length(stats_lines)) {
    yr <- range(es_df$ES, na.rm = TRUE)
    p_es <- p_es + ggplot2::annotate(
      "label",
      x = n_rank * 0.98,
      y = yr[1] + diff(yr) * 0.08,
      label = paste(stats_lines, collapse = "\n"),
      hjust = 1, vjust = 0,
      size = 3.0,
      fill = "white",
      color = "grey20",
      label.padding = ggplot2::unit(0.25, "lines")
    )
  }

  p_bar <- ggplot2::ggplot(hits_df, ggplot2::aes(x = rank, xend = rank, y = 0, yend = 1)) +
    ggplot2::geom_segment(color = "grey15", linewidth = 0.4) +
    ggplot2::scale_y_continuous(limits = c(0, 1), expand = c(0, 0)) +
    ggplot2::scale_x_continuous(limits = c(1, n_rank), expand = c(0.01, 0)) +
    ggplot2::labs(x = NULL, y = NULL) +
    theme_journal() +
    ggplot2::theme(
      axis.text = ggplot2::element_blank(),
      axis.ticks = ggplot2::element_blank(),
      panel.grid = ggplot2::element_blank(),
      plot.margin = ggplot2::margin(0, 8, 0, 6)
    )

  # Red→blue rank colorbar under barcode (Fig2/Fig3)
  bar_df <- data.frame(rank = seq_len(n_rank), y = 1)
  p_rank <- ggplot2::ggplot(bar_df, ggplot2::aes(x = rank, y = y, fill = rank)) +
    ggplot2::geom_tile(height = 1, width = 1) +
    ggplot2::scale_fill_gradientn(colours = bioinfo_gsea_rankbar, guide = "none") +
    ggplot2::scale_x_continuous(limits = c(1, n_rank), expand = c(0.01, 0)) +
    ggplot2::scale_y_continuous(expand = c(0, 0)) +
    ggplot2::labs(x = NULL, y = NULL) +
    theme_journal() +
    ggplot2::theme(
      axis.text = ggplot2::element_blank(),
      axis.ticks = ggplot2::element_blank(),
      panel.grid = ggplot2::element_blank(),
      panel.border = ggplot2::element_blank(),
      plot.margin = ggplot2::margin(0, 8, 0, 6)
    )

  p_met <- ggplot2::ggplot(metric_df, ggplot2::aes(x = rank, y = metric)) +
    ggplot2::geom_area(fill = "grey70", color = NA, alpha = 0.95) +
    ggplot2::geom_hline(yintercept = 0, color = "grey40", linewidth = 0.25) +
    ggplot2::labs(x = "Rank in ordered gene list", y = "Ranked metric") +
    theme_journal()

  if (!isTRUE(show_rankbar)) {
    if (requireNamespace("patchwork", quietly = TRUE)) {
      return(p_es / p_bar / p_met + patchwork::plot_layout(heights = c(2.4, 0.4, 1)))
    }
    if (requireNamespace("cowplot", quietly = TRUE)) {
      return(cowplot::plot_grid(p_es, p_bar, p_met, ncol = 1, rel_heights = c(2.4, 0.4, 1), align = "v"))
    }
    return(p_es)
  }
  if (requireNamespace("patchwork", quietly = TRUE)) {
    return(p_es / p_bar / p_rank / p_met + patchwork::plot_layout(heights = c(2.4, 0.35, 0.18, 1)))
  }
  if (requireNamespace("cowplot", quietly = TRUE)) {
    return(cowplot::plot_grid(
      p_es, p_bar, p_rank, p_met, ncol = 1,
      rel_heights = c(2.4, 0.35, 0.18, 1), align = "v"
    ))
  }
  p_es
}

#' Enrichment lollipop (Fig3-C): stem + sized/colored head by Count × padj.
#' Allowed when matching user journal reference Fig3-C; bar/dot remain defaults elsewhere.
plot_enrich_lollipop_journal <- function(df,
                                         term_col = "Description",
                                         count_col = "Count",
                                         p_col = "p.adjust",
                                         top_n = 15,
                                         title = NULL) {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  need <- c(term_col, count_col, p_col)
  miss <- setdiff(need, names(df))
  if (length(miss)) stop("Missing columns: ", paste(miss, collapse = ", "))
  d <- as.data.frame(df)
  d$.term <- as.character(d[[term_col]])
  d$.count <- as.numeric(d[[count_col]])
  d$.padj <- as.numeric(d[[p_col]])
  d$.neglog10 <- -log10(pmax(d$.padj, .Machine$double.xmin))
  d <- d[order(d$.neglog10, decreasing = TRUE), , drop = FALSE]
  d <- utils::head(d, top_n)
  d$.term <- factor(d$.term, levels = rev(unique(d$.term)))
  ggplot2::ggplot(d, ggplot2::aes(x = .neglog10, y = .term)) +
    ggplot2::geom_segment(
      ggplot2::aes(x = 0, xend = .neglog10, y = .term, yend = .term),
      color = "grey55", linewidth = 0.55
    ) +
    ggplot2::geom_point(ggplot2::aes(size = .count, color = .padj), alpha = 0.95) +
    ggplot2::scale_color_gradientn(
      colours = bioinfo_enrich_lollipop,
      name = "p.adjust",
      trans = "log10",
      guide = ggplot2::guide_colorbar(reverse = TRUE)
    ) +
    ggplot2::scale_size_continuous(name = "Count", range = c(3, 9)) +
    ggplot2::labs(
      x = expression(-log[10]~italic(P)[adjust]),
      y = NULL,
      title = title
    ) +
    theme_journal()
}

#' Feature / continuous UMAP (Fig3-F). Low = light gray; high = deep navy.
plot_umap_feature_journal <- function(df,
                                      x_col = "umap_1",
                                      y_col = "umap_2",
                                      feature_col = "score",
                                      title = "Feature plot",
                                      point_size = 0.4,
                                      legend_name = "Score") {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  need <- c(x_col, y_col, feature_col)
  miss <- setdiff(need, names(df))
  if (length(miss)) stop("Missing columns: ", paste(miss, collapse = ", "))
  d <- as.data.frame(df)
  d$.x <- as.numeric(d[[x_col]])
  d$.y <- as.numeric(d[[y_col]])
  d$.f <- as.numeric(d[[feature_col]])
  # plot low first so high scores sit on top (Fig3-F)
  d <- d[order(d$.f, na.last = FALSE), , drop = FALSE]
  ggplot2::ggplot(d, ggplot2::aes(x = .x, y = .y, color = .f)) +
    ggplot2::geom_point(size = point_size, alpha = 0.92) +
    scale_color_feature_blue(name = legend_name) +
    ggplot2::coord_fixed() +
    ggplot2::labs(x = "UMAP_1", y = "UMAP_2", title = title) +
    theme_journal() +
    ggplot2::theme(panel.grid = ggplot2::element_blank())
}

#' Stacked cell-proportion bars (Fig3-G). Long df: sample, celltype, proportion.
#' Optional facet_col (e.g. risk group). Uses High/Low red–blue when 2–3 META-like states.
plot_stacked_proportion_journal <- function(df,
                                            sample_col = "sample",
                                            celltype_col = "celltype",
                                            prop_col = "proportion",
                                            facet_col = NULL,
                                            title = "Cell proportions",
                                            palette = NULL) {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  need <- c(sample_col, celltype_col, prop_col)
  miss <- setdiff(need, names(df))
  if (length(miss)) stop("Missing columns: ", paste(miss, collapse = ", "))
  d <- as.data.frame(df)
  d$.sample <- as.factor(d[[sample_col]])
  d$.ct <- as.factor(d[[celltype_col]])
  d$.prop <- as.numeric(d[[prop_col]])
  nlev <- nlevels(d$.ct)
  cols <- palette
  if (is.null(cols)) {
    labs <- levels(d$.ct)
    # Fig3-G META Activate / Silence / Non_Malignant style
    meta_like <- grepl("activate|silence|non.?malig|risk.?high|risk.?low", labs, ignore.case = TRUE)
    if (nlev <= 3L && any(meta_like)) {
      base <- c(
        unname(bioinfo_survival["high"]),
        unname(bioinfo_survival["low"]),
        "#B8D4E8"
      )
      cols <- setNames(rep(base, length.out = nlev), labs)
    } else {
      cols <- setNames(rep(bioinfo_umap_discrete, length.out = nlev), labs)
    }
  }
  build_p <- function(dat, facet = NULL) {
    p0 <- ggplot2::ggplot(dat, ggplot2::aes(x = .sample, y = .prop, fill = .ct)) +
      ggplot2::geom_col(width = 0.92, color = NA) +
      ggplot2::scale_fill_manual(values = cols, name = NULL) +
      ggplot2::scale_y_continuous(expand = c(0, 0), limits = c(0, 1.0),
                                  name = "Estimated Proportion") +
      ggplot2::labs(x = NULL, title = title) +
      theme_journal() +
      ggplot2::theme(
        axis.text.x = ggplot2::element_blank(),
        axis.ticks.x = ggplot2::element_blank(),
        panel.grid.major.x = ggplot2::element_blank()
      )
    if (!is.null(facet) && facet %in% names(dat)) {
      dat$.facet <- as.factor(dat[[facet]])
      p0 <- ggplot2::ggplot(dat, ggplot2::aes(x = .sample, y = .prop, fill = .ct)) +
        ggplot2::geom_col(width = 0.92, color = NA) +
        ggplot2::facet_grid(~ .facet, scales = "free_x", space = "free_x") +
        ggplot2::scale_fill_manual(values = cols, name = NULL) +
        ggplot2::scale_y_continuous(expand = c(0, 0), limits = c(0, 1.0),
                                    name = "Estimated Proportion") +
        ggplot2::labs(x = NULL, title = title) +
        theme_journal() +
        ggplot2::theme(
          axis.text.x = ggplot2::element_blank(),
          axis.ticks.x = ggplot2::element_blank(),
          panel.grid.major.x = ggplot2::element_blank()
        )
    }
    p0
  }
  build_p(d, facet_col)
}

#' Format p-values for brackets (ns / * / ** / *** or exact).
.format_p_label <- function(p, stars = TRUE) {
  p <- as.numeric(p)
  out <- character(length(p))
  for (i in seq_along(p)) {
    if (is.na(p[i])) {
      out[i] <- "NA"
    } else if (!stars) {
      out[i] <- sprintf("p = %.3g", p[i])
    } else if (p[i] < 0.001) {
      out[i] <- "***"
    } else if (p[i] < 0.01) {
      out[i] <- "**"
    } else if (p[i] < 0.05) {
      out[i] <- "*"
    } else {
      out[i] <- "ns"
    }
  }
  out
}

#' KM + number-at-risk + log-rank p (+ optional 95% CI). Returns patchwork/cowplot
#' or survminer ggsurvplot; prefer combined ggplot for delivery_save_plot.
plot_km_risk_table_journal <- function(time,
                                       event,
                                       group,
                                       xlab = "Time",
                                       ylab = "Survival probability",
                                       title = NULL,
                                       conf.int = TRUE,
                                       risk_table = TRUE,
                                       palette = NULL) {
  g <- as.factor(group)
  cols <- palette
  if (is.null(cols)) {
    base_cols <- unname(c(
      bioinfo_survival["high"], bioinfo_survival["low"],
      bioinfo_groups["Other"], bioinfo_groups["Accent1"]
    ))
    cols <- setNames(rep(base_cols, length.out = nlevels(g)), levels(g))
  }
  # Prefer ggplot+risk-table for delivery_save_plot; set
  # options(bioinfo.km.use_survminer = TRUE) for classic ggsurvplot.
  use_survminer <- isTRUE(getOption("bioinfo.km.use_survminer", FALSE))
  if (use_survminer &&
      requireNamespace("survival", quietly = TRUE) &&
      requireNamespace("survminer", quietly = TRUE)) {
    df <- data.frame(time = as.numeric(time), event = as.numeric(event), group = g)
    fit <- survival::survfit(survival::Surv(time, event) ~ group, data = df)
    return(survminer::ggsurvplot(
      fit, data = df, palette = unname(cols[levels(g)]),
      conf.int = conf.int, pval = TRUE, risk.table = risk_table,
      legend.title = "", xlab = xlab, ylab = ylab, title = title,
      ggtheme = theme_journal(), tables.theme = theme_journal()
    ))
  }
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  if (!requireNamespace("survival", quietly = TRUE)) {
    stop("survival package required for plot_km_risk_table_journal", call. = FALSE)
  }
  df <- data.frame(time = as.numeric(time), event = as.numeric(event), group = g)
  fit <- survival::survfit(survival::Surv(time, event) ~ group, data = df)
  sdf <- data.frame(
    time = fit$time,
    surv = fit$surv,
    lower = fit$lower,
    upper = fit$upper,
    n.risk = fit$n.risk,
    group = rep(names(fit$strata), fit$strata),
    stringsAsFactors = FALSE
  )
  # strip "group=" prefix from strata names
  sdf$group <- sub("^group=", "", sdf$group)
  sdf$group <- factor(sdf$group, levels = levels(g))
  # log-rank
  sd <- survival::survdiff(survival::Surv(time, event) ~ group, data = df)
  pval <- 1 - stats::pchisq(sd$chisq, length(sd$n) - 1)
  p_lab <- sprintf("Log-rank p = %.3g", pval)
  p_km <- ggplot2::ggplot(sdf, ggplot2::aes(x = time, y = surv, color = group)) +
    ggplot2::geom_step(linewidth = 0.85)
  if (isTRUE(conf.int)) {
    p_km <- p_km +
      ggplot2::geom_ribbon(
        ggplot2::aes(ymin = lower, ymax = upper, fill = group),
        alpha = 0.12, color = NA, show.legend = FALSE
      ) +
      ggplot2::scale_fill_manual(values = cols, guide = "none")
  }
  p_km <- p_km +
    ggplot2::scale_color_manual(values = cols, name = NULL) +
    ggplot2::coord_cartesian(ylim = c(0, 1)) +
    ggplot2::annotate("text", x = Inf, y = Inf, label = p_lab, hjust = 1.05, vjust = 1.4, size = 3.2) +
    ggplot2::labs(x = if (risk_table) NULL else xlab, y = ylab, title = title) +
    theme_journal()
  if (!risk_table) return(p_km)
  # Risk table at selected times
  breaks <- pretty(range(df$time, na.rm = TRUE), n = 5)
  rt_rows <- lapply(levels(g), function(lev) {
    sub <- df[df$group == lev, , drop = FALSE]
    n_at <- vapply(breaks, function(t0) sum(sub$time >= t0), integer(1))
    data.frame(time = breaks, n = n_at, group = lev, stringsAsFactors = FALSE)
  })
  rt <- do.call(rbind, rt_rows)
  rt$group <- factor(rt$group, levels = levels(g))
  p_rt <- ggplot2::ggplot(rt, ggplot2::aes(x = time, y = group, label = n, color = group)) +
    ggplot2::geom_text(size = 3.1, show.legend = FALSE) +
    ggplot2::scale_color_manual(values = cols, guide = "none") +
    ggplot2::scale_x_continuous(limits = range(c(0, df$time), na.rm = TRUE)) +
    ggplot2::labs(x = xlab, y = "Number at risk") +
    theme_journal() +
    ggplot2::theme(panel.grid = ggplot2::element_blank())
  if (requireNamespace("patchwork", quietly = TRUE)) {
    return(p_km / p_rt + patchwork::plot_layout(heights = c(3, 1)))
  }
  if (requireNamespace("cowplot", quietly = TRUE)) {
    return(cowplot::plot_grid(p_km, p_rt, ncol = 1, rel_heights = c(3, 1), align = "v"))
  }
  p_km
}

#' Save KM objects that may be ggsurvplot / patchwork / ggplot.
save_km_journal <- function(km_obj, stem, width = 6.5, height = 6.2,
                            dpi = FIG_DPI, out_dir = ".") {
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  stem <- sub("\\.(png|svg|pdf)$", "", stem, ignore.case = TRUE)
  fpng <- file.path(out_dir, paste0(stem, ".png"))
  fsvg <- file.path(out_dir, paste0(stem, ".svg"))
  is_ggsurv <- inherits(km_obj, "ggsurvplot") ||
    (is.list(km_obj) && !is.null(km_obj$plot) && inherits(km_obj$plot, "ggplot"))
  if (is_ggsurv) {
    grDevices::png(fpng, width = width, height = height, units = "in", res = dpi)
    print(km_obj)
    grDevices::dev.off()
    try({
      grDevices::svg(fsvg, width = width, height = height)
      print(km_obj)
      grDevices::dev.off()
    }, silent = TRUE)
    return(invisible(list(png = fpng, svg = fsvg)))
  }
  save_plot_pub(km_obj, stem = stem, width = width, height = height, dpi = dpi, out_dir = out_dir)
}

#' Box + jitter + significance brackets (Fig1 g–j).
#' comparisons: list of c("A","B") or data.frame(group1, group2, p / p.label).
plot_box_bracket_journal <- function(df,
                                     value_col = "value",
                                     group_col = "group",
                                     comparisons = NULL,
                                     title = NULL,
                                     ylab = "Score",
                                     palette = NULL,
                                     stars = TRUE,
                                     seed = 1L) {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  need <- c(value_col, group_col)
  miss <- setdiff(need, names(df))
  if (length(miss)) stop("Missing columns: ", paste(miss, collapse = ", "))
  d <- as.data.frame(df)
  d$.val <- as.numeric(d[[value_col]])
  d$.grp <- as.factor(d[[group_col]])
  nlev <- nlevels(d$.grp)
  cols <- palette
  if (is.null(cols)) {
    base_cols <- unname(c(
      bioinfo_groups["Control"], bioinfo_groups["TreatA"], bioinfo_groups["TreatB"],
      bioinfo_groups["Other"], bioinfo_groups["Accent1"], bioinfo_groups["Accent2"]
    ))
    cols <- setNames(rep(base_cols, length.out = nlev), levels(d$.grp))
  }
  set.seed(seed)
  p <- ggplot2::ggplot(d, ggplot2::aes(x = .grp, y = .val, fill = .grp)) +
    ggplot2::geom_boxplot(width = 0.55, outlier.shape = NA, alpha = 0.55, color = "grey35") +
    ggplot2::geom_jitter(width = 0.12, height = 0, size = 1.4, alpha = 0.75, color = "grey25") +
    ggplot2::scale_fill_manual(values = cols, guide = "none") +
    ggplot2::labs(x = NULL, y = ylab, title = title) +
    theme_journal()
  # Build comparison table
  cmp <- NULL
  if (is.data.frame(comparisons) && nrow(comparisons) > 0) {
    cmp <- comparisons
    if (!"p.label" %in% names(cmp)) {
      pcol <- if ("p" %in% names(cmp)) "p" else if ("p.adj" %in% names(cmp)) "p.adj" else NA
      if (!is.na(pcol)) cmp$p.label <- .format_p_label(cmp[[pcol]], stars = stars)
    }
  } else if (is.list(comparisons) && length(comparisons)) {
    rows <- lapply(comparisons, function(pair) {
      g1 <- as.character(pair[[1]]); g2 <- as.character(pair[[2]])
      x1 <- d$.val[d$.grp == g1]; x2 <- d$.val[d$.grp == g2]
      pv <- tryCatch(stats::wilcox.test(x1, x2)$p.value, error = function(e) NA_real_)
      data.frame(group1 = g1, group2 = g2, p = pv, p.label = .format_p_label(pv, stars = stars),
                 stringsAsFactors = FALSE)
    })
    cmp <- do.call(rbind, rows)
  } else if (nlevels(d$.grp) == 2L) {
    lev <- levels(d$.grp)
    pv <- stats::wilcox.test(d$.val ~ d$.grp)$p.value
    cmp <- data.frame(group1 = lev[1], group2 = lev[2], p = pv,
                      p.label = .format_p_label(pv, stars = stars), stringsAsFactors = FALSE)
  }
  if (!is.null(cmp) && nrow(cmp) > 0) {
    y_max <- max(d$.val, na.rm = TRUE)
    y_range <- diff(range(d$.val, na.rm = TRUE))
    if (!is.finite(y_range) || y_range == 0) y_range <- 1
    cmp$xmin <- match(as.character(cmp$group1), levels(d$.grp))
    cmp$xmax <- match(as.character(cmp$group2), levels(d$.grp))
    cmp$y <- y_max + y_range * (0.08 + 0.12 * (seq_len(nrow(cmp)) - 1))
    p <- p +
      ggplot2::geom_segment(
        data = cmp,
        ggplot2::aes(x = xmin, xend = xmax, y = y, yend = y),
        inherit.aes = FALSE, color = "grey30", linewidth = 0.35
      ) +
      ggplot2::geom_text(
        data = cmp,
        ggplot2::aes(x = (xmin + xmax) / 2, y = y, label = p.label),
        inherit.aes = FALSE, vjust = -0.35, size = 3.2, color = "grey20"
      ) +
      ggplot2::coord_cartesian(ylim = c(NA, max(cmp$y) + y_range * 0.12))
  }
  p
}

#' Paired boxplots with grey connecting lines + p (Fig2-D).
#' Long format: id_col, group_col (2 levels), value_col.
plot_paired_box_journal <- function(df,
                                    id_col = "id",
                                    group_col = "group",
                                    value_col = "value",
                                    title = NULL,
                                    ylab = "Value",
                                    palette = NULL,
                                    paired_test = TRUE) {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  need <- c(id_col, group_col, value_col)
  miss <- setdiff(need, names(df))
  if (length(miss)) stop("Missing columns: ", paste(miss, collapse = ", "))
  d <- as.data.frame(df)
  d$.id <- as.character(d[[id_col]])
  d$.grp <- as.factor(d[[group_col]])
  d$.val <- as.numeric(d[[value_col]])
  if (nlevels(d$.grp) != 2L) stop("plot_paired_box_journal expects exactly 2 group levels", call. = FALSE)
  cols <- palette
  if (is.null(cols)) {
    cols <- setNames(
      unname(c(bioinfo_groups["Control"], bioinfo_groups["TreatA"])),
      levels(d$.grp)
    )
  }
  p <- ggplot2::ggplot(d, ggplot2::aes(x = .grp, y = .val, fill = .grp)) +
    ggplot2::geom_line(ggplot2::aes(group = .id), color = "grey70", linewidth = 0.4, alpha = 0.85) +
    ggplot2::geom_boxplot(width = 0.45, outlier.shape = NA, alpha = 0.5, color = "grey35") +
    ggplot2::geom_point(size = 1.8, alpha = 0.85, color = "grey25") +
    ggplot2::scale_fill_manual(values = cols, guide = "none") +
    ggplot2::labs(x = NULL, y = ylab, title = title) +
    theme_journal()
  if (isTRUE(paired_test)) {
    wide <- stats::reshape(
      d[, c(".id", ".grp", ".val")],
      idvar = ".id", timevar = ".grp", direction = "wide"
    )
    vcols <- grep("^\\.val", names(wide), value = TRUE)
    if (length(vcols) == 2L) {
      pv <- tryCatch(stats::wilcox.test(wide[[vcols[1]]], wide[[vcols[2]]], paired = TRUE)$p.value,
                     error = function(e) NA_real_)
      p_lab <- sprintf("Paired Wilcoxon p = %.3g", pv)
      p <- p + ggplot2::annotate(
        "text", x = 1.5, y = Inf, label = p_lab, vjust = 1.5, size = 3.2
      )
    }
  }
  p
}

#' Module/gene trend vs severity (or time/dose) axis with smooth + CI (Fig1 d/e).
plot_severity_trend_journal <- function(df,
                                        x_col = "severity",
                                        y_col = "value",
                                        group_col = NULL,
                                        title = NULL,
                                        xlab = "Severity",
                                        ylab = "Relative expression",
                                        palette = NULL,
                                        point_alpha = 0.55) {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  need <- c(x_col, y_col)
  miss <- setdiff(need, names(df))
  if (length(miss)) stop("Missing columns: ", paste(miss, collapse = ", "))
  d <- as.data.frame(df)
  d$.x <- as.numeric(d[[x_col]])
  d$.y <- as.numeric(d[[y_col]])
  if (!is.null(group_col) && group_col %in% names(d)) {
    d$.grp <- as.factor(d[[group_col]])
    nlev <- nlevels(d$.grp)
    cols <- palette
    if (is.null(cols)) {
      cols <- setNames(rep(bioinfo_palette, length.out = nlev), levels(d$.grp))
    }
    ggplot2::ggplot(d, ggplot2::aes(x = .x, y = .y, color = .grp, fill = .grp)) +
      ggplot2::geom_point(alpha = point_alpha, size = 1.6) +
      ggplot2::geom_smooth(method = "loess", se = TRUE, linewidth = 0.8, alpha = 0.15) +
      ggplot2::scale_color_manual(values = cols, name = NULL) +
      ggplot2::scale_fill_manual(values = cols, guide = "none") +
      ggplot2::labs(x = xlab, y = ylab, title = title) +
      theme_journal()
  } else {
    ggplot2::ggplot(d, ggplot2::aes(x = .x, y = .y)) +
      ggplot2::geom_point(alpha = point_alpha, size = 1.6, color = "grey35") +
      ggplot2::geom_smooth(method = "loess", se = TRUE, linewidth = 0.85,
                          color = unname(bioinfo_groups["Accent2"]),
                          fill = unname(bioinfo_groups["Accent2"]), alpha = 0.18) +
      ggplot2::labs(x = xlab, y = ylab, title = title) +
      theme_journal()
  }
}

#' Sample hierarchical clustering dendrogram / cladogram-style tree (Fig1-a).
#' mat: genes × samples numeric; group optional named vector or data.frame(sample, group).
plot_sample_dendrogram_journal <- function(mat,
                                           group = NULL,
                                           title = "Sample clustering",
                                           dist_method = "euclidean",
                                           hclust_method = "average",
                                           palette = NULL) {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  mat <- as.matrix(mat)
  storage.mode(mat) <- "numeric"
  if (is.null(colnames(mat))) colnames(mat) <- paste0("S", seq_len(ncol(mat)))
  hc <- stats::hclust(stats::dist(t(mat), method = dist_method), method = hclust_method)
  # Build rectangle segments from merge matrix (no ggdendro required)
  n <- nrow(hc$merge) + 1L
  x_pos <- rep(NA_real_, 2L * n - 1L)
  y_pos <- rep(0, 2L * n - 1L)
  for (i in seq_len(n)) {
    x_pos[i] <- match(i, hc$order)
    y_pos[i] <- 0
  }
  segs <- list()
  for (i in seq_len(nrow(hc$merge))) {
    a <- hc$merge[i, 1]; b <- hc$merge[i, 2]
    ia <- if (a < 0) -a else n + a
    ib <- if (b < 0) -b else n + b
    h <- hc$height[i]
    xa <- x_pos[ia]; xb <- x_pos[ib]
    ya <- y_pos[ia]; yb <- y_pos[ib]
    xmid <- (xa + xb) / 2
    segs[[length(segs) + 1L]] <- data.frame(x = xa, xend = xa, y = ya, yend = h)
    segs[[length(segs) + 1L]] <- data.frame(x = xb, xend = xb, y = yb, yend = h)
    segs[[length(segs) + 1L]] <- data.frame(x = xa, xend = xb, y = h, yend = h)
    x_pos[n + i] <- xmid
    y_pos[n + i] <- h
  }
  seg <- do.call(rbind, segs)
  lab_ord <- hc$labels[hc$order]
  lab_df <- data.frame(
    sample = lab_ord,
    x = seq_along(lab_ord),
    y = 0,
    stringsAsFactors = FALSE
  )
  if (!is.null(group)) {
    if (is.data.frame(group)) {
      gmap <- setNames(as.character(group[[2]]), as.character(group[[1]]))
    } else if (!is.null(names(group))) {
      gmap <- setNames(as.character(group), names(group))
    } else {
      gmap <- setNames(as.character(group), colnames(mat))
    }
    lab_df$group <- factor(unname(gmap[as.character(lab_df$sample)]))
  } else {
    lab_df$group <- factor("Sample")
  }
  nlev <- nlevels(lab_df$group)
  cols <- palette
  if (is.null(cols)) {
    cols <- setNames(rep(bioinfo_palette, length.out = max(nlev, 1L)), levels(lab_df$group))
  }
  ggplot2::ggplot() +
    ggplot2::geom_segment(
      data = seg,
      ggplot2::aes(x = x, xend = xend, y = y, yend = yend),
      color = "grey40", linewidth = 0.4
    ) +
    ggplot2::geom_point(
      data = lab_df,
      ggplot2::aes(x = x, y = y, color = group),
      size = 2.2
    ) +
    ggplot2::scale_color_manual(values = cols, name = NULL) +
    ggplot2::scale_x_continuous(breaks = lab_df$x, labels = lab_df$sample) +
    ggplot2::labs(x = NULL, y = "Height", title = title) +
    theme_journal() +
    ggplot2::theme(
      axis.text.x = ggplot2::element_text(angle = 45, hjust = 1, size = 8),
      panel.grid = ggplot2::element_blank()
    )
}

#' Pathway activity heatmap (GSVA-style; rows = pathways, cols = samples).
#' mat: pathways × samples; optional group for column annotation colors via gaps only.
plot_pathway_activity_heatmap_journal <- function(mat,
                                                  title = "Pathway activity",
                                                  cluster_rows = TRUE,
                                                  cluster_cols = TRUE) {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  mat <- as.matrix(mat)
  storage.mode(mat) <- "numeric"
  if (isTRUE(cluster_rows) && nrow(mat) > 2) {
    mat <- mat[stats::hclust(stats::dist(mat))$order, , drop = FALSE]
  }
  if (isTRUE(cluster_cols) && ncol(mat) > 2) {
    mat <- mat[, stats::hclust(stats::dist(t(mat)))$order, drop = FALSE]
  }
  d <- data.frame(
    pathway = factor(rep(rownames(mat), times = ncol(mat)), levels = rev(rownames(mat))),
    sample = factor(rep(colnames(mat), each = nrow(mat)), levels = colnames(mat)),
    value = as.vector(mat),
    stringsAsFactors = FALSE
  )
  ggplot2::ggplot(d, ggplot2::aes(x = sample, y = pathway, fill = value)) +
    ggplot2::geom_tile(color = "white", linewidth = 0.2) +
    scale_fill_diverging_rb(name = "Activity") +
    ggplot2::labs(x = NULL, y = NULL, title = title) +
    theme_journal() +
    ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 45, hjust = 1))
}

#' Density + box combo for PC (or any continuous) scores by group (Fig1-c).
plot_pc_density_box_journal <- function(df,
                                        value_col = "PC1",
                                        group_col = "group",
                                        title = NULL,
                                        xlab = NULL,
                                        palette = NULL) {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  need <- c(value_col, group_col)
  miss <- setdiff(need, names(df))
  if (length(miss)) stop("Missing columns: ", paste(miss, collapse = ", "))
  d <- as.data.frame(df)
  d$.val <- as.numeric(d[[value_col]])
  d$.grp <- as.factor(d[[group_col]])
  nlev <- nlevels(d$.grp)
  cols <- palette
  if (is.null(cols)) {
    base_cols <- unname(c(
      bioinfo_groups["Control"], bioinfo_groups["TreatA"], bioinfo_groups["TreatB"],
      bioinfo_groups["Accent1"], bioinfo_groups["Accent2"]
    ))
    cols <- setNames(rep(base_cols, length.out = nlev), levels(d$.grp))
  }
  if (is.null(xlab)) xlab <- value_col
  p_den <- ggplot2::ggplot(d, ggplot2::aes(x = .val, fill = .grp, color = .grp)) +
    ggplot2::geom_density(alpha = 0.25, linewidth = 0.6) +
    ggplot2::scale_fill_manual(values = cols, name = NULL) +
    ggplot2::scale_color_manual(values = cols, name = NULL) +
    ggplot2::labs(x = NULL, y = "Density", title = title) +
    theme_journal() +
    ggplot2::theme(axis.text.x = ggplot2::element_blank(), axis.ticks.x = ggplot2::element_blank())
  p_box <- ggplot2::ggplot(d, ggplot2::aes(x = .val, y = .grp, fill = .grp)) +
    ggplot2::geom_boxplot(width = 0.55, outlier.size = 0.8, alpha = 0.65, color = "grey35") +
    ggplot2::scale_fill_manual(values = cols, guide = "none") +
    ggplot2::labs(x = xlab, y = NULL) +
    theme_journal()
  if (requireNamespace("patchwork", quietly = TRUE)) {
    return(p_den / p_box + patchwork::plot_layout(heights = c(2, 1)))
  }
  if (requireNamespace("cowplot", quietly = TRUE)) {
    return(cowplot::plot_grid(p_den, p_box, ncol = 1, rel_heights = c(2, 1), align = "v"))
  }
  p_den
}
