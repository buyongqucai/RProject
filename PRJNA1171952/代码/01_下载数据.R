source("配置.R", encoding = "UTF-8")
setup_script_env()

source(file.path(PROJECT_ROOT, "共享脚本", "工具_SRA下载.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_RNA定量.R"), encoding = "UTF-8")
suppressPackageStartupMessages(library(tidyverse))

prefix_rds <- file.path(PATHS$中间数据, paste0(DATASET, "_expr_raw.rds"))
if (file.exists(prefix_rds)) {
  message("已存在表达矩阵，跳过下载与定量")
} else {
  runinfo <- sra_list_runs(cfg$bioproject)
  write.csv(runinfo, file.path(PATHS$源数据, paste0(DATASET, "_runinfo.csv")), row.names = FALSE)

  runinfo <- runinfo %>% filter(grepl(cfg$sample_filter, SampleName))
  runinfo$group <- case_when(
    grepl("_C-", runinfo$SampleName) ~ "SICM",
    grepl("_E-", runinfo$SampleName) ~ "Exercise",
    TRUE ~ NA_character_
  )
  runinfo <- runinfo %>% filter(!is.na(group))

  fq_dir <- file.path(PATHS$源数据, "FASTQ")
  sra_download_fastq(runinfo$Run, fq_dir)

  quant_dir <- file.path(PATHS$源数据, "salmon")
  expr <- run_bulk_quant(fq_dir, runinfo$Run, PROJECT_ROOT, quant_dir)

  sample_info <- runinfo %>%
    transmute(run = Run, sample = SampleName, title = SampleName, group = factor(group, levels = cfg$contrast))
  rownames(sample_info) <- sample_info$run
  colnames(expr) <- sample_info$run[match(colnames(expr), sample_info$run)]

  feature_info <- tibble(gene_id = rownames(expr), gene_symbol = rownames(expr))
  rownames(feature_info) <- rownames(expr)

  data_obj <- list(expr = as.matrix(expr), sample_info = sample_info, feature_info = feature_info,
                   platform = "SRA", data_type = "rnaseq_counts")
  save_bulk_download_objects(data_obj, PATHS, DATASET)
}
message("完成: 01_下载数据.R")
