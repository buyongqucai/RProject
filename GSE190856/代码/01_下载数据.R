source("配置.R", encoding = "UTF-8")
setup_script_env()

source(file.path(PROJECT_ROOT, "共享脚本", "工具_NCBI接口.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_RNA定量.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_GEO元数据.R"), encoding = "UTF-8")
suppressPackageStartupMessages(library(tidyverse))

gse <- cfg$gse_id
fname <- paste0(gse, "_RAW.tar")
tar_path <- file.path(PATHS$源数据, fname)
if (!file.exists(tar_path)) geo_download_file(gse, fname, PATHS$源数据)
geo_verify_download(tar_path, min_bytes = 500e6)
geo_save_manifest(gse, sprintf("https://ftp.ncbi.nlm.nih.gov/geo/series/%s/%s/suppl/%s",
                               geo_series_ftp_dir(gse), gse, fname), tar_path, PATHS)

extract_dir <- file.path(PATHS$源数据, paste0(gse, "_RAW"))
if (!dir.exists(extract_dir) || length(list.files(extract_dir, pattern = "GSM")) == 0) {
  dir.create(extract_dir, recursive = TRUE, showWarnings = FALSE)
  untar(tar_path, exdir = extract_dir)
}
nested <- list.files(extract_dir, pattern = "GSM.*\\.tar\\.gz$", full.names = TRUE)
for (nt in nested) {
  subdir <- file.path(extract_dir, tools::file_path_sans_ext(basename(nt)))
  if (!dir.exists(subdir) || length(list.files(subdir)) == 0) {
    dir.create(subdir, recursive = TRUE, showWarnings = FALSE)
    untar(nt, exdir = subdir)
  }
}

tenx_dirs <- find_10x_dirs(extract_dir)
counts_list <- setNames(lapply(tenx_dirs, parse_10x_from_dir), basename(tenx_dirs))

# 官方 GEO SOFT 元数据（GSE190856_family.soft.gz）
meta_out <- tibble::tribble(
  ~sample, ~geo_accession, ~genotype, ~time_point, ~group,
  "H001", "GSM5733020", "Wild-type littermate control", "steady state", "Steady",
  "H002", "GSM5733021", "Wild-type littermate control", "3 days post CLP", "CLP",
  "H003", "GSM5733022", "Wild-type", "steady state", "Steady",
  "H004", "GSM5733023", "Wild-type", "3 days post CLP", "CLP",
  "H007", "GSM5733026", "Wild-type", "7 days post CLP", "CLP",
  "H009", "GSM5733028", "Wild-type", "21 days post CLP", "CLP",
  "H011", "GSM5733029", "Wild-type littermate control", "7 days post CLP", "CLP"
) %>% mutate(group = factor(group, levels = c("Steady", "CLP")))

keep <- intersect(names(counts_list), meta_out$sample)
if (length(keep) == 0) stop("10x 样本名与 GEO 元数据不匹配: ", paste(names(counts_list), collapse = ", "))
counts_keep <- counts_list[keep]
meta_out <- meta_out %>% filter(sample %in% keep)

write.csv(meta_out, file.path(PATHS$中间数据, "sample_meta.csv"), row.names = FALSE)
saveRDS(list(counts = counts_keep, meta = meta_out), file.path(PATHS$中间数据, paste0(DATASET, "_raw_sc.rds")))
message("完成: 01_下载 (", length(counts_keep), " WT 样本)")
