source("配置.R", encoding = "UTF-8")
setup_script_env()

suppressPackageStartupMessages({
  library(Seurat)
  library(edgeR)
  library(limma)
  library(tidyverse)
})

obj <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_seurat.rds")))
DefaultAssay(obj) <- "RNA"

# 按样本聚合原始 counts（AggregateExpression 稳健处理 v5 多层对象）
agg <- AggregateExpression(obj, assays = "RNA", group.by = "sample",
                           slot = "counts", return.seurat = FALSE)
pb <- as.matrix(agg$RNA)

# 列名（样本）对齐回元数据（AggregateExpression 会把 '_' 替换为 '-'）
meta <- obj@meta.data
usam_raw <- unique(as.character(meta[["sample"]]))
map_clean <- setNames(usam_raw, make.names(gsub("_", "-", usam_raw)))
cn_clean <- make.names(colnames(pb))
colnames(pb) <- ifelse(cn_clean %in% names(map_clean), map_clean[cn_clean], colnames(pb))

grp_all <- meta[["group"]][match(colnames(pb), as.character(meta[["sample"]]))]
keep <- grp_all %in% cfg$contrast
pb <- pb[, keep, drop = FALSE]
group <- factor(grp_all[keep], levels = cfg$contrast)
message("Pseudobulk 样本: ", paste(colnames(pb), collapse = ", "))
message("分组: ", paste(as.character(group), collapse = ", "))

# edgeR: 过滤低表达 + TMM 组成归一化，消除全局偏移
dge <- DGEList(counts = pb, group = group)
keep_genes <- filterByExpr(dge, group = group)
dge <- dge[keep_genes, , keep.lib.sizes = FALSE]
dge <- calcNormFactors(dge, method = "TMM")

design <- model.matrix(~ 0 + group)
colnames(design) <- levels(group)
contrast_str <- paste0(cfg$contrast[1], "-", cfg$contrast[2])
contrast_matrix <- makeContrasts(contrasts = contrast_str, levels = design)

v <- voom(dge, design, plot = FALSE)
fit <- lmFit(v, design)
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
message("显著 DEG: ", nrow(deg_sig), " (上调 ", sum(deg_sig$log2FC > 0),
        " / 下调 ", sum(deg_sig$log2FC < 0),
        "; 样本级 pseudobulk edgeR-TMM + limma-voom, n=", ncol(pb), ")")
message("完成: 03_pseudobulk差异分析.R")
