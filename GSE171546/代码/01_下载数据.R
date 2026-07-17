source("配置.R", encoding = "UTF-8")
setup_script_env()

source(file.path(PROJECT_ROOT, "共享脚本", "工具_NCBI接口.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_RNA定量.R"), encoding = "UTF-8")

suppressPackageStartupMessages(library(tidyverse))

tar_name <- "GSE171546_RAW.tar"
tar_path <- file.path(PATHS$源数据, tar_name)
if (!file.exists(tar_path)) geo_download_file("GSE171546", tar_name, PATHS$源数据)

extract_dir <- file.path(PATHS$源数据, "GSE171546_RAW")
if (!dir.exists(extract_dir) || !any(grepl("_Count\\.txt\\.gz$", list.files(extract_dir)))) {
  parse_geo_raw_tar(tar_path, extract_dir)
}

expr <- parse_gse171546_counts(extract_dir)

count_files <- list.files(extract_dir, pattern = "_Count\\.txt\\.gz$", full.names = FALSE)
sample_info <- tibble(
  file = count_files,
  geo_accession = sub("_.*", "", count_files),
  sample = sub("_Count\\.txt\\.gz$", "", sub("^GSM[0-9]+_", "", count_files))
) %>%
  mutate(
    title = gsub("_", "-", sample),
    group = case_when(
      grepl("^H_CON", sample) ~ "Sham",
      grepl("CLP24H", sample, ignore.case = TRUE) ~ "CLP24h",
      grepl("CLP48H", sample, ignore.case = TRUE) ~ "CLP48h",
      grepl("CLP72H", sample, ignore.case = TRUE) ~ "CLP72h",
      TRUE ~ NA_character_
    )
  )

common <- intersect(colnames(expr), sample_info$sample)
expr <- expr[, common, drop = FALSE]
sample_info <- sample_info %>% filter(sample %in% common)
rownames(sample_info) <- sample_info$sample

keep <- sample_info$group %in% cfg$contrast
expr <- expr[, sample_info$sample[keep], drop = FALSE]
sample_info <- sample_info[keep, , drop = FALSE]
sample_info$group <- factor(sample_info$group, levels = cfg$contrast)

feature_info <- tibble(gene_id = rownames(expr), gene_symbol = rownames(expr))
rownames(feature_info) <- rownames(expr)

data_obj <- list(
  expr = as.matrix(expr),
  sample_info = sample_info,
  feature_info = feature_info,
  platform = "GPL24247",
  data_type = "rnaseq_counts"
)
save_bulk_download_objects(data_obj, PATHS, DATASET)
message("分组: ", paste(names(table(sample_info$group)), table(sample_info$group), sep = "=", collapse = ", "))
message("完成: 01_下载数据.R")
