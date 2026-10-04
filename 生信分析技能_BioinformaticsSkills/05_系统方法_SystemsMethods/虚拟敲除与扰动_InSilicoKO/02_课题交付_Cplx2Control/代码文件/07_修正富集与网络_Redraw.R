# Fix enrichment panels and redraw KO-centered networks from saved WT adjacency.
options(stringsAsFactors = FALSE)
vko <- "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除"
arch <- "C:/Users/10540/Desktop/琪乐无穷/五亚群留档"
tab_dir <- file.path(arch, "结果文件", "_跨亚群", "scTenifoldKnk", "数据文件")
fig_dir <- file.path(arch, "结果文件", "_跨亚群", "scTenifoldKnk", "图片文件")
obj_dir <- file.path(tab_dir, "敲除对象_KoObjects")
viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
if (file.exists(viz)) source(viz, encoding = "UTF-8")
suppressPackageStartupMessages({
  library(ggplot2)
  library(ggrepel)
})
if (!exists("theme_journal")) theme_journal <- function(...) theme_bw()
pal <- if (exists("bioinfo_palette")) bioinfo_palette else c("#4C78A8", "#F58518", "#54A24B", "#E45756")

save_plot <- function(p, stem, w, h) {
  ggplot2::ggsave(file.path(fig_dir, paste0(stem, ".png")), p, width = w, height = h, dpi = 600, bg = "white", limitsize = FALSE)
  ggplot2::ggsave(file.path(fig_dir, paste0(stem, ".svg")), p, width = w, height = h, bg = "white", limitsize = FALSE)
}

# ----- enrichment: real top terms, one spacious panel each -----
enr <- read.csv(file.path(tab_dir, "05_富集_Top50_Cplx2Enrich.csv"), check.names = FALSE)
enr$p_adj <- as.numeric(enr$Adjusted.P.value)
enr$neglog <- -log10(enr$p_adj + 1e-300)
enr$name <- sub(" \\(GO:[0-9]+\\)$", "", enr$Term)
subtypes <- c("cLTMR", "NF1", "NP", "PEP", "TRPM8")

panel_df <- function(s) {
  d <- enr[enr$subtype == s, , drop = FALSE]
  d <- d[order(d$p_adj), , drop = FALSE]
  d <- head(d, 6)
  d$name <- factor(d$name, levels = rev(unique(d$name)))
  d
}

for (s in subtypes) {
  d <- panel_df(s)
  p <- ggplot(d, aes(neglog, name)) +
    geom_col(fill = pal[1], width = 0.55) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.08))) +
    labs(
      title = paste0(s, ": top GO terms"),
      subtitle = "Top 50 genes by virtual-KO distance, not an FDR gene set",
      x = "-log10(adjusted P)", y = NULL
    ) +
    theme_journal() +
    theme(
      axis.text.y = element_text(size = 12),
      plot.margin = margin(18, 24, 16, 12),
      panel.spacing = unit(16, "pt")
    )
  save_plot(p, paste0("05_柱状图_突触富集_", s, "_Cplx2GO"), w = 9.5, h = 5.6)
}

# ----- networks from WT adjacency, Cplx2 at the center -----
draw_net <- function(subtype) {
  obj <- readRDS(file.path(obj_dir, paste0(subtype, "_Cplx2.rds")))
  wt <- as.matrix(obj$tensorNetworks$WT)
  dr <- obj$diffRegulation
  dr <- dr[dr$gene != "Cplx2" & dr$gene %in% colnames(wt), , drop = FALSE]
  dr <- dr[order(dr$distance, decreasing = TRUE), , drop = FALSE]
  nodes <- head(dr$gene, 12)
  wrow <- wt["Cplx2", nodes]
  # keep the link to Cplx2; add strong links among the ring
  ring <- wt[nodes, nodes, drop = FALSE]
  diag(ring) <- 0
  thr <- quantile(abs(ring), 0.85)
  edges <- data.frame(from = "Cplx2", to = nodes, weight = as.numeric(wrow), stringsAsFactors = FALSE)
  ij <- which(abs(ring) >= thr & upper.tri(ring), arr.ind = TRUE)
  if (nrow(ij)) {
    edges <- rbind(edges, data.frame(
      from = nodes[ij[, 1]], to = nodes[ij[, 2]],
      weight = ring[ij], stringsAsFactors = FALSE
    ))
  }
  ang <- seq(0, 2 * pi, length.out = length(nodes) + 1)[seq_along(nodes)]
  xy <- data.frame(
    name = c("Cplx2", nodes),
    x = c(0, cos(ang)),
    y = c(0, sin(ang)),
    stringsAsFactors = FALSE
  )
  distv <- c(NA, dr$distance[match(nodes, dr$gene)])
  xy$kind <- ifelse(xy$name == "Cplx2", "KO gene", "Predicted gene")
  xy$size <- ifelse(xy$name == "Cplx2", 14, 5 + 9 * distv[-1] / max(distv[-1]))
  el <- merge(edges, xy[, c("name", "x", "y")], by.x = "from", by.y = "name")
  el <- merge(el, xy[, c("name", "x", "y")], by.x = "to", by.y = "name", suffixes = c("_from", "_to"))
  p <- ggplot() +
    geom_segment(
      data = el,
      aes(x = x_from, y = y_from, xend = x_to, yend = y_to, linewidth = abs(weight)),
      color = "grey55", alpha = 0.8, lineend = "round"
    ) +
    geom_point(data = xy, aes(x, y, size = size, fill = kind), shape = 21, color = "grey20", stroke = 0.3) +
    geom_text_repel(
      data = xy, aes(x, y, label = name),
      size = 3.4, max.overlaps = 30, box.padding = 0.4, point.padding = 0.3,
      min.segment.length = 0, segment.color = "grey60"
    ) +
    scale_fill_manual(values = c("KO gene" = pal[4], "Predicted gene" = pal[1])) +
    scale_size_identity() +
    scale_linewidth_continuous(range = c(0.3, 1.4), guide = "none") +
    coord_equal(xlim = c(-1.7, 1.7), ylim = c(-1.7, 1.7), clip = "off") +
    labs(title = paste0(subtype, ": Cplx2 virtual-KO neighborhood"), fill = NULL) +
    theme_void(base_size = 12) +
    theme(
      plot.title = element_text(hjust = 0.5, face = "bold"),
      legend.position = "bottom",
      plot.background = element_rect(fill = "white", color = NA),
      plot.margin = margin(16, 16, 16, 16)
    )
  save_plot(p, paste0("06_网络图_", subtype, "_Cplx2Network"), w = 8, h = 8)
}

for (s in subtypes) draw_net(s)
message("REDRAW_DONE")
