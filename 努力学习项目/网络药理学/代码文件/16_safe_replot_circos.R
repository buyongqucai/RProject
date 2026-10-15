# Safe circos-only: rewrite fig 10 under 结果文件/图片文件; no Desktop; keep SVG if regenerating both.
options(stringsAsFactors = FALSE)
work_root <- "E:/RProject/努力学习项目/网络药理学"
stopifnot(!grepl("Desktop|桌面", normalizePath(work_root, winslash = "/", mustWork = FALSE)))
project_root <- "E:/RProject"
bio_root <- file.path(project_root, "生信分析技能_BioinformaticsSkills")
skill_root <- file.path(bio_root, "03_药物计算_DrugDiscovery", "网络药理学_NetworkPharmacology")
data_dir <- file.path(work_root, "数据文件")
fig_dir <- file.path(work_root, "代码文件", "结果文件", "图片文件")

source(file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                 "脚本_scripts", "出版级出图_PublicationPlot.R"), encoding = "UTF-8")
source(file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards",
                 "脚本_scripts", "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
for (sf in list.files(file.path(skill_root, "脚本_scripts"), pattern = "[.][Rr]$", full.names = TRUE)) {
  source(sf, encoding = "UTF-8")
}

skill_en <- "NetworkPharmacology"
kegg <- np_read_contract(data_dir, "kegg")
if (!"term" %in% names(kegg) && "Description" %in% names(kegg)) kegg$term <- kegg$Description
circ_stem <- delivery_stem(skill_en, "circos", "KEGG", order = 10L)
out <- np_save_kegg_chord(
  kegg, out_dir = fig_dir, stem = circ_stem,
  top_n = 15, label_genes = TRUE, width = 13, height = 11,
  dpi = if (exists("FIG_DPI")) FIG_DPI else 600L
)
png <- out$png
svg <- out$svg
stopifnot(file.exists(png), file.info(png)$size > 1000)
stopifnot(is.na(svg) || (file.exists(svg) && file.info(svg)$size > 1000))
message("OK 10 png=", file.info(png)$size, " svg=", if (is.na(svg)) NA else file.info(svg)$size)
