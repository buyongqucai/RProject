# 医学 SRMA 出图（对齐 PRISMA / Cochrane / 高分刊图套；VizStandards）
# 图面 English；标签黑；DPI 由 delivery_save_plot 保证

.plot_muted <- function() {
  if (exists("bioinfo_palette") && length(bioinfo_palette) >= 3L) {
    list(point = bioinfo_palette[[3]], diamond = bioinfo_palette[[1]], line = "grey40")
  } else {
    list(point = "#5B8FA8", diamond = "#C17B7B", line = "grey40")
  }
}

.theme_meta <- function(p) {
  if (exists("theme_journal", mode = "function")) {
    p <- p + theme_journal()
  } else {
    p <- p + ggplot2::theme_bw(base_size = 11)
  }
  p + ggplot2::theme(
    panel.grid.minor = ggplot2::element_blank(),
    axis.text.y = ggplot2::element_text(size = 9, colour = "#000000"),
    axis.text.x = ggplot2::element_text(colour = "#000000"),
    plot.title = ggplot2::element_text(colour = "#000000"),
    plot.subtitle = ggplot2::element_text(colour = "#000000"),
    plot.caption = ggplot2::element_text(colour = "#000000", size = 8)
  )
}

#' 经典 HR 森林图（研究方块 + 合并菱形；右侧 HR 文本）
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
  plot_df$hr_txt <- sprintf("%.2f (%.2f-%.2f)", plot_df$hr, plot_df$lo, plot_df$hi)
  plot_df$label <- factor(plot_df$label, levels = rev(plot_df$label))

  ann <- sprintf(
    "HR %.2f (%.2f-%.2f); k=%d; I2=%.0f%%; tau2=%.3f",
    exp(as.numeric(fit$b)),
    exp(as.numeric(fit$ci.lb)),
    exp(as.numeric(fit$ci.ub)),
    fit$k,
    fit$I2,
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
    ggplot2::geom_text(
      ggplot2::aes(x = max(hi, na.rm = TRUE) * 1.35, label = hr_txt),
      hjust = 0, size = 2.7, colour = "#000000"
    ) +
    ggplot2::scale_x_log10(
      breaks = c(0.2, 0.5, 1, 2),
      labels = c("0.2", "0.5", "1", "2")
    ) +
    ggplot2::coord_cartesian(
      xlim = c(
        max(0.08, min(plot_df$lo, na.rm = TRUE) * 0.85),
        max(plot_df$hi, na.rm = TRUE) * 2.2
      ),
      clip = "off"
    ) +
    ggplot2::labs(
      title = title,
      subtitle = if (is.null(subtitle) || !nzchar(subtitle)) NULL else subtitle,
      caption = ann,
      x = "Hazard ratio (log scale)",
      y = NULL
    )
  .theme_meta(p) + ggplot2::theme(plot.margin = ggplot2::margin(8, 80, 8, 8))
}

#' 留一法森林图
plot_loo_forest <- function(loo_df, title) {
  cols <- .plot_muted()
  loo_df$label <- paste0("Omit ", loo_df$omitted)
  loo_df$label <- factor(loo_df$label, levels = rev(loo_df$label))
  p <- ggplot2::ggplot(loo_df, ggplot2::aes(x = hr, y = label)) +
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
    )
  .theme_meta(p)
}

#' PRISMA 2020 风格流程（计数来自 CSV；Pilot 须诚实标注）
plot_prisma_flow <- function(counts_df, title = "PRISMA flow (Pilot)") {
  stopifnot(all(c("stage", "n", "note") %in% names(counts_df)))
  counts_df$stage <- factor(counts_df$stage, levels = rev(counts_df$stage))
  counts_df$tile_lab <- sprintf("%s\nn=%s", as.character(counts_df$stage), counts_df$n)
  cols <- .plot_muted()
  p <- ggplot2::ggplot(counts_df, ggplot2::aes(x = 1, y = stage)) +
    ggplot2::geom_tile(
      width = 0.72, height = 0.72,
      fill = "#F7F7F7", color = cols$line, linewidth = 0.45
    ) +
    ggplot2::geom_text(
      ggplot2::aes(label = tile_lab),
      size = 3.2, colour = "#000000", lineheight = 0.95
    ) +
    ggplot2::labs(
      title = title,
      subtitle = "Hand-picked path; not multi-database search",
      x = NULL, y = NULL,
      caption = "Replace stage counts for L2 full SR"
    ) +
    ggplot2::theme_void(base_size = 11) +
    ggplot2::theme(
      plot.title = ggplot2::element_text(colour = "#000000", face = "bold"),
      plot.subtitle = ggplot2::element_text(colour = "#000000", size = 9),
      plot.caption = ggplot2::element_text(colour = "#000000", size = 8),
      plot.margin = ggplot2::margin(10, 10, 10, 10)
    )
  p
}

#' 漏斗图（k<10 仅视觉，不做 Egger 结论）
plot_funnel_hr <- function(dat, fit, title = "Funnel plot (OS)") {
  cols <- .plot_muted()
  df <- data.frame(
    yi = dat$yi,
    sei = dat$sei,
    label = dat$label,
    stringsAsFactors = FALSE
  )
  k <- nrow(df)
  cap <- if (k < 10) {
    sprintf("k=%d < 10: visual asymmetry only; do not interpret Egger test", k)
  } else {
    sprintf("k=%d: inspect asymmetry; report Egger if pre-specified", k)
  }
  p <- ggplot2::ggplot(df, ggplot2::aes(x = yi, y = sei)) +
    ggplot2::geom_vline(xintercept = as.numeric(fit$b), linetype = 2, color = "grey55") +
    ggplot2::geom_point(size = 2.8, color = cols$point, shape = 16) +
    ggplot2::scale_y_reverse() +
    ggplot2::labs(
      title = title,
      subtitle = "Effect (log HR) vs SE",
      x = "log(HR)",
      y = "Standard error",
      caption = cap
    )
  .theme_meta(p)
}

#' Baujat：异质性贡献（对齐高分文补充诊断图）
plot_baujat_hr <- function(fit, title = "Baujat plot (OS)") {
  # Capture metafor::baujat coordinates without keeping the base plot
  tmp <- tempfile(fileext = ".png")
  grDevices::png(tmp, width = 4, height = 4, units = "in", res = 72)
  bj <- tryCatch(metafor::baujat(fit, grid = FALSE), error = function(e) NULL)
  grDevices::dev.off()
  unlink(tmp)
  if (is.null(bj) || !nrow(as.data.frame(bj))) {
    lo <- metafor::leave1out(fit)
    bj_df <- data.frame(
      study = as.character(fit$slab),
      x = abs(as.numeric(lo$QE) - as.numeric(fit$QE)),
      y = abs(as.numeric(lo$estimate) - as.numeric(fit$b)),
      stringsAsFactors = FALSE
    )
  } else {
    bj_df <- as.data.frame(bj)
    # metafor returns x/y; attach slab if present
    if (!"study" %in% names(bj_df)) {
      bj_df$study <- if ("slab" %in% names(bj_df)) as.character(bj_df$slab) else as.character(fit$slab)
    }
    names(bj_df)[names(bj_df) == "x"] <- "x"
    names(bj_df)[names(bj_df) == "y"] <- "y"
  }
  cols <- .plot_muted()
  nudge <- max(bj_df$y, na.rm = TRUE)
  if (!is.finite(nudge) || nudge <= 0) nudge <- 0.01
  p <- ggplot2::ggplot(bj_df, ggplot2::aes(x = x, y = y, label = study)) +
    ggplot2::geom_point(size = 2.8, color = cols$point) +
    ggplot2::geom_text(nudge_y = nudge * 0.06, size = 2.6, colour = "#000000") +
    ggplot2::labs(
      title = title,
      subtitle = "Heterogeneity contribution vs influence",
      x = "Contribution to heterogeneity",
      y = "Influence on pooled estimate"
    )
  .theme_meta(p)
}

#' RoB 2 交通灯（长表：study × domain → judgement）
plot_rob2_traffic <- function(rob_long, title = "RoB 2 traffic light (Pilot)") {
  stopifnot(all(c("study_id", "domain", "judgement") %in% names(rob_long)))
  lvl <- c("Low", "Some concerns", "High")
  rob_long$judgement <- factor(rob_long$judgement, levels = lvl)
  # Short axis labels for PlotQA
  map_dom <- c(
    "D1 Randomization process" = "D1 Random",
    "D2 Deviations from intended interventions" = "D2 Deviations",
    "D3 Missing outcome data" = "D3 Missing",
    "D4 Measurement of the outcome" = "D4 Outcome",
    "D5 Selection of the reported result" = "D5 Reporting",
    "Overall" = "Overall"
  )
  rob_long$domain_short <- ifelse(
    rob_long$domain %in% names(map_dom),
    unname(map_dom[rob_long$domain]),
    rob_long$domain
  )
  rob_long$domain_short <- factor(rob_long$domain_short, levels = unique(rob_long$domain_short))
  rob_long$study_short <- gsub("_", " ", rob_long$study_id)
  fill_map <- c(Low = "#6B8F71", `Some concerns` = "#D4A574", High = "#C17B7B")
  p <- ggplot2::ggplot(rob_long, ggplot2::aes(x = domain_short, y = study_short, fill = judgement)) +
    ggplot2::geom_tile(color = "white", linewidth = 0.6) +
    ggplot2::scale_fill_manual(values = fill_map, drop = FALSE) +
    ggplot2::labs(
      title = title,
      subtitle = "Single-rater Pilot; dual rating required for L2",
      x = NULL, y = NULL, fill = "Judgement"
    )
  .theme_meta(p) +
    ggplot2::theme(
      axis.text.x = ggplot2::element_text(angle = 25, hjust = 1, colour = "#000000"),
      legend.position = "bottom"
    )
}

#' 亚组森林图（按 population 字段）
plot_subgroup_forest <- function(dat, group_col = "population", title = "OS subgroup by population") {
  stopifnot(group_col %in% names(dat))
  cols <- .plot_muted()
  groups <- unique(as.character(dat[[group_col]]))
  rows <- list()
  for (g in groups) {
    d <- dat[dat[[group_col]] == g, , drop = FALSE]
    if (nrow(d) < 1) next
    if (nrow(d) == 1) {
      rows[[length(rows) + 1]] <- data.frame(
        label = paste0(g, ": ", d$label[[1]]),
        hr = exp(d$yi[[1]]),
        lo = exp(d$yi[[1]] - 1.96 * d$sei[[1]]),
        hi = exp(d$yi[[1]] + 1.96 * d$sei[[1]]),
        type = "study",
        stringsAsFactors = FALSE
      )
    } else {
      fit <- metafor::rma(yi = yi, vi = vi, data = d, method = "REML")
      rows[[length(rows) + 1]] <- data.frame(
        label = sprintf("%s (k=%d, I2=%.0f%%)", g, fit$k, fit$I2),
        hr = exp(as.numeric(fit$b)),
        lo = exp(as.numeric(fit$ci.lb)),
        hi = exp(as.numeric(fit$ci.ub)),
        type = "pool",
        stringsAsFactors = FALSE
      )
    }
  }
  plot_df <- do.call(rbind, rows)
  plot_df$label <- factor(plot_df$label, levels = rev(plot_df$label))
  p <- ggplot2::ggplot(plot_df, ggplot2::aes(x = hr, y = label)) +
    ggplot2::geom_vline(xintercept = 1, linetype = 2, color = "grey55", linewidth = 0.4) +
    ggplot2::geom_errorbar(
      ggplot2::aes(xmin = lo, xmax = hi),
      orientation = "y", width = 0.18, color = cols$line, linewidth = 0.45
    ) +
    ggplot2::geom_point(shape = 18, size = 3.6, color = cols$diamond) +
    ggplot2::scale_x_log10() +
    ggplot2::labs(
      title = title,
      subtitle = "Exploratory Pilot; pre-register for L2",
      x = "Hazard ratio (log scale)",
      y = NULL
    )
  .theme_meta(p)
}
