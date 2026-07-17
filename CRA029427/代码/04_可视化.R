source("配置.R", encoding = "UTF-8")
setup_script_env()

suppressPackageStartupMessages({
  library(Seurat)
  library(ggplot2)
  library(tidyverse)
})

obj <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_seurat.rds")))
deg <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_deg.rds")))

p_umap <- DimPlot(obj, group.by = "group", label = TRUE) + ggtitle(paste(DATASET, "UMAP"))
ggsave(file.path(PATHS$图形, paste0(DATASET, "_UMAP.pdf")), p_umap, width = 8, height = 6)

deg_plot <- deg %>%
  mutate(significance = case_when(
    padj < DEG_PADJ & log2FC > DEG_LOGFC ~ "Up",
    padj < DEG_PADJ & log2FC < -DEG_LOGFC ~ "Down",
    TRUE ~ "NS"
  ))
p_vol <- ggplot(deg_plot, aes(x = log2FC, y = -log10(padj), color = significance)) +
  geom_point(alpha = 0.6) +
  scale_color_manual(values = c(Up = "#E64B35", Down = "#4DBBD5", NS = "grey70")) +
  theme_bw() + labs(title = paste(DATASET, "pseudobulk 火山图"))
ggsave(file.path(PATHS$图形, paste0(DATASET, "_火山图.pdf")), p_vol, width = 8, height = 6)
message("完成: 04_可视化.R")
