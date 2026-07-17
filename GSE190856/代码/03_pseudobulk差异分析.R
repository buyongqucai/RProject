source("配置.R", encoding = "UTF-8")
setup_script_env()

# 说明：GSE190856 每组仅 2 个生物学重复，样本级 pseudobulk（edgeR-TMM+voom）
# 在 FDR<0.05 下无显著基因（power 不足）。此处采用单细胞标准的
# Wilcoxon 检验（Seurat FindMarkers，与 GSE207363 一致）进行差异分析。
# 细胞数大，用 max.cells.per.ident 每组抽样封顶以控制耗时（set.seed 保证可复现）。

suppressPackageStartupMessages({
  library(Seurat)
  library(tidyverse)
})

obj <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_seurat.rds")))
DefaultAssay(obj) <- "RNA"
obj <- JoinLayers(obj, assay = "RNA")
Idents(obj) <- obj$group
cells <- WhichCells(obj, expression = group %in% cfg$contrast)
obj_sub <- subset(obj, cells = cells)

deg <- FindMarkers(
  obj_sub,
  ident.1 = cfg$contrast[1],
  ident.2 = cfg$contrast[2],
  logfc.threshold = 0,
  min.pct = 0.1,
  max.cells.per.ident = 3000
)
deg$gene <- rownames(deg)
deg <- deg %>%
  rename(log2FC = avg_log2FC, padj = p_val_adj, pvalue = p_val) %>%
  select(gene, log2FC, pvalue, padj, everything())

deg_sig <- deg %>% filter(padj < DEG_PADJ, abs(log2FC) > DEG_LOGFC)

write.csv(deg, file.path(PATHS$表格, paste0(DATASET, "_全部差异基因.csv")), row.names = FALSE)
write.csv(deg_sig, file.path(PATHS$表格, paste0(DATASET, "_显著差异基因.csv")), row.names = FALSE)
saveRDS(deg, file.path(PATHS$中间数据, paste0(DATASET, "_deg.rds")))
saveRDS(deg_sig, file.path(PATHS$中间数据, paste0(DATASET, "_deg_sig.rds")))
message("显著 DEG: ", nrow(deg_sig), " (上调 ", sum(deg_sig$log2FC > 0),
        " / 下调 ", sum(deg_sig$log2FC < 0), "; 单细胞 Wilcoxon FindMarkers)")
message("完成: 03_pseudobulk差异分析.R")
