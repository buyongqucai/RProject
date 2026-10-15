# 清风项目 · 图谱套件出图 04：高级附图 16-19（FROZEN §E）
# 16 药味成分交集 UpSet / 17 药成分靶点通路桑基 / 18 筛选成分桑基(4x4) / 19 药味通路覆盖热图
# recipe 全部来自 05_高级附图_AdvancedPanels.R，本脚本只接线
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
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

scripts_dir <- file.path(skill_root, "脚本_scripts")
script_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
delivery_sf <- grep("04_交付网络布局", script_files, value = TRUE)
for (sf in c(setdiff(script_files, delivery_sf), delivery_sf)) {
  try(source(sf, encoding = "UTF-8"), silent = TRUE)
}
if (exists("setup_cjk_fonts")) setup_cjk_fonts()

skill_en <- "NetworkPharmacology"
net <- np_read_contract(data_dir, "network")
type_df <- np_read_contract(data_dir, "type_table")
rename_df <- np_read_contract(data_dir, "compound_rename")
hc_df <- np_read_contract(data_dir, "herb_compound_edges")
message("net=", nrow(net), " type=", nrow(type_df), " rename=", nrow(rename_df))

# --- 16 药味成分交集 UpSet（成员口径=化学成分名 × 药味） ---
rm_uni <- unique(rename_df[, c("compound_name", "herb_code")])
herb_codes <- sort(unique(rm_uni$herb_code))
comp_names <- sort(unique(rm_uni$compound_name))
memb <- as.data.frame(matrix(0L, nrow = length(comp_names), ncol = length(herb_codes)))
names(memb) <- herb_codes
rownames(memb) <- comp_names
for (i in seq_len(nrow(rm_uni))) {
  memb[rm_uni$compound_name[i], rm_uni$herb_code[i]] <- 1L
}
memb_df <- cbind(compound = rownames(memb), memb, stringsAsFactors = FALSE)
memb_mat <- memb
rownames(memb_mat) <- NULL
stem16 <- delivery_stem(skill_en, "upset", "HerbCompound", order = 16)
delivery_assert_name_ok(paste0(stem16, ".png"))
.np_save_upset_pub(memb_mat, stem = stem16, width = 11, height = 7, out_dir = fig_dir,
                   title = "Herb compound intersections", nintersects = 40L, dpi = 600L)
message("Saved ", stem16)

# --- 17 药成分靶点通路桑基（筛选总览） ---
p17 <- np_plot_hctp_sankey(net, type_df)
delivery_save_plot(p17, skill_en, "sankey", "HerbCompoundTargetPathway", 15.0, 11.0, fig_dir, bio_root, order = 17)
message("Saved sankey 17")

# --- 18 筛选成分桑基（前 16 成分 4x4 分面） ---
p18 <- np_plot_hctp_sankey_by_compound(net, type_df)
h18 <- if (exists("np_hctp_sankey_by_compound_height")) np_hctp_sankey_by_compound_height(net, type_df) else 15.0
delivery_save_plot(p18, skill_en, "sankey", "PerCompound_Filtered", 16.0, h18, fig_dir, bio_root, order = 18)
message("Saved sankey 18")

# --- 19 药味通路覆盖热图（Top20 通路，格子=交集靶点数） ---
p19 <- np_plot_herb_pathway_heatmap(net, type_df)
delivery_save_plot(p19, skill_en, "heatmap", "HerbPathwayCoverage", 11.0, 8.5, fig_dir, bio_root, order = 19)
message("Saved heatmap 19")

writeLines(
  c("advanced_panels=PASS",
    paste0("upset_members=", length(comp_names), " compounds x ", length(herb_codes), " herbs"),
    "16_upset=PASS", "17_sankey=PASS", "18_sankey_filtered=PASS", "19_heatmap=PASS"),
  file.path(dirname(fig_dir), "04_报告文件_Reports", "STATUS_advanced_panels.txt")
)
message("DONE advanced panels")
