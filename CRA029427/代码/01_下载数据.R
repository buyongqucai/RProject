source("配置.R", encoding = "UTF-8")
setup_script_env()

source(file.path(PROJECT_ROOT, "共享脚本", "工具_NGDC下载.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_RNA定量.R"), encoding = "UTF-8")

fq_dir <- file.path(PATHS$源数据, "FASTQ")
runs <- ngdc_fetch_gsa_page_runs(cfg$cra_id)
for (r in runs) ngdc_download_gsa_run(cfg$cra_id, r, fq_dir)

saveRDS(list(runs = runs, fq_dir = fq_dir), file.path(PATHS$中间数据, paste0(DATASET, "_download.rds")))
message("完成: 01_下载数据.R (", length(runs), " runs)")
