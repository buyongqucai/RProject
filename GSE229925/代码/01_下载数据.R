# GSE229925：从 GEO 补充文件读取 read count 矩阵

source("配置.R", encoding = "UTF-8")
setup_script_env()

suppressPackageStartupMessages({
  library(GEOquery)
  library(tidyverse)
})

download_gse229925_counts <- function() {
  supp_dir <- file.path(PATHS$源数据, "GSE229925")
  count_gz <- file.path(supp_dir, "GSE229925_genes.readcount.txt.gz")
  if (!file.exists(count_gz)) {
    message("正在下载 GSE229925 补充文件 ...")
    GEOquery::getGEOSuppFiles("GSE229925", baseDir = PATHS$源数据)
  }

  counts <- read.delim(gzfile(count_gz), row.names = 1, check.names = FALSE)
  gse_list <- GEOquery::getGEO("GSE229925", destdir = PATHS$源数据, GSEMatrix = TRUE)
  pdata <- Biobase::pData(gse_list[[1]])

  pdata$sample_code <- ifelse(grepl("^S,", pdata$title),
    paste0("S", sub(".*?(\\d+)$", "\\1", pdata$title)),
    paste0("C", sub(".*?(\\d+)$", "\\1", pdata$title))
  )

  group <- dplyr::case_when(
    grepl("^S,", pdata$title) ~ "Sham",
    grepl("^C1,", pdata$title) ~ "HEF",
    grepl("^C2,", pdata$title) ~ "LEF",
    grepl("^C3,", pdata$title) ~ "NEF",
    TRUE ~ NA_character_
  )

  sample_info <- tibble(
    geo_accession = pdata$geo_accession,
    title = pdata$title,
    sample_code = pdata$sample_code,
    group = factor(group, levels = c("Sham", "HEF", "LEF", "NEF"))
  )
  rownames(sample_info) <- sample_info$sample_code

  common <- intersect(colnames(counts), sample_info$sample_code)
  counts <- counts[, common, drop = FALSE]
  sample_info <- sample_info[common, , drop = FALSE]

  feature_info <- tibble(gene_id = rownames(counts), gene_symbol = rownames(counts))
  rownames(feature_info) <- rownames(counts)

  list(expr = as.matrix(counts), sample_info = sample_info, feature_info = feature_info,
       platform = "GPL24247", data_type = "rnaseq_counts")
}

data_obj <- download_gse229925_counts()
prefix <- file.path(PATHS$中间数据, DATASET)
saveRDS(data_obj$expr, paste0(prefix, "_expr_raw.rds"))
saveRDS(data_obj$sample_info, paste0(prefix, "_sample_info.rds"))
saveRDS(data_obj$feature_info, paste0(prefix, "_feature_info.rds"))
write.csv(data_obj$sample_info, paste0(prefix, "_sample_info.csv"), row.names = FALSE)

message("已保存: ", nrow(data_obj$expr), " 基因 x ", ncol(data_obj$expr), " 样本")
message("分组: ", paste(names(table(data_obj$sample_info$group)), table(data_obj$sample_info$group), sep = "=", collapse = ", "))
message("完成: 01_下载数据.R")