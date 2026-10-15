# Safe HCTP-only replot (11/12). Writes ONLY under 代码文件/结果文件/图片文件.
# Does not modify 数据文件/, Desktop, or git.
options(stringsAsFactors = FALSE)
stopifnot(!grepl("Desktop|桌面", normalizePath("E:/RProject/努力学习项目/网络药理学", winslash = "/", mustWork = FALSE)))

project_root <- "E:/RProject"
bio_root <- file.path(project_root, "生信分析技能_BioinformaticsSkills")
skill_root <- file.path(bio_root, "03_药物计算_DrugDiscovery", "网络药理学_NetworkPharmacology")
work_root <- file.path(project_root, "努力学习项目", "网络药理学")
data_dir <- file.path(work_root, "数据文件")
fig_dir <- file.path(work_root, "代码文件", "结果文件", "图片文件")
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

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
net <- np_read_contract(data_dir, "network")
type_df <- np_read_contract(data_dir, "type_table")
kegg_df <- utils::read.csv(file.path(data_dir, "富集KEGG_TopPathways.csv"),
                           stringsAsFactors = FALSE, check.names = FALSE, fileEncoding = "UTF-8")
pw_map <- stats::setNames(as.character(kegg_df$term), as.character(kegg_df$ID))
stopifnot(length(pw_map) > 0, nrow(net) > 0, nrow(type_df) > 0)

# Write to temp then rename would be ideal; delivery_save_plot writes final stems.
# Remove only incomplete same-stem outputs first (already cleaned zero-byte).
message("=== 11 columns ===")
p11 <- np_plot_hctp_network(net, type_df, pathway_mode = "columns", pathway_names = pw_map,
                            plot_width_in = 18.5, plot_height_in = 16.5)
delivery_save_plot(p11, skill_en, "network", "HerbCompoundTargetPathway", 18.5, 16.5, fig_dir, bio_root, order = 11L)
# sanity: refuse leave zero-byte
stem11 <- delivery_stem(skill_en, "network", "HerbCompoundTargetPathway", order = 11L)
for (ext in c(".png", ".svg")) {
  f <- file.path(fig_dir, paste0(stem11, ext))
  stopifnot(file.exists(f), file.info(f)$size > 1000)
}
message("OK 11 size png=", file.info(file.path(fig_dir, paste0(stem11, ".png")))$size)

message("=== 12 ellipse ===")
p12 <- np_plot_hctp_network(net, type_df, pathway_mode = "ellipse", pathway_names = pw_map,
                            plot_width_in = 18.5, plot_height_in = 16.5)
delivery_save_plot(p12, skill_en, "network", "HerbCompoundTargetPathway_Ellipse", 18.5, 16.5, fig_dir, bio_root, order = 12L)
stem12 <- delivery_stem(skill_en, "network", "HerbCompoundTargetPathway_Ellipse", order = 12L)
for (ext in c(".png", ".svg")) {
  f <- file.path(fig_dir, paste0(stem12, ext))
  stopifnot(file.exists(f), file.info(f)$size > 1000)
}
message("OK 12 size png=", file.info(file.path(fig_dir, paste0(stem12, ".png")))$size)
message("DONE HCTP")
