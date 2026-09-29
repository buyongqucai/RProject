# PDF-aligned figures from our own Cplx2 results.
# Fig5-style: Z(distance) vs |edge weight to Cplx2| in the WT scGRN.
# QQ: observed vs expected -log10 p.
# Egocentric: only FDR<0.05 genes. PEP has Cplx2-Scarb2.
# Not a copy of the Patterns figures. Reduced-parameter run (nNet=3, nCells=200).
options(stringsAsFactors = FALSE)
root <- "C:/Users/10540/Desktop/琪乐无穷/CPLX2虚拟敲除_Cplx2VirtualKO"
obj_dir <- file.path(root, "结果文件", "数据文件", "敲除对象_KoObjects")
fig_dir <- file.path(root, "结果文件", "图片文件")
tab_dir <- file.path(root, "结果文件", "数据文件")
viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
if (file.exists(viz)) source(viz, encoding = "UTF-8")
suppressPackageStartupMessages(library(ggplot2))
if (!exists("theme_journal")) theme_journal <- function(...) theme_bw()
subtypes <- c("cLTMR", "NF1", "NP", "PEP", "TRPM8")

save_plot <- function(p, stem, w, h) {
  ggsave(file.path(fig_dir, paste0(stem, ".png")), p, width = w, height = h, dpi = 600, bg = "white", limitsize = FALSE)
  ggsave(file.path(fig_dir, paste0(stem, ".svg")), p, width = w, height = h, bg = "white", limitsize = FALSE)
}

rows <- list()
for (s in subtypes) {
  obj <- readRDS(file.path(obj_dir, paste0(s, "_Cplx2.rds")))
  wt <- as.matrix(obj$tensorNetworks$WT)
  dr <- obj$diffRegulation
  dr$edge_to_ko <- wt["Cplx2", dr$gene]
  dr$abs_edge <- abs(dr$edge_to_ko)
  dr$subtype <- s
  dr$sig <- dr$p.adj < 0.05 & dr$gene != "Cplx2"
  rows[[s]] <- dr
}
dat <- do.call(rbind, rows)
write.csv(dat[, c("subtype","gene","distance","Z","abs_edge","p.value","p.adj","sig")],
          file.path(tab_dir, "08_边权与距离_EdgeWeightDistance.csv"), row.names = FALSE)

p5 <- ggplot(dat, aes(Z, abs_edge)) +
  geom_point(aes(color = sig), size = 0.7, alpha = 0.65) +
  scale_color_manual(values = c("FALSE" = "#6BAED6", "TRUE" = "#E31A1C"),
                     labels = c("FALSE" = "Not FDR < 0.05", "TRUE" = "FDR < 0.05")) +
  facet_wrap(~ subtype, scales = "free") +
  labs(
    title = "DR distance versus edge weight to Cplx2",
    subtitle = "Edges are WT scGRN weights. Red marks FDR < 0.05, excluding Cplx2 itself.",
    x = "Z-score of DR distance", y = "Absolute edge weight to Cplx2", color = NULL
  ) +
  theme_journal()
save_plot(p5, "08_散点图_距离与边权_DrDistanceEdge", w = 10, h = 7)

qq_df <- do.call(rbind, lapply(split(dat, dat$subtype), function(d) {
  d <- d[order(d$p.value), ]
  n <- nrow(d)
  d$exp <- -log10(ppoints(n))
  d$obs <- -log10(pmax(d$p.value, 1e-300))
  d
}))
pqq <- ggplot(qq_df, aes(exp, obs)) +
  geom_point(size = 0.5, alpha = 0.5, color = "#2171B5") +
  geom_abline(slope = 1, intercept = 0, color = "grey40") +
  facet_wrap(~ subtype, scales = "free") +
  labs(
    title = "QQ plot of virtual-KO p-values",
    x = "Expected -log10(p)", y = "Observed -log10(p)"
  ) +
  theme_journal()
save_plot(pqq, "08_散点图_P值QQ_PvalueQQ", w = 10, h = 7)

# PEP only: FDR genes are Cplx2 and Scarb2. One real GRN edge.
pep <- dat[dat$subtype == "PEP" & dat$gene %in% c("Cplx2", "Scarb2"), ]
w <- dat$edge_to_ko[dat$subtype == "PEP" & dat$gene == "Scarb2"]
nd <- data.frame(
  name = c("Cplx2", "Scarb2"),
  x = c(0, 1.4), y = c(0, 0),
  stringsAsFactors = FALSE
)
pnet <- ggplot() +
  geom_segment(aes(x = 0, y = 0, xend = 1.4, yend = 0), linewidth = 0.6, color = "grey40") +
  geom_point(data = nd, aes(x, y), size = 18, color = "#E31A1C") +
  geom_text(data = nd, aes(x, y, label = name), color = "white", fontface = "bold", size = 3.2) +
  annotate("text", x = 0.7, y = 0.18, label = sprintf("scGRN weight = %.3f", w), size = 3.5) +
  labs(
    title = "PEP: Cplx2 and the only other FDR < 0.05 gene",
    subtitle = "No other subtype had an additional FDR < 0.05 gene. Not a STRING network."
  ) +
  coord_equal(xlim = c(-0.6, 2), ylim = c(-0.6, 0.6), clip = "off") +
  theme_void() +
  theme(
    plot.title = element_text(face = "bold", hjust = 0.5),
    plot.subtitle = element_text(hjust = 0.5, color = "grey30", size = 9),
    plot.background = element_rect(fill = "white", color = NA),
    plot.margin = margin(16, 16, 16, 16)
  )
save_plot(pnet, "08_网络图_PEP显著基因_Cplx2Scarb2", w = 7, h = 4.2)
message("PDFSTYLE_DONE")
