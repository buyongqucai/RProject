# Fig19: Herb × pathway coverage heatmap + refresh polished Sankey 17
options(stringsAsFactors = FALSE)
work_root <- "E:/RProject/努力学习项目/网络药理学"
bio_root <- "E:/RProject/生信分析技能_BioinformaticsSkills"
skill_root <- file.path(bio_root, "03_药物计算_DrugDiscovery", "网络药理学_NetworkPharmacology")
data_dir <- file.path(work_root, "数据文件")
fig_dir <- file.path(work_root, "代码文件", "结果文件", "图片文件")

source(file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                 "脚本_scripts", "出版级出图_PublicationPlot.R"), encoding = "UTF-8")
source(file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards",
                 "脚本_scripts", "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
sfs <- list.files(file.path(skill_root, "脚本_scripts"), pattern = "[.][Rr]$", full.names = TRUE)
ds <- grep("04_交付", sfs, value = TRUE); asf <- grep("05_高级", sfs, value = TRUE)
for (sf in c(setdiff(sfs, c(ds, asf)), ds, asf)) source(sf, encoding = "UTF-8")

FIG_DPI <<- 300L
if (requireNamespace("showtext", quietly = TRUE)) {
  try(showtext::showtext_opts(dpi = 300L), silent = TRUE)
}

net <- np_read_contract(data_dir, "network")
type_df <- np_read_contract(data_dir, "type_table")

message("=== 17 polished overview Sankey ===")
p17 <- np_plot_hctp_sankey(
  net, type_df,
  title = "Herb–compound–target–pathway flow",
  max_compounds = 16L,
  max_targets = 16L,
  max_pathways = 12L,
  soft_floor_comp = TRUE,
  label_size = 3.8,
  layout = "compact"
)
delivery_save_plot(
  p17, "NetworkPharmacology", "sankey", "HerbCompoundTargetPathway",
  16, 11, fig_dir, bio_root, order = 17L
)
message("OK 17")

message("=== 19 Herb × pathway heatmap ===")
p19 <- np_plot_herb_pathway_heatmap(
  net, type_df,
  title = "Herb × pathway target coverage",
  max_pathways = 20L
)
delivery_save_plot(
  p19, "NetworkPharmacology", "heatmap", "HerbPathwayCoverage",
  12, 10, fig_dir, bio_root, order = 19L
)
message("OK 19 DONE")
