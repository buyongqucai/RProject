# Delivery-style layouts (override plot helpers when sourced after 03_*)
# 1) STRING PPI degree gradient — true concentric rings (unequal counts, outer denser)
# 2) HCTP — center targets; columns: pathways L/R outer; ellipse: pathways mid ring
#    (targets → pathways → herb/compound satellites); unified Degree size 60–120;
#    rounded target squares; black labels; no borders; solid edges; octagon flat-top;
#    pathways = flattened ellipses (ellipse mode); columns compound spacing ×1.30
#
# 出图后审核（项目级 SSOT）：统一可视化规范_VizStandards/出图后审核_PlotQA.R
# 布局完成后调用 viz_qa_network_nodes（密网 WARN 可接受，不 hard-fail）

.np_ensure_plotqa <- function(start = getwd()) {
  if (exists("viz_qa_network_nodes", mode = "function")) return(invisible(TRUE))
  if (exists("viz_qa_ensure_loaded", mode = "function")) {
    return(invisible(isTRUE(viz_qa_ensure_loaded(start))))
  }
  if (exists("ensure_plotqa", mode = "function")) {
    return(invisible(isTRUE(ensure_plotqa(start))))
  }
  p <- normalizePath(start, winslash = "/", mustWork = FALSE)
  for (i in seq_len(14)) {
    cands <- c(
      file.path(
        p, "00_基础_Foundation", "统一可视化规范_VizStandards",
        "脚本_scripts", "出图后审核_PlotQA.R"
      ),
      file.path(
        p, "生信分析技能_BioinformaticsSkills", "00_基础_Foundation",
        "统一可视化规范_VizStandards", "脚本_scripts", "出图后审核_PlotQA.R"
      )
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
  warning("PlotQA not found; skip network layout audit", call. = FALSE)
  invisible(FALSE)
}

#' Ring capacities: outermost ~50–55% of nodes; inner rings grow triangularly toward outside.
#' Innermost kept small (target 3–8 hubs when n allows).
.np_ring_capacities <- function(n, n_rings = NULL, outer_frac = 0.54) {
  n <- as.integer(n)
  if (n <= 1L) return(n)
  if (is.null(n_rings)) {
    # 4–5 rings: prefer 5 for larger graphs (n≥80); outer denser (~54%)
    n_rings <- if (n >= 80L) 5L else 4L
  }
  n_rings <- max(2L, min(as.integer(n_rings), n))
  outer_frac <- max(0.50, min(0.58, as.numeric(outer_frac)))
  outer <- as.integer(round(outer_frac * n))
  # leave ≥1 node per inner ring
  outer <- min(outer, n - (n_rings - 1L))
  outer <- max(1L, outer)
  remain <- n - outer
  n_inner <- n_rings - 1L
  if (n_inner == 1L) return(c(remain, outer))

  # triangular weights: ring k (1=innermost) weight = k → more nodes toward outside
  w <- as.numeric(seq_len(n_inner))
  exact <- remain * w / sum(w)
  caps <- as.integer(floor(exact))
  if (remain >= n_inner) caps <- pmax(1L, caps)
  diff <- remain - sum(caps)
  if (diff > 0L) {
    # largest-remainder, prefer outer inner-rings
    frac_order <- order(-(exact - floor(exact)), -seq_len(n_inner))
    i <- 1L
    while (diff > 0L) {
      j <- frac_order[((i - 1L) %% n_inner) + 1L]
      caps[j] <- caps[j] + 1L
      diff <- diff - 1L
      i <- i + 1L
    }
  } else if (diff < 0L) {
    while (diff < 0L) {
      cand <- which(caps > 1L)
      if (!length(cand)) break
      j <- cand[[which.max(caps[cand])]]
      caps[j] <- caps[j] - 1L
      diff <- diff + 1L
    }
  }

  # nudge innermost into [3, 8] when feasible
  if (caps[1L] < 3L && remain >= 3L + (n_inner - 1L)) {
    need <- min(3L, remain - (n_inner - 1L)) - caps[1L]
    for (k in rev(seq.int(2L, n_inner))) {
      if (need <= 0L) break
      take <- min(need, max(0L, caps[k] - 1L))
      caps[k] <- caps[k] - take
      caps[1L] <- caps[1L] + take
      need <- need - take
    }
  }
  if (caps[1L] > 8L && n_inner >= 2L) {
    excess <- caps[1L] - 8L
    caps[1L] <- 8L
    # push excess to outer inner-rings by weight
    w2 <- w[-1]
    add <- as.integer(floor(excess * w2 / sum(w2)))
    add_diff <- excess - sum(add)
    if (add_diff > 0L) {
      for (j in rev(seq_along(add))) {
        if (add_diff <= 0L) break
        add[j] <- add[j] + 1L
        add_diff <- add_diff - 1L
      }
    }
    caps[-1] <- caps[-1] + add
  }

  c(caps, outer)
}

#' Degree → data-coord fill radius for PPI circles (exact anti-overlap with geom_circle).
#' Shared visual domain: Degree → size ∈ [60, 120] → r = size / size_to_r.
#' Strict monotone of Degree only — never shrink by ring / hub cap (layout grows instead).
.np_ppi_degree_to_r <- function(degree, ring_id = NULL, n_rings = NULL,
                                size_min = 60, size_max = 120, size_to_r = 1600) {
  # ring_id / n_rings kept for API compatibility; intentionally unused
  invisible(ring_id)
  invisible(n_rings)
  size <- .np_degree_to_size(degree, size_min = size_min, size_max = size_max, transform = "sqrt")
  r <- .np_size_to_r(size, size_to_r = size_to_r)
  nms <- names(degree)
  if (!is.null(nms)) names(r) <- nms
  r
}

#' Chord-minimum ring radius for m nodes with max fill radius r_max.
.np_ppi_chord_ring_R <- function(m, r_max, safety = 1.12, ring_gap = 0.012) {
  r_max <- max(as.numeric(r_max), 1e-4)
  if (m <= 1L) return(max(r_max * 1.35, r_max + ring_gap))
  # 2 R sin(π/m) ≥ safety * (2 r_max) + soft gap
  (safety * (2 * r_max) + ring_gap) / (2 * sin(pi / m))
}

#' Even radial spacing from clearance floors + outer chord (no orphaned outer ring).
#' Equalizes *envelope* gaps (white space between fill shells), not raw center Δr —
#' so a dense tiny-node outer ring is not optically orphaned. Never shrinks below
#' chord or inter-ring fill clearance (|R_k−R_{k-1}| ≥ r_max_k + r_max_{k-1} + pad).
.np_ppi_even_ring_radii <- function(chord_R, max_r_on, pad = 0.014) {
  n <- length(chord_R)
  if (n <= 0L) return(numeric())
  if (n == 1L) return(max(chord_R[[1]], max_r_on[[1]] * 1.35, na.rm = TRUE))

  rmax <- pmax(as.numeric(max_r_on), 1e-4)
  clear_min <- numeric(n) # hard fill non-overlap floor between ring r-1 and r
  for (r in 2:n) {
    clear_min[r] <- rmax[r - 1L] + rmax[r] + as.numeric(pad)
  }

  R <- numeric(n)
  R[1] <- max(as.numeric(chord_R[1]), rmax[1] * 1.35, na.rm = TRUE)

  # Outer ring: chord dominates when dense; clearance chain is the floor
  R_clear_n <- R[1]
  for (r in 2:n) R_clear_n <- R_clear_n + clear_min[r]
  R[n] <- max(as.numeric(chord_R[n]), R_clear_n, na.rm = TRUE)

  # Equal envelope gaps:
  #   (R[r] - rmax[r]) - (R[r-1] + rmax[r-1]) = G  (same G for all steps)
  # ⇒ R[r] = R[r-1] + rmax[r-1] + rmax[r] + G
  # With R[n] fixed by chord: solve G, then place mid rings.
  sum_shell <- 0
  for (r in 2:n) sum_shell <- sum_shell + rmax[r - 1L] + rmax[r]
  G <- (R[n] - R[1] - sum_shell) / (n - 1)
  # never below pad (would mean fills collide); if chord too tight, G←pad and grow R[n]
  if (!is.finite(G) || G < as.numeric(pad)) {
    G <- as.numeric(pad)
    R[n] <- R[1] + sum_shell + G * (n - 1)
    R[n] <- max(R[n], as.numeric(chord_R[n]), na.rm = TRUE)
    G <- (R[n] - R[1] - sum_shell) / (n - 1)
    if (!is.finite(G) || G < as.numeric(pad)) G <- as.numeric(pad)
  }

  for (r in 2:n) {
    ideal <- R[r - 1L] + rmax[r - 1L] + rmax[r] + G
    floor_r <- max(as.numeric(chord_R[r]), R[r - 1L] + clear_min[r], na.rm = TRUE)
    R[r] <- max(ideal, floor_r, na.rm = TRUE)
  }
  # If a mid-ring chord floor pushed a ring out, rebuild remaining envelope gaps
  for (iter in seq_len(8L)) {
    changed <- FALSE
    for (r in 2:n) {
      floor_r <- max(as.numeric(chord_R[r]), R[r - 1L] + clear_min[r], na.rm = TRUE)
      if (R[r] < floor_r - 1e-9) {
        R[r] <- floor_r
        changed <- TRUE
      }
    }
    # re-spread envelope from first free segment to outer
    R[n] <- max(R[n], as.numeric(chord_R[n]), na.rm = TRUE)
    # recompute G from current R[1]..R[n] using remaining shell sums
    sum_shell <- 0
    for (r in 2:n) sum_shell <- sum_shell + rmax[r - 1L] + rmax[r]
    G2 <- (R[n] - R[1] - sum_shell) / (n - 1)
    if (!is.finite(G2) || G2 < as.numeric(pad)) G2 <- as.numeric(pad)
    for (r in 2:n) {
      ideal <- R[r - 1L] + rmax[r - 1L] + rmax[r] + G2
      floor_r <- max(as.numeric(chord_R[r]), R[r - 1L] + clear_min[r], na.rm = TRUE)
      new_r <- max(ideal, floor_r)
      if (abs(new_r - R[r]) > 1e-7) changed <- TRUE
      R[r] <- new_r
    }
    if (!changed) break
  }

  for (r in 2:n) {
    R[r] <- max(R[r], R[r - 1L] + clear_min[r], as.numeric(chord_R[r]), na.rm = TRUE)
  }
  R
}

#' True concentric rings by degree rank (hubs center). Adaptive radii avoid fill overlap.
#' Unequal ring sizes (outer denser); staggered phase (no spokes).
#' Fill radii are strict Degree→size→r (never capped). Ring radii grow to fit.
#' Within each ring, nodes sorted Degree descending clockwise from top.
.np_layout_concentric_degree <- function(g,
                                        n_rings = NULL,
                                        outer_frac = 0.50,
                                        r_nodes = NULL,
                                        ring_gap = 0.014,
                                        chord_safety = 1.18,
                                        hub_abs_cap = NULL,
                                        inter_pad = 0.022) {
  # hub_abs_cap kept for API compatibility; never applied (breaks Degree→size)
  invisible(hub_abs_cap)
  deg <- igraph::degree(g)
  vs <- igraph::V(g)$name
  d <- as.numeric(deg[vs])
  names(d) <- vs
  n <- length(vs)
  ord <- order(-d, vs) # Degree descending → hubs on inner rings

  if (n == 1L) {
    lay <- matrix(c(0, 0), nrow = 1L, dimnames = list(vs, c("x", "y")))
    attr(lay, "ring_id") <- setNames(1L, vs)
    attr(lay, "ring_capacities") <- 1L
    attr(lay, "ring_radii") <- 0
    attr(lay, "r_node") <- setNames(0.06, vs)
    return(lay)
  }

  caps <- .np_ring_capacities(n, n_rings = n_rings, outer_frac = outer_frac)
  n_rings <- length(caps)
  # partition ord into rings with increasing capacity (outer densest)
  ring_of_ord <- integer(n)
  pos <- 1L
  for (r in seq_len(n_rings)) {
    k <- caps[[r]]
    if (k > 0L) {
      ring_of_ord[pos:(pos + k - 1L)] <- r
      pos <- pos + k
    }
  }
  ring_id <- setNames(integer(n), vs)
  ring_id[ord] <- ring_of_ord

  if (is.null(r_nodes)) {
    # size = f(Degree) only — no ring shrink / hub cap
    r_node <- .np_ppi_degree_to_r(
      d, size_min = 60, size_max = 120, size_to_r = 1600
    )
  } else {
    r_node <- as.numeric(r_nodes[vs])
    names(r_node) <- vs
    r_node[is.na(r_node)] <- 0.04
  }

  max_r_on <- numeric(n_rings)
  min_r_on <- numeric(n_rings)
  chord_R <- numeric(n_rings)
  for (r in seq_len(n_rings)) {
    nodes_r <- vs[ring_id == r]
    m <- length(nodes_r)
    max_r_on[r] <- if (m) max(r_node[nodes_r], na.rm = TRUE) else 0.03
    min_r_on[r] <- if (m) min(r_node[nodes_r], na.rm = TRUE) else 0.03
    if (!is.finite(max_r_on[r]) || max_r_on[r] <= 0) max_r_on[r] <- 0.03
    if (!is.finite(min_r_on[r]) || min_r_on[r] <= 0) min_r_on[r] <- 0.03
    # hub ring: higher chord safety so large hubs do not kiss
    saf <- if (r == 1L) max(chord_safety, 1.32) else chord_safety
    chord_R[r] <- .np_ppi_chord_ring_R(
      m, max_r_on[r], safety = saf, ring_gap = ring_gap
    )
  }

  # Grow ring radii from true (uncapped) fill sizes — never shrink fills
  ring_rad <- .np_ppi_even_ring_radii(chord_R, max_r_on, pad = inter_pad)

  lay <- matrix(0, nrow = n, ncol = 2L)
  rownames(lay) <- vs
  for (r in seq_len(n_rings)) {
    # within-ring: Degree descending clockwise from top (ord already sorted)
    nodes <- ord[ring_of_ord == r]
    m <- length(nodes)
    if (!m) next
    # re-sort within ring by Degree desc (stable name tie-break) for clarity
    nodes <- nodes[order(-d[nodes], nodes)]
    rad <- ring_rad[r]
    golden <- pi * (3 - sqrt(5))
    phase <- (r - 1) * golden + if (m > 1L && (r %% 2L) == 0L) pi / m else 0
    ang <- if (m == 1L) {
      -pi / 2 + phase
    } else {
      # clockwise from top: start -π/2, increase angle
      2 * pi * (seq_len(m) - 1) / m + phase - pi / 2
    }
    lay[nodes, 1] <- rad * cos(ang)
    lay[nodes, 2] <- rad * sin(ang)
  }
  colnames(lay) <- c("x", "y")
  attr(lay, "ring_capacities") <- caps
  attr(lay, "ring_radii") <- ring_rad
  attr(lay, "ring_id") <- ring_id
  attr(lay, "r_node") <- r_node
  attr(lay, "outer_frac") <- outer_frac
  attr(lay, "max_r_on") <- max_r_on
  attr(lay, "min_r_on") <- min_r_on
  attr(lay, "chord_R") <- chord_R
  lay
}

#' PPI label size in ggplot mm — constant within each ring.
#' Inner rings larger font than outer; never per-node within a ring.
.np_ppi_label_size <- function(ring, n_rings,
                               inner = 3.2,
                               outer = 1.85) {
  if (!is.finite(n_rings) || n_rings <= 1L) return(inner)
  t <- (as.numeric(ring) - 1) / (n_rings - 1)
  t <- t^1.05
  inner + (outer - inner) * t
}

#' Clamp ggplot text size (mm) so label glyph box fits inside a circle of radius r
#' in data coords. Uses canvas half-range ↔ plot height to convert mm→data.
.np_label_size_fit_in_r <- function(r, label,
                                    plot_half_range,
                                    plot_height_mm = 240,
                                    width_factor = 0.52,
                                    height_factor = 1.05,
                                    fit_frac = 0.78,
                                    max_size = 3.2,
                                    min_size = 0.85) {
  r <- as.numeric(r)
  half <- as.numeric(plot_half_range)
  if (!is.finite(r) || r <= 0 || !is.finite(half) || half <= 0) {
    return(min_size)
  }
  dpm <- (2 * half) / as.numeric(plot_height_mm) # data units per mm
  nch <- max(nchar(as.character(label)), 1L)
  # width_data = nch * width_factor * size_mm * dpm; need width/2 ≤ r*fit_frac
  max_w <- (2 * r * fit_frac) / (nch * width_factor * dpm)
  max_h <- (2 * r * fit_frac) / (height_factor * dpm)
  max(min_size, min(max_size, max_w, max_h))
}

#' Cytoscape-style point size → ggplot geom_text size (mm).
#' ggplot2 stores text size in mm; `.pt` ≈ 2.845 (points per mm).
#' Use `size = (pt / ggplot2::.pt) * scale` — never pass raw Cytoscape pt as ggplot size.
#' `scale` fits dense delivery canvases; hierarchy of pt values is preserved.
.np_pt_to_ggplot_size <- function(pt, scale = 1) {
  (as.numeric(pt) / ggplot2::.pt) * as.numeric(scale)
}

#' STRING PPI 渐变图：Degree→颜色+大小；大 Degree 居中；真同心圆；去游离点
np_plot_string_ppi <- function(ppi,
                               title = "STRING PPI degree gradient",
                               label_top_n = NULL,
                               min_score = 900L,
                               drop_isolates = TRUE,
                               layout = c("concentric", "fr"),
                               n_rings = NULL,
                               outer_frac = 0.50) {
  if (!requireNamespace("igraph", quietly = TRUE)) stop("需要 igraph")
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
  layout <- match.arg(layout)
  resolved <- .np_string_endpoint_cols(ppi)
  df <- resolved$df
  a_col <- resolved$a
  b_col <- resolved$b
  if (is.na(a_col) || is.na(b_col)) {
    stop("PPI table missing node endpoint columns", call. = FALSE)
  }
  if (!is.null(min_score) && !is.na(resolved$score)) {
    thr <- .np_string_score_threshold(df[[resolved$score]], min_score)
    df <- df[as.numeric(df[[resolved$score]]) >= thr, , drop = FALSE]
  }
  edges <- data.frame(
    from = as.character(df[[a_col]]),
    to = as.character(df[[b_col]]),
    stringsAsFactors = FALSE
  )
  edges <- edges[nzchar(edges$from) & nzchar(edges$to), , drop = FALSE]
  if (!nrow(edges)) stop("No PPI edges at this score", call. = FALSE)

  g <- igraph::graph_from_data_frame(edges, directed = FALSE)
  g <- igraph::simplify(g, remove.multiple = TRUE, remove.loops = TRUE)
  if (isTRUE(drop_isolates)) {
    g <- igraph::delete_vertices(g, igraph::V(g)[igraph::degree(g) == 0])
  }
  if (igraph::vcount(g) < 2) stop("Fewer than 2 connected nodes", call. = FALSE)

  if (!requireNamespace("ggforce", quietly = TRUE)) {
    stop("Install ggforce for PPI data-coord circles", call. = FALSE)
  }
  deg <- igraph::degree(g)
  set.seed(42)
  lay <-   if (identical(layout, "concentric")) {
    .np_layout_concentric_degree(
      g, n_rings = n_rings, outer_frac = outer_frac,
      ring_gap = 0.014, chord_safety = 1.18, inter_pad = 0.022
    )
  } else {
    l <- igraph::layout_with_fr(g, niter = 1200)
    rownames(l) <- igraph::V(g)$name
    colnames(l) <- c("x", "y")
    l
  }

  dvec <- as.numeric(deg[igraph::V(g)$name])
  names(dvec) <- igraph::V(g)$name
  node_df <- data.frame(
    name = igraph::V(g)$name,
    degree = dvec,
    stringsAsFactors = FALSE
  )
  node_df$x <- lay[node_df$name, 1]
  node_df$y <- lay[node_df$name, 2]
  ring_attr <- attr(lay, "ring_id")
  if (!is.null(ring_attr)) {
    node_df$ring <- as.integer(unname(ring_attr[node_df$name]))
  } else {
    node_df$ring <- 1L
  }
  n_rings_used <- if (!is.null(attr(lay, "ring_capacities"))) {
    length(attr(lay, "ring_capacities"))
  } else {
    max(node_df$ring, na.rm = TRUE)
  }
  r_attr <- attr(lay, "r_node")
  if (!is.null(r_attr)) {
    node_df$r <- as.numeric(r_attr[node_df$name])
  } else {
    node_df$r <- .np_ppi_degree_to_r(
      setNames(node_df$degree, node_df$name),
      ring_id = setNames(node_df$ring, node_df$name),
      n_rings = n_rings_used
    )
  }
  node_df$size <- .np_degree_to_size(
    node_df$degree, size_min = 60, size_max = 120, transform = "sqrt"
  )
  # Enforce size↔r consistency: r must be monotone of Degree only
  node_df$r <- .np_size_to_r(node_df$size, size_to_r = 1600)
  # Verification: Degree→size strict monotonicity (Spearman; Pearson <1 under sqrt map)
  cor_ds <- suppressWarnings(stats::cor(node_df$degree, node_df$size, method = "spearman"))
  cor_dr <- suppressWarnings(stats::cor(node_df$degree, node_df$r, method = "spearman"))
  cor_ds_p <- suppressWarnings(stats::cor(node_df$degree, node_df$size, method = "pearson"))
  max_deg_names <- node_df$name[node_df$degree == max(node_df$degree)]
  max_size_names <- node_df$name[node_df$size == max(node_df$size)]
  if (!is.finite(cor_ds) || cor_ds < 0.99 || !is.finite(cor_dr) || cor_dr < 0.99) {
    warning(
      "PPI Degree→size/r Spearman failed: rho(deg,size)=", round(cor_ds, 4),
      " rho(deg,r)=", round(cor_dr, 4), call. = FALSE
    )
  }
  if (!any(max_deg_names %in% max_size_names)) {
    warning(
      "PPI max-Degree nodes are not max-size: deg=", paste(max_deg_names, collapse = ","),
      " size=", paste(max_size_names, collapse = ","), call. = FALSE
    )
  } else {
    message(
      "PPI verify OK: Spearman(deg,size)=", round(cor_ds, 4),
      " Pearson=", round(cor_ds_p, 4),
      " max_size_on=", paste(intersect(max_deg_names, max_size_names), collapse = ","),
      " size_range=[", round(min(node_df$size), 1), ",", round(max(node_df$size), 1), "]",
      " r_range=[", round(min(node_df$r), 4), ",", round(max(node_df$r), 4), "]"
    )
  }
  if (is.null(label_top_n) || !is.finite(label_top_n) || label_top_n >= nrow(node_df)) {
    node_df$label <- node_df$name
  } else {
    keep <- order(-node_df$degree, node_df$name)[seq_len(as.integer(label_top_n))]
    node_df$label <- ""
    node_df$label[keep] <- node_df$name[keep]
  }
  # Ring-constant label sizes by ring index only (inner > outer).
  # Do NOT clamp via plot_half — canvas growth would falsely shrink hub fonts.
  ring_rad_attr <- attr(lay, "ring_radii")
  ring_lab <- setNames(
    vapply(seq_len(n_rings_used), function(rr) {
      .np_ppi_label_size(rr, n_rings_used, inner = 3.2, outer = 1.85)
    }, numeric(1)),
    as.character(seq_len(n_rings_used))
  )
  node_df$label_size <- unname(ring_lab[as.character(node_df$ring)])
  message(
    "PPI ring fonts(mm)=", paste(round(ring_lab, 2), collapse = ","),
    " ring radii=", if (!is.null(ring_rad_attr)) paste(round(ring_rad_attr, 3), collapse = ",") else "NA",
    " caps=", paste(attr(lay, "ring_capacities"), collapse = ",")
  )
  node_df <- node_df[order(node_df$degree), , drop = FALSE]

  el <- igraph::as_data_frame(g, what = "edges")
  el$x <- lay[el$from, 1]
  el$y <- lay[el$from, 2]
  el$xend <- lay[el$to, 1]
  el$yend <- lay[el$to, 2]

  fill_cols <- c("#FFFFCC", "#C2E699", "#78C679", "#31A354", "#006837")
  caps_used <- attr(lay, "ring_capacities")
  outer_n <- if (!is.null(caps_used)) caps_used[length(caps_used)] else NA_integer_
  rad_msg <- if (!is.null(ring_rad_attr)) {
    paste(round(ring_rad_attr, 3), collapse = ",")
  } else {
    "NA"
  }
  message(
    "PPI concentric caps=", paste(caps_used, collapse = ","),
    " radii=", rad_msg,
    " outer_frac=", attr(lay, "outer_frac")
  )
  if (isTRUE(.np_ensure_plotqa())) {
    try(
      viz_qa_network_nodes(
        node_df,
        plot_id = paste0("StringPPI_", layout),
        dense_network = TRUE,
        hard_fail = FALSE
      ),
      silent = FALSE
    )
  }
  p <- ggplot2::ggplot() +
    ggplot2::geom_segment(
      data = el,
      ggplot2::aes(x = x, y = y, xend = xend, yend = yend),
      color = "grey70", alpha = 0.2, linewidth = 0.22, linetype = "solid"
    ) +
    # data-coord circles: fill radius matches layout anti-overlap (no mm/point mismatch)
    ggforce::geom_circle(
      data = node_df,
      ggplot2::aes(x0 = x, y0 = y, r = r, fill = degree),
      colour = NA, linewidth = 0, n = 48, alpha = 0.97
    ) +
    ggplot2::scale_fill_gradientn(colours = fill_cols, name = "Degree") +
    ggplot2::geom_text(
      data = node_df[nzchar(node_df$label), , drop = FALSE],
      ggplot2::aes(x = x, y = y, label = label, size = label_size),
      color = "grey5", fontface = "bold", check_overlap = FALSE,
      show.legend = FALSE
    ) +
    ggplot2::scale_size_identity() +
    ggplot2::labs(
      title = title,
      subtitle = sprintf(
        "STRING score ≥ 0.9 · isolates removed · Degree → color & size 60–120 (strict) · %d rings (outer≈%d/%d) · ring-constant fonts (n=%d, e=%d)",
        n_rings_used,
        if (is.na(outer_n)) NA_integer_ else outer_n,
        igraph::vcount(g),
        igraph::vcount(g), igraph::ecount(g)
      )
    ) +
    ggplot2::coord_equal(clip = "off") +
    ggplot2::theme_void(base_size = 11) +
    ggplot2::theme(
      plot.title = ggplot2::element_text(face = "bold", size = 12, hjust = 0.5),
      plot.subtitle = ggplot2::element_text(size = 8.5, color = "grey35", hjust = 0.5),
      legend.position = "right",
      plot.margin = ggplot2::margin(10, 14, 10, 10),
      plot.background = ggplot2::element_rect(fill = "white", color = NA)
    )
  p
}

#' Assign each compound to one herb; shared → herb with fewest assigned compounds
.np_assign_compounds_unique <- function(herb_to_comps) {
  herbs <- names(herb_to_comps)
  cand <- list()
  for (h in herbs) {
    for (c in herb_to_comps[[h]]) {
      cand[[c]] <- c(cand[[c]], h)
    }
  }
  assigned <- setNames(vector("list", length(herbs)), herbs)
  counts <- setNames(integer(length(herbs)), herbs)
  shared <- character()
  for (c in names(cand)) {
    hs <- unique(cand[[c]])
    if (length(hs) == 1L) {
      h <- hs[[1]]
      assigned[[h]] <- c(assigned[[h]], c)
      counts[[h]] <- counts[[h]] + 1L
    } else {
      shared <- c(shared, c)
    }
  }
  for (c in sort(unique(shared))) {
    hs <- unique(cand[[c]])
    h <- hs[which.min(counts[hs])]
    assigned[[h]] <- c(assigned[[h]], c)
    counts[[h]] <- counts[[h]] + 1L
  }
  lapply(assigned, unique)
}

#' Morandi muted herb/compound cluster colors — low chroma, hue-spread (distinct at a glance).
.np_herb_palette <- function(herbs) {
  # dusty rose · olive sage · slate blue · muted mustard · dusty mauve · soft teal · …
  base <- c(
    "#C4909A", "#9AAA7E", "#6E8FA8", "#C4A85A", "#A87898", "#5FA89A",
    "#B08A7A", "#8B7AA8", "#A89870", "#7A9AA8"
  )
  n <- length(herbs)
  cols <- if (n <= length(base)) base[seq_len(n)] else grDevices::colorRampPalette(base)(n)
  stats::setNames(cols, herbs)
}

# HCTP accents: herbs stay Morandi (.np_herb_palette); targets/pathways = pre-Morandi
.np_hctp_accents <- list(
  target = "#F5C6CB",                                    # light pink (pre-Morandi)
  pathway = c("#F7FCB9", "#41AB5D", "#00441B"),           # lime → mid green → dark green
  edge = "#8FA0A8",                                      # A–B / B–C muted grey
  edge_cd = "#2F6FBF"                                    # C–D pathway↔target distinct blue
)

# Cytoscape-style label points (converted via .np_pt_to_ggplot_size)
# Hierarchy 24 / 36 / 38 preserved; canvas_scale fits dense C-grid on delivery size.
.np_hctp_label_pt <- list(
  target = 24,      # gene symbols
  herb = 36,        # herb codes
  compound = 38,    # compound id/name
  pathway = 38,     # hsa IDs
  canvas_scale = 0.26  # (pt/.pt)*scale → ~2.2 / 3.3 / 3.5 mm
)

#' Map Degree → Cytoscape-style size parameter in [size_min, size_max] (default 60–120).
#' Then convert to data-coord half-extent: r = size / size_to_r (default 560 → r ∈ ~[0.107, 0.214]).
#' 60–120 is the shared visual size scale for ALL node types; ggplot draws via data-coord r.
#' size_to_r=560 (was 800) keeps fills readable on compact layouts.
.np_degree_to_size <- function(deg,
                               size_min = 60,
                               size_max = 120,
                               transform = c("sqrt", "linear")) {
  transform <- match.arg(transform)
  d <- as.numeric(deg)
  dmin <- min(d, na.rm = TRUE)
  dmax <- max(d, na.rm = TRUE)
  frac <- (d - dmin) / max(1e-9, dmax - dmin)
  if (identical(transform, "sqrt")) frac <- sqrt(pmax(0, frac))
  size_min + (size_max - size_min) * frac
}

.np_size_to_r <- function(size, size_to_r = 560) {
  as.numeric(size) / size_to_r
}

#' Pathway display labels: KEGG/ID only (e.g. hsa04210). Never full names; never wrap.
#' `pathway_names` is accepted for API compatibility but ignored for labeling.
.np_resolve_pathway_labels <- function(pathway_ids, pathway_names = NULL) {
  invisible(pathway_names)
  ids <- as.character(pathway_ids)
  labs <- ids
  names(labs) <- ids
  # strip any newlines / extra spaces so IDs stay single-line
  labs <- gsub("[\r\n]+", "", labs)
  labs <- gsub("\\s+", "", labs)
  labs
}

#' Rounded-square polygons in DATA coords (relative corner radius).
#' Formula: side = 2 * half_extent; r_corner = corner_frac * side (default 0.10).
#' Absolute mm rounding (ggforce::geom_shape) would make small/large nodes look
#' inconsistently sharp/round; data-coord polygons keep the same visual ratio.
.np_rounded_square_poly <- function(x0, y0, half, corner_frac = 0.10, n_arc = 10L) {
  half <- as.numeric(half)
  if (!is.finite(half) || half <= 0) {
    return(data.frame(x = numeric(), y = numeric()))
  }
  side <- 2 * half
  rc <- max(0, min(as.numeric(corner_frac) * side, half))
  if (rc <= 1e-12) {
    return(data.frame(
      x = c(x0 - half, x0 + half, x0 + half, x0 - half),
      y = c(y0 - half, y0 - half, y0 + half, y0 + half)
    ))
  }
  # quarter-circle arcs: BL → BR → TR → TL (centers inset by rc)
  centers <- list(
    c(x0 - half + rc, y0 - half + rc), # BL: angles pi → 3pi/2
    c(x0 + half - rc, y0 - half + rc), # BR: 3pi/2 → 2pi
    c(x0 + half - rc, y0 + half - rc), # TR: 0 → pi/2
    c(x0 - half + rc, y0 + half - rc)  # TL: pi/2 → pi
  )
  a0 <- c(pi, 3 * pi / 2, 0, pi / 2)
  a1 <- c(3 * pi / 2, 2 * pi, pi / 2, pi)
  xs <- numeric()
  ys <- numeric()
  for (k in seq_len(4L)) {
    ang <- seq(a0[k], a1[k], length.out = max(3L, as.integer(n_arc)))
    xs <- c(xs, centers[[k]][1] + rc * cos(ang))
    ys <- c(ys, centers[[k]][2] + rc * sin(ang))
  }
  data.frame(x = xs, y = ys)
}

#' Build rounded-square polygon table for all target nodes.
#' corner_frac = 0.10 → r_corner = 0.10 * side (≈10% of side as corner radius).
.np_square_shape_df <- function(nd, corner_frac = 0.10, n_arc = 10L) {
  empty <- data.frame(
    x = numeric(), y = numeric(), fill_col = character(),
    id = character(), stringsAsFactors = FALSE
  )
  if (!nrow(nd)) return(empty)
  fill_src <- if ("fill_col" %in% names(nd)) nd$fill_col else nd$fill
  do.call(rbind, lapply(seq_len(nrow(nd)), function(i) {
    poly <- .np_rounded_square_poly(
      nd$x[i], nd$y[i], nd$r[i],
      corner_frac = corner_frac, n_arc = n_arc
    )
    if (!nrow(poly)) return(empty[0, , drop = FALSE])
    data.frame(
      x = poly$x, y = poly$y,
      fill_col = fill_src[i], id = nd$name[i],
      stringsAsFactors = FALSE
    )
  }))
}

#' Ellipse boundary radius at angle phi (from +x, radians).
.np_ellipse_r_at <- function(a, b, phi) {
  a <- as.numeric(a)
  b <- as.numeric(b)
  den <- sqrt((b * cos(phi))^2 + (a * sin(phi))^2)
  if (!is.finite(den) || den <= 0) return(max(a, b, na.rm = TRUE))
  (a * b) / den
}

#' Edge-to-edge gap: ellipse (node1) ↔ circle/disk (node2), along center line.
.np_edge_gap_ellipse_disk <- function(x1, y1, a, b, x2, y2, r2) {
  dx <- as.numeric(x2) - as.numeric(x1)
  dy <- as.numeric(y2) - as.numeric(y1)
  dist <- sqrt(dx * dx + dy * dy)
  phi <- atan2(dy, dx)
  r1 <- .np_ellipse_r_at(a, b, phi)
  dist - r1 - as.numeric(r2)
}

#' Data units per cm under ggplot coord_equal + delivery canvas (conservative expand).
.np_data_units_per_cm <- function(x_span, y_span, width_in, height_in, expand = 1.10) {
  xs <- max(as.numeric(x_span), 1e-9) * as.numeric(expand)
  ys <- max(as.numeric(y_span), 1e-9) * as.numeric(expand)
  inches_per_data <- min(
    as.numeric(width_in) / xs,
    as.numeric(height_in) / ys
  )
  1 / (inches_per_data * 2.54)
}

#' Delivery-style HCTP network (updated layout rules)
#' columns: center targets → herb satellites → outermost pathway L/R columns
#' ellipse: center targets → mid pathway ring → outer herb+compound satellites
#' Unified Degree→size 60–120; rounded target squares; black labels; solid edges; no borders
np_plot_hctp_network <- function(net,
                                 type_df,
                                 title = "Herb–compound–target–pathway network",
                                 label_top_n = 45L,
                                 edge_alpha = 0.08,
                                 pathway_mode = c("columns", "ellipse"),
                                 pathway_names = NULL,
                                 size_min = 60,
                                 size_max = 120,
                                 size_to_r = 560,
                                 plot_width_in = 18.5,
                                 plot_height_in = 16.5) {
  if (!requireNamespace("igraph", quietly = TRUE)) stop("需要 igraph")
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
  if (!requireNamespace("ggforce", quietly = TRUE)) {
    stop("Install ggforce for octagon/ellipse/rounded nodes", call. = FALSE)
  }
  pathway_mode <- match.arg(pathway_mode)
  invisible(label_top_n)
  invisible(edge_alpha)

  edges <- np_normalize_network_edges(net)
  typ <- np_normalize_type_table(type_df)
  if (!nrow(edges)) stop("network edges empty", call. = FALSE)
  type_vec <- stats::setNames(typ$type, typ$term)

  edge_cls <- character(nrow(edges))
  for (i in seq_len(nrow(edges))) {
    ta <- type_vec[[edges$from[i]]]
    tb <- type_vec[[edges$to[i]]]
    edge_cls[i] <- paste(sort(c(ta, tb)), collapse = "-")
  }

  herb_comps <- list()
  for (i in which(edge_cls == "A-B")) {
    a <- edges$from[i]
    b <- edges$to[i]
    if (identical(type_vec[[a]], "A")) {
      herb_comps[[a]] <- c(herb_comps[[a]], b)
    } else {
      herb_comps[[b]] <- c(herb_comps[[b]], a)
    }
  }
  herb_comps <- lapply(herb_comps, unique)
  herbs <- names(sort(vapply(herb_comps, length, 1L), decreasing = TRUE))
  herb_comps <- herb_comps[herbs]
  assigned <- .np_assign_compounds_unique(herb_comps)

  targets <- sort(names(type_vec)[type_vec == "C"])
  pathways <- sort(names(type_vec)[type_vec == "D"])

  # global degree on full graph (unified size standard)
  g_all <- igraph::graph_from_data_frame(edges, directed = FALSE)
  g_all <- igraph::simplify(g_all)
  deg_all <- igraph::degree(g_all)

  path_deg <- setNames(integer(length(pathways)), pathways)
  for (i in which(edge_cls == "C-D")) {
    a <- edges$from[i]
    b <- edges$to[i]
    if (identical(type_vec[[a]], "D")) path_deg[[a]] <- path_deg[[a]] + 1L
    if (identical(type_vec[[b]], "D")) path_deg[[b]] <- path_deg[[b]] + 1L
  }
  pathways <- names(sort(path_deg, decreasing = TRUE))

  # Degree → size∈[60,120] → data-coord r (shared scale for A/B/C/D)
  all_names_pre <- unique(c(names(type_vec), edges$from, edges$to))
  deg_pre <- as.numeric(deg_all[all_names_pre])
  deg_pre[is.na(deg_pre)] <- 1
  size_pre <- .np_degree_to_size(deg_pre, size_min = size_min, size_max = size_max, transform = "sqrt")
  names(size_pre) <- all_names_pre
  r_pre <- .np_size_to_r(size_pre, size_to_r = size_to_r)
  names(r_pre) <- all_names_pre

  r_t <- if (length(targets)) max(r_pre[targets], na.rm = TRUE) else 0.1
  r_p <- if (length(pathways)) max(r_pre[pathways], na.rm = TRUE) else 0.1
  # Pathway node shape (ellipse mode): slightly flattened circles — wider than tall
  path_ell_a_frac <- 1.15
  path_ell_b_frac <- 0.85
  r_p_a <- r_p * path_ell_a_frac
  r_p_b <- r_p * path_ell_b_frac
  r_p_extent <- max(r_p_a, r_p_b) # conservative radial half-extent
  # Min pathway↔compound/herb edge gap (ellipse mode): 0.5 cm on delivery canvas
  gap_cm_min <- 0.5
  # Columns: +30% compound-to-compound clearance / orbit spacing vs prior baseline
  compound_spacing_factor <- if (identical(pathway_mode, "columns")) 1.30 else 1.0
  # Spacing: widen pitch/gaps so type-constant fonts fit without per-node shrink.
  # pitch_safety = hard non-overlap floor; *_factor / compound_clearance = visual breathing room.
  pitch_safety <- 1.12
  # Ellipse needs airier target pitch so gene labels stay inside pink squares
  if (identical(pathway_mode, "ellipse")) {
    pitch_factor_x <- 1.55
    pitch_factor_y <- 1.68
    compound_clearance <- 1.62
    pathway_v_gap_factor <- 2.15
    section_pad_tp <- 0.42
    ellipse_annulus_frac <- 0.52
    ellipse_clear_safety <- 0.22
  } else {
    pitch_factor_x <- 1.45
    pitch_factor_y <- 1.55
    compound_clearance <- 1.50
    pathway_v_gap_factor <- 2.00
    section_pad_tp <- 0.36
    ellipse_annulus_frac <- 0.55
    ellipse_clear_safety <- 0.18
  }
  # Per-herb compound ring boost (user "GC" → sample herb code GG 甘草)
  compound_clearance_boost <- c(GG = 2.55, GC = 2.55, DS = 1.90)
  compound_orbit_floor <- c(GG = 1.05, GC = 1.05) # min ring radius for cramped herbs
  section_pad_ph <- 0.14         # pathway↔herb floor pad
  section_pad_col_herb <- 0.14   # columns: target↔herb pad
  section_pad_col_path <- 0.95   # columns: beyond full satellite ring (enclosing)
  pitch_x <- 2 * r_t * pitch_factor_x
  pitch_y <- 2 * r_t * pitch_factor_y
  message(
    "HCTP compound_spacing_factor=", compound_spacing_factor,
    " (columns +30% compound packing; ellipse unchanged)"
  )

  # --- coordinates ---
  pos <- list()
  n_t <- length(targets)
  ncol <- max(8L, as.integer(ceiling(sqrt(n_t * 1.15))))
  nrow_g <- as.integer(ceiling(n_t / ncol))
  gx <- ((seq_len(n_t) - 1L) %% ncol) - (ncol - 1) / 2
  gy <- ((nrow_g - 1) / 2) - ((seq_len(n_t) - 1L) %/% ncol)
  gx <- gx * pitch_x
  gy <- gy * pitch_y
  for (i in seq_len(n_t)) pos[[targets[i]]] <- c(gx[i], gy[i])

  t_half_x <- if (n_t) max(abs(gx)) + r_t else r_t
  t_half_y <- if (n_t) max(abs(gy)) + r_t else r_t
  t_extent <- max(t_half_x, t_half_y)
  t_corner <- sqrt(t_half_x^2 + t_half_y^2) # AABB corner — ellipse clearance floor

  n_h <- length(herbs)
  herb_ang <- if (n_h == 1L) 0 else seq(0, 2 * pi, length.out = n_h + 1)[seq_len(n_h)] - pi / 2
  herb_cols <- .np_herb_palette(herbs)

  # compound orbits: large clusters use 2 rings to shrink outer radius (more compact)
  # orbit_plan[[h]] = list of data.frames(name, cr) per compound
  orbit_plan <- setNames(vector("list", n_h), herbs)
  outer_orbit <- setNames(numeric(n_h), herbs)
  for (i in seq_len(n_h)) {
    h <- herbs[i]
    comps <- assigned[[h]]
    m <- length(comps)
    if (!m) {
      orbit_plan[[i]] <- data.frame(name = character(), cr = numeric(), stringsAsFactors = FALSE)
      outer_orbit[[i]] <- 0
      next
    }
    r_h <- as.numeric(r_pre[[h]])
    if (!is.finite(r_h)) r_h <- 0.1
    r_b_max <- max(as.numeric(r_pre[comps]), na.rm = TRUE)
    if (!is.finite(r_b_max)) r_b_max <- 0.075
    # per-herb boost (GG/GC/DS) or mild extra clearance for moderate cramped rings
    boost <- if (h %in% names(compound_clearance_boost)) {
      compound_clearance_boost[[h]]
    } else if (m >= 4L && m <= 12L) {
      1.12
    } else if (m >= 20L) {
      1.20
    } else {
      1.0
    }
    # columns: compound_spacing_factor=1.30 widens ring radius + angular clearance
    clr <- compound_clearance * boost * compound_spacing_factor
    # chord safety slightly above 1 so adjacent compound fills never kiss
    chord_safe <- if (identical(pathway_mode, "ellipse")) {
      1.18
    } else {
      1.12 * compound_spacing_factor
    }
    ring_gap <- 2 * r_b_max * clr
    cr_hub <- r_h + r_b_max * clr
    # split into 2 rings when many compounds — keep multi-ring for dense herbs (e.g. DS)
    n_rings_c <- if (m >= 28L) 2L else 1L
    if (n_rings_c == 1L) {
      cr1 <- if (m == 1L) {
        cr_hub
      } else {
        max(cr_hub, chord_safe * r_b_max / sin(pi / m))
      }
      if (h %in% names(compound_orbit_floor)) {
        cr1 <- max(cr1, compound_orbit_floor[[h]] * compound_spacing_factor)
      }
      orbit_plan[[i]] <- data.frame(name = comps, cr = rep(cr1, m), stringsAsFactors = FALSE)
      outer_orbit[[i]] <- cr1
    } else {
      # fewer on inner ring → less DS center crush; ~40% inner / 60% outer
      n_inner <- as.integer(max(1L, ceiling(m * 0.40)))
      n_outer <- m - n_inner
      cr1 <- max(
        cr_hub,
        if (n_inner <= 1L) cr_hub else chord_safe * r_b_max / sin(pi / n_inner)
      )
      cr2 <- max(
        cr1 + ring_gap,
        if (n_outer <= 1L) cr1 + ring_gap else chord_safe * r_b_max / sin(pi / n_outer)
      )
      # prefer smaller outer: if single-ring is tighter, fall back
      cr_single <- max(cr_hub, chord_safe * r_b_max / sin(pi / m))
      if (cr_single <= cr2 * 0.92) {
        orbit_plan[[i]] <- data.frame(name = comps, cr = rep(cr_single, m), stringsAsFactors = FALSE)
        outer_orbit[[i]] <- cr_single
      } else {
        orbit_plan[[i]] <- data.frame(
          name = comps,
          cr = c(rep(cr1, n_inner), rep(cr2, n_outer)),
          stringsAsFactors = FALSE
        )
        outer_orbit[[i]] <- cr2
      }
    }
  }
  max_comp_r <- if (n_h) max(outer_orbit) else 0
  # compound fill half-extent on outermost orbit (for inter-section clearance)
  r_b_clear <- if (n_h) {
    rb <- vapply(herbs, function(h) {
      comps <- assigned[[h]]
      if (!length(comps)) return(0)
      mx <- max(as.numeric(r_pre[comps]), na.rm = TRUE)
      if (!is.finite(mx)) 0.075 else mx
    }, numeric(1))
    max(rb)
  } else {
    0.075
  }
  # cluster radial reach from herb center = orbit + compound radius (herb body sits inside)
  herb_clear <- max_comp_r + r_b_clear

  n_p <- length(pathways)
  n_left <- as.integer(ceiling(n_p / 2))
  left_p <- if (n_p) pathways[seq_len(n_left)] else character()
  right_p <- if (n_p > n_left) pathways[(n_left + 1):n_p] else character()

  # min herb ring so adjacent herb+compound clusters do not collide
  herb_r_min_cluster <- if (n_h >= 2L) {
    herb_clear * 1.03 / sin(pi / n_h)
  } else {
    t_extent + herb_clear + 0.15
  }

  if (identical(pathway_mode, "ellipse")) {
    # Pathway mid-ring must clear target AABB fills on ALL axes (esp. top/bottom).
    # Floor: axis half-extents + flattened-ellipse pathway + square half-diagonal + safety.
    # Reserve annulus band ≥ ~0.5 cm (refined post-layout via data↔cm conversion).
    r_t_clear <- r_t * sqrt(2) # rounded-square corner reach
    # Rough cm→data using expected outer span (herb ring); refined after placement.
    span_guess <- 2 * max(
      herb_r_min_cluster + herb_clear,
      t_extent + herb_clear + r_p_extent + 1.2
    )
    duc_guess <- .np_data_units_per_cm(
      span_guess, span_guess, plot_width_in, plot_height_in, expand = 1.10
    )
    gap_data_min <- gap_cm_min * duc_guess
    path_floor_x <- t_half_x + r_p_a + r_t_clear * 0.55 + section_pad_tp + ellipse_clear_safety
    path_floor_y <- t_half_y + r_p_b + r_t_clear * 0.55 + section_pad_tp + ellipse_clear_safety
    path_floor <- max(path_floor_x, path_floor_y, t_corner + r_p_extent * 1.15 + section_pad_tp)
    path_band <- max(
      2.4 * r_p_extent * pathway_v_gap_factor + ellipse_clear_safety,
      gap_data_min + r_p_extent * pitch_safety + section_pad_ph
    )
    herb_r <- max(
      path_floor + path_band + herb_clear + section_pad_ph,
      herb_r_min_cluster
    )
    path_ceil <- herb_r - herb_clear - r_p_extent * pitch_safety - section_pad_ph - gap_data_min
    if (!is.finite(path_ceil) || path_ceil < path_floor + 0.05) {
      herb_r <- path_floor + path_band + herb_clear + section_pad_ph
      path_ceil <- herb_r - herb_clear - r_p_extent * pitch_safety - section_pad_ph - gap_data_min
    }
    path_R <- path_floor + ellipse_annulus_frac * max(0, path_ceil - path_floor)
    # intra: chord spacing so pathway ellipses are not cramped (clamp to band)
    if (n_p > 1L) {
      path_R <- max(path_R, min(path_ceil, r_p_extent * pathway_v_gap_factor / sin(pi / n_p)))
    }
    path_R <- max(path_floor, min(path_R, path_ceil))
    # axis-matched ellipse: guarantee clearance on left/right AND top/bottom
    # Extra 12% on y — taller target grid was still hugging top/bottom pathways visually
    path_rx <- max(path_R, path_floor_x) * 1.04
    path_ry <- max(path_R * 0.98, path_floor_y) * 1.12
    pang <- if (n_p <= 1L) {
      0
    } else {
      seq(-pi / 2, -pi / 2 + 2 * pi, length.out = n_p + 1)[seq_len(n_p)]
    }
    for (i in seq_len(n_p)) {
      pos[[pathways[i]]] <- c(path_rx * cos(pang[i]), path_ry * sin(pang[i]))
    }
    message(
      "HCTP ellipse path shape a/b frac=", path_ell_a_frac, "/", path_ell_b_frac,
      " gap_cm_min=", gap_cm_min,
      " gap_data_guess=", round(gap_data_min, 4),
      " (canvas ", plot_width_in, "×", plot_height_in, " in)"
    )
  } else {
    # columns: herbs mid around targets; pathways placed after herbs (outer enclosing)
    herb_r <- max(
      t_extent + herb_clear + section_pad_col_herb,
      herb_r_min_cluster
    )
  }

  for (i in seq_len(n_h)) {
    h <- herbs[i]
    cx <- herb_r * cos(herb_ang[i])
    cy <- herb_r * sin(herb_ang[i])
    pos[[h]] <- c(cx, cy)
    plan <- orbit_plan[[h]]
    if (!nrow(plan)) next
    # place each ring separately with equal angular spacing + slight phase offset
    for (cr_val in unique(plan$cr)) {
      idx <- which(plan$cr == cr_val)
      mm <- length(idx)
      phase <- if (identical(cr_val, max(plan$cr)) && length(unique(plan$cr)) > 1L) pi / max(mm, 1L) else 0
      cang <- if (mm == 1L) 0 else 2 * pi * (seq_len(mm) - 1) / mm + phase
      for (j in seq_len(mm)) {
        nm <- plan$name[idx[j]]
        pos[[nm]] <- c(cx + cr_val * cos(cang[j]), cy + cr_val * sin(cang[j]))
      }
    }
  }

  if (!identical(pathway_mode, "ellipse")) {
    # Pathways L/R outermost: sit outside the full circular herb+compound ring
    # (herb_r + herb_clear), not merely max(|x|) of diagonal satellites.
    path_v_gap <- 2 * r_p * pathway_v_gap_factor
    placed_nms <- names(pos)
    placed_types <- unname(type_vec[placed_nms])
    abc <- !is.na(placed_types) & placed_types %in% c("A", "B", "C")
    if (any(abc)) {
      xy <- do.call(rbind, lapply(placed_nms[abc], function(nm) {
        matrix(as.numeric(pos[[nm]]), nrow = 1L)
      }))
      rr <- vapply(placed_nms[abc], function(nm) {
        r0 <- as.numeric(r_pre[[nm]])
        if (!is.finite(r0)) 0.1 else r0
      }, numeric(1))
      x_extent <- max(abs(xy[, 1]) + rr, na.rm = TRUE)
    } else {
      x_extent <- t_extent
    }
    # ring-enclosing floor: pathways wrap the whole herb satellite composition
    ring_enclose <- herb_r + herb_clear + r_p * pitch_safety + section_pad_col_path
    outer_x <- max(x_extent + r_p * pitch_safety + section_pad_col_path,
                   ring_enclose, t_extent + r_p + section_pad_col_path)
    # hard floor: pathways must sit clearly outside satellite ring (user-visible enclosure)
    outer_x <- max(outer_x, herb_r + herb_clear + r_p + 1.25)
    message(
      "HCTP columns outer_x=", round(outer_x, 3),
      " x_extent=", round(x_extent, 3),
      " ring_enclose=", round(ring_enclose, 3),
      " herb_r+clear=", round(herb_r + herb_clear, 3)
    )
    place_col <- function(nodes, x, pos_list) {
      m <- length(nodes)
      if (!m) return(pos_list)
      span <- (m - 1) * path_v_gap / 2
      ys <- if (m == 1L) 0 else seq(span, -span, length.out = m)
      for (i in seq_len(m)) pos_list[[nodes[i]]] <- c(x, ys[i])
      pos_list
    }
    pos <- place_col(left_p, -outer_x, pos)
    pos <- place_col(right_p, outer_x, pos)
  } else {
    outer_x <- herb_r + herb_clear
  }

  all_nodes <- names(pos)
  miss_edge <- setdiff(unique(c(edges$from, edges$to)), all_nodes)
  if (length(miss_edge)) {
    for (nm in miss_edge) {
      t <- type_vec[[nm]]
      if (identical(t, "B")) {
        h <- herbs[which.min(vapply(assigned, length, 1L))]
        base <- pos[[h]]
        assigned[[h]] <- c(assigned[[h]], nm)
        k <- length(assigned[[h]])
        pos[[nm]] <- base + c(0.65 * cos(k * 0.7), 0.65 * sin(k * 0.7))
      } else if (identical(t, "D")) {
        pos[[nm]] <- c(if (identical(pathway_mode, "ellipse")) (t_extent + r_p + 0.55) else outer_x, 0)
      } else {
        pos[[nm]] <- c(0, 0)
      }
    }
    all_nodes <- names(pos)
  }

  nd <- data.frame(
    name = all_nodes,
    type = unname(type_vec[all_nodes]),
    x = vapply(all_nodes, function(nm) as.numeric(pos[[nm]][1]), numeric(1)),
    y = vapply(all_nodes, function(nm) as.numeric(pos[[nm]][2]), numeric(1)),
    stringsAsFactors = FALSE
  )
  nd <- nd[!is.na(nd$type) & !is.na(nd$x) & !is.na(nd$y), , drop = FALSE]
  nd$degree <- as.numeric(deg_all[nd$name])
  nd$degree[is.na(nd$degree)] <- 1
  nd$size <- .np_degree_to_size(nd$degree, size_min = size_min, size_max = size_max, transform = "sqrt")
  nd$r <- .np_size_to_r(nd$size, size_to_r = size_to_r)

  nd$herb_owner <- NA_character_
  for (h in herbs) {
    nd$herb_owner[nd$name == h] <- h
    nd$herb_owner[nd$name %in% assigned[[h]]] <- h
  }
  accents <- .np_hctp_accents
  # fill_col (not "fill") avoids aes name collision with ggplot fill aesthetic
  nd$fill_col <- accents$target
  nd$fill_col[nd$type == "A"] <- unname(herb_cols[nd$name[nd$type == "A"]])
  for (h in herbs) {
    nd$fill_col[nd$type == "B" & nd$herb_owner == h] <- herb_cols[[h]]
  }
  # pathway color by pathway connectivity (visual); size still global Degree
  pd <- as.numeric(path_deg[nd$name[nd$type == "D"]])
  if (length(pd)) {
    pmin <- min(pd)
    pmax <- max(pd)
    path_pal <- grDevices::colorRampPalette(accents$pathway)(100)
    pr <- pmax(1L, pmin(100L, as.integer(round(1 + 99 * (pd - pmin) / max(1e-9, pmax - pmin)))))
    nd$fill_col[nd$type == "D"] <- path_pal[pr]
  }

  el <- edges
  el$ta <- type_vec[el$from]
  el$tb <- type_vec[el$to]
  el$pair <- vapply(seq_len(nrow(el)), function(i) {
    paste(sort(c(el$ta[i], el$tb[i])), collapse = "-")
  }, character(1))
  el$x <- vapply(el$from, function(nm) pos[[nm]][1], numeric(1))
  el$y <- vapply(el$from, function(nm) pos[[nm]][2], numeric(1))
  el$xend <- vapply(el$to, function(nm) pos[[nm]][1], numeric(1))
  el$yend <- vapply(el$to, function(nm) pos[[nm]][2], numeric(1))
  el_ab <- el[el$pair == "A-B", , drop = FALSE]
  keep_ab <- logical(nrow(el_ab))
  for (i in seq_len(nrow(el_ab))) {
    a <- el_ab$from[i]
    b <- el_ab$to[i]
    h <- if (identical(type_vec[[a]], "A")) a else b
    cpd <- if (identical(type_vec[[a]], "B")) a else b
    keep_ab[i] <- isTRUE(cpd %in% assigned[[h]])
  }
  el_ab <- el_ab[keep_ab, , drop = FALSE]
  el_bc <- el[el$pair == "B-C", , drop = FALSE]
  el_cd <- el[el$pair == "C-D", , drop = FALSE]

  nd_c <- nd[nd$type == "C", , drop = FALSE]
  nd_b <- nd[nd$type == "B", , drop = FALSE]
  nd_a <- nd[nd$type == "A", , drop = FALSE]
  nd_d <- nd[nd$type == "D", , drop = FALSE]

  # Pathway fills: ellipse mode → flattened ellipses (a > b); columns keep hexagons
  if (nrow(nd_d)) {
    if (identical(pathway_mode, "ellipse")) {
      nd_d$a <- nd_d$r * path_ell_a_frac
      nd_d$b <- nd_d$r * path_ell_b_frac
      nd_d$angle <- 0
    } else {
      nd_d$sides <- 6L
      nd_d$angle <- 0
    }
  }

  # Ellipse: assert no fill overlap between pathways (ellipses) and targets (rounded squares).
  # Conservative: dist(centers) > r_ell(φ) + r_c*√2 + safety; push mid-ring out if needed.
  if (identical(pathway_mode, "ellipse") && nrow(nd_d) && nrow(nd_c)) {
    min_gap <- Inf
    for (i in seq_len(nrow(nd_d))) {
      for (j in seq_len(nrow(nd_c))) {
        gap_ij <- .np_edge_gap_ellipse_disk(
          nd_d$x[i], nd_d$y[i], nd_d$a[i], nd_d$b[i],
          nd_c$x[j], nd_c$y[j], nd_c$r[j] * sqrt(2)
        ) - ellipse_clear_safety
        if (gap_ij < min_gap) min_gap <- gap_ij
      }
    }
    if (!is.finite(min_gap) || min_gap < 0) {
      # radial push: scale pathway positions outward until clearance holds
      push <- 1.0
      for (iter in 1:12) {
        if (is.finite(min_gap) && min_gap >= 0) break
        push <- push * 1.08
        nd_d$x <- nd_d$x * 1.08
        nd_d$y <- nd_d$y * 1.08
        for (i in seq_len(nrow(nd_d))) {
          pos[[nd_d$name[i]]] <- c(nd_d$x[i], nd_d$y[i])
        }
        nd$x[nd$type == "D"] <- nd_d$x
        nd$y[nd$type == "D"] <- nd_d$y
        min_gap <- Inf
        for (i in seq_len(nrow(nd_d))) {
          for (j in seq_len(nrow(nd_c))) {
            gap_ij <- .np_edge_gap_ellipse_disk(
              nd_d$x[i], nd_d$y[i], nd_d$a[i], nd_d$b[i],
              nd_c$x[j], nd_c$y[j], nd_c$r[j] * sqrt(2)
            ) - ellipse_clear_safety
            if (gap_ij < min_gap) min_gap <- gap_ij
          }
        }
      }
      el_cd$x <- vapply(el_cd$from, function(nm) pos[[nm]][1], numeric(1))
      el_cd$y <- vapply(el_cd$from, function(nm) pos[[nm]][2], numeric(1))
      el_cd$xend <- vapply(el_cd$to, function(nm) pos[[nm]][1], numeric(1))
      el_cd$yend <- vapply(el_cd$to, function(nm) pos[[nm]][2], numeric(1))
      message("HCTP ellipse path–target push×", round(push, 3), " min_gap=", round(min_gap, 4))
    }
    if (!is.finite(min_gap) || min_gap < 0) {
      warning(
        "HCTP ellipse: pathway–target fill overlap remains (min_gap=",
        round(min_gap, 4), "); inspect layout pads",
        call. = FALSE
      )
    } else {
      message("HCTP ellipse path–target clearance OK min_gap=", round(min_gap, 4))
    }
  }

  # Ellipse: enforce pathway ↔ compound/herb edge gap ≥ 0.5 cm (delivery canvas).
  # Convert cm→data from current node AABB under coord_equal; push herb satellites out.
  if (identical(pathway_mode, "ellipse") && nrow(nd_d) && (nrow(nd_a) + nrow(nd_b)) > 0L) {
    calc_span_duc <- function(nd_tbl) {
      xl <- Inf; xh <- -Inf; yl <- Inf; yh <- -Inf
      for (i in seq_len(nrow(nd_tbl))) {
        rr <- if (identical(nd_tbl$type[i], "D")) {
          max(nd_tbl$r[i] * path_ell_a_frac, nd_tbl$r[i] * path_ell_b_frac)
        } else {
          nd_tbl$r[i]
        }
        xl <- min(xl, nd_tbl$x[i] - rr)
        xh <- max(xh, nd_tbl$x[i] + rr)
        yl <- min(yl, nd_tbl$y[i] - rr)
        yh <- max(yh, nd_tbl$y[i] + rr)
      }
      list(
        x_span = xh - xl, y_span = yh - yl,
        duc = .np_data_units_per_cm(
          xh - xl, yh - yl, plot_width_in, plot_height_in, expand = 1.10
        )
      )
    }
    calc_min_path_ab_gap <- function(nd_d_tbl, nd_tbl) {
      ab <- nd_tbl[nd_tbl$type %in% c("A", "B"), c("x", "y", "r"), drop = FALSE]
      if (!nrow(ab)) return(Inf)
      mg <- Inf
      for (i in seq_len(nrow(nd_d_tbl))) {
        for (j in seq_len(nrow(ab))) {
          g <- .np_edge_gap_ellipse_disk(
            nd_d_tbl$x[i], nd_d_tbl$y[i], nd_d_tbl$a[i], nd_d_tbl$b[i],
            ab$x[j], ab$y[j], ab$r[j]
          )
          if (g < mg) mg <- g
        }
      }
      mg
    }
    span_info <- calc_span_duc(nd)
    gap_data_req <- gap_cm_min * span_info$duc
    min_ab_gap <- calc_min_path_ab_gap(nd_d, nd)
    push_ab <- 0
    for (iter in seq_len(20L)) {
      if (is.finite(min_ab_gap) && min_ab_gap >= gap_data_req - 1e-9) break
      need <- if (is.finite(min_ab_gap)) (gap_data_req - min_ab_gap) else gap_data_req
      need <- max(need, 0.01) * 1.02
      for (i in seq_len(n_h)) {
        h <- herbs[i]
        ang <- herb_ang[i]
        dxy <- c(need * cos(ang), need * sin(ang))
        if (!is.null(pos[[h]])) {
          pos[[h]] <- as.numeric(pos[[h]]) + dxy
          nd$x[nd$name == h] <- pos[[h]][1]
          nd$y[nd$name == h] <- pos[[h]][2]
        }
        for (cp in assigned[[h]]) {
          if (!is.null(pos[[cp]])) {
            pos[[cp]] <- as.numeric(pos[[cp]]) + dxy
            nd$x[nd$name == cp] <- pos[[cp]][1]
            nd$y[nd$name == cp] <- pos[[cp]][2]
          }
        }
      }
      herb_r <- herb_r + need
      push_ab <- push_ab + need
      span_info <- calc_span_duc(nd)
      gap_data_req <- gap_cm_min * span_info$duc
      min_ab_gap <- calc_min_path_ab_gap(nd_d, nd)
    }
    # refresh A/B tables + AB/BC edge endpoints after any radial push
    nd_a <- nd[nd$type == "A", , drop = FALSE]
    nd_b <- nd[nd$type == "B", , drop = FALSE]
    el_ab$x <- vapply(el_ab$from, function(nm) pos[[nm]][1], numeric(1))
    el_ab$y <- vapply(el_ab$from, function(nm) pos[[nm]][2], numeric(1))
    el_ab$xend <- vapply(el_ab$to, function(nm) pos[[nm]][1], numeric(1))
    el_ab$yend <- vapply(el_ab$to, function(nm) pos[[nm]][2], numeric(1))
    el_bc$x <- vapply(el_bc$from, function(nm) pos[[nm]][1], numeric(1))
    el_bc$y <- vapply(el_bc$from, function(nm) pos[[nm]][2], numeric(1))
    el_bc$xend <- vapply(el_bc$to, function(nm) pos[[nm]][1], numeric(1))
    el_bc$yend <- vapply(el_bc$to, function(nm) pos[[nm]][2], numeric(1))
    min_ab_gap_cm <- min_ab_gap / span_info$duc
    message(
      "HCTP ellipse path↔compound/herb: gap_data_req=", round(gap_data_req, 4),
      " (=", gap_cm_min, " cm × ", round(span_info$duc, 4), " data/cm;",
      " span=", round(span_info$x_span, 3), "×", round(span_info$y_span, 3),
      " canvas=", plot_width_in, "×", plot_height_in, " in)",
      " achieved_gap_data=", round(min_ab_gap, 4),
      " achieved_gap_cm=", round(min_ab_gap_cm, 3),
      " herb_push=", round(push_ab, 4)
    )
    if (!is.finite(min_ab_gap_cm) || min_ab_gap_cm + 1e-6 < gap_cm_min) {
      warning(
        "HCTP ellipse: pathway↔compound/herb min gap ",
        round(min_ab_gap_cm, 3), " cm < ", gap_cm_min, " cm",
        call. = FALSE
      )
    } else {
      stopifnot(min_ab_gap_cm + 1e-6 >= gap_cm_min)
      message(
        "HCTP ellipse ASSERT OK: min pathway↔compound/herb gap ≥ ",
        gap_cm_min, " cm (achieved ", round(min_ab_gap_cm, 3), " cm)"
      )
    }
  }

  # relative corner: r_corner = 0.10 * side; side = 2*r → same ratio for all Degree sizes
  target_corner_frac <- 0.10
  nd_c_shape <- .np_square_shape_df(nd_c, corner_frac = target_corner_frac, n_arc = 10L)
  nd_a$sides <- 8L
  nd_a$angle <- 0 # flat side horizontal (0°)
  # pathway labels: ID only (e.g. hsa04210), single line — never full names
  if (nrow(nd_d)) {
    nd_d$label <- unname(.np_resolve_pathway_labels(nd_d$name, pathway_names))
  }

  message(
    "HCTP pathways: ", nrow(nd_d),
    " left=", sum(nd_d$x < 0), " right=", sum(nd_d$x > 0),
    " mode=", pathway_mode,
    " size=[", size_min, ",", size_max, "]→r via /", size_to_r,
    " pitch_x=", round(pitch_x, 3), " pitch_y=", round(pitch_y, 3),
    " (fx=", pitch_factor_x, " fy=", pitch_factor_y, ")",
    " compound_clr=", compound_clearance,
    " compound_spacing_f=", compound_spacing_factor,
    " path_v_gap_f=", pathway_v_gap_factor,
    " herb_r=", round(herb_r, 3),
    if (!identical(pathway_mode, "ellipse")) paste0(" outer_x=", round(outer_x, 3)) else "",
    " target_n=", nrow(nd_c), " shape_rows=", nrow(nd_c_shape),
    " target_r_corner=", target_corner_frac, "*side",
    if (identical(pathway_mode, "ellipse")) {
      paste0(" path_ell_a/b=", path_ell_a_frac, "/", path_ell_b_frac)
    } else {
      ""
    },
    " labels=ID"
  )
  if (!nrow(nd_c) || !nrow(nd_c_shape)) {
    warning("HCTP target fills missing: n_C=", nrow(nd_c), " shape_rows=", nrow(nd_c_shape))
  }

  path_subtitle <- if (identical(pathway_mode, "ellipse")) {
    sprintf(
      "ellipse: pathway mid-ring (flattened ellipses a/b=%.2f/%.2f; ≥%.1f cm gap to compounds)",
      path_ell_a_frac, path_ell_b_frac, gap_cm_min
    )
  } else {
    sprintf(
      "columns: pathways L/R outer · compound spacing ×%.2f",
      compound_spacing_factor
    )
  }
  edge_col <- accents$edge
  edge_cd_col <- if (!is.null(accents$edge_cd)) accents$edge_cd else "#2F6FBF"
  # Cytoscape pt → ggplot mm: size = (pt / ggplot2::.pt) * canvas_scale
  # Type-constant fonts — never per-node clamp (spacing widened instead).
  lab_pt <- .np_hctp_label_pt
  lab_scale <- if (!is.null(lab_pt$canvas_scale)) lab_pt$canvas_scale else 0.26
  sz_herb <- .np_pt_to_ggplot_size(lab_pt$herb, scale = lab_scale)
  sz_comp <- .np_pt_to_ggplot_size(lab_pt$compound, scale = lab_scale)
  sz_tgt  <- .np_pt_to_ggplot_size(lab_pt$target, scale = lab_scale)
  sz_path <- .np_pt_to_ggplot_size(lab_pt$pathway, scale = lab_scale)
  message(
    "HCTP type fonts(mm): target=", round(sz_tgt, 2),
    " herb=", round(sz_herb, 2),
    " compound=", round(sz_comp, 2),
    " pathway=", round(sz_path, 2),
    " (pt ", lab_pt$target, "/", lab_pt$herb, "/", lab_pt$compound, "/", lab_pt$pathway,
    " ×scale ", lab_scale, ")"
  )
  if (nrow(nd_a)) nd_a$label_size <- sz_herb
  if (nrow(nd_b)) nd_b$label_size <- sz_comp
  if (nrow(nd_c)) nd_c$label_size <- sz_tgt
  if (nrow(nd_d)) nd_d$label_size <- sz_path

  path_geom <- if (identical(pathway_mode, "ellipse")) {
    ggforce::geom_ellipse(
      data = nd_d,
      ggplot2::aes(x0 = x, y0 = y, a = a, b = b, angle = angle, fill = fill_col),
      colour = NA, linewidth = 0, n = 64, alpha = 1
    )
  } else {
    ggforce::geom_regon(
      data = nd_d,
      ggplot2::aes(x0 = x, y0 = y, r = r, fill = fill_col, sides = sides, angle = angle),
      colour = NA, linewidth = 0, alpha = 1
    )
  }

  p <- ggplot2::ggplot() +
    # solid edges under fills — A–B / B–C muted grey; C–D distinct blue
    ggplot2::geom_segment(
      data = el_bc,
      ggplot2::aes(x = x, y = y, xend = xend, yend = yend),
      color = edge_col, alpha = 0.18, linewidth = 0.2, linetype = "solid"
    ) +
    ggplot2::geom_segment(
      data = el_ab,
      ggplot2::aes(x = x, y = y, xend = xend, yend = yend),
      color = edge_col, alpha = 0.28, linewidth = 0.28, linetype = "solid"
    ) +
    ggplot2::geom_segment(
      data = el_cd,
      ggplot2::aes(x = x, y = y, xend = xend, yend = yend),
      color = edge_cd_col, alpha = 0.42, linewidth = 0.40, linetype = "solid"
    ) +
    # targets FIRST among nodes: solid pink rounded squares (must be visible, not labels-only)
    ggplot2::geom_polygon(
      data = nd_c_shape,
      ggplot2::aes(x = x, y = y, group = id, fill = fill_col),
      colour = NA, linewidth = 0, alpha = 1
    ) +
    # compounds: circles in DATA coords — no border
    ggforce::geom_circle(
      data = nd_b,
      ggplot2::aes(x0 = x, y0 = y, r = r, fill = fill_col),
      colour = NA, linewidth = 0, n = 64, alpha = 1
    ) +
    # herbs: octagon flat-top, no border
    ggforce::geom_regon(
      data = nd_a,
      ggplot2::aes(x0 = x, y0 = y, r = r, fill = fill_col, sides = sides, angle = angle),
      colour = NA, linewidth = 0, alpha = 1
    ) +
    path_geom +
    ggplot2::scale_fill_identity() +
    # labels AFTER fills — type-constant font sizes
    ggplot2::geom_text(
      data = nd_a,
      ggplot2::aes(x = x, y = y, label = name, size = label_size),
      fontface = "bold", color = "black", hjust = 0.5, vjust = 0.5,
      show.legend = FALSE
    ) +
    ggplot2::geom_text(
      data = nd_b,
      ggplot2::aes(x = x, y = y, label = name, size = label_size),
      color = "black", hjust = 0.5, vjust = 0.5,
      show.legend = FALSE
    ) +
    ggplot2::geom_text(
      data = nd_c,
      ggplot2::aes(x = x, y = y, label = name, size = label_size),
      color = "black", hjust = 0.5, vjust = 0.5,
      show.legend = FALSE
    ) +
    ggplot2::geom_text(
      data = nd_d,
      ggplot2::aes(x = x, y = y, label = label, size = label_size),
      fontface = "bold", color = "black",
      hjust = 0.5, vjust = 0.5, lineheight = 1,
      show.legend = FALSE
    ) +
    ggplot2::scale_size_identity() +
    ggplot2::labs(
      title = title,
      subtitle = sprintf(
        "%s · Degree→size %d–%d (r=size/%g) · C–D edges blue · type-constant fonts · A=%d B=%d C=%d D=%d",
        path_subtitle, size_min, size_max, size_to_r,
        length(herbs), sum(vapply(assigned, length, 1L)), length(targets), length(pathways)
      )
    ) +
    ggplot2::coord_equal(clip = "off") +
    ggplot2::theme_void(base_size = 11) +
    ggplot2::theme(
      plot.title = ggplot2::element_text(face = "bold", size = 12, hjust = 0.5),
      plot.subtitle = ggplot2::element_text(size = 7.5, color = "grey35", hjust = 0.5),
      plot.margin = ggplot2::margin(12, 18, 12, 18),
      plot.background = ggplot2::element_rect(fill = "white", color = NA)
    )
  if (isTRUE(.np_ensure_plotqa())) {
    lab_map <- setNames(as.character(nd$name), nd$name)
    if (nrow(nd_d) && "label" %in% names(nd_d)) {
      lab_map[nd_d$name] <- as.character(nd_d$label)
    }
    sz_map <- setNames(rep(2.5, nrow(nd)), nd$name)
    if (nrow(nd_a)) sz_map[nd_a$name] <- nd_a$label_size
    if (nrow(nd_b)) sz_map[nd_b$name] <- nd_b$label_size
    if (nrow(nd_c)) sz_map[nd_c$name] <- nd_c$label_size
    if (nrow(nd_d)) sz_map[nd_d$name] <- nd_d$label_size
    qa_nodes <- data.frame(
      x = nd$x, y = nd$y, r = nd$r,
      label = unname(lab_map[nd$name]),
      label_size = unname(sz_map[nd$name]),
      stringsAsFactors = FALSE
    )
    try(
      viz_qa_network_nodes(
        qa_nodes,
        plot_id = paste0("HCTP_", pathway_mode),
        dense_network = TRUE,
        hard_fail = FALSE
      ),
      silent = FALSE
    )
  }
  p
}
