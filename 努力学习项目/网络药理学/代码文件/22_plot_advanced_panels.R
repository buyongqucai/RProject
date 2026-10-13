# Fig 16 UpSet / 17 complete Sankey / 18 Top-16 4×4 panels
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
source(file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards",
                 "脚本_scripts", "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
script_files <- list.files(file.path(skill_root, "脚本_scripts"), pattern = "[.][Rr]$", full.names = TRUE)
delivery_sf <- grep("04_交付网络布局", script_files, value = TRUE)
adv_sf <- grep("05_高级附图", script_files, value = TRUE)
for (sf in c(setdiff(script_files, c(delivery_sf, adv_sf)), delivery_sf, adv_sf)) {
  source(sf, encoding = "UTF-8")
}

skill_en <- "NetworkPharmacology"
net <- np_read_contract(data_dir, "network")
type_df <- np_read_contract(data_dir, "type_table")
rename_df <- np_read_contract(data_dir, "compound_rename", required = FALSE)
herb_comp <- np_read_contract(data_dir, "herb_compound_edges", required = FALSE)

FIG_DPI <<- 300L
if (requireNamespace("showtext", quietly = TRUE)) {
  try(showtext::showtext_opts(dpi = 300L), silent = TRUE)
}

message("=== 16 UpSet ===")
mem_c <- .np_herb_compound_membership(rename_df = rename_df, herb_comp_df = herb_comp)
.np_save_upset_pub(
  mem_c,
  stem = delivery_stem(skill_en, "upset", "HerbCompound", order = 16L),
  width = 12, height = 7.5, out_dir = fig_dir,
  title = "Herb–compound set intersections", nintersects = 35L, dpi = 300L
)

message("=== 17 filtered overview Sankey ===")
p17 <- np_plot_hctp_sankey(
  net, type_df,
  title = "Herb–compound–target–pathway flow",
  max_compounds = 22L, max_targets = 24L, max_pathways = 15L,
  soft_floor_comp = TRUE, label_size = 3.3, layout = "compact"
)
delivery_save_plot(
  p17, skill_en, "sankey", "HerbCompoundTargetPathway",
  16L, 12L, fig_dir, bio_root, order = 17L
)

message("=== 18 Top-16 4x4 ===")
p18 <- np_plot_hctp_sankey_by_compound(
  net, type_df,
  title = "Top-16 compounds · per-compound panels (4×4)",
  n_compounds = 16L, max_targets = 12L, max_pathways = 8L,
  label_size = 2.6, ncol = 4L
)
delivery_save_plot(
  p18, skill_en, "sankey", "PerCompound_Filtered",
  attr(p18, "suggest_width"), attr(p18, "suggest_height"),
  fig_dir, bio_root, order = 18L
)
message("DONE 16–18")
