source("配置.R", encoding = "UTF-8")
setup_script_env()

source(file.path(PROJECT_ROOT, "共享脚本", "工具_NGDC下载.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_RNA定量.R"), encoding = "UTF-8")
suppressPackageStartupMessages(library(tidyverse))

prefix_rds <- file.path(PATHS$中间数据, paste0(DATASET, "_expr_raw.rds"))
if (file.exists(prefix_rds)) {
  message("已存在表达矩阵，跳过")
} else {
  runs <- ngdc_fetch_gsa_page_runs(cfg$cra_id)
  fq_dir <- file.path(PATHS$源数据, "FASTQ")
  for (r in runs) ngdc_download_gsa_run(cfg$cra_id, r, fq_dir)

  sample_info <- tibble(
    run = runs,
    sample = runs,
    title = runs,
    group = ifelse(grepl("CLP|clp", runs, ignore.case = TRUE), "CLP", "Control")
  )
  sample_info$group <- factor(sample_info$group, levels = cfg$contrast)
  rownames(sample_info) <- sample_info$run

  quant_dir <- file.path(PATHS$源数据, "quant")
  expr <- run_bulk_quant(fq_dir, runs, PROJECT_ROOT, quant_dir)
  colnames(expr) <- sample_info$run[match(colnames(expr), sample_info$run)]

  feature_info <- tibble(gene_id = rownames(expr), gene_symbol = rownames(expr))
  rownames(feature_info) <- rownames(expr)
  save_bulk_download_objects(list(expr = as.matrix(expr), sample_info = sample_info, feature_info = feature_info), PATHS, DATASET)
}
message("完成: 01_下载数据.R")
