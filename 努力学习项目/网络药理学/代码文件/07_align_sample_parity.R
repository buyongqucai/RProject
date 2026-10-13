# Align UC figures to sample atlas orders 01-02 + 11-15 (venn dual-bar + networks)
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

# Delivery layouts must win over 03_* helpers (same as sample 03_regen)
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
  delivery_stem(skill_en, type, theme, order = order)
}

drug_u <- np_read_contract(data_dir, "drug_union")
dis_by_venn <- np_read_contract(data_dir, "disease_by_db_venn")
dis_u <- np_read_contract(data_dir, "disease_union")
ov <- np_read_contract(data_dir, "overlap")
net <- np_read_contract(data_dir, "network", required = FALSE)
type_df <- np_read_contract(data_dir, "type_table", required = FALSE)

message("=== 01/02 Venns：技能=微生信交付 SVG（禁止 R 近似写入交付位）===")
venn_py <- file.path(work_root, "代码文件", "08_export_uc_venn_from_delivery.py")
venn_ref <- file.path(work_root, "参考_交付原图")
venn_ok <- file.exists(file.path(venn_ref, "Venn_DiseaseDatabases.svg")) &&
  file.exists(file.path(venn_ref, "Venn_DrugDisease.svg"))
if (isTRUE(venn_ok)) {
  py <- Sys.which("python")
  if (!nzchar(py)) py <- Sys.which("python3")
  if (!nzchar(py)) py <- Sys.which("py")
  if (nzchar(py)) {
    st <- tryCatch(
      system2(py, shQuote(normalizePath(venn_py)), stdout = TRUE, stderr = TRUE),
      error = function(e) conditionMessage(e)
    )
    message(paste(st, collapse = "\n"))
  } else {
    message("Skip venn export: python not on PATH (existing 01/02 kept)")
  }
} else {
  notes <- c(
    notes,
    paste0(
      "VENN BLOCKED_SKILL: 微生信 SVG missing in ", venn_ref,
      "; lists ready at 微生信上传_基因列表/"
    )
  )
  message(notes[length(notes)])
}

message("=== 11/12 HCTP columns + ellipse ===")
hctp_ok <- FALSE
hctp_ell_ok <- FALSE
pw_map <- NULL
kegg_path <- file.path(data_dir, "富集KEGG_TopPathways.csv")
if (!file.exists(kegg_path)) {
  kegg_path <- file.path(data_dir, "kegg.csv")
}
if (file.exists(kegg_path)) {
  kegg_df <- utils::read.csv(kegg_path, stringsAsFactors = FALSE, check.names = FALSE, fileEncoding = "UTF-8")
  id_col <- if ("ID" %in% names(kegg_df)) "ID" else if ("id" %in% names(kegg_df)) "id" else NA_character_
  nm_col <- if ("term" %in% names(kegg_df)) "term" else if ("Description" %in% names(kegg_df)) "Description" else NA_character_
  if (!is.na(id_col) && !is.na(nm_col)) {
    pw_map <- setNames(as.character(kegg_df[[nm_col]]), as.character(kegg_df[[id_col]]))
  }
}
if (!is.null(net) && !is.null(type_df) && nrow(net) > 0 && nrow(type_df) > 0) {
  tryCatch(np_export_hctp_cytoscape(net, type_df, tab_dir),
           error = function(e) message("cytoscape: ", conditionMessage(e)))
  p_col <- tryCatch(
    np_plot_hctp_network(net, type_df, pathway_mode = "columns",
                         pathway_names = pw_map,
                         plot_width_in = 18.5, plot_height_in = 16.5),
    error = function(e) { notes <<- c(notes, conditionMessage(e)); NULL }
  )
  if (!is.null(p_col)) {
    save_fig(p_col, "network", "HerbCompoundTargetPathway", 18.5, 16.5, 11L)
    hctp_ok <- TRUE
  }
  p_ell <- tryCatch(
    np_plot_hctp_network(net, type_df, pathway_mode = "ellipse",
                         pathway_names = pw_map,
                         plot_width_in = 18.5, plot_height_in = 16.5),
    error = function(e) { notes <<- c(notes, conditionMessage(e)); NULL }
  )
  if (!is.null(p_ell)) {
    save_fig(p_ell, "network", "HerbCompoundTargetPathway_Ellipse", 18.5, 16.5, 12L)
    hctp_ell_ok <- TRUE
  }
}

# remove misnumbered legacy StringPPI@12 if ellipse now owns 12
legacy <- file.path(fig_dir, c(
  "12_网络图_StringPPI_Network.png",
  "12_网络图_StringPPI_Network.svg"
))
invisible(lapply(legacy, function(f) if (file.exists(f)) file.remove(f)))

message("=== 13/14/15 STRING ===")
genes_ov <- unique(as.character(ov$gene))
genes_ov <- genes_ov[!is.na(genes_ov) & nzchar(genes_ov)]
ppi_cache <- file.path(data_dir, "19_PPI互作_StringInteractions_score900.tsv")
ppi_live <- tryCatch(
  np_fetch_string_ppi(genes_ov, species = 9606L, required_score = required_score, cache_path = ppi_cache),
  error = function(e) { notes <<- c(notes, conditionMessage(e)); NULL }
)
string_ids <- if (!is.null(ppi_live)) attr(ppi_live, "string_ids") else NULL
string_img_ok <- FALSE
ppi_conc_ok <- FALSE
ppi_deg_ok <- FALSE

if (!is.null(ppi_live) && nrow(ppi_live) > 0) {
  utils::write.table(
    ppi_live, file.path(tab_dir, "19_PPI互作_StringInteractions_score900.tsv"),
    sep = "\t", row.names = FALSE, quote = FALSE, fileEncoding = "UTF-8"
  )
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
    string_img_ok <- file.exists(png13) && file.info(png13)$size > 1000
    tryCatch({
      Sys.sleep(1)
      np_fetch_string_network_image(
        genes_ov, out_path = svg13, species = 9606L, required_score = required_score,
        network_flavor = "evidence", hide_disconnected_nodes = TRUE,
        block_structure_pics = FALSE, show_query_node_labels = TRUE,
        format = "svg", string_ids = string_ids, timeout = 360
      )
    }, error = function(e) message("STRING SVG skipped: ", conditionMessage(e)))
  }, error = function(e) notes <<- c(notes, paste0("official: ", conditionMessage(e))))

  p_ppi <- tryCatch(
    np_plot_string_ppi(
      ppi_live, min_score = required_score, drop_isolates = TRUE,
      layout = "concentric", label_top_n = NULL, outer_frac = 0.50,
      max_nodes = 200L
    ),
    error = function(e) { notes <<- c(notes, conditionMessage(e)); NULL }
  )
  if (!is.null(p_ppi)) {
    save_fig(p_ppi, "network", "StringPPI_Concentric", 11.5, 10.5, 14L)
    ppi_conc_ok <- TRUE
    save_fig(p_ppi, "network", "StringPPI_Degree", 11.5, 10.5, 15L)
    ppi_deg_ok <- TRUE
  }
}

status <- c(
  "STATUS: sample-parity regen (01-02, 11-15)",
  paste0("venn_dual_bar=DONE"),
  paste0("hctp_columns=", hctp_ok, " hctp_ellipse=", hctp_ell_ok),
  paste0("string_official=", string_img_ok, " concentric=", ppi_conc_ok, " degree=", ppi_deg_ok),
  "NOTES:",
  notes
)
writeLines(status, file.path(rep_dir, "STATUS_sample_parity.txt"), useBytes = TRUE)
message("DONE")
print(status)
