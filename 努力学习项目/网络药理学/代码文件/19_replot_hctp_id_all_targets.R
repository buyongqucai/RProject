# Rebuild HCTP 11+12 after sameN + canvas coupling.
options(stringsAsFactors = FALSE)
work_root <- "E:/RProject/努力学习项目/网络药理学"
stopifnot(!grepl("Desktop|桌面", normalizePath(work_root, winslash = "/", mustWork = FALSE)))
project_root <- "E:/RProject"
bio_root <- file.path(project_root, "生信分析技能_BioinformaticsSkills")
skill_root <- file.path(bio_root, "03_药物计算_DrugDiscovery", "网络药理学_NetworkPharmacology")
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
# Pitch/spacing live in data coords; huge inches × FIG_DPI=600 stalls ggsave.
# Keep a large-but-printable canvas and lower DPI for HCTP raster only.
w <- 20; h <- 18
FIG_DPI <<- 300L
if (requireNamespace("showtext", quietly = TRUE)) {
  try(showtext::showtext_opts(dpi = 300L), silent = TRUE)
}

message("=== 11 columns sameN ===")
p11 <- np_plot_hctp_network(
  net, type_df, pathway_mode = "columns",
  pathway_label_mode = "id", label_all_targets = TRUE,
  plot_width_in = w, plot_height_in = h
)
delivery_save_plot(p11, skill_en, "network", "HerbCompoundTargetPathway", w, h, fig_dir, bio_root, order = 11L)
message("OK 11")

message("=== 12 ellipse sameN ===")
p12 <- np_plot_hctp_network(
  net, type_df, pathway_mode = "ellipse",
  pathway_label_mode = "id", label_all_targets = TRUE,
  plot_width_in = w, plot_height_in = h
)
delivery_save_plot(p12, skill_en, "network", "HerbCompoundTargetPathway_Ellipse", w, h, fig_dir, bio_root, order = 12L)
message("OK 12")
message("DONE HCTP sameN+canvas")
