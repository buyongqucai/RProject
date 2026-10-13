# Safe PPI replot (13/14/15). Uses local STRING cache; writes only under 结果文件.
# Does not modify 数据文件 raw tables (except optional result copy under 结果/数据文件).
# Does not write Desktop / git.
options(stringsAsFactors = FALSE)
work_root <- "E:/RProject/努力学习项目/网络药理学"
stopifnot(!grepl("Desktop|桌面", normalizePath(work_root, winslash = "/", mustWork = FALSE)))

project_root <- "E:/RProject"
bio_root <- file.path(project_root, "生信分析技能_BioinformaticsSkills")
skill_root <- file.path(bio_root, "03_药物计算_DrugDiscovery", "网络药理学_NetworkPharmacology")
data_dir <- file.path(work_root, "数据文件")
fig_dir <- file.path(work_root, "代码文件", "结果文件", "图片文件")
tab_dir <- file.path(work_root, "代码文件", "结果文件", "数据文件")
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(tab_dir, recursive = TRUE, showWarnings = FALSE)

source(file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                 "脚本_scripts", "出版级出图_PublicationPlot.R"), encoding = "UTF-8")
qa <- file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                "脚本_scripts", "出图后审核_PlotQA.R")
if (file.exists(qa)) source(qa, encoding = "UTF-8")
source(file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards",
                 "脚本_scripts", "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
script_files <- list.files(file.path(skill_root, "脚本_scripts"), pattern = "[.][Rr]$", full.names = TRUE)
delivery_sf <- grep("04_交付网络布局", script_files, value = TRUE)
for (sf in c(setdiff(script_files, delivery_sf), delivery_sf)) source(sf, encoding = "UTF-8")

skill_en <- "NetworkPharmacology"
required_score <- 900L
ov <- np_read_contract(data_dir, "overlap")
genes_ov <- unique(as.character(ov$gene))
genes_ov <- genes_ov[!is.na(genes_ov) & nzchar(genes_ov)]
stopifnot(length(genes_ov) > 10)

ppi_cache <- file.path(data_dir, "19_PPI互作_StringInteractions_score900.tsv")
stopifnot(file.exists(ppi_cache))  # prefer cache; avoid unexpected network if missing? allow fetch
message("PPI cache exists: ", ppi_cache)

ppi_live <- np_fetch_string_ppi(
  genes_ov, species = 9606L, required_score = required_score, cache_path = ppi_cache
)
stopifnot(!is.null(ppi_live), nrow(ppi_live) > 0)
string_ids <- attr(ppi_live, "string_ids")

# result-side copy only (not overwriting unrelated raw)
utils::write.table(
  ppi_live, file.path(tab_dir, "19_PPI互作_StringInteractions_score900.tsv"),
  sep = "\t", row.names = FALSE, quote = FALSE, fileEncoding = "UTF-8"
)

stem13 <- delivery_stem(skill_en, "network", "StringPPI", order = 13L)
png13 <- file.path(fig_dir, paste0(stem13, ".png"))
svg13 <- file.path(fig_dir, paste0(stem13, ".svg"))
message("=== 13 official STRING image ===")
tryCatch({
  np_fetch_string_network_image(
    genes_ov, out_path = png13, species = 9606L, required_score = required_score,
    network_flavor = "evidence", hide_disconnected_nodes = TRUE,
    block_structure_pics = FALSE, show_query_node_labels = TRUE,
    format = "highres_image", string_ids = string_ids, timeout = 360
  )
  stopifnot(file.exists(png13), file.info(png13)$size > 1000)
  message("OK 13 png=", file.info(png13)$size)
  tryCatch({
    Sys.sleep(1)
    np_fetch_string_network_image(
      genes_ov, out_path = svg13, species = 9606L, required_score = required_score,
      network_flavor = "evidence", hide_disconnected_nodes = TRUE,
      block_structure_pics = FALSE, show_query_node_labels = TRUE,
      format = "svg", string_ids = string_ids, timeout = 360
    )
  }, error = function(e) message("13 svg optional fail: ", conditionMessage(e)))
}, error = function(e) {
  message("13 FAIL (non-fatal for 14/15): ", conditionMessage(e))
})

message("=== 14/15 concentric topDegree<=200 ===")
p_ppi <- np_plot_string_ppi(
  ppi_live, min_score = required_score, drop_isolates = TRUE,
  layout = "concentric", label_top_n = NULL, outer_frac = 0.50, max_nodes = 200L
)
delivery_save_plot(p_ppi, skill_en, "network", "StringPPI_Concentric", 11.5, 10.5, fig_dir, bio_root, order = 14L)
delivery_save_plot(p_ppi, skill_en, "network", "StringPPI_Degree", 11.5, 10.5, fig_dir, bio_root, order = 15L)
for (ord in c(14L, 15L)) {
  th <- if (ord == 14L) "StringPPI_Concentric" else "StringPPI_Degree"
  st <- delivery_stem(skill_en, "network", th, order = ord)
  for (ext in c(".png", ".svg")) {
    f <- file.path(fig_dir, paste0(st, ext))
    stopifnot(file.exists(f), file.info(f)$size > 1000)
  }
}
message("DONE PPI")
