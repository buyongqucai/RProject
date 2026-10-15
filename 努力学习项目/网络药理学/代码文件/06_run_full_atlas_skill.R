# UC 全量图册 — 严格按 NetworkPharmacology §6 + PlotQA（防遮挡）
# 对齐 01_run_sample.R 图序；数据契约已由 04/05 脚本准备
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
# PlotQA is pulled by delivery_save_plot / publication plot
qa <- file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                "脚本_scripts", "出图后审核_PlotQA.R")
if (file.exists(qa)) source(qa, encoding = "UTF-8")

source(file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards",
                 "脚本_scripts", "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
for (sf in list.files(file.path(skill_root, "脚本_scripts"), pattern = "[.][Rr]$", full.names = TRUE)) {
  source(sf, encoding = "UTF-8")
}
library(ggplot2)
if (exists("setup_cjk_fonts")) setup_cjk_fonts()

skill_en <- "NetworkPharmacology"
fig_index <- list()
qa_notes <- character()

save_fig <- function(plot, type, theme, w, h, order, note = NULL) {
  # anti-occlusion: slightly wider/taller than sample when labels dense
  delivery_save_plot(plot, skill_en, type, theme, w, h, fig_dir, bio_root, order = order)
  stem <- delivery_stem(skill_en, type, theme, order = order)
  fig_index[[length(fig_index) + 1]] <<- data.frame(
    order = order, stem = stem, plot_type = type, theme = theme,
    note = if (is.null(note)) "" else note,
    stringsAsFactors = FALSE
  )
  invisible(stem)
}

# -------- load contracts --------
herb_targets <- np_read_all_herb_targets(data_dir)
herb_overlaps <- np_read_all_herb_overlaps(data_dir)
drug_u <- np_read_contract(data_dir, "drug_union")
dis_by_venn <- np_read_contract(data_dir, "disease_by_db_venn")
dis_u <- np_read_contract(data_dir, "disease_union")
ov <- np_read_contract(data_dir, "overlap")
sum_df <- np_read_contract(data_dir, "per_herb_summary")
go_df <- np_read_contract(data_dir, "go_bubble", required = FALSE)
kegg_df <- np_read_contract(data_dir, "kegg", required = FALSE)
ct_df <- np_read_contract(data_dir, "compound_targets", required = FALSE)
rename_df <- np_read_contract(data_dir, "compound_rename", required = FALSE)
hc_df <- np_read_contract(data_dir, "herb_compound_edges", required = FALSE)
net <- np_read_contract(data_dir, "network", required = FALSE)
type_df <- np_read_contract(data_dir, "type_table", required = FALSE)

# -------- 01/02 Venns：技能 SSOT = 微生信交付原图（与 01_run_sample.R 同路径）--------
# R np_plot_*_venn 仅为缺图回退，不得标 DONE
venn_py <- file.path(work_root, "代码文件", "08_export_uc_venn_from_delivery.py")
venn_ref <- file.path(work_root, "参考_交付原图")
venn_ok <- file.exists(file.path(venn_ref, "Venn_DiseaseDatabases.svg")) &&
  file.exists(file.path(venn_ref, "Venn_DrugDisease.svg"))
if (isTRUE(venn_ok) && file.exists(venn_py)) {
  py <- Sys.which("python")
  if (!nzchar(py)) py <- Sys.which("python3")
  if (!nzchar(py)) py <- Sys.which("py")
  if (!nzchar(py) && file.exists("E:/python3.13.14/python.exe")) {
    py <- "E:/python3.13.14/python.exe"
  }
  fig01 <- file.path(fig_dir, paste0(delivery_stem(skill_en, "venn", "DiseaseDatabases", order = 1), ".svg"))
  fig02 <- file.path(fig_dir, paste0(delivery_stem(skill_en, "venn", "DrugDisease", order = 2), ".svg"))
  if (file.exists(fig01) && file.exists(fig02)) {
    message("Venn already present; skip python export")
  } else if (!nzchar(py)) {
    stop("需要 python 以导出微生信韦恩交付图")
  } else {
    st <- system2(py, shQuote(normalizePath(venn_py)), stdout = TRUE, stderr = TRUE)
    message(paste(st, collapse = "\n"))
  }
  fig_index[[length(fig_index) + 1]] <- data.frame(
    order = 1, stem = delivery_stem(skill_en, "venn", "DiseaseDatabases", order = 1),
    plot_type = "venn", theme = "DiseaseDatabases",
    note = "微生信交付 SVG via 08/09",
    stringsAsFactors = FALSE
  )
  fig_index[[length(fig_index) + 1]] <- data.frame(
    order = 2, stem = delivery_stem(skill_en, "venn", "DrugDisease", order = 2),
    plot_type = "venn", theme = "DrugDisease",
    note = "微生信交付 SVG via 08/09",
    stringsAsFactors = FALSE
  )
} else {
  qa_notes <- c(
    qa_notes,
    paste0(
      "VENN BLOCKED_SKILL: put 微生信 SVG in ", venn_ref,
      " then run 08_export_uc_venn_from_delivery.py; ",
      "gene lists ready at 微生信上传_基因列表/; R approx is NOT delivery"
    )
  )
  # 可选：仅调试时画 R 近似，写入 _归档，不覆盖交付位
  message("Skip writing R Venns to 图片文件 (skill: delivery SVG required)")
}

# -------- 03 Per-herb bar (taller to reduce label overlap WARN) --------
p <- np_plot_per_herb_overlap(sum_df)
save_fig(p, "bar", "PerHerbDiseaseOverlap", 7.0, 6.0, 3L, "height+ for PlotQA label clearance")

# -------- 04/05 Compound overlap --------
ct_ov_edges <- NULL
ct_ov_sum <- NULL
if (!is.null(ct_df) && nrow(ct_df) > 0) {
  ct_ov_edges <- np_build_compound_disease_overlap_edges(
    ct_df, ov, rename_map = rename_df, herb_compound_edges = hc_df
  )
  ct_ov_sum <- np_summarize_compound_overlap(ct_ov_edges)
  utils::write.csv(ct_ov_edges, file.path(tab_dir, "06_成分疾病交集靶点_CompoundDiseaseOverlapTargets.csv"),
                   row.names = FALSE, fileEncoding = "UTF-8")
  utils::write.csv(ct_ov_sum, file.path(tab_dir, "07_成分疾病交集汇总_CompoundDiseaseOverlapSummary.csv"),
                   row.names = FALSE, fileEncoding = "UTF-8")
  # panels: auto height from skill helper
  p_ct <- np_plot_compound_overlap_panels(ct_ov_sum, target_per = 12L, max_per = 14L)
  h_ct <- np_compound_overlap_panels_height(ct_ov_sum, target_per = 12L, max_per = 14L)
  # cap height for file size but keep readable
  h_ct <- min(max(h_ct, 10), 28)
  save_fig(p_ct, "bar", "CompoundDiseaseOverlap", 16.0, h_ct, 4L, "equal axis-l+panel widths")

  p_ct_h <- np_plot_compound_overlap_by_herb(ct_ov_edges, target_per = 12L, max_per = 14L)
  h_ct_h <- np_compound_overlap_by_herb_height(ct_ov_edges, target_per = 12L, max_per = 14L)
  h_ct_h <- min(max(h_ct_h, 10), 32)
  save_fig(p_ct_h, "bar", "CompoundDiseaseOverlapByHerb", 16.0, h_ct_h, 5L, "equal axis-l+panel widths")
}

# -------- 06/07 GO (clusterProfiler table; wrap + taller canvas) --------
if (!is.null(go_df) && nrow(go_df) > 0) {
  # strip residual GO:IDs if any; lowercase
  go_df$term <- tolower(gsub("\\s*\\(GO:[0-9]+\\)\\s*$", "", as.character(go_df$term)))
  p <- np_plot_go_bubble(go_df, top_n = 8)
  save_fig(p, "bubble", "GO_BPCCMF", 11.0, 11.0, 6L, "top_n=8 + taller to avoid label clip")
  p <- np_plot_go_bar(go_df, top_n = 8)
  save_fig(p, "bar", "GO_BPCCMF", 12.0, 8.0, 7L)
}

# -------- 08/09 KEGG --------
if (!is.null(kegg_df) && nrow(kegg_df) > 0) {
  if (!"term" %in% names(kegg_df) && "Description" %in% names(kegg_df)) {
    kegg_df$term <- kegg_df$Description
  }
  p <- np_plot_kegg_lollipop(kegg_df, top_n = 20)
  save_fig(p, "lollipop", "KEGG_Pathways", 11.0, 9.0, 8L)
  p <- np_plot_kegg_bar(kegg_df, top_n = 20)
  save_fig(p, "bar", "KEGG_Pathways", 11.0, 9.0, 9L)

  # 10 circos
  if (requireNamespace("circlize", quietly = TRUE) &&
      any(c("geneID", "geneId") %in% names(kegg_df))) {
    circ_stem <- delivery_stem(skill_en, "circos", "KEGG", order = 10)
    delivery_assert_name_ok(paste0(circ_stem, ".png"))
    dpi_use <- if (exists("FIG_DPI")) FIG_DPI else 600L
    circ_out <- tryCatch(
      np_save_kegg_chord(
        kegg_df, out_dir = fig_dir, stem = circ_stem,
        top_n = 15, label_genes = TRUE, width = 13, height = 11, dpi = dpi_use
      ),
      error = function(e) {
        qa_notes <<- c(qa_notes, paste0("KEGG circos FAIL: ", conditionMessage(e)))
        NULL
      }
    )
    if (!is.null(circ_out) && file.exists(circ_out$png)) {
      fig_index[[length(fig_index) + 1]] <- data.frame(
        order = 10, stem = circ_stem, plot_type = "circos", theme = "KEGG",
        note = "circlize; gene labels on (watch occlusion WARN)",
        stringsAsFactors = FALSE
      )
    }
  } else {
    qa_notes <- c(qa_notes, "KEGG circos skipped: no circlize or geneID")
  }
}

# -------- 11/12 HCTP（对齐样例：columns=11 + ellipse=12）--------
hctp_ok <- FALSE
hctp_ell_ok <- FALSE
pw_map <- NULL
kegg_path <- file.path(data_dir, "富集KEGG_TopPathways.csv")
if (file.exists(kegg_path)) {
  kegg_nm <- utils::read.csv(kegg_path, stringsAsFactors = FALSE, check.names = FALSE, fileEncoding = "UTF-8")
  if (all(c("ID", "term") %in% names(kegg_nm))) {
    pw_map <- stats::setNames(as.character(kegg_nm$term), as.character(kegg_nm$ID))
  }
}
if (!is.null(net) && !is.null(type_df) && nrow(net) > 0 && nrow(type_df) > 0) {
  tryCatch({
    cyto <- np_export_hctp_cytoscape(net, type_df, tab_dir)
  }, error = function(e) message("cytoscape export: ", conditionMessage(e)))

  p_hctp <- tryCatch(
    np_plot_hctp_network(
      net, type_df,
      pathway_mode = "columns",
      pathway_names = pw_map,
      plot_width_in = 18.5,
      plot_height_in = 16.5
    ),
    error = function(e) {
      qa_notes <<- c(qa_notes, paste0("HCTP columns FAIL: ", conditionMessage(e)))
      NULL
    }
  )
  if (!is.null(p_hctp)) {
    save_fig(p_hctp, "network", "HerbCompoundTargetPathway", 18.5, 16.5, 11L, "columns = sample order 11")
    hctp_ok <- TRUE
  }

  p_ell <- tryCatch(
    np_plot_hctp_network(
      net, type_df,
      pathway_mode = "ellipse",
      pathway_names = pw_map,
      plot_width_in = 18.5,
      plot_height_in = 16.5
    ),
    error = function(e) {
      qa_notes <<- c(qa_notes, paste0("HCTP ellipse FAIL: ", conditionMessage(e)))
      NULL
    }
  )
  if (!is.null(p_ell)) {
    save_fig(p_ell, "network", "HerbCompoundTargetPathway_Ellipse", 18.5, 16.5, 12L, "ellipse = sample order 12")
    hctp_ell_ok <- TRUE
  }
} else {
  qa_notes <- c(qa_notes, "HCTP skipped: missing network/type")
}

# -------- 13/14/15 STRING（对齐样例：官方图 + Concentric + Degree）--------
ppi_ok <- FALSE
string_img_ok <- FALSE
ppi_conc_ok <- FALSE
ppi_deg_ok <- FALSE
required_score <- 900L
genes_ov <- unique(as.character(ov$gene))
genes_ov <- genes_ov[!is.na(genes_ov) & nzchar(genes_ov)]
ppi_cache <- file.path(data_dir, "19_PPI互作_StringInteractions_score900.tsv")
ppi_live <- tryCatch(
  np_fetch_string_ppi(
    genes_ov,
    species = 9606L,
    required_score = required_score,
    cache_path = ppi_cache
  ),
  error = function(e) {
    qa_notes <<- c(qa_notes, paste0("STRING fetch FAIL: ", conditionMessage(e)))
    NULL
  }
)
string_ids <- if (!is.null(ppi_live)) attr(ppi_live, "string_ids") else NULL

if (!is.null(ppi_live) && nrow(ppi_live) > 0) {
  utils::write.table(
    ppi_live, file.path(tab_dir, "19_PPI互作_StringInteractions_score900.tsv"),
    sep = "\t", row.names = FALSE, quote = FALSE, fileEncoding = "UTF-8"
  )
  ppi_ok <- TRUE

  # 13 官方 STRING 黑底证据图（样例同源）
  stem13 <- delivery_stem(skill_en, "network", "StringPPI", order = 13L)
  png13 <- file.path(fig_dir, paste0(stem13, ".png"))
  svg13 <- file.path(fig_dir, paste0(stem13, ".svg"))
  tryCatch({
    np_fetch_string_network_image(
      genes_ov,
      out_path = png13,
      species = 9606L,
      required_score = required_score,
      network_flavor = "evidence",
      hide_disconnected_nodes = TRUE,
      block_structure_pics = FALSE,
      show_query_node_labels = TRUE,
      format = "highres_image",
      string_ids = string_ids,
      timeout = 360
    )
    string_img_ok <- file.exists(png13) && file.info(png13)$size > 1000
    if (isTRUE(string_img_ok)) {
      fig_index[[length(fig_index) + 1]] <<- data.frame(
        order = 13, stem = stem13, plot_type = "network", theme = "StringPPI",
        note = "official STRING image (evidence/3D)",
        stringsAsFactors = FALSE
      )
      tryCatch({
        Sys.sleep(1)
        np_fetch_string_network_image(
          genes_ov, out_path = svg13, species = 9606L,
          required_score = required_score, network_flavor = "evidence",
          hide_disconnected_nodes = TRUE, block_structure_pics = FALSE,
          show_query_node_labels = TRUE, format = "svg",
          string_ids = string_ids, timeout = 360
        )
      }, error = function(e) message("STRING SVG skipped: ", conditionMessage(e)))
    }
  }, error = function(e) {
    qa_notes <<- c(qa_notes, paste0("STRING official image FAIL: ", conditionMessage(e)))
  })

  # 14 Concentric + 15 Degree（样例同图双存）
  p_ppi <- tryCatch(
    np_plot_string_ppi(
      ppi_live,
      min_score = required_score,
      drop_isolates = TRUE,
      layout = "concentric",
      label_top_n = NULL,
      outer_frac = 0.50,
      max_nodes = 200L
    ),
    error = function(e) {
      qa_notes <<- c(qa_notes, paste0("STRING concentric FAIL: ", conditionMessage(e)))
      NULL
    }
  )
  if (!is.null(p_ppi)) {
    save_fig(p_ppi, "network", "StringPPI_Concentric", 11.5, 10.5, 14L, "sample order 14")
    ppi_conc_ok <- TRUE
    save_fig(p_ppi, "network", "StringPPI_Degree", 11.5, 10.5, 15L, "sample order 15 (same concentric degree map)")
    ppi_deg_ok <- TRUE
  }
}

# 清理旧错误编号：曾把 concentric 存成 12_StringPPI
legacy12 <- file.path(fig_dir, "12_网络图_StringPPI_Network.png")
legacy12s <- file.path(fig_dir, "12_网络图_StringPPI_Network.svg")
if (file.exists(legacy12) && !isTRUE(hctp_ell_ok)) {
  # keep until ellipse writes over naming collision — ellipse stem differs
}
if (file.exists(legacy12)) {
  # ellipse theme is HerbCompoundTargetPathway_Ellipse; StringPPI@12 is wrong → remove
  file.remove(legacy12)
  if (file.exists(legacy12s)) file.remove(legacy12s)
  message("Removed legacy misnumbered 12_StringPPI (now ellipse @12 / official @13)")
}

# -------- exports / STATUS checklist --------
idx <- do.call(rbind, fig_index)
utils::write.csv(idx, file.path(tab_dir, "00_图册索引_FigureIndex.csv"),
                 row.names = FALSE, fileEncoding = "UTF-8")

checklist <- data.frame(
  delivery_figure = c(
    "疾病数据库韦恩", "疾病药物交集韦恩", "单药∩疾病柱图",
    "成分疾病交集(均分)", "成分疾病交集(按药)",
    "GO气泡", "GO柱状",
    "KEGG棒棒糖", "KEGG柱状", "KEGG圈图",
    "HCTP columns", "HCTP ellipse",
    "STRING 官方图", "STRING Concentric", "STRING Degree"
  ),
  order = c(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15),
  status = c(
    if (isTRUE(venn_ok)) "DONE" else "BLOCKED_微生信SVG",
    if (isTRUE(venn_ok)) "DONE" else "BLOCKED_微生信SVG",
    "DONE",
    if (!is.null(ct_ov_sum) && nrow(ct_ov_sum)) "DONE" else "MISSING",
    if (!is.null(ct_ov_edges) && nrow(ct_ov_edges)) "DONE" else "MISSING",
    if (!is.null(go_df) && nrow(go_df)) "DONE" else "MISSING",
    if (!is.null(go_df) && nrow(go_df)) "DONE" else "MISSING",
    if (!is.null(kegg_df) && nrow(kegg_df)) "DONE" else "MISSING",
    if (!is.null(kegg_df) && nrow(kegg_df)) "DONE" else "MISSING",
    if (any(idx$order == 10)) "DONE" else "MISSING",
    if (hctp_ok) "DONE" else "MISSING",
    if (hctp_ell_ok) "DONE" else "MISSING",
    if (string_img_ok) "DONE" else "MISSING",
    if (ppi_conc_ok) "DONE" else "MISSING",
    if (ppi_deg_ok) "DONE" else "MISSING"
  ),
  stringsAsFactors = FALSE
)
utils::write.csv(checklist, file.path(tab_dir, "00_交付图册对账_FigureChecklist.csv"),
                 row.names = FALSE, fileEncoding = "UTF-8")

n_done <- sum(checklist$status == "DONE")
status <- c(
  paste0("STATUS: ", if (n_done >= 15) "COMPLETE" else "PARTIAL", " (", n_done, "/15)"),
  "disease: Ulcerative Colitis",
  "plotting: NetworkPharmacology skill SSOT aligned to sample orders 01-15",
  "enrichment: clusterProfiler (not Enrichr)",
  paste0("hctp_columns=", hctp_ok, " hctp_ellipse=", hctp_ell_ok),
  paste0("string_official=", string_img_ok, " concentric=", ppi_conc_ok, " degree=", ppi_deg_ok),
  "atlas_parity: dual-bar Venns; HCTP columns+ellipse; STRING official+concentric+degree",
  "blocked: KEGG official pathway bitmaps (external); DisGeNET; 肉桂 empty targets",
  paste0("fig_dir: ", fig_dir),
  "QA_NOTES:",
  qa_notes
)
writeLines(status, file.path(rep_dir, "STATUS.txt"), useBytes = TRUE)
message("ATLAS DONE")
print(checklist)
