# Network comparison (06) only. Exploratory Top50 enrichment plots are retired:
# do not trim/redraw them — official 05 comes from 38 (response-gene ORA / empty).
options(stringsAsFactors = FALSE)
SKIP_EXPLOR_ENRICH <- TRUE

desk <- "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除"
algo <- "scTenifoldKnk_1.4.3_GPU"
viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
if (file.exists(viz)) source(viz, encoding = "UTF-8")
suppressPackageStartupMessages(library(ggplot2))
if (!exists("theme_journal")) theme_journal <- function(...) ggplot2::theme_bw()
ont_cols <- c(BP = "#1B9E77", CC = "#D95F02", MF = "#7570B3")

save_plot <- function(p, dir, stem, w = 8, h = 6) {
  dir.create(dir, recursive = TRUE, showWarnings = FALSE)
  if (exists("save_plot_pub", mode = "function")) {
    save_plot_pub(p, stem = stem, width = w, height = h, dpi = 600, out_dir = dir)
  } else {
    ggplot2::ggsave(file.path(dir, paste0(stem, ".png")), p, width = w, height = h, dpi = 600, bg = "white")
    ggplot2::ggsave(file.path(dir, paste0(stem, ".svg")), p, width = w, height = h, bg = "white")
  }
}

subtypes <- c("PEP", "NF1")
targets <- c("Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21")
controls <- c(PEP = "Ret", NF1 = "Rdx")

if (isTRUE(SKIP_EXPLOR_ENRICH)) {
  message("skip exploratory Top50 enrichment redraw; official 05 from script 38 only")
} else {
  stop("exploratory Top50 enrichment plotting is retired")
}

message("network comparison 06")
read_sig <- function(st, gene) {
  pth <- file.path(desk, "结果文件", st, algo, gene, "数据文件", "扰动_Dr.csv")
  if (!file.exists(pth)) return(character())
  d <- read.csv(pth, check.names = FALSE)
  d <- d[d$gene != gene & is.finite(d$p.adj) & d$p.adj < 0.05, , drop = FALSE]
  sort(unique(d$gene))
}

pep_cplx2 <- read_sig("PEP", "Cplx2")
nf1_cplx2 <- read_sig("NF1", "Cplx2")
nf1_ctrl <- read_sig("NF1", "Rdx")
pep_ctrl <- read_sig("PEP", "Ret")

nodes <- data.frame(
  panel = character(), hub = character(), gene = character(),
  shared = logical(), stringsAsFactors = FALSE
)
edges <- data.frame(
  panel = character(), hub = character(), gene = character(), stringsAsFactors = FALSE
)
panels <- c("PEP: Cplx2 KO", "NF1: Cplx2 KO", "NF1: control Rdx KO")
add_panel <- function(label, hub, genes, shared_genes) {
  for (gene in genes) {
    nodes <<- rbind(nodes, data.frame(panel = label, hub = hub, gene = gene, shared = gene %in% shared_genes, stringsAsFactors = FALSE))
    edges <<- rbind(edges, data.frame(panel = label, hub = hub, gene = gene, stringsAsFactors = FALSE))
  }
}
shared_nf1 <- intersect(nf1_cplx2, nf1_ctrl)
add_panel(panels[1], "Cplx2", pep_cplx2, intersect(pep_cplx2, pep_ctrl))
add_panel(panels[2], "Cplx2", nf1_cplx2, shared_nf1)
add_panel(panels[3], "Rdx", nf1_ctrl, shared_nf1)

hub_df <- data.frame(
  panel = panels, hub = c("Cplx2", "Cplx2", "Rdx"), stringsAsFactors = FALSE
)
if (nrow(nodes)) {
  nodes$y <- ave(seq_len(nrow(nodes)), nodes$panel, FUN = function(i) {
    k <- length(i)
    if (k == 1) 0 else seq(0.6, -0.6, length.out = k)
  })
  edges$y <- nodes$y[match(paste(edges$panel, edges$gene), paste(nodes$panel, nodes$gene))]
} else {
  nodes$y <- numeric()
  edges$y <- numeric()
}
hub_df$y <- 0

p_net <- ggplot() +
  geom_segment(
    data = edges, aes(x = 0, y = 0, xend = 1, yend = y),
    color = "grey45", linewidth = 0.8
  ) +
  geom_point(data = hub_df, aes(0, y), size = 11, color = "#2166AC") +
  geom_text(data = hub_df, aes(0, y, label = hub), color = "white", fontface = "bold", size = 3.6) +
  geom_point(data = nodes, aes(1, y, color = shared), size = 9) +
  geom_text(data = nodes, aes(1, y, label = gene), color = "white", size = 3) +
  geom_text(
    data = data.frame(
      panel = panels,
      label = c(
        sprintf("no FDR < 0.05 partner genes (n=%d)", length(pep_cplx2)),
        sprintf("n=%d; %s also respond to control KO", length(nf1_cplx2), paste(shared_nf1, collapse = ", ")),
        sprintf("control KO shows the same n=%d genes", length(nf1_ctrl))
      ),
      stringsAsFactors = FALSE
    ),
    aes(0.5, -1.05, label = label), size = 3.4, color = "grey25"
  ) +
  facet_wrap(~ factor(panel, levels = panels), nrow = 1) +
  scale_color_manual(values = c("FALSE" = "#C17B7B", "TRUE" = "#B0A44F"), labels = c("KO-specific", "shared with control")) +
  coord_equal(xlim = c(-0.35, 1.35), ylim = c(-1.25, 1.15), clip = "off") +
  labs(
    title = "KO-response comparison, scTenifoldKnk 1.4.3 GPU",
    subtitle = "Nodes: FDR < 0.05 response genes after virtual KO. Edges: response relation, not STRING PPI. Computational prediction.",
    color = NULL
  ) +
  theme_void() +
  theme(
    legend.position = "bottom",
    strip.text = element_text(size = 11, face = "bold"),
    plot.title = element_text(face = "bold"),
    plot.subtitle = element_text(color = "grey30")
  )

cross_fig <- file.path(desk, "结果文件", "_跨亚群", algo, "图片文件")
save_plot(p_net, cross_fig, "06_网络图_KO响应对比_PepNf1KoCompare", 11, 5.6)

writeLines(
  c(
    "06 KO-response comparison for current PEP/NF1 (scTenifoldKnk 1.4.3 GPU).",
    sprintf("PEP Cplx2 KO: %d FDR<0.05 partners; NF1 Cplx2 KO: %d (%s shared with control Rdx).",
            length(pep_cplx2), length(nf1_cplx2), paste(shared_nf1, collapse = ",")),
    "STRING PPI edges were not queried: no Cplx2-specific partner genes survive FDR in either subtype.",
    "Cross-engine (GenKI vs Knk) comparison is a separate task per the plans."
  ),
  file.path(cross_fig, "..", "报告文件", "STATUS_网络对比图.txt")
)
message("TRIM_NET_DONE")
