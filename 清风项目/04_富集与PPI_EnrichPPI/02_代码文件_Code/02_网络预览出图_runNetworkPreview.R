# 清风项目 · 图谱套件出图 02：STRING 官方网络图(13) + PPI 渐变兜底 + STATUS_network_preview
# 接线自样例 02_run_network_preview.R；recipe 在 03_STRING与网络图_StringNetwork.R
options(stringsAsFactors = FALSE)

skill_root <- "E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology"
bio_root <- "E:/RProject/生信分析技能_BioinformaticsSkills"
viz_script <- file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                        "脚本_scripts", "出版级出图_PublicationPlot.R")
if (file.exists(viz_script)) source(viz_script, encoding = "UTF-8")
delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")

data_dir <- "E:/RProject/清风项目/03_药病交集与网络_OverlapAndNetwork/01_数据文件_Data/02_结果数据_ResultTables/图谱契约数据_FigureContractData"
fig_dir <- "E:/RProject/清风项目/04_富集与PPI_EnrichPPI/03_图片文件_Figures"
tab_dir <- "E:/RProject/清风项目/04_富集与PPI_EnrichPPI/01_数据文件_Data/02_结果数据_ResultTables/图谱套件编号表_FigureSuiteTables"
rep_dir <- "E:/RProject/清风项目/04_富集与PPI_EnrichPPI/04_报告文件_Reports"
for (d in c(fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

scripts_dir <- file.path(skill_root, "脚本_scripts")
script_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
delivery_sf <- grep("04_交付网络布局", script_files, value = TRUE)
for (sf in c(setdiff(script_files, delivery_sf), delivery_sf)) {
  try(source(sf, encoding = "UTF-8"), silent = TRUE)
}
if (exists("setup_cjk_fonts")) setup_cjk_fonts()

skill_en <- "NetworkPharmacology"
required_score <- 900L

ov <- np_read_contract(data_dir, "overlap")
genes <- unique(as.character(ov$gene))
genes <- genes[!is.na(genes) & nzchar(genes)]
message("Overlap genes: ", length(genes), " · STRING required_score=", required_score)

ppi_cache <- file.path(data_dir, "19_PPI互作_StringInteractions_score900.tsv")
ppi_cache_out <- file.path(tab_dir, "19_PPI互作_StringInteractions_score900.tsv")

string_ok <- FALSE
image_ok <- FALSE
ppi <- NULL
string_err <- NULL
string_ids <- NULL

tryCatch({
  ppi <- np_fetch_string_ppi(
    genes, species = 9606L, required_score = required_score,
    cache_path = ppi_cache, force = !file.exists(ppi_cache)
  )
  string_ids <- attr(ppi, "string_ids")
  file.copy(ppi_cache, ppi_cache_out, overwrite = TRUE)
  string_ok <- is.data.frame(ppi) && nrow(ppi) > 0
  message("STRING edges @0.9: ", nrow(ppi))
}, error = function(e) {
  string_err <<- conditionMessage(e)
  legacy <- file.path(data_dir, "PPI互作_StringInteractions.tsv")
  if (file.exists(legacy)) {
    ppi <<- utils::read.delim(legacy, stringsAsFactors = FALSE, check.names = FALSE)
    string_ok <<- nrow(ppi) > 0
    message("Using legacy PPI cache (API failed: ", string_err, ")")
  }
})

stem_official <- delivery_stem(skill_en, "network", "StringPPI", order = 13)
png_official <- file.path(fig_dir, paste0(stem_official, ".png"))
svg_official <- file.path(fig_dir, paste0(stem_official, ".svg"))

tryCatch({
  np_fetch_string_network_image(
    genes, out_path = png_official, species = 9606L, required_score = required_score,
    network_flavor = "evidence", hide_disconnected_nodes = TRUE,
    block_structure_pics = FALSE, show_query_node_labels = TRUE,
    format = "highres_image", string_ids = string_ids, timeout = 360
  )
  image_ok <- file.exists(png_official) && file.info(png_official)$size > 1000
  tryCatch({
    Sys.sleep(1)
    np_fetch_string_network_image(
      genes, out_path = svg_official, species = 9606L, required_score = required_score,
      network_flavor = "evidence", hide_disconnected_nodes = TRUE,
      block_structure_pics = FALSE, show_query_node_labels = TRUE,
      format = "svg", string_ids = string_ids, timeout = 360
    )
  }, error = function(e) message("STRING SVG skipped: ", conditionMessage(e)))
}, error = function(e) {
  string_err <<- paste(c(string_err, conditionMessage(e)), collapse = " | ")
  message("STRING official image failed: ", conditionMessage(e))
})

stem_deg <- delivery_stem(skill_en, "network", "StringPPI_Degree", order = 15)
if (isTRUE(string_ok)) {
  tryCatch({
    p_ppi <- np_plot_string_ppi(ppi, min_score = required_score, drop_isolates = TRUE,
                                layout = "concentric", label_top_n = NULL)
    delivery_save_plot(p_ppi, skill_en, "network", "StringPPI_Degree", 11.5, 10.5, fig_dir, bio_root, order = 15)
    delivery_save_plot(p_ppi, skill_en, "network", "StringPPI_Concentric", 11.5, 10.5, fig_dir, bio_root, order = 14)
    message("Saved PPI degree gradient: ", stem_deg)
  }, error = function(e) message("R PPI degree plot failed: ", conditionMessage(e)))
} else {
  message("STRING PPI BLOCKED: ", string_err)
}

writeLines(
  c(
    paste0("STRING_PPI_official_image=", if (isTRUE(image_ok)) "PASS" else "BLOCKED_EXTERNAL"),
    paste0("STRING_PPI_degree_gradient=", if (file.exists(file.path(fig_dir, paste0(stem_deg, ".png")))) "PASS" else "FAIL"),
    paste0("required_score=", required_score),
    paste0("string_edges=", if (!is.null(ppi)) nrow(ppi) else 0),
    paste0("string_error=", if (is.null(string_err)) "" else string_err),
    "layout=PPI concentric Degree"
  ),
  file.path(rep_dir, "STATUS_network_preview.txt")
)
message("DONE — official=", image_ok, " edges=", string_ok)
