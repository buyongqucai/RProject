source("配置.R", encoding = "UTF-8")
setup_script_env()

source(file.path(PROJECT_ROOT, "共享脚本", "工具_NGDC下载.R"), encoding = "UTF-8")

paths <- ngdc_download_omix(cfg$omix_id, PATHS$源数据)
count_file <- paths$count
meta_file <- paths$metadata

message("OMIX count: ", count_file)
message("OMIX metadata: ", meta_file)
saveRDS(list(count_file = count_file, meta_file = meta_file),
        file.path(PATHS$中间数据, paste0(DATASET, "_omix_paths.rds")))
message("完成: 01_下载数据.R")
