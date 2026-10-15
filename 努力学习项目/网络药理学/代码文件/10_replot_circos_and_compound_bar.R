# Regenerate fig 04 + 10 after skill plot tweaks
options(stringsAsFactors = FALSE)
project_root <- "E:/RProject"
bio_root <- file.path(project_root, "生信分析技能_BioinformaticsSkills")
skill_root <- file.path(bio_root, "03_药物计算_DrugDiscovery", "网络药理学_NetworkPharmacology")
work_root <- file.path(project_root, "努力学习项目", "网络药理学")
data_dir <- file.path(work_root, "数据文件")
fig_dir <- file.path(work_root, "代码文件", "结果文件", "图片文件")
tab_dir <- file.path(work_root, "代码文件", "结果文件", "数据文件")

source(file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                 "脚本_scripts", "出版级出图_PublicationPlot.R"), encoding = "UTF-8")
qa <- file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                "脚本_scripts", "出图后审核_PlotQA.R")
if (file.exists(qa)) source(qa, encoding = "UTF-8")
source(file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards",
                 "脚本_scripts", "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
for (sf in list.files(file.path(skill_root, "脚本_scripts"), pattern = "[.][Rr]$", full.names = TRUE)) {
  source(sf, encoding = "UTF-8")
}
skill_en <- "NetworkPharmacology"

# --- 04 compound overlap equal panels ---
sum_path <- file.path(tab_dir, "07_成分疾病交集汇总_CompoundDiseaseOverlapSummary.csv")
if (!file.exists(sum_path)) {
  # rebuild from contracts if needed
  ct_df <- np_read_contract(data_dir, "compound_targets")
  ov <- np_read_contract(data_dir, "overlap")
  rename_df <- np_read_contract(data_dir, "compound_rename", required = FALSE)
  hc_df <- np_read_contract(data_dir, "herb_compound_edges", required = FALSE)
  edges <- np_build_compound_disease_overlap_edges(ct_df, ov, rename_map = rename_df, herb_compound_edges = hc_df)
  sum_df <- np_summarize_compound_overlap(edges)
  utils::write.csv(sum_df, sum_path, row.names = FALSE, fileEncoding = "UTF-8")
} else {
  sum_df <- utils::read.csv(sum_path, stringsAsFactors = FALSE, check.names = FALSE, fileEncoding = "UTF-8")
}
p04 <- np_plot_compound_overlap_panels(sum_df, target_per = 12L, max_per = 14L)
h04 <- np_compound_overlap_panels_height(sum_df, target_per = 12L, max_per = 14L)
h04 <- min(max(h04, 10), 28)
# fixed axis-l + panel widths need enough canvas (~2.6+2.8 per column × 2)
delivery_save_plot(p04, skill_en, "bar", "CompoundDiseaseOverlap", 16, h04, fig_dir, bio_root, order = 4L)
message("OK 04")

# --- 05 by herb (same aligned panel rule) ---
edges_path <- file.path(tab_dir, "06_成分疾病交集靶点_CompoundDiseaseOverlapTargets.csv")
if (file.exists(edges_path)) {
  edges <- utils::read.csv(edges_path, stringsAsFactors = FALSE, check.names = FALSE, fileEncoding = "UTF-8")
  p05 <- np_plot_compound_overlap_by_herb(edges, target_per = 12L, max_per = 14L)
  h05 <- np_compound_overlap_by_herb_height(edges, target_per = 12L, max_per = 14L)
  h05 <- min(max(h05, 10), 32)
  delivery_save_plot(p05, skill_en, "bar", "CompoundDiseaseOverlapByHerb", 16, h05, fig_dir, bio_root, order = 5L)
  message("OK 05")
}

# --- 10 KEGG circos ---
kegg <- np_read_contract(data_dir, "kegg")
if (!"term" %in% names(kegg) && "Description" %in% names(kegg)) kegg$term <- kegg$Description
circ_stem <- delivery_stem(skill_en, "circos", "KEGG", order = 10L)
out <- np_save_kegg_chord(
  kegg, out_dir = fig_dir, stem = circ_stem,
  top_n = 15, label_genes = TRUE, width = 13, height = 11,
  dpi = if (exists("FIG_DPI")) FIG_DPI else 600L
)
message("OK 10 ", out$png)
message("DONE")
