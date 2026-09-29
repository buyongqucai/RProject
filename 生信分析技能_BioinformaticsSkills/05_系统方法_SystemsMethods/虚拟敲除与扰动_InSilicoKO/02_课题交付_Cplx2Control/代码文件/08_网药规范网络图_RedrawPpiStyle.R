# Enrichment: each subtype's real top terms (no empty placeholder).
# Networks: netpharm PPI concentric degree gradient (layout SSOT), edges from saved WT GRN.
options(stringsAsFactors = FALSE)
root <- "C:/Users/10540/Desktop/琪乐无穷/CPLX2虚拟敲除_Cplx2VirtualKO"
tab_dir <- file.path(root, "结果文件", "数据文件")
fig_dir <- file.path(root, "结果文件", "图片文件")
obj_dir <- file.path(tab_dir, "敲除对象_KoObjects")
layout_r <- "E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology/脚本_scripts/04_交付网络布局_DeliveryNetworkLayouts.R"
viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
if (file.exists(viz)) source(viz, encoding = "UTF-8")
source(layout_r, encoding = "UTF-8")
suppressPackageStartupMessages({
  library(ggplot2)
  library(igraph)
  library(ggforce)
})
if (!exists("theme_journal")) theme_journal <- function(...) theme_bw()
pal <- if (exists("bioinfo_palette")) bioinfo_palette else c("#4C78A8")
subtypes <- c("cLTMR", "NF1", "NP", "PEP", "TRPM8")
save_plot <- function(p, stem, w, h) {
  ggplot2::ggsave(file.path(fig_dir, paste0(stem, ".png")), p, width = w, height = h, dpi = 600, bg = "white", limitsize = FALSE)
  ggplot2::ggsave(file.path(fig_dir, paste0(stem, ".svg")), p, width = w, height = h, bg = "white", limitsize = FALSE)
}

save_plot <- function(p, stem, w, h) {
  ggplot2::ggsave(file.path(fig_dir, paste0(stem, ".png")), p, width = w, height = h, dpi = 600, bg = "white", limitsize = FALSE)
  ggplot2::ggsave(file.path(fig_dir, paste0(stem, ".svg")), p, width = w, height = h, bg = "white", limitsize = FALSE)
}

enr <- read.csv(file.path(tab_dir, "05_富集_Top50_Cplx2Enrich.csv"), check.names = FALSE)
enr$p_adj <- as.numeric(enr$Adjusted.P.value)
enr$neglog <- -log10(enr$p_adj + 1e-300)
enr$name <- sub(" \\(GO:[0-9]+\\)$", "", enr$Term)
for (s in subtypes) {
  d <- enr[enr$subtype == s, , drop = FALSE]
  d <- head(d[order(d$p_adj), , drop = FALSE], 6)
  d$name <- factor(d$name, levels = rev(unique(d$name)))
  p <- ggplot(d, aes(neglog, name)) +
    geom_col(fill = pal[1], width = 0.55) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.12))) +
    labs(
      title = paste0(s, ": top GO terms"),
      subtitle = "Top 50 genes by virtual-KO distance",
      x = "-log10(adjusted P)", y = NULL
    ) +
    theme_journal() +
    theme(axis.text.y = element_text(size = 12), plot.margin = margin(20, 28, 18, 14))
  save_plot(p, paste0("05_柱状图_突触富集_", s, "_Cplx2GO"), w = 10, h = 6.2)
}

draw_ppi_style <- function(subtype, n_fixed = 40L, n_rings = 4L) {
  obj <- readRDS(file.path(obj_dir, paste0(subtype, "_Cplx2.rds")))
  wt <- as.matrix(obj$tensorNetworks$WT)
  dr <- obj$diffRegulation
  dr <- dr[order(dr$distance, decreasing = TRUE), , drop = FALSE]
  others <- dr$gene[dr$gene != "Cplx2" & dr$gene %in% colnames(wt)]
  genes <- c("Cplx2", head(others, n_fixed - 1L))
  stopifnot(length(genes) == n_fixed)
  sub <- wt[genes, genes, drop = FALSE]
  diag(sub) <- 0
  # Keep every selected gene: threshold is the weakest |W| that still
  # connects all n_fixed nodes, so the count does not change per figure.
  ord <- order(abs(sub), decreasing = TRUE)
  edges <- data.frame(from = character(), to = character(), stringsAsFactors = FALSE)
  g <- igraph::make_empty_graph(n = length(genes), directed = FALSE)
  igraph::V(g)$name <- genes
  for (k in ord) {
    ij <- arrayInd(k, dim(sub))
    if (ij[1] >= ij[2]) next
    if (sub[ij] == 0) next
    edges <- rbind(edges, data.frame(
      from = genes[ij[1]], to = genes[ij[2]], stringsAsFactors = FALSE
    ))
    g <- igraph::add_edges(g, c(genes[ij[1]], genes[ij[2]]))
    if (all(igraph::degree(g) > 0)) break
  }
  g <- igraph::simplify(g)
  stopifnot(igraph::vcount(g) == n_fixed)
  lay <- .np_layout_concentric_degree(g, n_rings = n_rings, outer_frac = 0.54)
  r_node <- attr(lay, "r_node")
  ring_id <- attr(lay, "ring_id")
  n_rings <- length(attr(lay, "ring_capacities"))
  node_df <- data.frame(
    name = igraph::V(g)$name,
    x = lay[, 1], y = lay[, 2],
    degree = as.numeric(igraph::degree(g)),
    r = as.numeric(r_node[igraph::V(g)$name]),
    ring = as.integer(ring_id[igraph::V(g)$name]),
    stringsAsFactors = FALSE
  )
  node_df$label <- node_df$name
  ring_lab <- setNames(
    vapply(seq_len(n_rings), function(rr) .np_ppi_label_size(rr, n_rings, inner = 3.2, outer = 1.85), numeric(1)),
    as.character(seq_len(n_rings))
  )
  node_df$label_size <- unname(ring_lab[as.character(node_df$ring)])
  el <- igraph::as_data_frame(g, what = "edges")
  el$x <- lay[el$from, 1]
  el$y <- lay[el$from, 2]
  el$xend <- lay[el$to, 1]
  el$yend <- lay[el$to, 2]
  fill_cols <- c("#FFFFCC", "#C2E699", "#78C679", "#31A354", "#006837")
  caps <- attr(lay, "ring_capacities")
  p <- ggplot() +
    geom_segment(data = el, aes(x = x, y = y, xend = xend, yend = yend),
                 color = "grey70", alpha = 0.2, linewidth = 0.22) +
    ggforce::geom_circle(data = node_df, aes(x0 = x, y0 = y, r = r, fill = degree),
                         colour = NA, n = 48, alpha = 0.97) +
    scale_fill_gradientn(colours = fill_cols, name = "Degree") +
    geom_text(data = node_df, aes(x = x, y = y, label = label, size = label_size),
              color = "grey5", fontface = "bold", check_overlap = FALSE, show.legend = FALSE) +
    scale_size_identity() +
    labs(
      title = paste0(subtype, " virtual-KO GRN"),
      subtitle = sprintf(
        "Fixed n=40 · 4 concentric rings · outer≈%d/%d · Degree → color & size 60–120 · e=%d",
        caps[length(caps)], igraph::vcount(g), igraph::ecount(g)
      )
    ) +
    coord_equal(clip = "off") +
    theme_void(base_size = 11) +
    theme(
      plot.title = element_text(face = "bold", size = 12, hjust = 0.5),
      plot.subtitle = element_text(size = 8, color = "grey35", hjust = 0.5),
      legend.position = "right",
      plot.margin = margin(10, 14, 10, 10),
      plot.background = element_rect(fill = "white", color = NA)
    )
  save_plot(p, paste0("06_网络图_", subtype, "_Cplx2Network"), w = 11, h = 9)
}

save_plot <- function(p, stem, w, h) {
  ggplot2::ggsave(file.path(fig_dir, paste0(stem, ".png")), p, width = w, height = h, dpi = 600, bg = "white", limitsize = FALSE)
  ggplot2::ggsave(file.path(fig_dir, paste0(stem, ".svg")), p, width = w, height = h, bg = "white", limitsize = FALSE)
}
for (s in subtypes) draw_ppi_style(s)
message("STYLE_DONE")
