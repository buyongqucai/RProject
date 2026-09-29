options(stringsAsFactors = FALSE)
root <- "C:/Users/10540/Desktop/琪乐无穷/CPLX2虚拟敲除_Cplx2VirtualKO"
tab <- file.path(root, "结果文件", "数据文件", "04_扰动基因_五亚群_Cplx2DrAll.csv")
fig <- file.path(root, "结果文件", "图片文件")
viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
if (file.exists(viz)) source(viz, encoding = "UTF-8")
suppressPackageStartupMessages(library(ggplot2))
if (!exists("theme_journal")) theme_journal <- function(...) theme_bw()

dr <- read.csv(tab, check.names = FALSE)
dr <- dr[dr$gene != "Cplx2", , drop = FALSE]
dr$neglog <- -log10(pmax(dr$p.adj, 1e-300))
dr$sig <- dr$p.adj < 0.05
p <- ggplot(dr, aes(FC, neglog, color = sig)) +
  geom_point(size = 0.7, alpha = 0.7) +
  scale_color_manual(values = c("FALSE" = "grey70", "TRUE" = "#E45756")) +
  facet_wrap(~ subtype, scales = "free") +
  labs(
    title = "Cplx2 virtual KO rank statistic",
    x = "Fold change of regulation distance",
    y = "-log10(FDR)",
    color = "FDR < 0.05"
  ) +
  theme_journal()
ggplot2::ggsave(file.path(fig, "04_散点图_扰动排名_Cplx2RankScatter.png"), p, width = 10, height = 7, dpi = 600)
ggplot2::ggsave(file.path(fig, "04_散点图_扰动排名_Cplx2RankScatter.svg"), p, width = 10, height = 7)
message("SCATTER_DONE")
