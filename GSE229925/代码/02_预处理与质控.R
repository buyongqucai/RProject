source("配置.R", encoding = "UTF-8")
setup_script_env()

suppressPackageStartupMessages({
  library(limma)
  library(tidyverse)
  library(ggplot2)
})

prefix <- file.path(PATHS$中间数据, DATASET)
expr_raw <- readRDS(paste0(prefix, "_expr_raw.rds"))
sample_info <- readRDS(paste0(prefix, "_sample_info.rds"))
feature_info <- readRDS(paste0(prefix, "_feature_info.rds"))

contrast_groups <- cfg$contrast
keep_samples <- sample_info$group %in% contrast_groups
expr <- expr_raw[, keep_samples, drop = FALSE]
sample_info <- sample_info[keep_samples, , drop = FALSE]
sample_info$group <- factor(sample_info$group, levels = contrast_groups)

message("对比: ", contrast_groups[1], " vs ", contrast_groups[2])
message("样本数: ", paste(table(sample_info$group), collapse = " / "))

# count 过滤
keep_feat <- rowSums(expr >= 10) >= 2
expr <- expr[keep_feat, , drop = FALSE]
message("过滤后保留 ", nrow(expr), " 基因")

# log2-CPM 用于可视化；limma-voom 用原始 count
expr_log <- limma::voom(expr, plot = FALSE)$E

box_df <- tibble(
  sample = rep(colnames(expr_log), each = nrow(expr_log)),
  expression = as.vector(expr_log),
  group = rep(sample_info$group, times = nrow(expr_log))
)
p_box <- ggplot(box_df, aes(x = sample, y = expression, fill = group)) +
  geom_boxplot(outlier.size = 0.3) + theme_bw() +
  theme(axis.text.x = element_text(angle = 90, hjust = 1, size = 6)) +
  labs(title = paste(DATASET, "表达分布"), x = NULL, y = "log2-CPM")
ggsave(file.path(PATHS$图形, paste0(DATASET, "_质控箱线图.pdf")), p_box, width = 10, height = 5)

pca <- prcomp(t(expr_log), scale. = TRUE)
var_pct <- round(100 * summary(pca)$importance[2, 1:2], 1)
pca_df <- tibble(PC1 = pca$x[,1], PC2 = pca$x[,2], sample = rownames(pca$x), group = sample_info$group)
p_pca <- ggplot(pca_df, aes(x = PC1, y = PC2, color = group, label = sample)) +
  geom_point(size = 3) + geom_text(vjust = -0.8, size = 2.5, check_overlap = TRUE) + theme_bw() +
  labs(title = paste(DATASET, "PCA"), x = paste0("PC1 (", var_pct[1], "%)"), y = paste0("PC2 (", var_pct[2], "%)"))
ggsave(file.path(PATHS$图形, paste0(DATASET, "_质控PCA.pdf")), p_pca, width = 8, height = 6)

saveRDS(expr, paste0(prefix, "_expr_matrix.rds"))
saveRDS(sample_info, paste0(prefix, "_sample_info_final.rds"))
message("完成: 02_预处理与质控.R")