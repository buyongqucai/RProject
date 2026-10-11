# STRING API PPI + herb–compound–target–pathway network (R preview)
# Cytoscape remains optional after user reviews these figures.

.np_string_api_base <- "https://string-db.org/api"

#' POST helper for STRING REST (identifiers as %0d-joined)
.np_string_post <- function(method, body, timeout = 120) {
  url <- paste0(.np_string_api_base, "/tsv/", method)
  if (requireNamespace("httr", quietly = TRUE)) {
    resp <- httr::POST(
      url,
      body = body,
      encode = "form",
      httr::timeout(timeout)
    )
    if (httr::http_error(resp)) {
      stop(
        "STRING API error (", method, "): ",
        httr::status_code(resp), " ",
        substr(httr::content(resp, as = "text", encoding = "UTF-8"), 1, 300),
        call. = FALSE
      )
    }
    return(httr::content(resp, as = "text", encoding = "UTF-8"))
  }
  # base fallback
  con <- NULL
  on.exit(if (!is.null(con)) try(close(con), silent = TRUE), add = TRUE)
  form <- paste(
    vapply(names(body), function(nm) {
      paste0(
        utils::URLencode(nm, reserved = TRUE), "=",
        utils::URLencode(as.character(body[[nm]]), reserved = TRUE)
      )
    }, character(1)),
    collapse = "&"
  )
  con <- url(url, open = "r")
  # url() cannot POST easily; require httr
  stop("Install httr for STRING API calls", call. = FALSE)
}

#' Normalize score threshold across API (0–1000) and web export (0–1)
.np_string_score_threshold <- function(scores, min_score) {
  sc <- as.numeric(scores)
  thr <- as.numeric(min_score)
  if (!length(sc) || !is.finite(thr)) return(thr)
  mx <- max(sc, na.rm = TRUE)
  if (is.finite(mx) && mx <= 1.5 && thr > 1.5) thr <- thr / 1000
  if (is.finite(mx) && mx > 1.5 && thr <= 1.5) thr <- thr * 1000
  thr
}

#' Map gene symbols → STRING IDs (cached within call)
.np_string_map_ids <- function(genes,
                               species = 9606L,
                               caller_identity = "RProject_NetworkPharmacology") {
  ids_txt <- .np_string_post(
    "get_string_ids",
    list(
      identifiers = paste(genes, collapse = "\r"),
      species = as.character(species),
      limit = "1",
      echo_query = "1",
      caller_identity = caller_identity
    )
  )
  ids <- utils::read.delim(text = ids_txt, stringsAsFactors = FALSE, check.names = FALSE)
  if (!nrow(ids) || !"stringId" %in% names(ids)) {
    stop("STRING get_string_ids returned no mappings", call. = FALSE)
  }
  string_ids <- unique(as.character(ids$stringId))
  string_ids <- string_ids[!is.na(string_ids) & nzchar(string_ids)]
  if (!length(string_ids)) stop("No STRING IDs mapped", call. = FALSE)
  list(ids = ids, string_ids = string_ids)
}

#' Download official STRING network image (3D bubbles, evidence edges)
#' Matches web export: required_score=900, hide isolates, show structure pics.
#' Pass gene symbols (not ENSP) so labels match the STRING web export.
#' @param format one of image | highres_image | svg
np_fetch_string_network_image <- function(genes,
                                          out_path,
                                          species = 9606L,
                                          required_score = 900L,
                                          network_flavor = "evidence",
                                          network_type = "functional",
                                          hide_disconnected_nodes = TRUE,
                                          block_structure_pics = FALSE,
                                          show_query_node_labels = TRUE,
                                          format = c("highres_image", "image", "svg"),
                                          caller_identity = "RProject_NetworkPharmacology",
                                          string_ids = NULL,
                                          timeout = 300) {
  format <- match.arg(format)
  genes <- unique(as.character(genes))
  genes <- genes[!is.na(genes) & nzchar(genes)]
  if (!length(genes)) stop("genes is empty", call. = FALSE)
  if (!requireNamespace("httr", quietly = TRUE)) stop("Install httr", call. = FALSE)
  # Prefer gene symbols as identifiers so show_query_node_labels shows symbols
  # (passing ENSP makes labels look like 9606.ENSP…).
  if (!is.null(string_ids)) {
    message("Note: string_ids ignored for image labels; using gene symbols")
  }

  url <- paste0(.np_string_api_base, "/", format, "/network")
  body <- list(
    identifiers = paste(genes, collapse = "\r"),
    species = as.character(species),
    required_score = as.character(required_score),
    network_type = network_type,
    network_flavor = network_flavor,
    hide_disconnected_nodes = if (isTRUE(hide_disconnected_nodes)) "1" else "0",
    block_structure_pics_in_bubbles = if (isTRUE(block_structure_pics)) "1" else "0",
    show_query_node_labels = if (isTRUE(show_query_node_labels)) "1" else "0",
    caller_identity = caller_identity
  )
  resp <- httr::POST(url, body = body, encode = "form", httr::timeout(timeout))
  if (httr::http_error(resp)) {
    stop(
      "STRING image API error: ", httr::status_code(resp), " ",
      substr(httr::content(resp, as = "text", encoding = "UTF-8"), 1, 400),
      call. = FALSE
    )
  }
  dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)
  raw <- httr::content(resp, as = "raw")
  writeBin(raw, out_path)
  message("STRING network image saved: ", out_path, " (", length(raw), " bytes)")
  invisible(out_path)
}

#' Fetch STRING PPI edges for gene symbols; cache to TSV
#' @return data.frame with preferredName_A/B, score, ...
np_fetch_string_ppi <- function(genes,
                                species = 9606L,
                                required_score = 900L,
                                cache_path = NULL,
                                caller_identity = "RProject_NetworkPharmacology",
                                force = FALSE) {
  genes <- unique(as.character(genes))
  genes <- genes[!is.na(genes) & nzchar(genes)]
  if (!length(genes)) stop("genes is empty", call. = FALSE)

  if (!is.null(cache_path) && file.exists(cache_path) && !force) {
    message("STRING PPI: using cache ", cache_path)
    cached <- utils::read.delim(cache_path, stringsAsFactors = FALSE, check.names = FALSE)
    # accept API or STRING-web export schemas
    ok <- tryCatch({
      r <- .np_string_endpoint_cols(cached)
      !is.na(r$a) && !is.na(r$b) && nrow(r$df) > 0
    }, error = function(e) FALSE)
    if (ok) return(.np_string_endpoint_cols(cached)$df)
    message("STRING PPI cache schema unusable; refetching…")
  }

  if (!requireNamespace("httr", quietly = TRUE)) {
    stop("Install httr to call STRING API", call. = FALSE)
  }

  mapped <- .np_string_map_ids(genes, species = species, caller_identity = caller_identity)
  string_ids <- mapped$string_ids

  Sys.sleep(1)
  net_txt <- .np_string_post(
    "network",
    list(
      identifiers = paste(string_ids, collapse = "\r"),
      species = as.character(species),
      required_score = as.character(required_score),
      network_type = "functional",
      caller_identity = caller_identity
    )
  )
  ppi <- utils::read.delim(text = net_txt, stringsAsFactors = FALSE, check.names = FALSE)
  if (!nrow(ppi)) {
    warning("STRING network returned 0 edges at score >= ", required_score)
  }
  attr(ppi, "string_ids") <- string_ids

  if (!is.null(cache_path)) {
    dir.create(dirname(cache_path), recursive = TRUE, showWarnings = FALSE)
    utils::write.table(
      ppi, cache_path, sep = "\t", quote = FALSE,
      row.names = FALSE, fileEncoding = "UTF-8"
    )
    message("STRING PPI cached: ", cache_path, " (edges=", nrow(ppi), ")")
  }
  ppi
}

#' Normalize edge table from network.csv (ID/SYMBOL or from/to)
np_normalize_network_edges <- function(net) {
  if (is.null(net) || !nrow(net)) {
    return(data.frame(from = character(), to = character(), stringsAsFactors = FALSE))
  }
  nm <- names(net)
  if (all(c("from", "to") %in% nm)) {
    out <- data.frame(from = as.character(net$from), to = as.character(net$to), stringsAsFactors = FALSE)
  } else if (all(c("ID", "SYMBOL") %in% nm)) {
    out <- data.frame(from = as.character(net$ID), to = as.character(net$SYMBOL), stringsAsFactors = FALSE)
  } else if (ncol(net) >= 2) {
    out <- data.frame(
      from = as.character(net[[1]]),
      to = as.character(net[[2]]),
      stringsAsFactors = FALSE
    )
  } else {
    stop("network edge table needs two columns", call. = FALSE)
  }
  out <- out[!is.na(out$from) & !is.na(out$to) & nzchar(out$from) & nzchar(out$to), , drop = FALSE]
  out
}

np_normalize_type_table <- function(type_df) {
  if (is.null(type_df) || !nrow(type_df)) {
    return(data.frame(term = character(), type = character(), stringsAsFactors = FALSE))
  }
  nm <- names(type_df)
  term_col <- if ("term" %in% nm) "term" else nm[1]
  type_col <- if ("type" %in% nm) "type" else nm[2]
  data.frame(
    term = as.character(type_df[[term_col]]),
    type = as.character(type_df[[type_col]]),
    stringsAsFactors = FALSE
  )
}

#' Layered layout for A/B/C/D multilayer network (rows = layers)
.np_layout_layered <- function(g, type_vec, layers = c("A", "B", "C", "D")) {
  if (!requireNamespace("igraph", quietly = TRUE)) stop("需要 igraph")
  vs <- igraph::V(g)$name
  typ <- unname(type_vec[vs])
  typ[is.na(typ)] <- "?"
  set.seed(42)
  lay <- igraph::layout_with_fr(g, niter = 800)
  colnames(lay) <- c("x", "y")
  rownames(lay) <- vs
  # top = first layer (herb on top when layers = A,B,C,D)
  y_map <- stats::setNames(as.numeric(rev(seq_along(layers))), layers)
  for (t in layers) {
    idx <- which(typ == t)
    if (!length(idx)) next
    # evenly space nodes on x within layer; fixed y per layer
    ord <- order(lay[idx, "x"], vs[idx])
    n <- length(idx)
    lay[idx[ord], "x"] <- if (n == 1L) 0 else seq(-1, 1, length.out = n)
    lay[idx, "y"] <- y_map[[t]]
  }
  # unknown types at bottom
  idx_u <- which(!typ %in% layers)
  if (length(idx_u)) {
    ord <- order(lay[idx_u, "x"], vs[idx_u])
    n <- length(idx_u)
    lay[idx_u[ord], "x"] <- if (n == 1L) 0 else seq(-1, 1, length.out = n)
    lay[idx_u, "y"] <- 0
  }
  lay
}

scales_rescale <- function(x, to = c(0, 1)) {
  rng <- range(x, na.rm = TRUE)
  if (!is.finite(diff(rng)) || diff(rng) < 1e-12) return(rep(mean(to), length(x)))
  (x - rng[1]) / diff(rng) * diff(to) + to[1]
}

.np_network_type_cols <- function() {
  c(
    A = "#6B8F71",  # herb
    B = "#C17B7B",  # compound
    C = "#5B8FA8",  # target
    D = "#8B7BA8",  # pathway
    Gene = "#5B8FA8",
    Other = "#BDBDBD"
  )
}

#' ggplot network from igraph + layout matrix
.np_gg_network <- function(g, lay, node_df, edge_alpha = 0.12,
                           title = "", subtitle = "",
                           label_top_n = 40L, show_legend = TRUE) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
  if (!requireNamespace("igraph", quietly = TRUE)) stop("需要 igraph")

  el <- igraph::as_data_frame(g, what = "edges")
  if (!nrow(el)) stop("graph has no edges", call. = FALSE)
  el$x <- lay[el$from, 1]
  el$y <- lay[el$from, 2]
  el$xend <- lay[el$to, 1]
  el$yend <- lay[el$to, 2]

  nd <- node_df
  nd$x <- lay[nd$name, 1]
  nd$y <- lay[nd$name, 2]
  nd <- nd[order(nd$size), , drop = FALSE]

  # label hubs / type A/D always
  lab_idx <- order(-nd$size)
  keep <- unique(c(
    which(nd$type %in% c("A", "D")),
    lab_idx[seq_len(min(label_top_n, length(lab_idx)))]
  ))
  nd$label <- ""
  nd$label[keep] <- nd$name[keep]
  # shorten long pathway labels already short (hsa); compound codes ok

  cols <- .np_network_type_cols()
  p <- ggplot2::ggplot() +
    ggplot2::geom_segment(
      data = el,
      ggplot2::aes(x = x, y = y, xend = xend, yend = yend),
      color = "grey70", alpha = edge_alpha, linewidth = 0.25
    ) +
    ggplot2::geom_point(
      data = nd,
      ggplot2::aes(x = x, y = y, size = size, fill = type),
      shape = 21, color = "white", stroke = 0.25, alpha = 0.92
    ) +
    ggplot2::scale_fill_manual(values = cols, name = "Node type") +
    ggplot2::scale_size_continuous(range = c(1.8, 9.5), name = "Degree") +
    ggplot2::geom_text(
      data = nd[nzchar(nd$label), , drop = FALSE],
      ggplot2::aes(x = x, y = y, label = label),
      size = 2.1, color = "grey15",
      vjust = -1.1, check_overlap = TRUE
    ) +
    ggplot2::labs(title = title, subtitle = subtitle, x = NULL, y = NULL) +
    ggplot2::coord_equal(clip = "off") +
    ggplot2::theme_void(base_size = 11) +
    ggplot2::theme(
      plot.title = ggplot2::element_text(face = "bold", size = 12, hjust = 0.5),
      plot.subtitle = ggplot2::element_text(size = 9, color = "grey35", hjust = 0.5),
      legend.position = if (show_legend) "right" else "none",
      plot.margin = ggplot2::margin(10, 12, 10, 12),
      plot.background = ggplot2::element_rect(fill = "white", color = NA)
    )
  if (exists("np_apply_journal", mode = "function")) {
    # keep void axes but journal title fonts
    p <- p + ggplot2::theme(
      plot.title = ggplot2::element_text(face = "bold", size = 12, hjust = 0.5),
      legend.title = ggplot2::element_text(face = "bold", size = 9)
    )
  }
  p
}

#' Resolve STRING edge endpoint columns (API vs web export)
.np_string_endpoint_cols <- function(df) {
  nm <- names(df)
  # strip leading # from web-export headers
  nm_clean <- sub("^#", "", nm)
  names(df) <- nm_clean
  nm <- names(df)
  pick <- function(cands) {
    hit <- cands[cands %in% nm]
    if (length(hit)) hit[[1]] else NA_character_
  }
  a <- pick(c("preferredName_A", "preferredNameA", "node1", "protein1", "from"))
  b <- pick(c("preferredName_B", "preferredNameB", "node2", "protein2", "to"))
  if (is.na(a) || is.na(b)) {
    if (all(c("stringId_A", "stringId_B") %in% nm)) {
      a <- "stringId_A"
      b <- "stringId_B"
    }
  }
  score <- pick(c("score", "combined_score", "combinedScore"))
  list(df = df, a = a, b = b, score = score)
}

#' Concentric layout by degree (hubs in center) — reference panel style
.np_layout_concentric_degree <- function(g) {
  deg <- igraph::degree(g)
  vs <- igraph::V(g)$name
  d <- as.numeric(deg[vs])
  n <- length(vs)
  ord <- order(-d, vs)
  ranks <- seq_len(n)
  rad <- 0.08 + 0.92 * ((ranks - 1) / max(1, n - 1))
  ang <- (ranks * pi * (3 - sqrt(5))) %% (2 * pi)
  lay <- matrix(0, nrow = n, ncol = 2)
  rownames(lay) <- vs
  lay[ord, 1] <- rad * cos(ang)
  lay[ord, 2] <- rad * sin(ang)
  colnames(lay) <- c("x", "y")
  lay
}

#' STRING PPI preview: score filter, drop isolates, concentric hubs (R fallback)
#' For official 3D/evidence look use np_fetch_string_network_image().
np_plot_string_ppi <- function(ppi,
                               title = "STRING PPI network (confidence ≥ 0.9)",
                               label_top_n = 80L,
                               min_score = 900L,
                               drop_isolates = TRUE,
                               layout = c("concentric", "fr")) {
  if (!requireNamespace("igraph", quietly = TRUE)) stop("需要 igraph")
  layout <- match.arg(layout)
  resolved <- .np_string_endpoint_cols(ppi)
  df <- resolved$df
  a_col <- resolved$a
  b_col <- resolved$b
  if (is.na(a_col) || is.na(b_col)) {
    stop("PPI table missing node endpoint columns (preferredName_A/B or node1/node2)", call. = FALSE)
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
  if (!nrow(edges)) stop("No PPI edges to plot at this score", call. = FALSE)

  g <- igraph::graph_from_data_frame(edges, directed = FALSE)
  g <- igraph::simplify(g, remove.multiple = TRUE, remove.loops = TRUE)
  if (isTRUE(drop_isolates)) {
    g <- igraph::delete_vertices(g, igraph::V(g)[igraph::degree(g) == 0])
  }
  if (igraph::vcount(g) < 2) stop("Fewer than 2 connected nodes after filtering", call. = FALSE)

  deg <- igraph::degree(g)
  set.seed(42)
  lay <- if (layout == "concentric") {
    .np_layout_concentric_degree(g)
  } else {
    l <- igraph::layout_with_fr(g, niter = 1200)
    rownames(l) <- igraph::V(g)$name
    colnames(l) <- c("x", "y")
    l
  }

  # green degree gradient (reference concentric figure)
  dvec <- as.numeric(deg[igraph::V(g)$name])
  node_df <- data.frame(
    name = igraph::V(g)$name,
    degree = dvec,
    size = dvec,
    stringsAsFactors = FALSE
  )
  el <- igraph::as_data_frame(g, what = "edges")
  el$x <- lay[el$from, 1]
  el$y <- lay[el$from, 2]
  el$xend <- lay[el$to, 1]
  el$yend <- lay[el$to, 2]

  # label most hubs; outer ring fewer labels
  lab_n <- min(as.integer(label_top_n), nrow(node_df))
  keep <- order(-node_df$degree, node_df$name)[seq_len(lab_n)]
  node_df$label <- ""
  node_df$label[keep] <- node_df$name[keep]
  node_df$x <- lay[node_df$name, 1]
  node_df$y <- lay[node_df$name, 2]
  node_df <- node_df[order(node_df$degree), , drop = FALSE]

  fill_cols <- c("#F7FCB9", "#ADDD8E", "#41AB5D", "#006837")
  ggplot2::ggplot() +
    ggplot2::geom_segment(
      data = el,
      ggplot2::aes(x = x, y = y, xend = xend, yend = yend),
      color = "grey70", alpha = 0.22, linewidth = 0.28
    ) +
    ggplot2::geom_point(
      data = node_df,
      ggplot2::aes(x = x, y = y, size = size, fill = degree),
      shape = 21, color = "grey25", stroke = 0.2, alpha = 0.95
    ) +
    ggplot2::scale_fill_gradientn(colours = fill_cols, name = "Degree") +
    ggplot2::scale_size_continuous(range = c(2.2, 11), guide = "none") +
    ggplot2::geom_text(
      data = node_df[nzchar(node_df$label), , drop = FALSE],
      ggplot2::aes(x = x, y = y, label = label),
      size = 2.0, color = "grey10", fontface = "bold",
      check_overlap = TRUE
    ) +
    ggplot2::labs(
      title = title,
      subtitle = sprintf(
        "score ≥ 0.9 · isolates removed · n_nodes = %d · n_edges = %d · concentric by Degree",
        igraph::vcount(g), igraph::ecount(g)
      )
    ) +
    ggplot2::coord_equal(clip = "off") +
    ggplot2::theme_void(base_size = 11) +
    ggplot2::theme(
      plot.title = ggplot2::element_text(face = "bold", size = 12, hjust = 0.5),
      plot.subtitle = ggplot2::element_text(size = 8.5, color = "grey35", hjust = 0.5),
      legend.position = "right",
      plot.margin = ggplot2::margin(10, 12, 10, 12),
      plot.background = ggplot2::element_rect(fill = "white", color = NA)
    )
}

#' Herb–compound–target–pathway multilayer network preview
#' @param net edge table; @param type_df node types A/B/C/D
np_plot_hctp_network <- function(net,
                                 type_df,
                                 title = "Herb–compound–target–pathway network",
                                 label_top_n = 45L,
                                 edge_alpha = 0.08) {
  if (!requireNamespace("igraph", quietly = TRUE)) stop("需要 igraph")
  edges <- np_normalize_network_edges(net)
  typ <- np_normalize_type_table(type_df)
  if (!nrow(edges)) stop("network edges empty", call. = FALSE)

  type_vec <- setNames(typ$type, typ$term)
  g <- igraph::graph_from_data_frame(edges, directed = FALSE)
  g <- igraph::simplify(g, remove.multiple = TRUE, remove.loops = TRUE)
  vs <- igraph::V(g)$name
  missing <- setdiff(vs, names(type_vec))
  if (length(missing)) {
    type_vec[missing] <- "?"
  }
  deg <- igraph::degree(g)
  lay <- .np_layout_layered(g, type_vec)

  node_df <- data.frame(
    name = vs,
    type = unname(type_vec[vs]),
    size = as.numeric(deg[vs]),
    stringsAsFactors = FALSE
  )
  # pretty legend labels
  node_df$type <- factor(
    node_df$type,
    levels = c("A", "B", "C", "D", "?"),
    labels = c("A herb", "B compound", "C target", "D pathway", "Other")
  )
  # map fill keys back for scale — use short codes in aes
  node_df$type_code <- as.character(type_vec[vs])
  node_df$type_code[!node_df$type_code %in% c("A", "B", "C", "D")] <- "Other"

  el <- igraph::as_data_frame(g, what = "edges")
  el$x <- lay[el$from, 1]
  el$y <- lay[el$from, 2]
  el$xend <- lay[el$to, 1]
  el$yend <- lay[el$to, 2]

  nd <- node_df
  nd$x <- lay[nd$name, 1]
  nd$y <- lay[nd$name, 2]
  nd <- nd[order(nd$size), , drop = FALSE]
  lab_idx <- order(-nd$size)
  keep <- unique(c(
    which(nd$type_code %in% c("A", "D")),
    lab_idx[seq_len(min(label_top_n, length(lab_idx)))]
  ))
  nd$label <- ""
  nd$label[keep] <- nd$name[keep]

  cols <- .np_network_type_cols()
  n_a <- sum(nd$type_code == "A")
  n_b <- sum(nd$type_code == "B")
  n_c <- sum(nd$type_code == "C")
  n_d <- sum(nd$type_code == "D")

  ggplot2::ggplot() +
    ggplot2::geom_segment(
      data = el,
      ggplot2::aes(x = x, y = y, xend = xend, yend = yend),
      color = "grey75", alpha = edge_alpha, linewidth = 0.2
    ) +
    ggplot2::geom_point(
      data = nd,
      ggplot2::aes(x = x, y = y, size = size, fill = type_code),
      shape = 21, color = "white", stroke = 0.2, alpha = 0.93
    ) +
    ggplot2::scale_fill_manual(
      values = cols,
      breaks = c("A", "B", "C", "D"),
      labels = c("Herb (A)", "Compound (B)", "Target (C)", "Pathway (D)"),
      name = "Layer"
    ) +
    ggplot2::scale_size_continuous(range = c(1.6, 10), name = "Degree") +
    ggplot2::geom_text(
      data = nd[nzchar(nd$label), , drop = FALSE],
      ggplot2::aes(x = x, y = y, label = label),
      size = 2.0, color = "grey10", vjust = -1.05, check_overlap = TRUE
    ) +
    ggplot2::labs(
      title = title,
      subtitle = sprintf(
        "Layers A–B–C–D · herbs=%d compounds=%d targets=%d pathways=%d · edges=%d",
        n_a, n_b, n_c, n_d, igraph::ecount(g)
      )
    ) +
    ggplot2::coord_cartesian(clip = "off") +
    ggplot2::theme_void(base_size = 11) +
    ggplot2::theme(
      plot.title = ggplot2::element_text(face = "bold", size = 12, hjust = 0.5),
      plot.subtitle = ggplot2::element_text(size = 8.5, color = "grey35", hjust = 0.5),
      legend.position = "right",
      plot.margin = ggplot2::margin(12, 14, 12, 14),
      plot.background = ggplot2::element_rect(fill = "white", color = NA)
    )
}

#' Export Cytoscape-ready edge/node tables for multilayer network
np_export_hctp_cytoscape <- function(net, type_df, out_dir) {
  edges <- np_normalize_network_edges(net)
  typ <- np_normalize_type_table(type_df)
  if (!requireNamespace("igraph", quietly = TRUE)) {
    nodes <- unique(c(edges$from, edges$to))
    node_tbl <- data.frame(
      name = nodes,
      type = typ$type[match(nodes, typ$term)],
      stringsAsFactors = FALSE
    )
  } else {
    g <- igraph::graph_from_data_frame(edges, directed = FALSE)
    g <- igraph::simplify(g)
    deg <- igraph::degree(g)
    nodes <- igraph::V(g)$name
    node_tbl <- data.frame(
      name = nodes,
      type = typ$type[match(nodes, typ$term)],
      Degree = as.integer(deg[nodes]),
      stringsAsFactors = FALSE
    )
  }
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  e_path <- file.path(out_dir, "13_网络边_HerbCompoundTargetPathway_Cytoscape.csv")
  n_path <- file.path(out_dir, "14_网络节点_HerbCompoundTargetPathway_Cytoscape.csv")
  utils::write.csv(
    data.frame(source = edges$from, target = edges$to, stringsAsFactors = FALSE),
    e_path, row.names = FALSE, fileEncoding = "UTF-8"
  )
  utils::write.csv(node_tbl, n_path, row.names = FALSE, fileEncoding = "UTF-8")
  invisible(list(edges = e_path, nodes = n_path))
}
