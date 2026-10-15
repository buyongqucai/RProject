# 清风项目 · 图谱套件出图 03：HCTP columns(11)/ellipse(12) + PPI Degree(15)/Concentric(14)
# 接线自样例 03_regen_hctp_layouts.R；布局 SSOT = 04_交付网络布局_DeliveryNetworkLayouts.R
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
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(tab_dir, recursive = TRUE, showWarnings = FALSE)

scripts_dir <- file.path(skill_root, "脚本_scripts")
script_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
# Delivery layouts must win over 03_* plot helpers
delivery_sf <- grep("04_交付网络布局", script_files, value = TRUE)
for (sf in c(setdiff(script_files, delivery_sf), delivery_sf)) {
  try(source(sf, encoding = "UTF-8"), silent = TRUE)
}
if (exists("setup_cjk_fonts")) setup_cjk_fonts()

skill_en <- "NetworkPharmacology"
net <- np_read_contract(data_dir, "network")
type_df <- np_read_contract(data_dir, "type_table")
message("Loaded network rows=", nrow(net), " type rows=", nrow(type_df))

# --- A) columns HCTP (Fig 11) ---
p_col <- np_plot_hctp_network(net, type_df, pathway_mode = "columns")
delivery_save_plot(p_col, skill_en, "network", "HerbCompoundTargetPathway",
                   18.5, 16.5, fig_dir, bio_root, order = 11)
message("Saved columns HCTP")

# --- B) ellipse HCTP (Fig 12) ---
p_ell <- np_plot_hctp_network(net, type_df, pathway_mode = "ellipse")
delivery_save_plot(p_ell, skill_en, "network", "HerbCompoundTargetPathway_Ellipse",
                   18.5, 16.5, fig_dir, bio_root, order = 12)
message("Saved ellipse HCTP")

# --- C) STRING PPI Degree (15) + Concentric alias (14) ---
ppi_candidates <- c(
  file.path(data_dir, "19_PPI互作_StringInteractions_score900.tsv"),
  file.path(data_dir, "PPI互作_StringInteractions_score900.tsv"),
  file.path(data_dir, "PPI互作_StringInteractions.tsv"),
  file.path(tab_dir, "19_PPI互作_StringInteractions_score900.tsv")
)
ppi_candidates <- unique(ppi_candidates[file.exists(ppi_candidates)])
pref <- grep("score900", ppi_candidates, value = TRUE)
if (length(pref)) ppi_candidates <- c(pref, setdiff(ppi_candidates, pref))
ppi <- NULL
if (length(ppi_candidates)) {
  message("Loading PPI: ", ppi_candidates[[1]])
  ppi <- tryCatch(
    utils::read.delim(ppi_candidates[[1]], stringsAsFactors = FALSE, check.names = FALSE),
    error = function(e) { message("PPI read failed: ", conditionMessage(e)); NULL }
  )
} else {
  message("No local PPI TSV found")
}

if (!is.null(ppi) && nrow(ppi) > 0) {
  p_ppi <- np_plot_string_ppi(ppi, min_score = 900L, drop_isolates = TRUE,
                              layout = "concentric", label_top_n = NULL, outer_frac = 0.50)
  delivery_save_plot(p_ppi, skill_en, "network", "StringPPI_Degree", 11.5, 10.5, fig_dir, bio_root, order = 15)
  delivery_save_plot(p_ppi, skill_en, "network", "StringPPI_Concentric", 11.5, 10.5, fig_dir, bio_root, order = 14)
  message("Saved PPI Degree + Concentric")
} else {
  message("SKIP PPI regen — no PPI table available")
}

message("DONE")
