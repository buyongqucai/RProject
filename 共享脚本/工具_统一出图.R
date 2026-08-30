# 四数据集统一出图：600 DPI、防标签遮挡、自适应画幅

FIG_DPI <- 600L

`%||%` <- function(x, y) if (is.null(x)) y else x

._fig_font_ready <- FALSE
setup_plot_fonts <- function(base_size = 12) {
  if (!._fig_font_ready) {
    assign("._fig_font_ready", TRUE, envir = topenv())
  }
  # ggplot 使用系统默认字体，避免 SimHei + Cairo + ggrepel 触发 invalid font type
  ggplot2::theme_set(ggplot2::theme_bw(base_size = base_size) +
                       ggplot2::theme(
                         plot.title = ggplot2::element_text(face = "bold", size = base_size + 1),
                         axis.text = ggplot2::element_text(size = base_size - 1),
                         legend.text = ggplot2::element_text(size = base_size - 2)
                       ))
  ""
}

ext_setup_font <- setup_plot_fonts

theme_no_overlap <- function() {
  ggplot2::theme(
    legend.position = "right",
    legend.box = "vertical",
    plot.margin = ggplot2::margin(10, 14, 10, 10),
    axis.text.x = ggplot2::element_text(angle = 0, hjust = 0.5),
    axis.text.y = ggplot2::element_text(size = rel(0.95))
  )
}

wrap_labels <- function(x, width = 40) {
  vapply(x, function(s) {
    if (is.na(s) || nchar(s) <= width) return(as.character(s))
    paste(strwrap(as.character(s), width = width), collapse = "\n")
  }, character(1), USE.NAMES = FALSE)
}

enrich_plot_size <- function(n_show, labels = NULL) {
  n <- max(1L, as.integer(n_show))
  max_chars <- if (length(labels)) max(nchar(as.character(labels)), na.rm = TRUE) else 40L
  list(
    width = max(12, 8 + max_chars * 0.12),
    height = max(9, n * 0.55 + max(0, (max_chars - 40) * 0.04))
  )
}

# clusterProfiler dotplot 默认 label_format 会截断为省略号；返回完整描述
enrich_full_labels <- function(x) as.character(x)

safe_ggsave <- function(filename, plot, width, height, ...) {
  setup_plot_fonts()
  has_st <- "showtext" %in% loadedNamespaces()
  if (has_st) try(showtext::showtext_auto(FALSE), silent = TRUE)
  on.exit(if (has_st) try(showtext::showtext_auto(TRUE), silent = TRUE), add = TRUE)
  args <- list(filename = filename, plot = plot, width = width, height = height, dpi = FIG_DPI, ...)
  if (requireNamespace("Cairo", quietly = TRUE)) {
    args$device <- Cairo::CairoPDF
  }
  do.call(ggplot2::ggsave, args)
  invisible(filename)
}

safe_pdf <- function(filename, width, height, code) {
  has_st <- "showtext" %in% loadedNamespaces()
  if (has_st) try(showtext::showtext_auto(FALSE), silent = TRUE)
  on.exit({
    if (has_st) try(showtext::showtext_auto(TRUE), silent = TRUE)
  }, add = TRUE)
  if (requireNamespace("Cairo", quietly = TRUE)) {
    Cairo::CairoPDF(filename, width = width, height = height, dpi = FIG_DPI)
  } else {
    pdf(filename, width = width, height = height)
  }
  on.exit(dev.off(), add = TRUE)
  force(code)
  invisible(filename)
}

save_enrich_plots <- function(res, base, title, tab_dir, fig_dir) {
  if (is.null(res) || nrow(as.data.frame(res)) == 0) {
    message("无富集结果: ", base)
    return(invisible(NULL))
  }
  setup_plot_fonts()
  df <- as.data.frame(res)
  write.csv(df, file.path(tab_dir, paste0(base, ".csv")), row.names = FALSE)
  n_show <- min(15, nrow(df))
  lbl_raw <- df$Description[seq_len(n_show)]
  sz <- enrich_plot_size(n_show, lbl_raw)
  lbl <- enrich_full_labels
  p_dot <- clusterProfiler::dotplot(res, showCategory = n_show, label_format = enrich_full_labels) +
    ggplot2::ggtitle(title) +
    ggplot2::theme(axis.text.y = ggplot2::element_text(size = 9)) +
    ggplot2::scale_y_discrete(labels = lbl)
  safe_ggsave(file.path(fig_dir, paste0(base, ".pdf")), p_dot, sz$width, sz$height)
  df_bar <- as.data.frame(res) %>% dplyr::slice_head(n = n_show) %>%
    dplyr::mutate(Description = enrich_full_labels(Description))
  p_bar <- ggplot2::ggplot(df_bar, ggplot2::aes(reorder(Description, Count), Count, fill = p.adjust)) +
    ggplot2::geom_col() + ggplot2::coord_flip() +
    ggplot2::scale_fill_gradient(low = "#E64B35", high = "#4DBBD5", trans = "log10") +
    ggplot2::labs(title = paste0(title, " (bar)"), x = NULL, y = "Count", fill = "p.adj") +
    ggplot2::theme(axis.text.y = ggplot2::element_text(size = 9)) +
    ggplot2::scale_y_discrete(labels = enrich_full_labels)
  safe_ggsave(file.path(fig_dir, paste0(base, "图.pdf")), p_bar, sz$width, sz$height)
  message("保存富集: ", base)
}

add_ggrepel <- function(p, data, mapping_label, fam = "", size = 3.2) {
  if (!requireNamespace("ggrepel", quietly = TRUE) || !nrow(data)) return(p)
  p + ggrepel::geom_text_repel(
    data = data, mapping = mapping_label, size = size,
    max.overlaps = 30, box.padding = 0.45, point.padding = 0.3,
    min.segment.length = 0, segment.size = 0.25, force = 2, force_pull = 0.5,
    show.legend = FALSE
  )
}
