# 医学 SRMA 森林图（VizStandards / journal muted；图面 English）

.plot_muted <- function() {
  if (exists("bioinfo_palette") && length(bioinfo_palette) >= 3L) {
    list(point = bioinfo_palette[[3]], diamond = bioinfo_palette[[1]], line = "grey40")
  } else {
    list(point = "#5B8FA8", diamond = "#C17B7B", line = "grey40")
  }
}

#' 经典 HR 森林图（研究 + 合并菱形）
plot_hr_forest <- function(dat, fit, title, subtitle = NULL) {
  cols <- .plot_muted()
  stud <- data.frame(
    label = dat$label,
    hr = exp(dat$yi),
    lo = exp(dat$yi - 1.96 * dat$sei),
    hi = exp(dat$yi + 1.96 * dat$sei),
    weight = as.numeric(weights(fit)),
    type = "study",
    stringsAsFactors = FALSE
  )
  pool <- data.frame(
    label = sprintf("Pooled REML (I2=%.0f%%)", fit$I2),
    hr = exp(as.numeric(fit$b)),
    lo = exp(as.numeric(fit$ci.lb)),
    hi = exp(as.numeric(fit$ci.ub)),
    weight = 100,
    type = "pool",
    stringsAsFactors = FALSE
  )
  plot_df <- rbind(stud, pool)
  plot_df$label <- factor(plot_df$label, levels = rev(plot_df$label))

  ann <- sprintf(
    "HR %.2f (%.2f-%.2f); k=%d; tau2=%.3f",
    exp(as.numeric(fit$b)),
    exp(as.numeric(fit$ci.lb)),
    exp(as.numeric(fit$ci.ub)),
    fit$k,
    as.numeric(fit$tau2)
  )

  p <- ggplot2::ggplot(plot_df, ggplot2::aes(x = hr, y = label)) +
    ggplot2::geom_vline(xintercept = 1, linetype = 2, color = "grey55", linewidth = 0.4) +
    ggplot2::geom_errorbar(
      ggplot2::aes(xmin = lo, xmax = hi),
      orientation = "y", width = 0.18, color = cols$line, linewidth = 0.45
    ) +
    ggplot2::geom_point(
      data = subset(plot_df, type == "study"),
      shape = 15, size = 2.6, color = cols$point
    ) +
    ggplot2::geom_point(
      data = subset(plot_df, type == "pool"),
      shape = 18, size = 4.2, color = cols$diamond
    ) +
    ggplot2::scale_x_log10(
      breaks = c(0.2, 0.5, 1, 2),
      labels = c("0.2", "0.5", "1", "2")
    ) +
    ggplot2::coord_cartesian(xlim = c(
      max(0.08, min(plot_df$lo) * 0.85),
      max(2.2, max(plot_df$hi) * 1.05)
    )) +
    ggplot2::labs(
      title = title,
      subtitle = if (is.null(subtitle) || !nzchar(subtitle)) NULL else subtitle,
      caption = ann,
      x = "Hazard ratio (log scale)",
      y = NULL
    )

  if (exists("theme_journal", mode = "function")) {
    p <- p + theme_journal()
  } else {
    p <- p + ggplot2::theme_bw(base_size = 11)
  }
  p + ggplot2::theme(
    panel.grid.minor = ggplot2::element_blank(),
    axis.text.y = ggplot2::element_text(size = 9)
  )
}

#' 留一法森林图
plot_loo_forest <- function(loo_df, title) {
  cols <- .plot_muted()
  loo_df$label <- paste0("Omit ", loo_df$omitted)
  loo_df$label <- factor(loo_df$label, levels = rev(loo_df$label))
  ggplot2::ggplot(loo_df, ggplot2::aes(x = hr, y = label)) +
    ggplot2::geom_vline(xintercept = 1, linetype = 2, color = "grey55", linewidth = 0.4) +
    ggplot2::geom_errorbar(
      ggplot2::aes(xmin = hr_lo, xmax = hr_hi),
      orientation = "y", width = 0.18, color = cols$line, linewidth = 0.45
    ) +
    ggplot2::geom_point(shape = 15, size = 2.6, color = cols$point) +
    ggplot2::scale_x_log10() +
    ggplot2::labs(
      title = title,
      subtitle = "Pooled HR after omitting one trial",
      x = "Hazard ratio (log scale)",
      y = NULL
    ) +
    (if (exists("theme_journal", mode = "function")) theme_journal() else ggplot2::theme_bw(base_size = 11))
}
