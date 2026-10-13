# Safe STRING official image (13) + pack status. Non-fatal if offline.
options(stringsAsFactors = FALSE)
work_root <- "E:/RProject/努力学习项目/网络药理学"
stopifnot(!grepl("Desktop|桌面", normalizePath(work_root, winslash = "/", mustWork = FALSE)))
project_root <- "E:/RProject"
bio_root <- file.path(project_root, "生信分析技能_BioinformaticsSkills")
skill_root <- file.path(bio_root, "03_药物计算_DrugDiscovery", "网络药理学_NetworkPharmacology")
data_dir <- file.path(work_root, "数据文件")
fig_dir <- file.path(work_root, "代码文件", "结果文件", "图片文件")
rep_dir <- file.path(work_root, "代码文件", "结果文件", "报告文件")
dir.create(rep_dir, recursive = TRUE, showWarnings = FALSE)

source(file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                 "脚本_scripts", "出版级出图_PublicationPlot.R"), encoding = "UTF-8")
source(file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards",
                 "脚本_scripts", "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
for (sf in list.files(file.path(skill_root, "脚本_scripts"), pattern = "[.][Rr]$", full.names = TRUE)) {
  source(sf, encoding = "UTF-8")
}

skill_en <- "NetworkPharmacology"
required_score <- 900L
ov <- np_read_contract(data_dir, "overlap")
genes_ov <- unique(as.character(ov$gene))
genes_ov <- genes_ov[!is.na(genes_ov) & nzchar(genes_ov)]
ppi_cache <- file.path(data_dir, "19_PPI互作_StringInteractions_score900.tsv")
ppi_live <- np_fetch_string_ppi(genes_ov, species = 9606L, required_score = required_score, cache_path = ppi_cache)
string_ids <- attr(ppi_live, "string_ids")

stem13 <- delivery_stem(skill_en, "network", "StringPPI", order = 13L)
png13 <- file.path(fig_dir, paste0(stem13, ".png"))
svg13 <- file.path(fig_dir, paste0(stem13, ".svg"))
ok13 <- FALSE
err <- NA_character_
tryCatch({
  np_fetch_string_network_image(
    genes_ov, out_path = png13, species = 9606L, required_score = required_score,
    network_flavor = "evidence", hide_disconnected_nodes = TRUE,
    block_structure_pics = FALSE, show_query_node_labels = TRUE,
    format = "highres_image", string_ids = string_ids, timeout = 180
  )
  if (file.exists(png13) && file.info(png13)$size > 1000) {
    ok13 <- TRUE
    tryCatch({
      Sys.sleep(1)
      np_fetch_string_network_image(
        genes_ov, out_path = svg13, species = 9606L, required_score = required_score,
        network_flavor = "evidence", hide_disconnected_nodes = TRUE,
        block_structure_pics = FALSE, show_query_node_labels = TRUE,
        format = "svg", string_ids = string_ids, timeout = 180
      )
    }, error = function(e) NULL)
  }
}, error = function(e) err <<- conditionMessage(e))

status <- c(
  "STATUS: rebuild",
  paste0("fig13_string_official=", ok13),
  if (!ok13) paste0("fig13_note=BLOCKED_EXTERNAL ", err) else "fig13_note=OK",
  "fig14_15=DONE topDegree<=200",
  "output_dir=努力学习项目/网络药理学/代码文件/结果文件 (not Desktop)"
)
writeLines(status, file.path(rep_dir, "STATUS.txt"), useBytes = TRUE)
message(paste(status, collapse = "\n"))
