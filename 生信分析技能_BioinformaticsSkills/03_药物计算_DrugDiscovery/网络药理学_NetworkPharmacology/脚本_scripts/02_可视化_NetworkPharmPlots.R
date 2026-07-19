# 网络药理学 — 可视化（对齐 D:\网络药理学文件\交付文件\图片）
# 疾病多库韦恩：VennDiagram 固定四色 + 底部 Size of each list（非 count 热力填色）

np_npg <- c("#E64B35", "#4DBBD5", "#00A087", "#3C5488", "#F39B7F", "#8491B4", "#91D1C2", "#B09C85")
# 交付 SVG 四库色：TTD / DrugBank / GeneCards / OMIM
np_venn_db_cols <- c(
  TTD = "#006600",
  DrugBank = "#5A9BD4",
  GeneCards = "#F15A60",
  OMIM = "#CFCF1B"
)
# 交付 GO 柱：BP 青绿 / CC 橙 / MF 蓝紫（对齐 BPCCMF柱状图.tiff）
np_go_bar_cols <- c(
  BP = "#1B9E77",
  CC = "#D95F02",
  MF = "#7570B3"
)
np_enrich_cats <- c(
  BP = "#1B9E77", CC = "#D95F02", MF = "#7570B3",
  KEGG = "#E07070", Other = "#A0A0A0"
)
# 交付 KEGG Group 色（对齐 KEGG柱状图 / 棒棒糖 SVG npg 四色）
np_kegg_group_cols <- c(
  "Cellular Processes" = "#4DBBD5",
  "Environmental Information Processing" = "#00A087",
  "Human Diseases" = "#E64B35",
  "Organismal Systems" = "#3C5488"
)
np_kegg_group_levels <- names(np_kegg_group_cols)
# GO 气泡 -log10(p) 绿→黄→红（对齐 BPCCMF气泡图）
np_go_pval_cols <- c("#00FF00", "#85E200", "#B1C400", "#E6A000", "#FF6600", "#FF0000")

np_apply_journal <- function(p) {
  if (exists("theme_journal", mode = "function")) {
    p + theme_journal(base_size = 11)
  } else {
    p + ggplot2::theme_bw(base_size = 11) +
      ggplot2::theme(panel.grid.minor = ggplot2::element_blank())
  }
}

#' 从 disease_by_db 取固定顺序的命名列表
np_disease_sets_ordered <- function(disease_by_db, order = names(np_venn_db_cols)) {
  out <- list()
  for (nm in order) {
    genes <- unique(as.character(disease_by_db$gene[disease_by_db$source == nm]))
    genes <- genes[!is.na(genes) & nzchar(genes)]
    if (length(genes)) out[[nm]] <- genes
  }
  if (!length(out)) {
    # fallback: whatever sources exist
    out <- np_disease_sets(disease_by_db)
  }
  out
}

#' 疾病多库真韦恩 — 交付风格（VennDiagram + Size of each list）
#' 返回 ggplot/grob 组合；由 delivery_save_plot / ggsave 保存时用 cowplot
np_plot_disease_db_venn <- function(disease_by_db) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
  if (!requireNamespace("VennDiagram", quietly = TRUE)) {
    stop("Install VennDiagram for delivery-style Venn plots")
  }
  sets <- np_disease_sets_ordered(disease_by_db)
  if (length(sets) < 2) stop("疾病库集合不足 2")

  nms <- names(sets)
  fills <- unname(np_venn_db_cols[nms])
  fills[is.na(fills)] <- np_npg[seq_along(fills)]
  sizes <- vapply(sets, length, integer(1))
  union_n <- length(unique(unlist(sets, use.names = FALSE)))

  # suppress VennDiagram log file
  futile.logger::flog.threshold(futile.logger::ERROR, name = "VennDiagramLogger")

  vd <- VennDiagram::venn.diagram(
    x = sets,
    filename = NULL,
    disable.logging = TRUE,
    fill = fills,
    alpha = 0.50,
    cex = 1.35,
    cat.cex = 1.15,
    cat.col = fills,
    cat.fontface = "bold",
    cat.dist = rep(0.06, length(sets)),
    margin = 0.08,
    lwd = 1.2,
    col = fills,
    fontfamily = "sans",
    cat.fontfamily = "sans",
    main = NULL,
    print.mode = "raw",
    sigdigs = 0
  )

  bar_df <- data.frame(
    database = factor(nms, levels = nms),
    n = as.numeric(sizes),
    fill = fills,
    stringsAsFactors = FALSE
  )
  p_bar <- ggplot2::ggplot(bar_df, ggplot2::aes(database, n, fill = fill)) +
    ggplot2::geom_col(width = 0.72, alpha = 0.55, color = NA, show.legend = FALSE) +
    ggplot2::geom_text(
      ggplot2::aes(label = n),
      vjust = -0.35, size = 3.2,
      color = fills
    ) +
    ggplot2::scale_fill_identity() +
    ggplot2::scale_y_continuous(expand = ggplot2::expansion(mult = c(0, 0.18))) +
    ggplot2::labs(
      title = "Size of each list",
      subtitle = paste0("Union = ", union_n, " unique genes"),
      x = NULL, y = NULL
    ) +
    ggplot2::theme_classic(base_size = 11) +
    ggplot2::theme(
      plot.title = ggplot2::element_text(face = "italic", hjust = 0.5, size = 11),
      plot.subtitle = ggplot2::element_text(hjust = 0.5, size = 9, color = "grey40"),
      axis.text.x = ggplot2::element_text(size = 10),
      axis.line.y = ggplot2::element_line(color = "grey50"),
      axis.ticks.y = ggplot2::element_line(color = "grey50")
    )

  # compose: title + venn grob + bar
  if (!requireNamespace("cowplot", quietly = TRUE)) {
    stop("Install cowplot to compose delivery-style Venn + bar panel")
  }
  title_gg <- cowplot::ggdraw() +
    cowplot::draw_label(
      "Disease genes across databases",
      fontface = "bold", size = 14, hjust = 0.5
    )
  sub_gg <- cowplot::ggdraw() +
    cowplot::draw_label(
      "Queried by English disease name · full GeneCards for Venn",
      size = 10, color = "grey40", hjust = 0.5
    )
  venn_gg <- cowplot::ggdraw(vd)
  cowplot::plot_grid(
    title_gg, sub_gg, venn_gg, p_bar,
    ncol = 1,
    rel_heights = c(0.06, 0.04, 0.62, 0.28)
  )
}

#' 药物 vs 疾病 两集合韦恩（固定双色 + 底部大小柱）
np_plot_drug_disease_venn <- function(drug_genes, disease_genes) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
  if (!requireNamespace("VennDiagram", quietly = TRUE)) {
    stop("Install VennDiagram for delivery-style Venn plots")
  }
  if (!requireNamespace("cowplot", quietly = TRUE)) stop("Install cowplot")

  sets <- list(
    Drug = unique(as.character(drug_genes$gene)),
    Disease = unique(as.character(disease_genes$gene))
  )
  fills <- c("#00A087", "#3C5488")
  sizes <- vapply(sets, length, integer(1))
  union_n <- length(unique(unlist(sets, use.names = FALSE)))
  inter_n <- length(intersect(sets$Drug, sets$Disease))

  futile.logger::flog.threshold(futile.logger::ERROR, name = "VennDiagramLogger")
  vd <- VennDiagram::venn.diagram(
    x = sets,
    filename = NULL,
    disable.logging = TRUE,
    fill = fills,
    alpha = 0.50,
    cex = 1.4,
    cat.cex = 1.2,
    cat.col = fills,
    cat.fontface = "bold",
    margin = 0.06,
    lwd = 1.2,
    col = fills,
    fontfamily = "sans",
    cat.fontfamily = "sans",
    print.mode = "raw"
  )

  bar_df <- data.frame(
    set = factor(c("Drug", "Disease", "Overlap"), levels = c("Drug", "Disease", "Overlap")),
    n = c(sizes[["Drug"]], sizes[["Disease"]], inter_n),
    fill = c(fills[1], fills[2], "#8491B4"),
    stringsAsFactors = FALSE
  )
  p_bar <- ggplot2::ggplot(bar_df, ggplot2::aes(set, n, fill = fill)) +
    ggplot2::geom_col(width = 0.65, alpha = 0.55, show.legend = FALSE) +
    ggplot2::geom_text(ggplot2::aes(label = n), vjust = -0.35, size = 3.3) +
    ggplot2::scale_fill_identity() +
    ggplot2::scale_y_continuous(expand = ggplot2::expansion(mult = c(0, 0.15))) +
    ggplot2::labs(
      title = "Size of each list",
      subtitle = paste0("Union = ", union_n),
      x = NULL, y = NULL
    ) +
    ggplot2::theme_classic(base_size = 11) +
    ggplot2::theme(
      plot.title = ggplot2::element_text(face = "italic", hjust = 0.5, size = 11),
      plot.subtitle = ggplot2::element_text(hjust = 0.5, size = 9, color = "grey40")
    )

  title_gg <- cowplot::ggdraw() +
    cowplot::draw_label("Drug targets vs disease genes", fontface = "bold", size = 14, hjust = 0.5)
  sub_gg <- cowplot::ggdraw() +
    cowplot::draw_label(
      "Herb-union targets vs filtered disease union",
      size = 10, color = "grey40", hjust = 0.5
    )
  cowplot::plot_grid(
    title_gg, sub_gg, cowplot::ggdraw(vd), p_bar,
    ncol = 1, rel_heights = c(0.06, 0.04, 0.62, 0.28)
  )
}


#' 通路/GO 长标签：按词折行（不截断省略号，避免语义丢失）
np_wrap_term <- function(x, width = 42) {
  x <- as.character(x)
  vapply(x, function(s) {
    if (is.na(s) || !nzchar(s)) return("")
    if (requireNamespace("stringr", quietly = TRUE)) {
      return(stringr::str_wrap(s, width = width))
    }
    words <- strsplit(s, "\\s+")[[1]]
    lines <- character()
    cur <- ""
    for (w in words) {
      trial <- if (nzchar(cur)) paste(cur, w) else w
      if (nchar(trial) <= width) {
        cur <- trial
      } else {
        if (nzchar(cur)) lines <- c(lines, cur)
        cur <- w
      }
    }
    if (nzchar(cur)) lines <- c(lines, cur)
    paste(lines, collapse = "\n")
  }, character(1), USE.NAMES = FALSE)
}

#' GeneRatio "a/b" → numeric a/b
np_parse_gene_ratio <- function(x) {
  x <- as.character(x)
  vapply(x, function(s) {
    if (is.na(s) || !nzchar(s)) return(NA_real_)
    parts <- strsplit(s, "/", fixed = TRUE)[[1]]
    if (length(parts) < 2) return(suppressWarnings(as.numeric(s)))
    a <- suppressWarnings(as.numeric(parts[1]))
    b <- suppressWarnings(as.numeric(parts[2]))
    if (is.na(a) || is.na(b) || b == 0) return(NA_real_)
    a / b
  }, numeric(1), USE.NAMES = FALSE)
}

#' 标准化 KEGG 表：pvalue / count / Group(one_type) / GeneRatio
np_prep_kegg_df <- function(kegg_df, top_n = 20) {
  df <- kegg_df
  if (any(duplicated(names(df)))) df <- df[, !duplicated(names(df)), drop = FALSE]
  term_col <- if ("term" %in% names(df)) "term" else names(df)[1]
  p_col <- if ("pvalue" %in% names(df)) {
    "pvalue"
  } else if ("padj" %in% names(df)) {
    "padj"
  } else if ("p.adjust" %in% names(df)) {
    "p.adjust"
  } else {
    NA_character_
  }
  count_col <- if ("count" %in% names(df)) {
    "count"
  } else if ("Count" %in% names(df)) {
    "Count"
  } else {
    NA_character_
  }
  grp_col <- if ("one_type" %in% names(df)) {
    "one_type"
  } else if ("Group" %in% names(df)) {
    "Group"
  } else if ("group" %in% names(df)) {
    "group"
  } else {
    NA_character_
  }

  out <- data.frame(
    term = as.character(df[[term_col]]),
    stringsAsFactors = FALSE
  )
  if (is.na(p_col)) {
    out$pvalue <- seq_len(nrow(out))
  } else {
    out$pvalue <- as.numeric(df[[p_col]])
  }
  out$neglogp <- -log10(pmax(out$pvalue, 1e-300))
  if (is.na(count_col)) {
    out$count <- 10L
  } else {
    out$count <- as.numeric(df[[count_col]])
    out$count[is.na(out$count)] <- 10
  }
  if (is.na(grp_col)) {
    out$Group <- factor(
      rep(np_kegg_group_levels, length.out = nrow(out)),
      levels = np_kegg_group_levels
    )
  } else {
    out$Group <- as.character(df[[grp_col]])
    out$Group[!out$Group %in% np_kegg_group_levels] <- "Cellular Processes"
    out$Group <- factor(out$Group, levels = np_kegg_group_levels)
  }
  if ("GeneRatio" %in% names(df)) {
    out$GeneRatio <- np_parse_gene_ratio(df$GeneRatio)
  } else if ("gene_ratio" %in% names(df)) {
    out$GeneRatio <- np_parse_gene_ratio(df$gene_ratio)
  } else {
    out$GeneRatio <- NA_real_
  }

  out <- out[order(out$pvalue), , drop = FALSE]
  out <- utils::head(out, top_n)
  # 交付顺序：先按 Group，组内按 -log10(p) 降序
  out <- out[order(out$Group, -out$neglogp), , drop = FALSE]
  out$term_plot <- np_wrap_term(out$term, width = 40)
  # 保证 factor 顺序与行顺序一致（ggplot 自下而上 → rev）
  out$term_plot <- factor(out$term_plot, levels = rev(unique(out$term_plot)))
  rownames(out) <- NULL
  out
}

#' 富集图通用主题：白底框线 + 浅网格 + Y 轴标签边距
np_theme_enrich <- function(y_text_size = 8.5, base_size = 11) {
  ggplot2::theme_bw(base_size = base_size) +
    ggplot2::theme(
      panel.grid.major = ggplot2::element_line(color = "grey90", linewidth = 0.35),
      panel.grid.minor = ggplot2::element_line(color = "grey94", linewidth = 0.2),
      axis.text.y = ggplot2::element_text(
        size = y_text_size, lineheight = 0.95, hjust = 1, color = "grey20"
      ),
      axis.text.x = ggplot2::element_text(size = base_size - 1, color = "grey20"),
      axis.title = ggplot2::element_text(size = base_size),
      legend.title = ggplot2::element_text(size = base_size - 1),
      legend.text = ggplot2::element_text(size = base_size - 2),
      plot.title = ggplot2::element_blank(),
      plot.margin = ggplot2::margin(8, 12, 8, 8),
      strip.background = ggplot2::element_rect(fill = "grey92", color = "grey70"),
      strip.text.y = ggplot2::element_text(size = base_size - 1, face = "bold", angle = 0)
    )
}

#' 单药交集 — 水平柱（参考 panel f 分类着色）
np_plot_per_herb_overlap <- function(summary_df) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
  df <- summary_df
  df$n_overlap_genes <- as.numeric(df$n_overlap_genes)
  df <- df[order(df$n_overlap_genes), , drop = FALSE]
  df$herb_en <- factor(df$herb_en, levels = df$herb_en)
  cols <- rep(np_npg, length.out = nrow(df))
  p <- ggplot2::ggplot(df, ggplot2::aes(n_overlap_genes, herb_en, fill = herb_en)) +
    ggplot2::geom_col(width = 0.72, show.legend = FALSE, color = NA) +
    ggplot2::geom_text(
      ggplot2::aes(label = n_overlap_genes),
      hjust = -0.2, size = 3.3, color = "grey20"
    ) +
    ggplot2::scale_fill_manual(values = setNames(cols, df$herb_en)) +
    ggplot2::scale_x_continuous(expand = ggplot2::expansion(mult = c(0, 0.18))) +
    ggplot2::labs(
      title = "Per-herb disease-overlap targets",
      subtitle = "Single-drug granularity",
      x = "Overlap gene count", y = NULL
    )
  np_apply_journal(p)
}

#' 子图差异配色（每面板一色）
np_compound_panel_palette <- function(n) {
  base <- c(
    "#E64B35", "#4DBBD5", "#00A087", "#3C5488", "#F39B7F",
    "#8491B4", "#91D1C2", "#B09C85", "#DC0000", "#7E6148",
    "#1B9E77", "#D95F02", "#7570B3", "#E7298A", "#66A61E",
    "#E6AB02", "#A6761D", "#666666"
  )
  if (n <= length(base)) return(base[seq_len(n)])
  grDevices::colorRampPalette(base)(n)
}

#' Mix hex color with white (toward_white in [0,1]); avoids adjustcolor red.f quirks
.np_lighten_color <- function(col, toward_white = 0.45) {
  toward_white <- max(0, min(1, as.numeric(toward_white)))
  ramp <- grDevices::colorRampPalette(c("white", col))(101)
  idx <- as.integer(round((1 - toward_white) * 100)) + 1L
  ramp[max(1L, min(101L, idx))]
}

#' Shade variants of one base color (light → base → slightly darker)
.np_shade_variants <- function(col, n) {
  n <- as.integer(n)
  if (n <= 1L) return(col)
  light <- .np_lighten_color(col, toward_white = 0.40)
  dark <- grDevices::colorRampPalette(c(col, "#1A1A1A"))(5)[2]
  grDevices::colorRampPalette(c(light, col, dark))(n)
}

#' 单面板水平柱（化学名；面板主色 + 按数值深浅）
.np_compound_overlap_one_panel <- function(df, panel_title, panel_color,
                                           show_x = TRUE, wrap_width = 40,
                                           label_max = 42) {
  df <- df[order(df$n_overlap_targets, df$compound_name), , drop = FALSE]
  lab <- as.character(df$compound_name)
  miss <- is.na(lab) | !nzchar(lab)
  lab[miss] <- as.character(df$compound_id[miss])
  too_long <- nchar(lab) > label_max
  lab[too_long] <- paste0(substr(lab[too_long], 1L, label_max - 1L), "…")
  if (exists("np_wrap_term", mode = "function")) {
    lab <- np_wrap_term(lab, width = wrap_width)
  }
  df$ylab <- factor(lab, levels = unique(lab))
  n_show <- nrow(df)
  y_cex <- if (n_show > 16) 6.0 else if (n_show > 10) 6.8 else 7.6
  xlim_max <- max(df$n_overlap_targets, na.rm = TRUE)
  # light → panel_color ramp by value
  ramp <- grDevices::colorRampPalette(c(
    .np_lighten_color(panel_color, toward_white = 0.45),
    panel_color
  ))(100)
  t <- (df$n_overlap_targets - min(df$n_overlap_targets)) /
    max(1e-9, max(df$n_overlap_targets) - min(df$n_overlap_targets))
  df$fill_col <- ramp[pmax(1L, pmin(100L, as.integer(round(t * 99)) + 1L))]

  p <- ggplot2::ggplot(df, ggplot2::aes(n_overlap_targets, ylab)) +
    ggplot2::geom_col(
      ggplot2::aes(fill = fill_col),
      width = 0.72, color = NA, alpha = 0.92
    ) +
    ggplot2::scale_fill_identity() +
    ggplot2::geom_text(
      ggplot2::aes(label = n_overlap_targets),
      hjust = -0.2, size = 2.35, color = "grey20"
    ) +
    ggplot2::scale_x_continuous(
      limits = c(0, max(xlim_max * 1.16, 1)),
      expand = ggplot2::expansion(mult = c(0, 0.02))
    ) +
    ggplot2::labs(
      title = panel_title,
      x = if (show_x) "Overlap target count" else NULL,
      y = NULL
    )
  np_apply_journal(p) +
    ggplot2::theme(
      axis.text.y = ggplot2::element_text(size = y_cex, lineheight = 0.9, hjust = 1),
      axis.title.x = ggplot2::element_text(size = 8.5),
      plot.title = ggplot2::element_text(
        face = "bold", size = 10, hjust = 0, color = panel_color
      ),
      legend.position = "none",
      panel.grid.major.y = ggplot2::element_blank(),
      panel.grid.major.x = ggplot2::element_line(color = "grey92", linewidth = 0.3),
      plot.margin = ggplot2::margin(8, 14, 6, 6),
      plot.background = ggplot2::element_rect(
        fill = grDevices::adjustcolor(panel_color, alpha.f = 0.04),
        color = NA
      ),
      panel.background = ggplot2::element_rect(fill = "white", color = NA)
    )
}

#' 选择子图网格：每格成分数接近；优先 2 列（长化学名可读）
np_choose_compound_panel_grid <- function(n, target_per = 14L, max_per = 16L) {
  n <- as.integer(n)
  if (n <= 0) return(list(n_panel = 1L, nrow = 1L, ncol = 1L, per = 0L))
  if (n <= max_per) {
    return(list(n_panel = 1L, nrow = 1L, ncol = 1L, per = n))
  }
  n_panel <- max(1L, as.integer(ceiling(n / target_per)))
  while (as.integer(ceiling(n / n_panel)) > max_per) {
    n_panel <- n_panel + 1L
  }
  if (n_panel <= 2L) {
    ncol <- as.integer(n_panel)
    nrow <- 1L
  } else {
    ncol <- 2L
    nrow <- as.integer(ceiling(n_panel / 2))
  }
  list(
    n_panel = n_panel,
    nrow = nrow,
    ncol = ncol,
    per = as.integer(ceiling(n / n_panel))
  )
}

#' 拼图标题条
.np_compound_overlap_compose <- function(panels, ncol, main_title, subtitle) {
  if (!requireNamespace("cowplot", quietly = TRUE)) {
    stop("Install cowplot for multi-panel compound overlap figures", call. = FALSE)
  }
  n_panel <- length(panels)
  nrow <- as.integer(ceiling(n_panel / ncol))
  n_slot <- nrow * ncol
  if (length(panels) < n_slot) {
    panels <- c(panels, rep(list(cowplot::ggdraw()), n_slot - length(panels)))
  }
  grid_plot <- cowplot::plot_grid(plotlist = panels, ncol = ncol)
  title <- cowplot::ggdraw() +
    cowplot::draw_label(main_title, fontface = "bold", size = 13, hjust = 0.5)
  sub <- cowplot::ggdraw() +
    cowplot::draw_label(subtitle, size = 9, color = "grey35", hjust = 0.5)
  cowplot::plot_grid(title, sub, grid_plot, ncol = 1, rel_heights = c(0.04, 0.03, 0.93))
}

#' 均分排名子图（适配单药 70–80 / 多药合并）
np_plot_compound_overlap_panels <- function(summary_df,
                                            target_per = 14L,
                                            max_per = 16L,
                                            ncol = NULL) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
  need <- c("compound_id", "compound_name", "n_overlap_targets")
  miss <- setdiff(need, names(summary_df))
  if (length(miss)) stop("summary_df 缺列: ", paste(miss, collapse = ", "), call. = FALSE)

  df <- summary_df
  df$n_overlap_targets <- as.numeric(df$n_overlap_targets)
  df <- df[order(-df$n_overlap_targets, df$compound_name), , drop = FALSE]
  n <- nrow(df)
  if (!n) stop("compound summary is empty", call. = FALSE)

  grid <- np_choose_compound_panel_grid(n, target_per = target_per, max_per = max_per)
  n_panel <- grid$n_panel
  if (!is.null(ncol)) {
    grid$ncol <- as.integer(ncol)
    grid$nrow <- as.integer(ceiling(n_panel / grid$ncol))
  }
  base <- n %/% n_panel
  rem <- n %% n_panel
  sizes <- rep(base, n_panel)
  if (rem > 0) sizes[seq_len(rem)] <- sizes[seq_len(rem)] + 1L
  cols <- np_compound_panel_palette(n_panel)

  panels <- vector("list", n_panel)
  idx <- 1L
  for (i in seq_len(n_panel)) {
    take <- sizes[i]
    part <- df[idx:(idx + take - 1L), , drop = FALSE]
    rank_lo <- idx
    rank_hi <- idx + take - 1L
    idx <- idx + take
    title <- sprintf("Ranks %d–%d  ·  n = %d", rank_lo, rank_hi, nrow(part))
    panels[[i]] <- .np_compound_overlap_one_panel(
      part, title, panel_color = cols[i], show_x = TRUE,
      wrap_width = 38, label_max = 40
    )
  }
  .np_compound_overlap_compose(
    panels, grid$ncol,
    "Compound–disease overlap targets (equal panels)",
    sprintf(
      "Chemical names · %d compounds · %d×%d panels (~%d each, by rank)",
      n, grid$nrow, grid$ncol, grid$per
    )
  )
}

#' 按药物分面子图；单药成分过多时再均分，同药同色系
#' @param edges 需 herb_en, compound_id, compound_name, target_gene
np_plot_compound_overlap_by_herb <- function(edges,
                                             target_per = 14L,
                                             max_per = 16L,
                                             ncol = 2L) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
  need <- c("herb_en", "compound_id", "compound_name", "target_gene")
  miss <- setdiff(need, names(edges))
  if (length(miss)) stop("edges 缺列: ", paste(miss, collapse = ", "), call. = FALSE)

  agg <- stats::aggregate(
    target_gene ~ herb_en + compound_id + compound_name,
    data = edges,
    FUN = function(x) length(unique(x))
  )
  names(agg)[names(agg) == "target_gene"] <- "n_overlap_targets"
  herbs <- names(sort(table(agg$herb_en), decreasing = TRUE))
  herb_cols <- setNames(np_compound_panel_palette(length(herbs)), herbs)

  panels <- list()
  for (h in herbs) {
    d <- agg[agg$herb_en == h, , drop = FALSE]
    d <- d[order(-d$n_overlap_targets, d$compound_name), , drop = FALSE]
    n_h <- nrow(d)
    base_col <- herb_cols[[h]]
    if (n_h <= max_per) {
      panels[[length(panels) + 1]] <- .np_compound_overlap_one_panel(
        d, sprintf("%s  ·  n = %d", h, n_h), panel_color = base_col,
        show_x = TRUE, wrap_width = 36, label_max = 38
      )
    } else {
      # split large herb into equal chunks; shade variants of same color
      n_sub <- as.integer(ceiling(n_h / target_per))
      while (as.integer(ceiling(n_h / n_sub)) > max_per) n_sub <- n_sub + 1L
      base_sz <- n_h %/% n_sub
      rem <- n_h %% n_sub
      sizes <- rep(base_sz, n_sub)
      if (rem > 0) sizes[seq_len(rem)] <- sizes[seq_len(rem)] + 1L
      shades <- .np_shade_variants(base_col, n_sub)
      idx <- 1L
      for (s in seq_len(n_sub)) {
        part <- d[idx:(idx + sizes[s] - 1L), , drop = FALSE]
        idx <- idx + sizes[s]
        panels[[length(panels) + 1]] <- .np_compound_overlap_one_panel(
          part,
          sprintf("%s (%d/%d)  ·  n = %d", h, s, n_sub, nrow(part)),
          panel_color = shades[s],
          show_x = TRUE, wrap_width = 36, label_max = 38
        )
      }
    }
  }
  n_panel <- length(panels)
  ncol <- as.integer(ncol)
  nrow <- as.integer(ceiling(n_panel / ncol))
  .np_compound_overlap_compose(
    panels, ncol,
    "Compound–disease overlap targets by herb",
    sprintf(
      "Chemical names · %d herbs · %d panels · large herbs auto-split",
      length(herbs), n_panel
    )
  )
}

#' 图高：均分子图
np_compound_overlap_panels_height <- function(summary_df,
                                              target_per = 14L,
                                              max_per = 16L,
                                              ncol = NULL,
                                              per_row = 0.26,
                                              min_h = 10,
                                              max_h = 28) {
  n <- nrow(summary_df)
  grid <- np_choose_compound_panel_grid(n, target_per = target_per, max_per = max_per)
  if (!is.null(ncol)) {
    grid$ncol <- as.integer(ncol)
    grid$nrow <- as.integer(ceiling(grid$n_panel / grid$ncol))
  }
  h <- 1.8 + grid$nrow * grid$per * per_row
  as.numeric(max(min_h, min(max_h, h)))
}

#' 图高：按药分面（含大药再拆分）
np_compound_overlap_by_herb_height <- function(edges,
                                               target_per = 14L,
                                               max_per = 16L,
                                               ncol = 2L,
                                               per_row = 0.24,
                                               min_h = 10,
                                               max_h = 30) {
  agg <- unique(edges[, c("herb_en", "compound_id")])
  herb_n <- table(agg$herb_en)
  n_panel <- 0L
  max_per_panel <- 0L
  for (nn in as.integer(herb_n)) {
    if (nn <= max_per) {
      n_panel <- n_panel + 1L
      max_per_panel <- max(max_per_panel, nn)
    } else {
      n_sub <- as.integer(ceiling(nn / target_per))
      while (as.integer(ceiling(nn / n_sub)) > max_per) n_sub <- n_sub + 1L
      n_panel <- n_panel + n_sub
      max_per_panel <- max(max_per_panel, as.integer(ceiling(nn / n_sub)))
    }
  }
  nrow <- as.integer(ceiling(n_panel / ncol))
  h <- 1.8 + nrow * max_per_panel * per_row
  as.numeric(max(min_h, min(max_h, h)))
}

#' 兼容旧接口：单图水平柱
np_plot_compound_overlap_bar <- function(summary_df, top_n = NULL, style = c("bar", "lollipop")) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
  style <- match.arg(style)
  df <- summary_df
  if (!nrow(df)) stop("compound overlap summary is empty", call. = FALSE)
  df$n_overlap_targets <- as.numeric(df$n_overlap_targets)
  df <- df[order(df$n_overlap_targets, df$compound_name), , drop = FALSE]
  if (!is.null(top_n) && is.finite(top_n) && top_n > 0 && top_n < nrow(df)) {
    df <- utils::tail(df, as.integer(top_n))
  }
  lab <- as.character(df$compound_name)
  miss <- is.na(lab) | !nzchar(lab)
  lab[miss] <- as.character(df$compound_id[miss])
  if (exists("np_wrap_term", mode = "function")) lab <- np_wrap_term(lab, width = 36)
  df$ylab <- factor(lab, levels = unique(lab))
  col0 <- np_compound_panel_palette(1)
  p <- ggplot2::ggplot(df, ggplot2::aes(n_overlap_targets, ylab, fill = n_overlap_targets)) +
    ggplot2::geom_col(width = 0.72, color = NA) +
    ggplot2::scale_fill_gradient(low = "#FADBD8", high = col0, name = "Overlap\ntargets") +
    ggplot2::geom_text(
      ggplot2::aes(label = n_overlap_targets),
      hjust = -0.2, size = 2.5, color = "grey20"
    ) +
    ggplot2::scale_x_continuous(expand = ggplot2::expansion(mult = c(0, 0.14))) +
    ggplot2::labs(
      title = "Compound–disease overlap targets",
      subtitle = sprintf("Chemical names only (n = %d)", nrow(df)),
      x = "Overlap target count", y = NULL
    )
  np_apply_journal(p) +
    ggplot2::theme(
      axis.text.y = ggplot2::element_text(size = 6.5, lineheight = 0.9, hjust = 1),
      legend.position = "right",
      panel.grid.major.y = ggplot2::element_blank(),
      plot.margin = ggplot2::margin(10, 16, 10, 8)
    )
}

#' Suggested figure height (inches) for a single full compound list
np_compound_overlap_fig_height <- function(n, per_row = 0.175, min_h = 8, max_h = 28) {
  h <- max(min_h, min(max_h, 1.8 + n * per_row))
  as.numeric(h)
}

#' GO 气泡 — 交付 BP/CC/MF 分面：X=enrichment，size=count，color=-log10(pvalue)
np_plot_go_bubble <- function(go_df, top_n = 10) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
  df <- go_df
  df$pvalue <- as.numeric(df$pvalue)
  df$enrichment <- as.numeric(df$enrichment)
  df$count <- as.numeric(df$count)
  if (!"ontology" %in% names(df)) df$ontology <- "BP"
  df$ontology <- factor(as.character(df$ontology), levels = c("BP", "CC", "MF"))
  df$neglogp <- -log10(pmax(df$pvalue, 1e-300))

  # 每个 ontology 取 top_n（按 enrichment 降序，对齐交付气泡）
  parts <- split(df, df$ontology)
  parts <- lapply(parts, function(d) {
    d <- d[order(-d$enrichment, d$pvalue), , drop = FALSE]
    utils::head(d, top_n)
  })
  df <- do.call(rbind, parts)
  rownames(df) <- NULL

  df$term_lab <- np_wrap_term(df$term, width = 36)
  # 分面内：enrichment 高的在上
  df <- df[order(df$ontology, df$enrichment, -df$neglogp), , drop = FALSE]
  df$term_lab <- factor(df$term_lab, levels = unique(df$term_lab))

  p <- ggplot2::ggplot(
    df,
    ggplot2::aes(enrichment, term_lab, size = count, color = neglogp)
  ) +
    ggplot2::geom_point(alpha = 0.92) +
    ggplot2::facet_grid(
      ontology ~ .,
      scales = "free_y",
      space = "free_y"
    ) +
    ggplot2::scale_color_gradientn(
      colours = np_go_pval_cols,
      name = "-log 10 (pvalue)"
    ) +
    ggplot2::scale_size_continuous(
      range = c(2.5, 10),
      name = "count",
      breaks = function(x) pretty(x, n = 3)
    ) +
    ggplot2::scale_x_continuous(expand = ggplot2::expansion(mult = c(0.04, 0.08))) +
    ggplot2::labs(x = NULL, y = NULL) +
    ggplot2::guides(
      color = ggplot2::guide_colorbar(order = 1, barwidth = 0.7, barheight = 5),
      size = ggplot2::guide_legend(
        order = 2,
        override.aes = list(color = "grey30")
      )
    ) +
    np_theme_enrich(8.2) +
    ggplot2::theme(
      strip.text.y = ggplot2::element_text(angle = 0, face = "bold", size = 10),
      panel.spacing.y = ggplot2::unit(0.4, "lines"),
      legend.position = "right"
    )
  p
}

#' GO 柱状 — 交付竖柱：Y=Enrichment，按 BP/CC/MF 分组着色，柱顶数值
np_plot_go_bar <- function(go_df, top_n = 10) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
  df <- go_df
  df$enrichment <- as.numeric(df$enrichment)
  df$pvalue <- as.numeric(df$pvalue)
  if (!"ontology" %in% names(df)) df$ontology <- "BP"
  df$ontology <- factor(as.character(df$ontology), levels = c("BP", "CC", "MF"))

  parts <- split(df, df$ontology)
  parts <- lapply(parts, function(d) {
    d <- d[order(-d$enrichment, d$pvalue), , drop = FALSE]
    utils::head(d, top_n)
  })
  df <- do.call(rbind, parts)
  rownames(df) <- NULL

  # x 顺序：ontology 内 enrichment 降序
  df <- df[order(df$ontology, -df$enrichment), , drop = FALSE]
  df$term_x <- factor(df$term, levels = unique(df$term))
  df$lab <- sprintf("%.2f", df$enrichment)
  ont_lab <- c(
    BP = "Biological process",
    CC = "Cellular component",
    MF = "Molecular function"
  )

  p <- ggplot2::ggplot(
    df,
    ggplot2::aes(term_x, enrichment, fill = ontology)
  ) +
    ggplot2::geom_col(width = 0.78, color = NA, show.legend = TRUE) +
    ggplot2::geom_text(
      ggplot2::aes(label = lab),
      vjust = -0.35,
      size = 2.4,
      color = "grey15"
    ) +
    ggplot2::facet_grid(
      . ~ ontology,
      scales = "free_x",
      space = "free_x",
      labeller = ggplot2::labeller(ontology = ont_lab),
      switch = "x"
    ) +
    ggplot2::scale_fill_manual(
      values = np_go_bar_cols,
      name = NULL,
      breaks = c("BP", "CC", "MF")
    ) +
    ggplot2::scale_y_continuous(
      expand = ggplot2::expansion(mult = c(0, 0.12))
    ) +
    ggplot2::labs(x = NULL, y = "Enrichment") +
    ggplot2::theme_classic(base_size = 11) +
    ggplot2::theme(
      axis.text.x = ggplot2::element_text(
        angle = 70, hjust = 1, vjust = 1, size = 6.5, color = "grey25",
        lineheight = 0.9
      ),
      axis.text.y = ggplot2::element_text(size = 10),
      axis.title.y = ggplot2::element_text(size = 12, face = "bold"),
      strip.background = ggplot2::element_blank(),
      strip.placement = "outside",
      strip.text = ggplot2::element_text(size = 10, face = "bold"),
      legend.position = "top",
      legend.justification = "right",
      legend.direction = "horizontal",
      plot.margin = ggplot2::margin(10, 12, 6, 8),
      plot.title = ggplot2::element_blank(),
      panel.spacing.x = ggplot2::unit(0.8, "lines")
    )
  p
}

#' KEGG 棒棒糖 — 交付：Group 分色线段+点，size=Count，X=-log10(pvalue)
np_plot_kegg_lollipop <- function(kegg_df, top_n = 20) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
  df <- np_prep_kegg_df(kegg_df, top_n = top_n)

  p <- ggplot2::ggplot(df, ggplot2::aes(neglogp, term_plot, color = Group)) +
    ggplot2::geom_segment(
      ggplot2::aes(x = 0, xend = neglogp, y = term_plot, yend = term_plot),
      linewidth = 0.55, show.legend = FALSE
    ) +
    ggplot2::geom_point(ggplot2::aes(size = count), alpha = 0.95) +
    ggplot2::scale_color_manual(
      values = np_kegg_group_cols,
      name = "Group",
      drop = FALSE
    ) +
    ggplot2::scale_size_continuous(
      range = c(2.8, 8.5),
      name = "Count",
      breaks = function(x) pretty(x, n = 5)
    ) +
    ggplot2::scale_x_continuous(
      name = "-log10(pvalue)",
      expand = ggplot2::expansion(mult = c(0, 0.06))
    ) +
    ggplot2::labs(y = NULL) +
    ggplot2::guides(
      color = ggplot2::guide_legend(order = 2, override.aes = list(size = 3.5)),
      size = ggplot2::guide_legend(order = 1, override.aes = list(color = "grey30"))
    ) +
    np_theme_enrich(8) +
    ggplot2::theme(legend.position = "right")
  p
}

#' KEGG 柱状 — 交付：Group 分色水平柱，X=-log10(pvalue)
np_plot_kegg_bar <- function(kegg_df, top_n = 20) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
  df <- np_prep_kegg_df(kegg_df, top_n = top_n)

  p <- ggplot2::ggplot(df, ggplot2::aes(neglogp, term_plot, fill = Group)) +
    ggplot2::geom_col(width = 0.72, color = NA) +
    ggplot2::scale_fill_manual(
      values = np_kegg_group_cols,
      name = "Group",
      drop = FALSE
    ) +
    ggplot2::scale_x_continuous(
      name = "-log10(pvalue)",
      expand = ggplot2::expansion(mult = c(0, 0.06))
    ) +
    ggplot2::labs(y = NULL) +
    np_theme_enrich(8) +
    ggplot2::theme(
      legend.position = "right",
      panel.grid.major.y = ggplot2::element_line(color = "grey90", linewidth = 0.3)
    )
  p
}

# KEGG chord / circos qualitative pathway colors (delivery-style multi-hue)
np_kegg_chord_palette <- function(n) {
  base <- c(
    "#E69F00", "#D55E00", "#CC79A7", "#882255", "#AA3377",
    "#EE6677", "#E64B35", "#F39B7F", "#0072B2", "#56B4E9",
    "#009E73", "#00A087", "#44AA99", "#117733", "#332288",
    "#3C5488", "#661100", "#999933", "#DDCC77", "#88CCEE"
  )
  if (n <= length(base)) return(base[seq_len(n)])
  grDevices::colorRampPalette(base)(n)
}

#' Build gene×pathway incidence + metadata from KEGG enrichment (needs geneID)
np_prep_kegg_chord <- function(kegg_df, top_n = 20) {
  df <- kegg_df
  if (any(duplicated(names(df)))) df <- df[, !duplicated(names(df)), drop = FALSE]
  gene_col <- if ("geneID" %in% names(df)) {
    "geneID"
  } else if ("geneId" %in% names(df)) {
    "geneId"
  } else if ("gene" %in% names(df)) {
    "gene"
  } else {
    NA_character_
  }
  if (is.na(gene_col)) {
    stop(
      "KEGG chord requires a geneID / geneId / gene column with slash-separated symbols",
      call. = FALSE
    )
  }
  term_col <- if ("term" %in% names(df)) "term" else names(df)[1]
  p_col <- if ("pvalue" %in% names(df)) {
    "pvalue"
  } else if ("padj" %in% names(df)) {
    "padj"
  } else if ("p.adjust" %in% names(df)) {
    "p.adjust"
  } else {
    stop("KEGG chord requires pvalue / padj / p.adjust", call. = FALSE)
  }

  out <- data.frame(
    term = as.character(df[[term_col]]),
    pvalue = as.numeric(df[[p_col]]),
    geneID = as.character(df[[gene_col]]),
    stringsAsFactors = FALSE
  )
  out <- out[!is.na(out$pvalue) & nzchar(out$geneID), , drop = FALSE]
  out <- out[order(out$pvalue), , drop = FALSE]
  out <- utils::head(out, top_n)
  out$neglogp <- -log10(pmax(out$pvalue, 1e-300))
  out$term <- make.unique(out$term, sep = " ")

  edge_list <- lapply(seq_len(nrow(out)), function(i) {
    genes <- unlist(strsplit(out$geneID[i], "/|;|,|\\|", perl = TRUE), use.names = FALSE)
    genes <- trimws(genes)
    genes <- genes[nzchar(genes) & !is.na(genes)]
    if (!length(genes)) return(NULL)
    data.frame(gene = genes, pathway = out$term[i], stringsAsFactors = FALSE)
  })
  edges <- do.call(rbind, edge_list)
  if (is.null(edges) || !nrow(edges)) {
    stop("No gene–pathway edges parsed from geneID", call. = FALSE)
  }
  edges <- unique(edges)

  genes <- sort(unique(edges$gene))
  pathways <- out$term
  mat <- matrix(0, nrow = length(genes), ncol = length(pathways),
                dimnames = list(genes, pathways))
  for (i in seq_len(nrow(edges))) {
    mat[edges$gene[i], edges$pathway[i]] <- 1
  }
  # order genes by degree (hubs first) for readable left arc
  gene_deg <- rowSums(mat)
  genes <- names(sort(gene_deg, decreasing = TRUE))
  mat <- mat[genes, pathways, drop = FALSE]

  list(
    mat = mat,
    pathways = pathways,
    genes = genes,
    neglogp = setNames(out$neglogp, out$term),
    pvalue = setNames(out$pvalue, out$term),
    n_edges = nrow(edges)
  )
}

#' Draw KEGG gene–pathway chord (circlize; English labels). Call inside an open device.
np_draw_kegg_chord <- function(chord, label_genes = TRUE) {
  if (!requireNamespace("circlize", quietly = TRUE)) {
    stop("Install circlize for KEGG chord / circos plots", call. = FALSE)
  }
  mat <- chord$mat
  pathways <- chord$pathways
  genes <- chord$genes
  neglogp <- chord$neglogp[pathways]
  n_pw <- length(pathways)
  n_gene <- length(genes)

  pw_cols <- np_kegg_chord_palette(n_pw)
  names(pw_cols) <- pathways
  # -log10(p) scale (green → blue) — used for gene band to match delivery refs
  nl_range <- range(neglogp, finite = TRUE)
  if (diff(nl_range) < 1e-9) nl_range <- nl_range + c(-0.5, 0.5)
  pval_pal <- grDevices::colorRampPalette(
    c("#B8E186", "#7FC97F", "#41B6C4", "#225EA8", "#081D58")
  )(100)
  neglog_to_col <- function(x) {
    t <- (x - nl_range[1]) / (nl_range[2] - nl_range[1])
    t <- pmax(0, pmin(1, t))
    pval_pal[pmax(1L, pmin(100L, as.integer(round(t * 99)) + 1L))]
  }

  # Gene continuous band = best-pathway -log10(p) (delivery style; no invented logFC)
  gene_best_nl <- vapply(genes, function(g) {
    hit <- pathways[mat[g, ] > 0]
    if (!length(hit)) return(NA_real_)
    max(neglogp[hit], na.rm = TRUE)
  }, numeric(1))
  gene_cols_map <- setNames(
    ifelse(is.na(gene_best_nl), "#D9D9D9", neglog_to_col(gene_best_nl)),
    genes
  )
  grid.col <- c(gene_cols_map, pw_cols)

  # gaps: small within blocks; modest split between gene ↔ pathway hemispheres
  gaps <- c(rep(0.5, max(0, n_gene - 1)), 3.5, rep(1.0, max(0, n_pw - 1)), 3.5)
  circlize::circos.clear()
  circlize::circos.par(
    start.degree = 90,
    gap.after = gaps,
    clock.wise = FALSE,
    track.margin = c(0.01, 0.01),
    cell.padding = c(0.002, 0, 0.002, 0),
    points.overflow.warning = FALSE,
    canvas.xlim = c(-1.15, 1.55),
    canvas.ylim = c(-1.15, 1.15)
  )

  # link colors: pathway-colored ribbons (matrix form; vector col is unreliable in circlize 0.4.18)
  col_mat <- matrix(
    NA_character_,
    nrow = nrow(mat), ncol = ncol(mat),
    dimnames = dimnames(mat)
  )
  for (j in seq_len(ncol(mat))) {
    col_mat[, j] <- grDevices::adjustcolor(pw_cols[[colnames(mat)[j]]], alpha.f = 0.48)
  }
  col_mat[mat == 0] <- NA

  circlize::chordDiagram(
    mat,
    order = c(genes, pathways),
    grid.col = grid.col,
    col = col_mat,
    transparency = 0,
    annotationTrack = "grid",
    annotationTrackHeight = 0.06,
    # only one outer track for gene labels — do NOT preallocate a 2nd color track
    # (that duplicated grid.col and created an extra outermost color ring)
    preAllocateTracks = list(
      list(track.height = if (label_genes) 0.10 else 0.02)
    ),
    directional = 1,
    direction.type = "diffHeight",
    diffHeight = 0.02,
    link.sort = TRUE,
    link.largest.ontop = TRUE
  )

  if (label_genes) {
    cex_lab <- if (n_gene > 90) 0.26 else if (n_gene > 60) 0.32 else 0.42
    circlize::circos.trackPlotRegion(
      track.index = 1,
      bg.border = NA,
      panel.fun = function(x, y) {
        sector <- circlize::get.cell.meta.data("sector.index")
        if (!sector %in% genes) return(invisible(NULL))
        xlim <- circlize::get.cell.meta.data("xlim")
        circlize::circos.text(
          mean(xlim), 0.15, sector,
          facing = "clockwise",
          niceFacing = TRUE,
          adj = c(0, 0.5),
          cex = cex_lab,
          col = "grey20"
        )
      }
    )
  }

  # legends in right canvas margin (circle stays visually centered)
  x0 <- 1.05
  y_top <- 1.05
  n_bar <- 80
  bar_x <- seq(x0, x0 + 0.42, length.out = n_bar + 1)
  bar_cols <- grDevices::colorRampPalette(
    c("#B8E186", "#7FC97F", "#41B6C4", "#225EA8", "#081D58")
  )(n_bar)
  for (i in seq_len(n_bar)) {
    graphics::rect(bar_x[i], y_top - 0.045, bar_x[i + 1], y_top, col = bar_cols[i], border = NA)
  }
  graphics::rect(bar_x[1], y_top - 0.045, bar_x[n_bar + 1], y_top, border = "grey40", lwd = 0.6)
  graphics::text(x0 + 0.21, y_top + 0.07, "-log10(pvalue)", cex = 0.78, font = 2)
  graphics::text(bar_x[1], y_top - 0.09, sprintf("%.0f", nl_range[1]), cex = 0.65, adj = c(0.5, 1))
  graphics::text(bar_x[n_bar + 1], y_top - 0.09, sprintf("%.0f", nl_range[2]), cex = 0.65, adj = c(0.5, 1))

  graphics::text(x0 + 0.02, y_top - 0.16, "KEGG Pathways", cex = 0.72, font = 2, adj = c(0, 0.5))
  leg_cex <- if (n_pw > 18) 0.52 else 0.6
  step <- if (n_pw > 18) 0.055 else 0.062
  y_leg <- y_top - 0.22
  for (i in seq_len(n_pw)) {
    yy <- y_leg - (i - 1) * step
    if (yy < -1.05) break
    graphics::points(x0 + 0.02, yy, pch = 19, col = pw_cols[i], cex = 1.05)
    graphics::text(x0 + 0.055, yy, pathways[i], adj = c(0, 0.5), cex = leg_cex, col = "grey15")
  }

  circlize::circos.clear()
  invisible(chord)
}

#' Save KEGG chord/circos as bilingual PNG+SVG (base graphics; not ggplot)
np_save_kegg_chord <- function(kegg_df, out_dir, stem = "圈图_KEGG_Circos",
                               top_n = 20, label_genes = TRUE,
                               width = 11, height = 9, dpi = 600) {
  chord <- np_prep_kegg_chord(kegg_df, top_n = top_n)
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  stem <- sub("\\.(png|svg|pdf)$", "", stem, ignore.case = TRUE)
  fpng <- file.path(out_dir, paste0(stem, ".png"))
  fsvg <- file.path(out_dir, paste0(stem, ".svg"))

  draw_one <- function() {
    op <- par(mar = c(0.4, 0.4, 0.4, 0.4), bg = "white", xpd = NA)
    on.exit(par(op), add = TRUE)
    np_draw_kegg_chord(chord, label_genes = label_genes)
  }

  grDevices::png(fpng, width = width, height = height, units = "in", res = dpi, bg = "white")
  tryCatch(draw_one(), finally = grDevices::dev.off())

  ok_svg <- FALSE
  if (requireNamespace("svglite", quietly = TRUE)) {
    try({
      svglite::svglite(fsvg, width = width, height = height, bg = "white")
      draw_one()
      grDevices::dev.off()
      ok_svg <- TRUE
    }, silent = TRUE)
  }
  if (!ok_svg) {
    try({
      grDevices::svg(fsvg, width = width, height = height, bg = "white")
      draw_one()
      grDevices::dev.off()
      ok_svg <- TRUE
    }, silent = TRUE)
  }
  invisible(list(png = fpng, svg = if (ok_svg) fsvg else NA_character_, chord = chord))
}

