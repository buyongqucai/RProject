# Roomier synaptic GO bars, one subtype per file, plus a tall combined figure.
options(stringsAsFactors = FALSE)
root <- "C:/Users/10540/Desktop/琪乐无穷/CPLX2虚拟敲除_Cplx2VirtualKO"
tab_dir <- file.path(root, "结果文件", "数据文件")
fig_dir <- file.path(root, "结果文件", "图片文件")
viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
if (file.exists(viz)) source(viz, encoding = "UTF-8")
suppressPackageStartupMessages(library(ggplot2))
if (!exists("theme_journal")) theme_journal <- function(...) theme_bw()
fill1 <- if (exists("bioinfo_palette")) bioinfo_palette[1] else "#4C78A8"

save_plot <- function(p, stem, w, h) {
  ggplot2::ggsave(file.path(fig_dir, paste0(stem, ".png")), p, width = w, height = h, dpi = 600, limitsize = FALSE)
  ggplot2::ggsave(file.path(fig_dir, paste0(stem, ".svg")), p, width = w, height = h, limitsize = FALSE)
}

enr <- read.csv(file.path(tab_dir, "05_富集_Top50_Cplx2Enrich.csv"), check.names = FALSE)
focus <- grepl("synaptic vesicle|SNARE|neurotransmitter", enr$Term, ignore.case = TRUE)
enr <- enr[focus, , drop = FALSE]
enr$neglog <- -log10(as.numeric(enr$Adjusted.P.value) + 1e-300)
enr$name <- sub(" \\(GO:[0-9]+\\)$", "", enr$Term)
enr$go_id <- sub(".*\\((GO:[0-9]+)\\)$", "\\1", enr$Term)
subtypes <- c("cLTMR", "NF1", "NP", "PEP", "TRPM8")

one_panel <- function(s) {
  d <- enr[enr$subtype == s, , drop = FALSE]
  d <- d[order(d$neglog, decreasing = TRUE), , drop = FALSE]
  d <- head(d, 5)
  if (!nrow(d)) {
    d <- data.frame(name = "No synaptic GO term in the top 50", neglog = 0, go_id = "", stringsAsFactors = FALSE)
  }
  d$name <- factor(d$name, levels = rev(d$name))
  ggplot(d, aes(neglog, name)) +
    geom_col(fill = fill1, width = 0.62) +
    geom_text(aes(label = go_id), hjust = -0.05, size = 3.2) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.35))) +
    labs(title = s, x = "-log10(adjusted P)", y = NULL) +
    theme_journal() +
    theme(
      axis.text.y = element_text(size = 12),
      plot.margin = margin(16, 28, 16, 12)
    )
}

for (s in subtypes) {
  save_plot(one_panel(s), paste0("05_柱状图_突触富集_", s, "_Cplx2GO"), w = 9, h = 4.8)
}

# Combined, with generous panel spacing
parts <- lapply(subtypes, function(s) {
  d <- enr[enr$subtype == s, c("subtype", "name", "neglog"), drop = FALSE]
  d <- head(d[order(d$neglog, decreasing = TRUE), , drop = FALSE], 5)
  if (!nrow(d)) {
    d <- data.frame(
      subtype = s,
      name = "No synaptic GO term in the top 50",
      neglog = 0,
      stringsAsFactors = FALSE
    )
  }
  d
})
alld <- do.call(rbind, parts)
alld$label <- paste(alld$subtype, alld$name, sep = " | ")
alld$label <- factor(alld$label, levels = rev(unique(alld$label)))
p <- ggplot(alld, aes(neglog, label)) +
  geom_col(fill = fill1, width = 0.55) +
  labs(
    title = "Synaptic GO terms among top 50 ranked genes",
    subtitle = "Not an FDR-significant gene set",
    x = "-log10(adjusted P)", y = NULL
  ) +
  theme_journal() +
  theme(axis.text.y = element_text(size = 10), plot.margin = margin(12, 20, 12, 8))
save_plot(p, "05_柱状图_突触富集_Cplx2SynapticGO", w = 10, h = 12)
message("ENR_DONE")
