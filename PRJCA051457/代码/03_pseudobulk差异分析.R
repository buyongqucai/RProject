source("配置.R", encoding = "UTF-8")
setup_script_env()
source(file.path(PROJECT_ROOT, "共享脚本", "工具_单细胞差异分析.R"), encoding = "UTF-8")

suppressPackageStartupMessages({
  library(Seurat)
  library(DESeq2)
  library(tidyverse)
})

obj <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_seurat.rds")))
DefaultAssay(obj) <- "RNA"
if ("JoinLayers" %in% ls("package:Seurat")) obj <- JoinLayers(obj)
counts <- tryCatch(
  GetAssayData(obj, layer = "counts"),
  error = function(e) as.matrix(obj[["RNA"]]$counts)
)
meta <- obj@meta.data[colnames(counts), , drop = FALSE] %>%
  mutate(
    sample_id = if ("sample" %in% colnames(.)) .data$sample else .data$orig.ident,
    celltype = if ("seurat_clusters" %in% colnames(.)) .data$seurat_clusters else "all",
    group = as.character(.data$group)
  )

keep <- meta$group %in% cfg$contrast
counts <- counts[, keep, drop = FALSE]
meta <- meta[keep, , drop = FALSE]
meta$group <- factor(meta$group, levels = cfg$contrast)

deg <- run_scrna_pseudobulk_deg(
  counts, meta,
  celltype_col = "celltype",
  group_col = "group",
  contrast = cfg$contrast,
  sample_col = "sample_id"
)

deg <- deg %>% rename(log2FC = log2FoldChange) %>% filter(!is.na(gene))
deg_sig <- deg %>% filter(padj < DEG_PADJ, abs(log2FC) > DEG_LOGFC)

write.csv(deg, file.path(PATHS$表格, paste0(DATASET, "_全部差异基因.csv")), row.names = FALSE)
write.csv(deg_sig, file.path(PATHS$表格, paste0(DATASET, "_显著差异基因.csv")), row.names = FALSE)
saveRDS(deg, file.path(PATHS$中间数据, paste0(DATASET, "_deg.rds")))
saveRDS(deg_sig, file.path(PATHS$中间数据, paste0(DATASET, "_deg_sig.rds")))
message("显著 DEG: ", nrow(deg_sig))
message("完成: 03_pseudobulk差异分析.R")
