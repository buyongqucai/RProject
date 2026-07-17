source("配置.R", encoding = "UTF-8")
setup_script_env()


suppressPackageStartupMessages({
  library(limma)
  library(tidyverse)
})

prefix <- file.path(PATHS$中间数据, DATASET)
expr <- readRDS(paste0(prefix, "_expr_matrix.rds"))
sample_info <- readRDS(paste0(prefix, "_sample_info_final.rds"))

group <- factor(sample_info$group, levels = cfg$contrast)
names(group) <- rownames(sample_info)

run_limma_deg <- function(expr_mat, group_factor, contrast_vec) {
  design <- model.matrix(~ 0 + group_factor)
  colnames(design) <- levels(group_factor)

  contrast_name <- paste(contrast_vec, collapse = "-")
  contrast_str <- paste0(contrast_vec[1], "-", contrast_vec[2])
  contrast_matrix <- makeContrasts(contrasts = contrast_str, levels = design)

  fit <- lmFit(expr_mat, design)
  fit2 <- contrasts.fit(fit, contrast_matrix)
  fit2 <- eBayes(fit2)

  deg <- topTable(fit2, number = Inf, adjust.method = "BH", sort.by = "P")
  deg$gene <- rownames(deg)
  deg
}

if (cfg$type == "microarray") {
  message("Running limma for microarray data...")
  deg <- run_limma_deg(expr, group, cfg$contrast)
  deg <- deg %>%
    rename(log2FC = logFC, padj = adj.P.Val, pvalue = P.Value) %>%
    select(gene, log2FC, AveExpr, t, pvalue, padj, everything())
} else {
  message("Running limma-voom for RNA-seq normalized matrix...")
  # GEO Series Matrix for RNA-seq often provides log2-normalized values
  design <- model.matrix(~ 0 + group)
  colnames(design) <- levels(group)

  contrast_str <- paste0(cfg$contrast[1], "-", cfg$contrast[2])
  contrast_matrix <- makeContrasts(contrasts = contrast_str, levels = design)

  v <- voom(expr, design, plot = FALSE)
  fit <- lmFit(v, design)
  fit2 <- contrasts.fit(fit, contrast_matrix)
  fit2 <- eBayes(fit2)

  deg <- topTable(fit2, number = Inf, adjust.method = "BH", sort.by = "P")
  deg$gene <- rownames(deg)
  deg <- deg %>%
    rename(log2FC = logFC, padj = adj.P.Val, pvalue = P.Value) %>%
    select(gene, log2FC, AveExpr, t, pvalue, padj, everything())

  message("Note: For raw count data, use DESeq2 with count matrix.")
  message("      GSE229925 Series Matrix provides normalized values; limma-voom is applied.")
}

deg_sig <- deg %>%
  filter(padj < DEG_PADJ, abs(log2FC) > DEG_LOGFC)

write.csv(deg, file.path(PATHS$tables, paste0(DATASET, "_全部差异基因.csv")), row.names = FALSE)
write.csv(deg_sig, file.path(PATHS$tables, paste0(DATASET, "_显著差异基因.csv")), row.names = FALSE)
saveRDS(deg, file.path(PATHS$中间数据, paste0(DATASET, "_deg.rds")))
saveRDS(deg_sig, file.path(PATHS$中间数据, paste0(DATASET, "_deg_sig.rds")))

message("Total genes tested: ", nrow(deg))
message("Significant DEGs (padj < ", DEG_PADJ, ", |log2FC| > ", DEG_LOGFC, "): ", nrow(deg_sig))
message("  Upregulated: ", sum(deg_sig$log2FC > 0))
message("  Downregulated: ", sum(deg_sig$log2FC < 0))
message("Done: 03_deg_analysis.R")