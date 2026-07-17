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
if (length(counts_list) == 0) {
  tenx_dirs <- find_10x_dirs(extract_dir)
  counts_list <- setNames(lapply(tenx_dirs, parse_10x_from_dir), basename(tenx_dirs))
}
if (length(counts_list) == 0) stop("未找到 10x 矩阵")

# 官方 GSM 对照（GEO 页面）
meta <- tibble::tibble(
  geo_accession = c("GSM6285062", "GSM6285063", "GSM6285064", "GSM6285065"),
  sample = c("Sample1", "Sample2", "Sample3", "Sample4"),
  title = c("control sample", "sham sample", "sepsis sample", "sepsis + LL-TS sample"),
  group = factor(c("Control", "Sham", "Sepsis", "LLTS"),
                 levels = c("Control", "Sham", "Sepsis", "LLTS"))
)
# 按样本名匹配到 GEO 官方分组（修复：此前误把样本名当作分组导致 group=NA）
sample_names <- names(counts_list)
groups <- vapply(sample_names, function(s) {
  idx <- which(vapply(meta$sample, function(x) grepl(x, s, fixed = TRUE), logical(1)))
  if (length(idx)) as.character(meta$group[idx[1]]) else NA_character_
}, character(1))
if (any(is.na(groups))) {
  # 兜底：按 GEO 顺序 GSM6285062..65 -> Control/Sham/Sepsis/LLTS
  groups[is.na(groups)] <- c("Control", "Sham", "Sepsis", "LLTS")[seq_along(sample_names)][is.na(groups)]
}
meta_out <- tibble::tibble(sample = sample_names, group = factor(groups, levels = levels(meta$group)))
write.csv(meta_out, file.path(PATHS$中间数据, "sample_meta.csv"), row.names = FALSE)

saveRDS(list(counts = counts_list, meta = meta_out), file.path(PATHS$中间数据, paste0(DATASET, "_raw_sc.rds")))
message("完成: 01_下载数据.R (", length(counts_list), " 样本, GEO 官方 RAW)")
