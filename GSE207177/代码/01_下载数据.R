source("配置.R", encoding = "UTF-8")
setup_script_env()

source(file.path(PROJECT_ROOT, "共享脚本", "工具_NCBI接口.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_RNA定量.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_GEO元数据.R"), encoding = "UTF-8")

gse <- cfg$gse_id
fname <- paste0(gse, "_RAW.tar")
tar_path <- file.path(PATHS$源数据, fname)
url <- sprintf("https://ftp.ncbi.nlm.nih.gov/geo/series/%s/%s/suppl/%s",
                geo_series_ftp_dir(gse), gse, fname)
if (!file.exists(tar_path)) geo_download_file(gse, fname, PATHS$源数据)
geo_verify_download(tar_path, min_bytes = 200e6)
geo_save_manifest(gse, url, tar_path, PATHS)

extract_dir <- file.path(PATHS$源数据, paste0(gse, "_RAW"))
if (!dir.exists(extract_dir) || length(list.files(extract_dir)) == 0) {
  parse_geo_raw_tar(tar_path, extract_dir)
}

counts_list <- read_flat_10x_samples(extract_dir)
if (length(counts_list) == 0) stop("未找到 10x 矩阵")

assign_group <- function(s) {
  if (grepl("n-1|n-2|control", s, ignore.case = TRUE)) return("Control")
  if (grepl("clp-12h|clp-24h|clp", s, ignore.case = TRUE)) return("CLP")
  NA_character_
}
sample_names <- names(counts_list)
groups <- vapply(sample_names, assign_group, character(1))
if (any(is.na(groups))) stop("无法从文件名解析分组: ", paste(sample_names[is.na(groups)], collapse = ", "))

meta_out <- tibble::tibble(
  sample = sample_names,
  group = factor(groups, levels = c("Control", "CLP12h", "CLP24h", "CLP"))
)
meta_out$group_detail <- ifelse(grepl("12h", sample_names), "CLP12h",
                         ifelse(grepl("24h", sample_names), "CLP24h",
                         ifelse(groups == "Control", "Control", "CLP")))
meta_out$group <- factor(ifelse(groups == "CLP", "CLP", "Control"), levels = c("Control", "CLP"))

write.csv(meta_out, file.path(PATHS$中间数据, "sample_meta.csv"), row.names = FALSE)
saveRDS(list(counts = counts_list, meta = meta_out), file.path(PATHS$中间数据, paste0(DATASET, "_raw_sc.rds")))
message("完成: 01_下载数据.R (", length(counts_list), " 样本)")
