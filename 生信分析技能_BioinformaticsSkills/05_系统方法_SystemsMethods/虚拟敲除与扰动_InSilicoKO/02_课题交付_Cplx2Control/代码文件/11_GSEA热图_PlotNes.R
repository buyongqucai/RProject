options(stringsAsFactors = FALSE)
root <- "C:/Users/10540/Desktop/琪乐无穷/CPLX2虚拟敲除_Cplx2VirtualKO"
csv <- file.path(root, "结果文件", "数据文件", "08_GSEA_突触条目_SynapseGsea.csv")
fig <- file.path(root, "结果文件", "图片文件")
viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
if (file.exists(viz)) source(viz, encoding = "UTF-8")
suppressPackageStartupMessages(library(ggplot2))
if (!exists("theme_journal")) theme_journal <- function(...) theme_bw()
d <- read.csv(csv, check.names = FALSE)
p <- ggplot(d, aes(subtype, Description, fill = NES)) +
  geom_tile(color = "white", linewidth = 0.4) +
  geom_text(aes(label = sprintf("%.2f", p.adjust)), size = 3) +
  scale_fill_gradient2(low = "#2166AC", mid = "white", high = "#B2182B", midpoint = 1) +
  labs(
    title = "GSEA NES for prespecified synaptic terms",
    subtitle = "Numbers are adjusted P. None are below 0.05.",
    x = NULL, y = NULL, fill = "NES"
  ) +
  theme_journal() +
  theme(axis.text.x = element_text(angle = 30, hjust = 1))
ggsave(file.path(fig, "08_热图_突触GSEA_SynapseNES.png"), p, width = 8, height = 4.2, dpi = 600, bg = "white")
ggsave(file.path(fig, "08_热图_突触GSEA_SynapseNES.svg"), p, width = 8, height = 4.2, bg = "white")
message("HEAT_DONE")
