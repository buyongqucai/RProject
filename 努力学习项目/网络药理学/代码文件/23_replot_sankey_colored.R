# Optimize Fig17 overview Sankey (cleaner) + Fig18 4×4 panels
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

# --- 17: tighter overview ---
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

# --- 18: 4×4 ---
message("=== 18 Top-16 4×4 ===")
p18 <- np_plot_hctp_sankey_by_compound(
  net, type_df,
  title = "Top-16 compounds · per-compound panels (4×4)",
  n_compounds = 16L,
  max_targets = 10L,
  max_pathways = 6L,
  label_size = 2.8,
  ncol = 4L
)
delivery_save_plot(
  p18, "NetworkPharmacology", "sankey", "PerCompound_Filtered",
  18, 18, fig_dir, bio_root, order = 18L
)
message("OK 18 DONE")
