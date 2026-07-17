source("配置.R", encoding = "UTF-8")
setup_script_env()
source(file.path(PROJECT_ROOT, "共享脚本", "工具_单细胞差异分析.R"), encoding = "UTF-8")

suppressPackageStartupMessages({
  library(Seurat)
  library(tidyverse)
})

seurat_rds <- file.path(PATHS$中间数据, paste0(DATASET, "_seurat.rds"))
if (file.exists(seurat_rds)) {
  message("加载已有 Seurat 对象")
} else {
  raw_rds <- file.path(PATHS$中间数据, paste0(DATASET, "_raw_sc.rds"))
  if (!file.exists(raw_rds)) {
    source(file.path(PROJECT_ROOT, "共享脚本", "工具_RNA定量.R"), encoding = "UTF-8")
    dl <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_download.rds")))
    tenx <- find_10x_dirs(dl$fq_dir)
    if (length(tenx) == 0) {
      stop("CRA029427: 需 kb count 自 FASTQ 生成 10x 矩阵（pip install kb-python）")
    }
    counts_list <- setNames(lapply(tenx, parse_10x_from_dir), basename(tenx))
    meta <- tibble(
      sample = names(counts_list),
      group = ifelse(grepl("CLP|clp", names(counts_list), ignore.case = TRUE), "CLP", "Control")
    )
    saveRDS(list(counts = counts_list, meta = meta), raw_rds)
  }
  raw <- readRDS(raw_rds)
  counts <- raw$counts
  meta <- raw$meta
  objs <- list()
  for (i in seq_along(counts)) {
    sid <- names(counts)[i]
    o <- build_seurat_from_10x(counts[[i]], project = sid)
    o$sample <- sid
    o$group <- as.character(meta$group[i])
    objs[[sid]] <- o
  }
  obj <- merge(objs[[1]], y = objs[-1], add.cell.ids = names(objs))
  obj <- run_seurat_qc_cluster(obj)
  saveRDS(obj, seurat_rds)
}
message("完成: 02_单细胞预处理.R")
