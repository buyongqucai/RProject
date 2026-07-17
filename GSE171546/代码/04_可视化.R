source("配置.R", encoding = "UTF-8")
setup_script_env()

suppressPackageStartupMessages({
  library(tidyverse)
  library(ggplot2)
  library(pheatmap)
  library(RColorBrewer)
  library(ggrepel)
})

prefix <- file.path(PATHS$中间数据, DATASET)
expr <- readRDS(paste0(prefix, "_expr_matrix.rds"))
sample_info <- readRDS(paste0(prefix, "_sample_info_final.rds"))
deg <- readRDS(paste0(prefix, "_deg.rds"))
deg_sig <- readRDS(paste0(prefix, "_deg_sig.rds"))

suppressPackageStartupMessages(library(limma))
expr_log <- voom(expr, model.matrix(~ sample_info$group), plot = FALSE)$E

deg_plot <- deg %>%
  mutate(significance = case_when(
    padj < DEG_PADJ & log2FC > DEG_LOGFC ~ "Up",
    padj < DEG_PADJ & log2FC < -DEG_LOGFC ~ "Down",
    TRUE ~ "NS"
  ))

top_label <- deg_plot %>% filter(significance != "NS") %>% arrange(padj) %>% head(15)
p_volcano <- ggplot(deg_plot, aes(x = log2FC, y = -log10(padj), color = significance)) +
  geom_point(alpha = 0.6, size = 1.5) +
  scale_color_manual(values = c(Up = "#E64B35", Down = "#4DBBD5", NS = "grey70")) +
  geom_vline(xintercept = c(-DEG_LOGFC, DEG_LOGFC), linetype = "dashed", color = "grey40") +
  geom_hline(yintercept = -log10(DEG_PADJ), linetype = "dashed", color = "grey40") +
  ggrepel::geom_text_repel(data = top_label, aes(label = gene), size = 3, max.overlaps = 20, color = "black") +
  theme_bw() +
  labs(title = paste(DATASET, "火山图"), subtitle = paste0(cfg$contrast[1], " vs ", cfg$contrast[2]),
       x = expression(log[2] ~ FC), y = expression(-log[10] ~ adj.P))
ggsave(file.path(PATHS$图形, paste0(DATASET, "_火山图.pdf")), p_volcano, width = 8, height = 7)

top_genes <- deg_sig %>% arrange(padj) %>% head(50) %>% pull(gene)
if (length(top_genes) >= 2) {
  mat <- expr_log[top_genes, , drop = FALSE]
  mat_scaled <- t(scale(t(mat)))
  mat_scaled[is.na(mat_scaled)] <- 0
  annotation_col <- data.frame(Group = sample_info$group)
  rownames(annotation_col) <- rownames(sample_info)
  ann_colors <- list(Group = setNames(brewer.pal(3, "Set1")[1:2], cfg$contrast))
  pdf(file.path(PATHS$图形, paste0(DATASET, "_Top50热图.pdf")), width = 10, height = 12)
  pheatmap(mat_scaled, annotation_col = annotation_col, annotation_colors = ann_colors,
           show_rownames = TRUE, fontsize_row = 7, main = paste(DATASET, "Top 50 DEGs"),
           color = colorRampPalette(c("#4DBBD5", "white", "#E64B35"))(100))
  dev.off()
}

pca <- prcomp(t(expr_log), scale. = TRUE)
var_pct <- round(100 * summary(pca)$importance[2, 1:2], 1)
pca_df <- tibble(PC1 = pca$x[, 1], PC2 = pca$x[, 2], sample = rownames(pca$x), group = sample_info$group)
p_pca <- ggplot(pca_df, aes(x = PC1, y = PC2, color = group)) +
  geom_point(size = 4) + theme_bw() +
  labs(title = paste(DATASET, "PCA"), x = paste0("PC1 (", var_pct[1], "%)"), y = paste0("PC2 (", var_pct[2], "%)"))
ggsave(file.path(PATHS$图形, paste0(DATASET, "_PCA.pdf")), p_pca, width = 7, height = 6)
message("完成: 04_可视化.R")
