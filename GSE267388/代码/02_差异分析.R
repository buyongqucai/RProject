source("配置.R", encoding = "UTF-8")
setup_script_env()

suppressPackageStartupMessages({
  library(limma)
  library(tidyverse)
})

mat <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_expr_matrix.rds")))
sample_info <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_sample_info.rds")))
rownames(sample_info) <- sample_info$sample
mat <- mat[, sample_info$sample, drop = FALSE]

group <- factor(sample_info$group, levels = cfg$contrast)
design <- model.matrix(~ 0 + group)
colnames(design) <- levels(group)
contrast_str <- paste0(cfg$contrast[1], "-", cfg$contrast[2])
contrast_matrix <- makeContrasts(contrasts = contrast_str, levels = design)

if (max(mat, na.rm = TRUE) > 50) {
  v <- voom(mat, design, plot = FALSE)
  fit <- lmFit(v, design)
} else {
  fit <- lmFit(log2(mat + 1), design)
}
fit2 <- contrasts.fit(fit, contrast_matrix)
fit2 <- eBayes(fit2)
deg <- topTable(fit2, number = Inf, adjust.method = "BH", sort.by = "P")
deg$gene <- rownames(deg)
deg <- deg %>%
  rename(log2FC = logFC, padj = adj.P.Val, pvalue = P.Value) %>%
  select(gene, log2FC, AveExpr, t, pvalue, padj, everything())
deg_sig <- deg %>% filter(padj < DEG_PADJ, abs(log2FC) > DEG_LOGFC)

write.csv(deg, file.path(PATHS$表格, paste0(DATASET, "_全部差异基因.csv")), row.names = FALSE)
write.csv(deg_sig, file.path(PATHS$表格, paste0(DATASET, "_显著差异基因.csv")), row.names = FALSE)
saveRDS(deg, file.path(PATHS$中间数据, paste0(DATASET, "_deg.rds")))
saveRDS(deg_sig, file.path(PATHS$中间数据, paste0(DATASET, "_deg_sig.rds")))
message("显著 DEG: ", nrow(deg_sig))
message("完成: 02_差异分析.R")
