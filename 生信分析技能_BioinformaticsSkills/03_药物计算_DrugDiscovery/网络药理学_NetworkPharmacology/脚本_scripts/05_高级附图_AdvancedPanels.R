# Advanced NetPharm panels: UpSet / Sankey / herb×pathway heatmap
# Sourced after 01–04 delivery scripts. Status: FROZEN (standards §E, 2026-07-26).

#' Binary herb×compound matrix from 成分重命名_CompoundRenameMap (or herb_compound_edges).
.np_herb_compound_membership <- function(rename_df = NULL, herb_comp_df = NULL) {
  if (!is.null(rename_df) && nrow(rename_df)) {
    df <- rename_df
    hcol <- if ("herb_zh" %in% names(df) && any(nzchar(as.character(df$herb_zh)))) {
      "herb_zh"
    } else if ("herb_code" %in% names(df)) {
      "herb_code"
    } else {
      "herb"
    }
    ccol <- "compound_id"
  } else if (!is.null(herb_comp_df) && nrow(herb_comp_df)) {
    df <- herb_comp_df
    hcol <- if ("herb_zh" %in% names(df) && any(nzchar(as.character(df$herb_zh)))) {
      "herb_zh"
    } else {
      "herb_code"
    }
    ccol <- "compound_id"
  } else {
    stop("Need compound_rename or herb_compound_edges", call. = FALSE)
  }
  df$h <- as.character(df[[hcol]])
  df$c <- as.character(df[[ccol]])
  df <- df[nzchar(df$h) & nzchar(df$c), , drop = FALSE]
  herbs <- sort(unique(df$h))
  comps <- sort(unique(df$c))
  mat <- matrix(0L, nrow = length(comps), ncol = length(herbs),
                dimnames = list(comps, herbs))
  for (i in seq_len(nrow(df))) {
    mat[df$c[i], df$h[i]] <- 1L
  }
  as.data.frame(mat, check.names = FALSE)
}

#' Herb×target membership via A–B–C paths in network edges.
.np_herb_target_membership <- function(net, type_df) {
  edges <- np_normalize_network_edges(net)
  typ <- np_normalize_type_table(type_df)
  type_vec <- stats::setNames(typ$type, typ$term)
  ab <- edges
  ab$ta <- unname(type_vec[ab$from])
  ab$tb <- unname(type_vec[ab$to])
  ab_keep <- (!is.na(ab$ta) & !is.na(ab$tb) &
                ((ab$ta == "A" & ab$tb == "B") | (ab$ta == "B" & ab$tb == "A")))
  ab <- ab[ab_keep, , drop = FALSE]
  herb_of <- character()
  for (i in seq_len(nrow(ab))) {
    a <- ab$from[i]; b <- ab$to[i]
    if (identical(type_vec[[a]], "A")) {
      herb_of[b] <- a
    } else {
      herb_of[a] <- b
    }
  }
  bc <- edges
  bc$ta <- unname(type_vec[bc$from])
  bc$tb <- unname(type_vec[bc$to])
  bc_keep <- (!is.na(bc$ta) & !is.na(bc$tb) &
                ((bc$ta == "B" & bc$tb == "C") | (bc$ta == "C" & bc$tb == "B")))
  bc <- bc[bc_keep, , drop = FALSE]
  pairs <- list()
  for (i in seq_len(nrow(bc))) {
    a <- bc$from[i]; b <- bc$to[i]
    cpd <- if (identical(type_vec[[a]], "B")) a else b
    tgt <- if (identical(type_vec[[a]], "C")) a else b
    h <- herb_of[[cpd]]
    if (!is.null(h) && !is.na(h) && nzchar(h)) {
      pairs[[length(pairs) + 1L]] <- c(h = h, t = tgt)
    }
  }
  if (!length(pairs)) stop("No herb–target membership via A–B–C", call. = FALSE)
  pdf <- as.data.frame(do.call(rbind, pairs), stringsAsFactors = FALSE)
  herbs <- sort(unique(pdf$h))
  tgts <- sort(unique(pdf$t))
  mat <- matrix(0L, nrow = length(tgts), ncol = length(herbs),
                dimnames = list(tgts, herbs))
  for (i in seq_len(nrow(pdf))) mat[pdf$t[i], pdf$h[i]] <- 1L
  as.data.frame(mat, check.names = FALSE)
}

#' UpSet of herb membership (compounds or targets).
np_plot_herb_upset <- function(membership_df,
                               title = "Herb set intersections",
                               nintersects = 40L,
                               mb_ratio = c(0.55, 0.45),
                               text_scale = 1.2) {
  if (!requireNamespace("UpSetR", quietly = TRUE)) {
    stop("Install UpSetR for np_plot_herb_upset", call. = FALSE)
  }
  stopifnot(is.data.frame(membership_df), ncol(membership_df) >= 2L)
  # UpSetR wants 0/1 columns named by sets
  for (j in seq_len(ncol(membership_df))) {
    membership_df[[j]] <- as.integer(membership_df[[j]] > 0)
  }
  UpSetR::upset(
    membership_df,
    nsets = ncol(membership_df),
    nintersects = as.integer(nintersects),
    order.by = "freq",
    decreasing = TRUE,
    mb.ratio = mb_ratio,
    text.scale = text_scale,
    mainbar.y.label = "Intersection size",
    sets.x.label = "Set size",
    keep.order = FALSE
  )
  # UpSetR draws to current device; wrap as recorded plot for ggsave-like save
  invisible(NULL)
}

#' Save UpSetR plot via grDevices (not ggplot).
#' Set bars + unique-intersection queries use `.np_herb_palette` (multi-hue).
.np_save_upset_pub <- function(membership_df, stem, width, height, out_dir,
                               title = NULL, nintersects = 40L, dpi = 300L) {
  if (!requireNamespace("UpSetR", quietly = TRUE)) {
    stop("Install UpSetR", call. = FALSE)
  }
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  stem <- sub("\\.(png|svg|pdf)$", "", stem, ignore.case = TRUE)
  fpng <- file.path(out_dir, paste0(stem, ".png"))
  fsvg <- file.path(out_dir, paste0(stem, ".svg"))
  for (j in seq_len(ncol(membership_df))) {
    membership_df[[j]] <- as.integer(as.numeric(membership_df[[j]]) > 0)
  }
  set_sizes <- colSums(membership_df)
  set_order <- names(sort(set_sizes, decreasing = TRUE))
  pal <- .np_herb_palette(set_order)
  # Unique-set intersections get herb colors (shared bars keep vivid main.bar.color)
  queries <- lapply(set_order, function(h) {
    list(
      query = UpSetR::intersects,
      params = list(h),
      color = unname(pal[[h]]),
      active = TRUE
    )
  })
  draw_upset <- function() {
    print(UpSetR::upset(
      membership_df,
      sets = set_order,
      keep.order = TRUE,
      nsets = length(set_order),
      nintersects = as.integer(nintersects),
      order.by = "freq",
      mb.ratio = c(0.55, 0.45),
      text.scale = 1.35,
      mainbar.y.label = "Intersection size",
      sets.x.label = "Set size",
      main.bar.color = "#E74C3C",
      sets.bar.color = unname(pal[set_order]),
      matrix.color = "#5D6D7E",
      shade.color = "#FDEBD0",
      queries = queries,
      query.legend = "none"
    ))
    invisible(title)
  }
  grDevices::png(fpng, width = width, height = height, units = "in", res = as.integer(dpi))
  draw_upset()
  grDevices::dev.off()
  ok_svg <- FALSE
  if (requireNamespace("svglite", quietly = TRUE)) {
    try({
      svglite::svglite(fsvg, width = width, height = height)
      draw_upset()
      grDevices::dev.off()
      ok_svg <- file.exists(fsvg) && file.info(fsvg)$size > 0
    }, silent = TRUE)
  }
  if (!ok_svg) {
    grDevices::svg(fsvg, width = width, height = height)
    draw_upset()
    grDevices::dev.off()
  }
  invisible(list(png = fpng, svg = fsvg))
}

#' Build truncated alluvium long data: Herb → Compound → Target → Pathway
#' Compounds are ranked by complete-path frequency (not raw graph degree),
#' so Top-N always have intact A–B–C–D interlocking.
.np_sankey_flows <- function(net, type_df,
                             max_compounds = 40L,
                             max_targets = 35L,
                             max_pathways = 12L) {
  edges <- np_normalize_network_edges(net)
  typ <- np_normalize_type_table(type_df)
  type_vec <- stats::setNames(typ$type, typ$term)
  g <- igraph::graph_from_data_frame(edges, directed = FALSE)
  g <- igraph::simplify(g)
  deg <- igraph::degree(g)

  pick_pair <- function(ta, tb) {
    ea <- edges
    ea$ta <- unname(type_vec[ea$from])
    ea$tb <- unname(type_vec[ea$to])
    keep <- (!is.na(ea$ta) & !is.na(ea$tb) &
               ((ea$ta == ta & ea$tb == tb) | (ea$ta == tb & ea$tb == ta)))
    ea <- ea[keep, , drop = FALSE]
    from_a <- character(nrow(ea))
    to_b <- character(nrow(ea))
    for (i in seq_len(nrow(ea))) {
      if (identical(type_vec[[ea$from[i]]], ta)) {
        from_a[i] <- ea$from[i]; to_b[i] <- ea$to[i]
      } else {
        from_a[i] <- ea$to[i]; to_b[i] <- ea$from[i]
      }
    }
    data.frame(a = from_a, b = to_b, stringsAsFactors = FALSE)
  }
  ab <- pick_pair("A", "B")
  bc <- pick_pair("B", "C")
  cd <- pick_pair("C", "D")

  score <- function(nms) {
    s <- as.numeric(deg[nms]); s[is.na(s)] <- 0; stats::setNames(s, nms)
  }
  paths <- unique(cd$b)
  keep_d <- names(sort(score(paths), decreasing = TRUE))
  keep_d <- keep_d[seq_len(min(length(keep_d), as.integer(max_pathways)))]
  cd <- cd[cd$b %in% keep_d, , drop = FALSE]

  if (!requireNamespace("dplyr", quietly = TRUE)) stop("Need dplyr", call. = FALSE)
  # Full interlocking pool on selected pathways, then Top-N compounds by path freq
  flow <- dplyr::inner_join(
    dplyr::rename(ab, herb = a, compound = b),
    dplyr::rename(bc, compound = a, target = b),
    by = "compound",
    relationship = "many-to-many"
  )
  flow <- dplyr::inner_join(
    flow,
    dplyr::rename(cd, target = a, pathway = b),
    by = "target",
    relationship = "many-to-many"
  )
  flow <- dplyr::as_tibble(flow) |>
    dplyr::count(herb, compound, target, pathway, name = "freq")
  if (!nrow(flow)) {
    return(as.data.frame(flow))
  }

  sc <- sort(tapply(flow$freq, flow$compound, sum), decreasing = TRUE)
  comps <- names(sc)
  same_b <- comps[grepl("^same[0-9]+$", comps, ignore.case = TRUE)]
  rest <- setdiff(comps, same_b)
  keep_b <- unique(c(same_b, rest))
  keep_b <- keep_b[seq_len(min(length(keep_b), as.integer(max_compounds)))]
  flow <- flow[flow$compound %in% keep_b, , drop = FALSE]

  sc_t <- sort(tapply(flow$freq, flow$target, sum), decreasing = TRUE)
  keep_c <- names(sc_t)[seq_len(min(length(sc_t), as.integer(max_targets)))]
  flow <- flow[flow$target %in% keep_c, , drop = FALSE]

  # Drop empty after target trim (rare)
  flow <- flow[flow$freq > 0, , drop = FALSE]
  as.data.frame(flow)
}

#' Sankey/alluvial ggplot for HCTP layers (truncated).
#' `layout`: "complete" (fuller overview) or "compact" (fewer nodes, larger type).
np_plot_hctp_sankey <- function(net, type_df,
                                title = "Herb–compound–target–pathway flow",
                                max_compounds = 12L,
                                max_targets = 10L,
                                max_pathways = 8L,
                                label_min_y = 1,
                                soft_floor_comp = TRUE,
                                label_size = 4.2,
                                layout = c("compact", "complete")) {
  layout <- match.arg(layout)
  if (!requireNamespace("ggalluvial", quietly = TRUE)) {
    stop("Install ggalluvial for np_plot_hctp_sankey", call. = FALSE)
  }
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("Need ggplot2", call. = FALSE)
  if (!requireNamespace("ggnewscale", quietly = TRUE)) {
    stop("Install ggnewscale for colored sankey strata", call. = FALSE)
  }
  flow <- .np_sankey_flows(
    net, type_df,
    max_compounds = max_compounds,
    max_targets = max_targets,
    max_pathways = max_pathways
  )
  if (!nrow(flow)) stop("Sankey flow empty after truncation", call. = FALSE)
  .np_short_lab <- function(x, n = 22L) {
    x <- as.character(x)
    m <- regexpr("hsa[0-9]+", x, ignore.case = TRUE, perl = TRUE)
    hsa <- character(length(x))
    ok <- !is.na(m) & m > 0L
    if (any(ok)) {
      hsa[ok] <- substr(x[ok], m[ok], m[ok] + attr(m, "match.length")[ok] - 1L)
    }
    out <- ifelse(nzchar(hsa), hsa, x)
    ifelse(nchar(out) > n, paste0(substr(out, 1L, as.integer(n) - 1L), "\u2026"), out)
  }
  flow$pathway <- .np_short_lab(flow$pathway, 12L)
  flow$compound <- .np_short_lab(flow$compound, 12L)
  flow$herb <- .np_short_lab(flow$herb, 8L)
  flow$target <- .np_short_lab(flow$target, 10L)
  ord_lev <- function(col) {
    tot <- tapply(flow$freq, flow[[col]], sum)
    names(sort(tot, decreasing = TRUE))
  }
  flow$herb <- factor(flow$herb, levels = ord_lev("herb"))
  flow$compound <- factor(flow$compound, levels = ord_lev("compound"))
  flow$target <- factor(flow$target, levels = ord_lev("target"))
  flow$pathway <- factor(flow$pathway, levels = ord_lev("pathway"))

  flow$y <- as.numeric(flow$freq)
  if (isTRUE(soft_floor_comp)) {
    tot <- tapply(flow$y, flow$compound, sum)
    floor_v <- sum(tot) / (length(tot) * if (identical(layout, "complete")) 1.35 else 1.6)
    boost <- pmax(tot, floor_v) / pmax(tot, 1e-9)
    flow$y <- flow$y * unname(boost[as.character(flow$compound)])
  }

  n_comp <- nlevels(flow$compound)
  if (identical(layout, "complete")) {
    suggest_w <- 17L
    suggest_h <- as.integer(max(13L, ceiling(n_comp * 0.32 + nlevels(flow$target) * 0.12 + 5)))
    sub_lab <- sprintf(
      "Complete HCTP · herbs=%d · compounds=%d · targets=%d · pathways=%d",
      nlevels(flow$herb), n_comp, nlevels(flow$target), nlevels(flow$pathway)
    )
  } else {
    suggest_w <- 15L
    suggest_h <- 10L
    sub_lab <- sprintf(
      "Top-%d compounds · targets=%d · pathways=%d",
      n_comp, nlevels(flow$target), nlevels(flow$pathway)
    )
  }

  herb_cols <- .np_herb_palette(levels(flow$herb))
  .ramp_named <- function(nms, cols) {
    n <- length(nms)
    if (!n) return(character())
    stats::setNames(grDevices::colorRampPalette(cols)(n), nms)
  }
  stratum_cols <- c(
    herb_cols,
    .ramp_named(levels(flow$compound), c("#A6CEE3", "#6BAED6", "#3182BD", "#08519C")),
    .ramp_named(levels(flow$target), c("#FCBBA1", "#FC9272", "#EF3B2C", "#A50F15")),
    .ramp_named(levels(flow$pathway), c("#A1D99B", "#74C476", "#238B45", "#00441B"))
  )

  p <- ggplot2::ggplot(
    flow,
    ggplot2::aes(
      y = y,
      axis1 = herb, axis2 = compound, axis3 = target, axis4 = pathway
    )
  ) +
    ggalluvial::geom_alluvium(
      ggplot2::aes(fill = herb),
      width = 1 / 10, alpha = 0.38, knot.pos = 0.35, color = "white", linewidth = 0.15
    ) +
    ggplot2::scale_fill_manual(values = herb_cols, guide = "none") +
    ggnewscale::new_scale_fill() +
    ggalluvial::geom_stratum(
      ggplot2::aes(fill = ggplot2::after_stat(as.character(stratum))),
      width = 1 / 4.2, color = "white", linewidth = 0.55, alpha = 1
    ) +
    ggplot2::scale_fill_manual(values = stratum_cols, guide = "none", na.value = "#BDBDBD") +
    ggplot2::geom_text(
      stat = ggalluvial::StatStratum,
      ggplot2::aes(label = ggplot2::after_stat(stratum)),
      size = label_size,
      fontface = "bold",
      min.y = 0,
      check_overlap = TRUE,
      color = "grey8"
    ) +
    ggplot2::scale_x_discrete(
      limits = c("Herb", "Compound", "Target", "Pathway"),
      expand = c(0.08, 0.08)
    ) +
    ggplot2::labs(title = title, subtitle = sub_lab, y = NULL) +
    ggplot2::theme_minimal(base_size = 15) +
    ggplot2::theme(
      panel.grid = ggplot2::element_blank(),
      panel.background = ggplot2::element_rect(fill = "#F7F5F0", color = NA),
      plot.background = ggplot2::element_rect(fill = "white", color = NA),
      axis.text.y = ggplot2::element_blank(),
      axis.title = ggplot2::element_blank(),
      axis.text.x = ggplot2::element_text(size = 13, face = "bold", color = "grey20"),
      plot.title = ggplot2::element_text(face = "bold", hjust = 0.5, size = 16),
      plot.subtitle = ggplot2::element_text(size = 9.5, color = "grey45", hjust = 0.5),
      plot.margin = ggplot2::margin(14, 20, 14, 16)
    )
  attr(p, "suggest_width") <- suggest_w
  attr(p, "suggest_height") <- suggest_h
  attr(p, "n_compound") <- n_comp
  p
}

#' Filtered per-compound Sankey panels: Herb → Target → Pathway (facet = compound).
#' Keeps `same*` first, then top-degree compounds.
np_plot_hctp_sankey_by_compound <- function(net, type_df,
                                            title = "Per-compound flow (filtered)",
                                            n_compounds = 8L,
                                            max_targets = 8L,
                                            max_pathways = 6L,
                                            label_size = 3.0,
                                            ncol = 4L) {
  if (!requireNamespace("ggalluvial", quietly = TRUE)) {
    stop("Install ggalluvial", call. = FALSE)
  }
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("Need ggplot2", call. = FALSE)
  flow0 <- .np_sankey_flows(
    net, type_df,
    max_compounds = 60L,
    max_targets = 50L,
    max_pathways = 20L
  )
  if (!nrow(flow0)) stop("Empty flow for per-compound sankey", call. = FALSE)

  .np_short_lab <- function(x, n = 18L) {
    x <- as.character(x)
    m <- regexpr("hsa[0-9]+", x, ignore.case = TRUE, perl = TRUE)
    hsa <- character(length(x))
    ok <- !is.na(m) & m > 0L
    if (any(ok)) {
      hsa[ok] <- substr(x[ok], m[ok], m[ok] + attr(m, "match.length")[ok] - 1L)
    }
    out <- ifelse(nzchar(hsa), hsa, x)
    ifelse(nchar(out) > n, paste0(substr(out, 1L, as.integer(n) - 1L), "\u2026"), out)
  }
  flow0$pathway <- .np_short_lab(flow0$pathway, 12L)
  flow0$compound <- .np_short_lab(flow0$compound, 12L)
  flow0$herb <- .np_short_lab(flow0$herb, 8L)
  flow0$target <- .np_short_lab(flow0$target, 10L)

  score <- sort(tapply(flow0$freq, flow0$compound, sum), decreasing = TRUE)
  comps <- names(score)
  same <- comps[grepl("^same[0-9]+$", comps, ignore.case = TRUE)]
  rest <- setdiff(comps, same)
  keep_c <- unique(c(same, rest))
  keep_c <- keep_c[seq_len(min(length(keep_c), as.integer(n_compounds)))]

  flow <- flow0[flow0$compound %in% keep_c, , drop = FALSE]
  # Top targets / pathways within selected compounds
  t_score <- sort(tapply(flow$freq, flow$target, sum), decreasing = TRUE)
  p_score <- sort(tapply(flow$freq, flow$pathway, sum), decreasing = TRUE)
  keep_t <- names(t_score)[seq_len(min(length(t_score), as.integer(max_targets)))]
  keep_p <- names(p_score)[seq_len(min(length(p_score), as.integer(max_pathways)))]
  flow <- flow[flow$target %in% keep_t & flow$pathway %in% keep_p, , drop = FALSE]
  if (!nrow(flow)) stop("No rows after per-compound filter", call. = FALSE)

  flow$compound <- factor(flow$compound, levels = keep_c[keep_c %in% unique(flow$compound)])
  flow$herb <- factor(flow$herb, levels = names(sort(tapply(flow$freq, flow$herb, sum), decreasing = TRUE)))
  flow$target <- factor(flow$target, levels = keep_t[keep_t %in% unique(flow$target)])
  flow$pathway <- factor(flow$pathway, levels = keep_p[keep_p %in% unique(flow$pathway)])
  flow$y <- as.numeric(flow$freq)

  herb_cols <- .np_herb_palette(levels(flow$herb))
  .ramp_named <- function(nms, cols) {
    n <- length(nms)
    if (!n) return(character())
    stats::setNames(grDevices::colorRampPalette(cols)(n), nms)
  }
  stratum_cols <- c(
    herb_cols,
    .ramp_named(levels(flow$target), c("#FCBBA1", "#FC9272", "#EF3B2C", "#A50F15")),
    .ramp_named(levels(flow$pathway), c("#A1D99B", "#74C476", "#238B45", "#00441B"))
  )

  p <- ggplot2::ggplot(
    flow,
    ggplot2::aes(y = y, axis1 = herb, axis2 = target, axis3 = pathway)
  ) +
    ggalluvial::geom_alluvium(
      ggplot2::aes(fill = herb),
      width = 1 / 6, alpha = 0.55, knot.pos = 0.3, color = NA
    ) +
    ggplot2::scale_fill_manual(values = herb_cols, guide = "none") +
    ggnewscale::new_scale_fill() +
    ggalluvial::geom_stratum(
      ggplot2::aes(fill = ggplot2::after_stat(as.character(stratum))),
      width = 1 / 4, color = "grey25", linewidth = 0.3, alpha = 0.95
    ) +
    ggplot2::scale_fill_manual(values = stratum_cols, guide = "none", na.value = "#BDBDBD") +
    ggplot2::geom_text(
      stat = ggalluvial::StatStratum,
      ggplot2::aes(label = ggplot2::after_stat(stratum)),
      size = label_size, fontface = "bold", min.y = 0, color = "grey10"
    ) +
    ggplot2::scale_x_discrete(
      limits = c("Herb", "Target", "Pathway"),
      expand = c(0.05, 0.05)
    ) +
    ggplot2::facet_wrap(~compound, ncol = as.integer(ncol), scales = "free_y") +
    ggplot2::labs(
      title = title,
      subtitle = sprintf(
        "Filtered compounds=%d (same* first) · targets≤%d · pathways≤%d",
        nlevels(flow$compound), max_targets, max_pathways
      ),
      y = NULL
    ) +
    ggplot2::theme_minimal(base_size = 12) +
    ggplot2::theme(
      panel.grid = ggplot2::element_blank(),
      axis.text.y = ggplot2::element_blank(),
      axis.title = ggplot2::element_blank(),
      axis.text.x = ggplot2::element_text(size = 10, face = "bold"),
      strip.text = ggplot2::element_text(face = "bold", size = 11),
      strip.background = ggplot2::element_rect(fill = "grey95", color = NA),
      plot.title = ggplot2::element_text(face = "bold", hjust = 0.5, size = 15),
      plot.subtitle = ggplot2::element_text(size = 9, color = "grey40", hjust = 0.5),
      panel.spacing = ggplot2::unit(0.6, "lines"),
      plot.margin = ggplot2::margin(8, 12, 8, 10)
    )
  n_panel <- nlevels(flow$compound)
  nrow_f <- as.integer(ceiling(n_panel / max(1L, as.integer(ncol))))
  # Prefer square-ish 4×4 page
  attr(p, "suggest_width") <- if (as.integer(ncol) >= 4L) 18L else 16L
  attr(p, "suggest_height") <- as.integer(max(12L, 4.2 * nrow_f + 2L))
  attr(p, "n_compound") <- n_panel
  p
}

#' Core-target HCTP subnet: top Degree targets + linked B/D/A.
np_plot_core_target_subnet <- function(net, type_df,
                                       title = "Core target subnet",
                                       top_targets = 40L,
                                       plot_width_in = 12,
                                       plot_height_in = 10) {
  if (!requireNamespace("igraph", quietly = TRUE)) stop("Need igraph", call. = FALSE)
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("Need ggplot2", call. = FALSE)
  edges <- np_normalize_network_edges(net)
  typ <- np_normalize_type_table(type_df)
  type_vec <- stats::setNames(typ$type, typ$term)
  g <- igraph::graph_from_data_frame(edges, directed = FALSE)
  g <- igraph::simplify(g)
  deg <- igraph::degree(g)
  targets <- names(type_vec)[type_vec == "C"]
  targets <- intersect(targets, names(deg))
  targets <- names(sort(deg[targets], decreasing = TRUE))
  keep_c <- targets[seq_len(min(length(targets), as.integer(top_targets)))]

  # neighbors of keep_c
  nb <- unique(unlist(lapply(keep_c, function(v) {
    if (!v %in% igraph::V(g)$name) return(character())
    igraph::neighbors(g, v)$name
  })))
  keep_b <- nb[nb %in% names(type_vec)[type_vec == "B"]]
  keep_d <- nb[nb %in% names(type_vec)[type_vec == "D"]]
  # herbs linked to keep_b
  nb_b <- unique(unlist(lapply(keep_b, function(v) {
    if (!v %in% igraph::V(g)$name) return(character())
    igraph::neighbors(g, v)$name
  })))
  keep_a <- nb_b[nb_b %in% names(type_vec)[type_vec == "A"]]
  keep <- unique(c(keep_a, keep_b, keep_c, keep_d))
  sub <- igraph::induced_subgraph(g, vids = keep)
  set.seed(42)
  lay <- igraph::layout_with_fr(sub, niter = 800)
  rownames(lay) <- igraph::V(sub)$name
  nd <- data.frame(
    name = igraph::V(sub)$name,
    x = lay[, 1], y = lay[, 2],
    type = unname(type_vec[igraph::V(sub)$name]),
    degree = as.numeric(igraph::degree(sub)),
    stringsAsFactors = FALSE
  )
  nd$type[is.na(nd$type)] <- "?"
  # sizes
  nd$r <- 0.08 + 0.12 * (nd$degree - min(nd$degree)) / max(1e-9, max(nd$degree) - min(nd$degree))
  nd$r[nd$type == "C"] <- nd$r[nd$type == "C"] * 1.15
  nd$r[nd$type == "A"] <- nd$r[nd$type == "A"] * 1.25
  fill_map <- c(A = "#80B1D3", B = "#B0B0B0", C = "#F0B2AE", D = "#41AB5D", `?` = "#CCCCCC")
  nd$fill <- unname(fill_map[nd$type])
  # herb pastel override
  herbs <- nd$name[nd$type == "A"]
  if (length(herbs)) {
    hp <- .np_herb_palette(herbs)
    nd$fill[nd$type == "A"] <- unname(hp[nd$name[nd$type == "A"]])
    # compounds near owner: color by first A neighbor
    for (i in which(nd$type == "B")) {
      nm <- nd$name[i]
      ns <- igraph::neighbors(sub, nm)$name
      ha <- ns[ns %in% herbs]
      if (length(ha)) nd$fill[i] <- hp[[ha[1]]]
    }
  }
  el <- igraph::as_data_frame(sub, what = "edges")
  el$x <- nd$x[match(el$from, nd$name)]
  el$y <- nd$y[match(el$from, nd$name)]
  el$xend <- nd$x[match(el$to, nd$name)]
  el$yend <- nd$y[match(el$to, nd$name)]
  # labels: all A/D; top compounds; all targets (n≤40)
  nd$label <- ""
  nd$label[nd$type %in% c("A", "C", "D")] <- nd$name[nd$type %in% c("A", "C", "D")]
  top_b <- nd$name[nd$type == "B"][order(nd$degree[nd$type == "B"], decreasing = TRUE)]
  top_b <- top_b[seq_len(min(25L, length(top_b)))]
  nd$label[nd$name %in% top_b] <- nd$name[nd$name %in% top_b]

  ggplot2::ggplot() +
    ggplot2::geom_segment(
      data = el, ggplot2::aes(x = x, y = y, xend = xend, yend = yend),
      color = "#7A8A94", alpha = 0.25, linewidth = 0.3
    ) +
    ggplot2::geom_point(
      data = nd, ggplot2::aes(x = x, y = y, size = r * 40, color = fill),
      alpha = 0.95
    ) +
    ggplot2::geom_text(
      data = nd[nzchar(nd$label), , drop = FALSE],
      ggplot2::aes(x = x, y = y, label = label),
      size = 2.2, color = "grey10", check_overlap = FALSE
    ) +
    ggplot2::scale_color_identity() +
    ggplot2::scale_size_identity() +
    ggplot2::coord_equal() +
    ggplot2::labs(
      title = title,
      subtitle = sprintf(
        "TopDegree targets≤%d · induced A/B/C/D · n=%d e=%d · FR layout",
        top_targets, igraph::vcount(sub), igraph::ecount(sub)
      )
    ) +
    ggplot2::theme_void(base_size = 11) +
    ggplot2::theme(
      plot.title = ggplot2::element_text(face = "bold", hjust = 0.5),
      plot.subtitle = ggplot2::element_text(size = 8, color = "grey35", hjust = 0.5),
      plot.margin = ggplot2::margin(10, 12, 10, 12)
    )
}

#' Herb × pathway coverage heatmap from A–B–C–D Sankey flows.
#' Cell = number of distinct intersection targets linking herb to pathway.
np_plot_herb_pathway_heatmap <- function(net, type_df,
                                         title = "Herb × pathway target coverage",
                                         max_pathways = 20L,
                                         min_count = 1L) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("Need ggplot2", call. = FALSE)
  flow <- .np_sankey_flows(
    net, type_df,
    max_compounds = 80L,
    max_targets = 80L,
    max_pathways = as.integer(max_pathways)
  )
  if (!nrow(flow)) stop("Empty flow for herb–pathway heatmap", call. = FALSE)
  .np_short_lab <- function(x, n = 28L) {
    x <- as.character(x)
    m <- regexpr("hsa[0-9]+", x, ignore.case = TRUE, perl = TRUE)
    hsa <- character(length(x))
    ok <- !is.na(m) & m > 0L
    if (any(ok)) {
      hsa[ok] <- substr(x[ok], m[ok], m[ok] + attr(m, "match.length")[ok] - 1L)
    }
    out <- ifelse(nzchar(hsa), paste0(hsa, " ", sub(".*hsa[0-9]+\\s*", "", x, ignore.case = TRUE)), x)
    out <- trimws(out)
    ifelse(nchar(out) > n, paste0(substr(out, 1L, as.integer(n) - 1L), "\u2026"), out)
  }
  flow$pathway_lab <- .np_short_lab(flow$pathway, 26L)
  agg <- stats::aggregate(
    target ~ herb + pathway_lab,
    data = flow,
    FUN = function(z) length(unique(z))
  )
  names(agg)[3] <- "n_target"
  agg <- agg[agg$n_target >= as.integer(min_count), , drop = FALSE]
  p_ord <- names(sort(tapply(agg$n_target, agg$pathway_lab, sum), decreasing = TRUE))
  h_ord <- names(sort(tapply(agg$n_target, agg$herb, sum), decreasing = TRUE))
  agg$pathway_lab <- factor(agg$pathway_lab, levels = rev(p_ord))
  agg$herb <- factor(agg$herb, levels = h_ord)

  ggplot2::ggplot(agg, ggplot2::aes(x = herb, y = pathway_lab, fill = n_target)) +
    ggplot2::geom_tile(color = "white", linewidth = 0.45) +
    ggplot2::geom_text(
      ggplot2::aes(label = n_target),
      size = 3.2, color = "grey15", fontface = "bold"
    ) +
    ggplot2::scale_fill_gradientn(
      colours = c("#F7FBF4", "#C7E9C0", "#74C476", "#238B45", "#00441B"),
      name = "Targets"
    ) +
    ggplot2::labs(
      title = title,
      subtitle = sprintf(
        "Distinct disease-intersection targets per herb–pathway · Top%d pathways",
        length(p_ord)
      ),
      x = NULL, y = NULL
    ) +
    ggplot2::coord_fixed(ratio = 0.55) +
    ggplot2::theme_minimal(base_size = 12) +
    ggplot2::theme(
      panel.grid = ggplot2::element_blank(),
      axis.text.x = ggplot2::element_text(angle = 40, hjust = 1, face = "bold", size = 11),
      axis.text.y = ggplot2::element_text(size = 9.5),
      plot.title = ggplot2::element_text(face = "bold", hjust = 0.5, size = 14),
      plot.subtitle = ggplot2::element_text(size = 9, color = "grey40", hjust = 0.5),
      legend.position = "right",
      plot.margin = ggplot2::margin(10, 14, 10, 10)
    )
}
