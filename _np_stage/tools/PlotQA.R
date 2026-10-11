# 出图后审核 PlotQA — 项目级（SSOT: 统一可视化规范_VizStandards）
# 文档：../文档_docs/出图后审核_PlotQA.md
# 依赖：base R；ggplot 启发式需 ggplot2（项目已用）
#
# 钩子：
# - delivery_save_plot / 手动：viz_qa_after_plot(plot, plot_id)
# - 网络布局后：viz_qa_network_nodes(nodes_df, plot_id=...)

.viz_qa_severity_rank <- function(x) {
  match(toupper(as.character(x)), c("PASS", "WARN", "FAIL"), nomatch = 1L)
}

.viz_qa_worse <- function(...) {
  vals <- toupper(unlist(list(...), use.names = FALSE))
  vals <- vals[nzchar(vals) & !is.na(vals)]
  if (!length(vals)) return("PASS")
  c("PASS", "WARN", "FAIL")[max(.viz_qa_severity_rank(vals))]
}

#' 标签长度 / 版式风险启发式
#'
#' @param plot_or_data ggplot、character 标签向量、或含 label/name 列的 data.frame
#' @param max_warn 单标签字符数 WARN 阈值
#' @param max_fail 单标签字符数 FAIL 阈值（严重版式风险）
#' @param long_chars 「偏长」计数阈值
#' @param warn_frac 偏长标签占比 WARN 阈值
viz_qa_check_label_length <- function(plot_or_data,
                                      max_warn = 40L,
                                      max_fail = 80L,
                                      long_chars = 28L,
                                      warn_frac = 0.25) {
  labels <- .viz_qa_extract_labels(plot_or_data)
  labels <- labels[nzchar(labels) & !is.na(labels)]
  if (!length(labels)) {
    return(list(
      check = "label_length", status = "PASS",
      n = 0L, max_len = 0L, n_long = 0L, frac_long = 0,
      message = "no labels"
    ))
  }
  lens <- nchar(labels, type = "chars", allowNA = TRUE)
  lens[is.na(lens)] <- 0L
  max_len <- max(lens)
  n_long <- sum(lens > as.integer(long_chars))
  frac_long <- n_long / length(labels)
  status <- "PASS"
  if (max_len > as.integer(max_fail)) {
    status <- "FAIL"
  } else if (max_len > as.integer(max_warn) || frac_long > as.numeric(warn_frac)) {
    status <- "WARN"
  }
  list(
    check = "label_length",
    status = status,
    n = length(labels),
    max_len = as.integer(max_len),
    n_long = as.integer(n_long),
    frac_long = round(frac_long, 4),
    message = sprintf(
      "max_len=%d n_long(>%d)=%d/%d (%.1f%%)",
      max_len, long_chars, n_long, length(labels), 100 * frac_long
    )
  )
}

#' 通用 AABB / 圆重叠
#'
#' @param bboxes data.frame，支持：
#'   - xmin,xmax,ymin,ymax
#'   - 或 x,y,r（圆 → AABB）
#' @param warn_frac / fail_frac 重叠对数占组合数比例
#' @param fail_deep_frac 中心距 < 0.5*(r1+r2) 的深重叠占比（仅圆模式）
viz_qa_check_bbox_overlap <- function(bboxes,
                                      warn_frac = 0.02,
                                      fail_frac = 0.25,
                                      fail_deep_frac = 0.10,
                                      max_pairs_check = 20000L) {
  bb <- .viz_qa_normalize_bboxes(bboxes)
  n <- nrow(bb)
  if (n < 2L) {
    return(list(
      check = "bbox_overlap", status = "PASS",
      n = n, n_overlap = 0L, frac = 0, n_deep = 0L,
      message = "n<2"
    ))
  }
  # 组合数过大时抽样（密网）
  idx <- seq_len(n)
  pair_budget <- as.integer(max_pairs_check)
  comb_n <- n * (n - 1L) / 2
  sample_note <- ""
  if (comb_n > pair_budget) {
    # 贪心：按面积从大到小取前 m 个再全对，外加随机补充
    area <- pmax(0, bb$xmax - bb$xmin) * pmax(0, bb$ymax - bb$ymin)
    m <- min(n, max(40L, as.integer(sqrt(2 * pair_budget))))
    keep <- order(-area, idx)[seq_len(m)]
    idx <- sort(unique(keep))
    bb <- bb[idx, , drop = FALSE]
    n <- nrow(bb)
    sample_note <- sprintf("; sampled_n=%d", n)
  }
  n_overlap <- 0L
  n_deep <- 0L
  has_r <- all(c("x", "y", "r") %in% names(bb))
  for (i in seq_len(n - 1L)) {
    for (j in seq.int(i + 1L, n)) {
      ox <- bb$xmin[i] < bb$xmax[j] && bb$xmax[i] > bb$xmin[j]
      oy <- bb$ymin[i] < bb$ymax[j] && bb$ymax[i] > bb$ymin[j]
      if (ox && oy) {
        n_overlap <- n_overlap + 1L
        if (has_r) {
          d <- sqrt((bb$x[i] - bb$x[j])^2 + (bb$y[i] - bb$y[j])^2)
          if (is.finite(d) && d < 0.5 * (bb$r[i] + bb$r[j])) {
            n_deep <- n_deep + 1L
          }
        }
      }
    }
  }
  n_pairs <- as.integer(n * (n - 1L) / 2)
  frac <- if (n_pairs > 0) n_overlap / n_pairs else 0
  deep_frac <- if (n_pairs > 0) n_deep / n_pairs else 0
  status <- "PASS"
  if (frac > as.numeric(fail_frac) || deep_frac > as.numeric(fail_deep_frac)) {
    status <- "FAIL"
  } else if (n_overlap >= 1L && frac > as.numeric(warn_frac)) {
    status <- "WARN"
  } else if (n_overlap >= 1L && n <= 30L) {
    # 小图即使比例低也提示
    status <- "WARN"
  }
  list(
    check = "bbox_overlap",
    status = status,
    n = n,
    n_overlap = n_overlap,
    n_pairs = n_pairs,
    frac = round(frac, 4),
    n_deep = n_deep,
    message = sprintf(
      "overlap_pairs=%d/%d (%.2f%%) deep=%d%s",
      n_overlap, n_pairs, 100 * frac, n_deep, sample_note
    )
  )
}

#' 近似标签框重叠（中心点 + 按字符数估宽高）
viz_qa_check_label_overlap <- function(x, y, labels,
                                       label_size_mm = 2.5,
                                       char_w = 0.55,
                                       char_h = 1.05,
                                       warn_frac = 0.05,
                                       fail_frac = 0.40,
                                       dense_network = FALSE) {
  labels <- as.character(labels)
  ok <- !is.na(x) & !is.na(y) & nzchar(labels) & !is.na(labels)
  x <- as.numeric(x)[ok]
  y <- as.numeric(y)[ok]
  labels <- labels[ok]
  if (length(labels) < 2L) {
    return(list(
      check = "label_overlap", status = "PASS",
      n = length(labels), n_overlap = 0L, frac = 0,
      message = "n_label<2"
    ))
  }
  if (length(label_size_mm) == 1L) {
    label_size_mm <- rep(as.numeric(label_size_mm), length(labels))
  } else {
    label_size_mm <- as.numeric(label_size_mm)[ok]
  }
  # 数据坐标尺度：用点云范围归一化字号 → 框半宽
  xr <- diff(range(x, na.rm = TRUE))
  yr <- diff(range(y, na.rm = TRUE))
  span <- max(xr, yr, 1e-6)
  # mm→相对数据：经验系数，使密网可检出而不致全 FAIL
  scale <- span / 80
  nch <- pmax(nchar(labels, type = "chars"), 1L)
  hx <- pmax(nch * char_w * label_size_mm * scale * 0.08, span * 0.004)
  hy <- pmax(char_h * label_size_mm * scale * 0.08, span * 0.004)
  bb <- data.frame(
    xmin = x - hx, xmax = x + hx,
    ymin = y - hy, ymax = y + hy
  )
  if (isTRUE(dense_network)) {
    warn_frac <- max(warn_frac, 0.12)
    fail_frac <- max(fail_frac, 0.55)
  }
  res <- viz_qa_check_bbox_overlap(
    bb, warn_frac = warn_frac, fail_frac = fail_frac, fail_deep_frac = 1
  )
  res$check <- "label_overlap"
  if (isTRUE(dense_network) && identical(res$status, "FAIL") &&
      isTRUE(res$frac <= 0.55)) {
    res$status <- "WARN"
    res$message <- paste0(res$message, "; dense_network→FAIL capped to WARN")
  }
  res
}

#' 打印结构化 PASS/WARN/FAIL；返回汇总 list
viz_qa_report <- function(checks, plot_id = "", hard_fail = NULL) {
  if (is.null(hard_fail)) {
    hard_fail <- isTRUE(getOption("bioinfo.plotqa.hard_fail", FALSE))
  }
  if (inherits(checks, "list") && !is.null(checks$check)) {
    checks <- list(checks)
  }
  if (!length(checks)) {
    message("[PlotQA] ", plot_id, " — no checks")
    return(invisible(list(status = "PASS", plot_id = plot_id, checks = list())))
  }
  statuses <- vapply(checks, function(z) {
    if (is.null(z$status)) "PASS" else as.character(z$status)
  }, character(1))
  overall <- .viz_qa_worse(statuses)
  prefix <- if (nzchar(plot_id)) paste0("[PlotQA:", plot_id, "] ") else "[PlotQA] "
  message(prefix, "overall=", overall)
  for (z in checks) {
    msg <- if (!is.null(z$message)) z$message else ""
    message(sprintf(
      "  - %s: %s | %s",
      if (!is.null(z$check)) z$check else "check",
      if (!is.null(z$status)) z$status else "?",
      msg
    ))
  }
  if (isTRUE(hard_fail) && identical(overall, "FAIL")) {
    stop(prefix, "FAIL — refuse delivery (bioinfo.plotqa.hard_fail=TRUE)", call. = FALSE)
  }
  invisible(list(status = overall, plot_id = plot_id, checks = checks))
}

#' 网络节点：填充重叠 + 标签重叠 + 标签长度
#'
#' @param nodes_df 需含 x,y；推荐 r；标签列 label 或 name
viz_qa_network_nodes <- function(nodes_df,
                                 plot_id = "network",
                                 dense_network = NULL,
                                 hard_fail = NULL) {
  if (!is.data.frame(nodes_df) || !nrow(nodes_df)) {
    return(viz_qa_report(list(list(
      check = "network", status = "PASS", message = "empty nodes"
    )), plot_id = plot_id, hard_fail = hard_fail))
  }
  need <- c("x", "y")
  if (!all(need %in% names(nodes_df))) {
    stop("viz_qa_network_nodes: need columns x,y", call. = FALSE)
  }
  n <- nrow(nodes_df)
  if (is.null(dense_network)) dense_network <- n >= 80L
  lab_col <- if ("label" %in% names(nodes_df)) "label" else if ("name" %in% names(nodes_df)) "name" else NA_character_
  labels <- if (!is.na(lab_col)) as.character(nodes_df[[lab_col]]) else rep("", n)
  r <- if ("r" %in% names(nodes_df)) as.numeric(nodes_df$r) else rep(NA_real_, n)
  if (all(is.na(r))) {
    # 无半径：用点间距中位数估一个小 r，仅作弱填充检查
    if (n >= 2L) {
      # 子样估计
      take <- seq_len(min(n, 80L))
      dd <- as.matrix(stats::dist(cbind(nodes_df$x[take], nodes_df$y[take])))
      med <- stats::median(dd[upper.tri(dd)], na.rm = TRUE)
      r <- rep(max(med * 0.15, 1e-4), n)
    } else {
      r <- rep(0.01, n)
    }
  }
  fill_bb <- data.frame(
    x = as.numeric(nodes_df$x), y = as.numeric(nodes_df$y), r = r,
    xmin = as.numeric(nodes_df$x) - r,
    xmax = as.numeric(nodes_df$x) + r,
    ymin = as.numeric(nodes_df$y) - r,
    ymax = as.numeric(nodes_df$y) + r
  )
  chk_fill <- viz_qa_check_bbox_overlap(fill_bb)
  chk_fill$check <- "fill_overlap"
  lab_sz <- if ("label_size" %in% names(nodes_df)) nodes_df$label_size else 2.5
  chk_lab <- viz_qa_check_label_overlap(
    nodes_df$x, nodes_df$y, labels,
    label_size_mm = lab_sz,
    dense_network = isTRUE(dense_network)
  )
  chk_len <- viz_qa_check_label_length(labels)
  viz_qa_report(list(chk_fill, chk_lab, chk_len), plot_id = plot_id, hard_fail = hard_fail)
}

#' 从 ggplot 抽取标签并做长度 +（若有 x/y/label）弱重叠检查
viz_qa_ggplot_heuristic <- function(plot, plot_id = "ggplot", hard_fail = NULL) {
  if (!inherits(plot, "ggplot") && !inherits(plot, "grob")) {
    return(viz_qa_report(list(list(
      check = "ggplot", status = "PASS", message = "not a ggplot"
    )), plot_id = plot_id, hard_fail = hard_fail))
  }
  if (!inherits(plot, "ggplot")) {
    return(viz_qa_report(list(list(
      check = "ggplot", status = "WARN",
      message = "grob/patchwork — skip build heuristic; visual Read required"
    )), plot_id = plot_id, hard_fail = hard_fail))
  }
  labels <- character()
  xy_lab <- NULL
  if (requireNamespace("ggplot2", quietly = TRUE)) {
    built <- try(ggplot2::ggplot_build(plot), silent = TRUE)
    if (!inherits(built, "try-error") && length(built$data)) {
      for (d in built$data) {
        if (!is.null(d$label)) {
          lab <- as.character(d$label)
          labels <- c(labels, lab)
          if (!is.null(d$x) && !is.null(d$y)) {
            keep <- nzchar(lab) & !is.na(lab)
            if (any(keep)) {
              xy_lab <- rbind(
                xy_lab,
                data.frame(
                  x = as.numeric(d$x[keep]),
                  y = as.numeric(d$y[keep]),
                  label = lab[keep],
                  stringsAsFactors = FALSE
                )
              )
            }
          }
        }
      }
    }
  }
  # 轴标题等（长标题版式风险）
  labs_plot <- try(plot$labels, silent = TRUE)
  if (is.list(labs_plot)) {
    for (nm in c("title", "subtitle", "x", "y", "colour", "fill")) {
      if (!is.null(labs_plot[[nm]])) {
        labels <- c(labels, as.character(labs_plot[[nm]]))
      }
    }
  }
  checks <- list(viz_qa_check_label_length(labels))
  if (!is.null(xy_lab) && nrow(xy_lab) >= 2L) {
    checks[[length(checks) + 1L]] <- viz_qa_check_label_overlap(
      xy_lab$x, xy_lab$y, xy_lab$label, dense_network = nrow(xy_lab) >= 80L
    )
  }
  viz_qa_report(checks, plot_id = plot_id, hard_fail = hard_fail)
}

#' 保存后钩子（供 delivery_save_plot 调用）
viz_qa_after_plot <- function(plot, plot_id = "", hard_fail = NULL) {
  if (inherits(plot, "ggplot")) {
    return(viz_qa_ggplot_heuristic(plot, plot_id = plot_id, hard_fail = hard_fail))
  }
  invisible(list(status = "PASS", plot_id = plot_id, checks = list()))
}

# ---- internals ----

.viz_qa_extract_labels <- function(plot_or_data) {
  if (is.character(plot_or_data) || is.factor(plot_or_data)) {
    return(as.character(plot_or_data))
  }
  if (is.data.frame(plot_or_data)) {
    for (col in c("label", "name", "gene", "Description", "Description_wrap", "term")) {
      if (col %in% names(plot_or_data)) {
        return(as.character(plot_or_data[[col]]))
      }
    }
    return(character())
  }
  if (inherits(plot_or_data, "ggplot") && requireNamespace("ggplot2", quietly = TRUE)) {
    built <- try(ggplot2::ggplot_build(plot_or_data), silent = TRUE)
    if (!inherits(built, "try-error") && length(built$data)) {
      out <- character()
      for (d in built$data) {
        if (!is.null(d$label)) out <- c(out, as.character(d$label))
      }
      return(out)
    }
  }
  character()
}

.viz_qa_normalize_bboxes <- function(bboxes) {
  if (!is.data.frame(bboxes)) stop("bboxes must be a data.frame", call. = FALSE)
  if (all(c("xmin", "xmax", "ymin", "ymax") %in% names(bboxes))) {
    out <- data.frame(
      xmin = as.numeric(bboxes$xmin), xmax = as.numeric(bboxes$xmax),
      ymin = as.numeric(bboxes$ymin), ymax = as.numeric(bboxes$ymax)
    )
    if (all(c("x", "y", "r") %in% names(bboxes))) {
      out$x <- as.numeric(bboxes$x)
      out$y <- as.numeric(bboxes$y)
      out$r <- as.numeric(bboxes$r)
    }
    return(out)
  }
  if (all(c("x", "y", "r") %in% names(bboxes))) {
    x <- as.numeric(bboxes$x)
    y <- as.numeric(bboxes$y)
    r <- as.numeric(bboxes$r)
    return(data.frame(
      x = x, y = y, r = r,
      xmin = x - r, xmax = x + r,
      ymin = y - r, ymax = y + r
    ))
  }
  stop("bboxes need xmin..ymax or x,y,r", call. = FALSE)
}

#' 定位并 source 本脚本（供其它技能调用）
viz_qa_ensure_loaded <- function(start = getwd()) {
  if (exists("viz_qa_report", mode = "function")) return(invisible(TRUE))
  p <- normalizePath(start, winslash = "/", mustWork = FALSE)
  for (i in seq_len(14)) {
    cands <- c(
      file.path(
        p, "生信分析技能_BioinformaticsSkills", "00_基础_Foundation",
        "统一可视化规范_VizStandards", "脚本_scripts", "出图后审核_PlotQA.R"
      ),
      file.path(
        p, "00_基础_Foundation", "统一可视化规范_VizStandards",
        "脚本_scripts", "出图后审核_PlotQA.R"
      ),
      file.path(p, "脚本_scripts", "出图后审核_PlotQA.R")
    )
    for (cand in cands) {
      if (file.exists(cand)) {
        source(cand, encoding = "UTF-8")
        return(invisible(TRUE))
      }
    }
    parent <- dirname(p)
    if (identical(parent, p)) break
    p <- parent
  }
  warning("PlotQA: 未找到 出图后审核_PlotQA.R", call. = FALSE)
  invisible(FALSE)
}
