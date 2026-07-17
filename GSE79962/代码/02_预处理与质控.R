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

# Subset to contrast groups if RNA-seq has multiple groups
contrast_groups <- cfg$contrast
keep_samples <- sample_info$group %in% contrast_groups
expr <- expr_raw[, keep_samples, drop = FALSE]
sample_info <- sample_info[keep_samples, , drop = FALSE]
sample_info$group <- factor(sample_info$group, levels = contrast_groups)

message("Analyzing contrast: ", contrast_groups[1], " vs ", contrast_groups[2])
message("Samples: ", paste(table(sample_info$group), collapse = " / "))

# Log-transform if values look like raw intensities (max > 100)
if (max(expr, na.rm = TRUE) > 100) {
  message("Applying log2(x + 1) transformation")
  expr <- log2(expr + 1)
}

# Filter low-expression features
if (cfg$type == "microarray") {
  keep_feat <- rowSums(expr > quantile(expr, 0.25, na.rm = TRUE)) >= (0.75 * ncol(expr))
} else {
  # RNA-seq matrix from GEO is often log-count or normalized; use median threshold
  keep_feat <- rowMeans(expr, na.rm = TRUE) > median(rowMeans(expr, na.rm = TRUE))
}
expr <- expr[keep_feat, , drop = FALSE]
message("Retained ", nrow(expr), " features after filtering")

# Between-array normalization for microarray
if (cfg$type == "microarray") {
  expr <- normalizeBetweenArrays(expr, method = "quantile")
}

# Collapse duplicate gene symbols (keep highest mean expression)
if ("gene_symbol" %in% colnames(feature_info)) {
  symbols <- feature_info$gene_symbol[match(rownames(expr), rownames(feature_info))]
  valid <- !is.na(symbols) & symbols != "" & symbols != "---"
  expr <- expr[valid, , drop = FALSE]
  symbols <- symbols[valid]
  expr <- avereps(expr, ID = symbols)
  message("Collapsed to ", nrow(expr), " unique gene symbols")
}

# QC: boxplot
box_df <- tibble(
  sample = rep(colnames(expr), each = nrow(expr)),
  expression = as.vector(expr),
  group = rep(sample_info$group, times = nrow(expr))
)

p_box <- ggplot(box_df, aes(x = sample, y = expression, fill = group)) +
  geom_boxplot(outlier.size = 0.3) +
  theme_bw() +
  theme(axis.text.x = element_text(angle = 90, hjust = 1, size = 6)) +
  labs(title = paste(DATASET, "Expression distribution"), x = NULL, y = "log2 expression")

ggsave(file.path(PATHS$figures, paste0(DATASET, "_质控箱线图.pdf")),
       p_box, width = 10, height = 5)

# QC: PCA
pca <- prcomp(t(expr), scale. = TRUE)
var_pct <- round(100 * summary(pca)$importance[2, 1:2], 1)
pca_df <- tibble(
  PC1 = pca$x[, 1],
  PC2 = pca$x[, 2],
  sample = rownames(pca$x),
  group = sample_info$group
)

p_pca <- ggplot(pca_df, aes(x = PC1, y = PC2, color = group, label = sample)) +
  geom_point(size = 3) +
  geom_text(vjust = -0.8, size = 2.5, check_overlap = TRUE) +
  theme_bw() +
  labs(
    title = paste(DATASET, "PCA"),
    x = paste0("PC1 (", var_pct[1], "%)"),
    y = paste0("PC2 (", var_pct[2], "%)")
  )

ggsave(file.path(PATHS$figures, paste0(DATASET, "_质控PCA.pdf")),
       p_pca, width = 8, height = 6)

saveRDS(expr, paste0(prefix, "_expr_matrix.rds"))
saveRDS(sample_info, paste0(prefix, "_sample_info_final.rds"))

message("Saved preprocessed matrix: ", paste0(prefix, "_expr_matrix.rds"))
message("Done: 02_preprocess_qc.R")