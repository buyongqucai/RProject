# 出版级出图：高分期刊多面板风格（journal muted palette）
# 规范源：统一可视化规范_VizStandards
#
# 强制：
# - DPI≥600；同名 SVG+PNG；图面 English only
# - theme_journal()：白底、细轴线、浅灰主网格、无次网格、干净图例
# - 配色：分组 muted 绿/红/紫；发散蓝-白-红；火山 up红/down青绿；富集 ontology 分色
# - 富集默认：水平柱状图 / 气泡点图（bar/dot first）；棒棒糖（lollipop）已弃用为默认，勿再作为标准图种
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
# Feature / expression continuous blues (UMAP feature plots, gene scores)
bioinfo_feature_blue <- c("#F7FBFF", "#DEEBF7", "#C6DBEF", "#9ECAE1", "#6BAED6", "#4292C6", "#2171B5", "#084594")

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
  "#D4A574", "#7A9E9F", "#B8956B", "#A0A0A0"
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
  ggplot2::scale_color_manual(values = bioinfo_umap_discrete, ...)
}
scale_fill_umap_discrete <- function(...) {
  ggplot2::scale_fill_manual(values = bioinfo_umap_discrete, ...)
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
plot_umap_discrete_journal <- function(df,
                                       x_col = "umap_1",
                                       y_col = "umap_2",
                                       label_col = "celltype",
                                       title = "UMAP",
                                       point_size = 0.35) {
  stopifnot(requireNamespace("ggplot2", quietly = TRUE))
  need <- c(x_col, y_col, label_col)
  miss <- setdiff(need, names(df))
  if (length(miss)) stop("Missing columns: ", paste(miss, collapse = ", "))
  d <- as.data.frame(df)
  d$.x <- as.numeric(d[[x_col]])
  d$.y <- as.numeric(d[[y_col]])
  d$.lab <- as.factor(d[[label_col]])
  ggplot2::ggplot(d, ggplot2::aes(x = .x, y = .y, color = .lab)) +
    ggplot2::geom_point(size = point_size, alpha = 0.85) +
    scale_color_umap_discrete(name = NULL) +
    ggplot2::coord_fixed() +
    ggplot2::labs(x = "UMAP_1", y = "UMAP_2", title = title) +
    theme_journal() +
    ggplot2::theme(panel.grid = ggplot2::element_blank())
}
