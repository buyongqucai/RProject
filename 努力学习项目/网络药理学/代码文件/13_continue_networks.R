# Continue atlas: 12 HCTP ellipse + 13/14/15 STRING (after interrupted 06)
options(stringsAsFactors = FALSE)
project_root <- "E:/RProject"
bio_root <- file.path(project_root, "生信分析技能_BioinformaticsSkills")
skill_root <- file.path(bio_root, "03_药物计算_DrugDiscovery", "网络药理学_NetworkPharmacology")
work_root <- file.path(project_root, "努力学习项目", "网络药理学")
data_dir <- file.path(work_root, "数据文件")
fig_dir <- file.path(work_root, "代码文件", "结果文件", "图片文件")
tab_dir <- file.path(work_root, "代码文件", "结果文件", "数据文件")
rep_dir <- file.path(work_root, "代码文件", "结果文件", "报告文件")
for (d in c(fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

source(file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                 "脚本_scripts", "出版级出图_PublicationPlot.R"), encoding = "UTF-8")
qa <- file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                "脚本_scripts", "出图后审核_PlotQA.R")
if (file.exists(qa)) source(qa, encoding = "UTF-8")
source(file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards",
                 "脚本_scripts", "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
script_files <- list.files(file.path(skill_root, "脚本_scripts"), pattern = "[.][Rr]$", full.names = TRUE)
delivery_sf <- grep("04_交付网络布局", script_files, value = TRUE)
other_sf <- setdiff(script_files, delivery_sf)
for (sf in c(other_sf, delivery_sf)) source(sf, encoding = "UTF-8")
library(ggplot2)
if (exists("setup_cjk_fonts")) setup_cjk_fonts()

skill_en <- "NetworkPharmacology"
required_score <- 900L
notes <- character()

save_fig <- function(plot, type, theme, w, h, order) {
  delivery_save_plot(plot, skill_en, type, theme, w, h, fig_dir, bio_root, order = order)
}

net <- np_read_contract(data_dir, "network")
type_df <- np_read_contract(data_dir, "type_table")
ov <- np_read_contract(data_dir, "overlap")
kegg_df <- utils::read.csv(file.path(data_dir, "富集KEGG_TopPathways.csv"),
                           stringsAsFactors = FALSE, check.names = FALSE, fileEncoding = "UTF-8")
pw_map <- stats::setNames(as.character(kegg_df$term), as.character(kegg_df$ID))

message("=== 11/12 HCTP ===")
p_col <- np_plot_hctp_network(net, type_df, pathway_mode = "columns", pathway_names = pw_map,
                              plot_width_in = 18.5, plot_height_in = 16.5)
save_fig(p_col, "network", "HerbCompoundTargetPathway", 18.5, 16.5, 11L)
message("OK 11")
p_ell <- np_plot_hctp_network(net, type_df, pathway_mode = "ellipse", pathway_names = pw_map,
                              plot_width_in = 18.5, plot_height_in = 16.5)
save_fig(p_ell, "network", "HerbCompoundTargetPathway_Ellipse", 18.5, 16.5, 12L)
message("OK 12")

message("=== 13/14/15 STRING ===")
genes_ov <- unique(as.character(ov$gene))
genes_ov <- genes_ov[!is.na(genes_ov) & nzchar(genes_ov)]
ppi_cache <- file.path(data_dir, "19_PPI互作_StringInteractions_score900.tsv")
ppi_live <- np_fetch_string_ppi(genes_ov, species = 9606L, required_score = required_score, cache_path = ppi_cache)
string_ids <- attr(ppi_live, "string_ids")
utils::write.table(ppi_live, file.path(tab_dir, "19_PPI互作_StringInteractions_score900.tsv"),
                   sep = "\t", row.names = FALSE, quote = FALSE, fileEncoding = "UTF-8")

stem13 <- delivery_stem(skill_en, "network", "StringPPI", order = 13L)
png13 <- file.path(fig_dir, paste0(stem13, ".png"))
svg13 <- file.path(fig_dir, paste0(stem13, ".svg"))
tryCatch({
  np_fetch_string_network_image(
    genes_ov, out_path = png13, species = 9606L, required_score = required_score,
    network_flavor = "evidence", hide_disconnected_nodes = TRUE,
    block_structure_pics = FALSE, show_query_node_labels = TRUE,
    format = "highres_image", string_ids = string_ids, timeout = 360
  )
  tryCatch({
    Sys.sleep(1)
    np_fetch_string_network_image(
      genes_ov, out_path = svg13, species = 9606L, required_score = required_score,
      network_flavor = "evidence", hide_disconnected_nodes = TRUE,
      block_structure_pics = FALSE, show_query_node_labels = TRUE,
      format = "svg", string_ids = string_ids, timeout = 360
    )
  }, error = function(e) message("SVG skip: ", conditionMessage(e)))
  message("OK 13")
}, error = function(e) {
  notes <<- c(notes, conditionMessage(e))
  message("13 FAIL: ", conditionMessage(e))
})

p_ppi <- np_plot_string_ppi(
  ppi_live, min_score = required_score, drop_isolates = TRUE,
  layout = "concentric", label_top_n = NULL, outer_frac = 0.50, max_nodes = 200L
)
save_fig(p_ppi, "network", "StringPPI_Concentric", 11.5, 10.5, 14L)
save_fig(p_ppi, "network", "StringPPI_Degree", 11.5, 10.5, 15L)
message("OK 14/15")

writeLines(c("STATUS: continue_networks", notes), file.path(rep_dir, "STATUS_continue.txt"), useBytes = TRUE)
message("DONE")
