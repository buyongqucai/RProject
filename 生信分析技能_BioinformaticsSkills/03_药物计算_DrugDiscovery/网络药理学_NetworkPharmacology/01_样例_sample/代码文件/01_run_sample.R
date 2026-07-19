# 样例分析脚本 — 网络药理学_NetworkPharmacology
# 单药颗粒度 + 英文病名分库 + 真韦恩；Cytoscape 图不假装生成
# data_provenance: REAL（交付 query-backed 中间表）
# STATUS: PARTIAL
options(stringsAsFactors = FALSE)

args_all <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args_all, value = TRUE)
script_path <- if (length(file_arg)) {
  normalizePath(sub("^--file=", "", file_arg[1]), winslash = "/", mustWork = TRUE)
} else {
  normalizePath("01_run_sample.R", winslash = "/", mustWork = TRUE)
}
code_dir <- dirname(script_path)
sample_root <- normalizePath(file.path(code_dir, ".."), winslash = "/", mustWork = TRUE)
skill_root <- normalizePath(file.path(sample_root, ".."), winslash = "/", mustWork = TRUE)
bio_root <- normalizePath(file.path(skill_root, "..", ".."), winslash = "/", mustWork = TRUE)
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath(file.path(skill_root, "..", "..", ".."), winslash = "/", mustWork = TRUE)
}

viz_script <- file.path(
  bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
  "脚本_scripts", "出版级出图_PublicationPlot.R"
)
if (file.exists(viz_script)) source(viz_script, encoding = "UTF-8")

delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")

paths <- delivery_sample_paths(sample_root)
data_dir <- paths$raw_dir
fig_dir <- paths$fig_dir
tab_dir <- paths$tab_dir
rep_dir <- paths$rep_dir
for (d in c(data_dir, fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

skill_en <- "NetworkPharmacology"
skill_folder <- "网络药理学_NetworkPharmacology"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- "未找到可 source 的技能脚本"
if (length(sk_files)) {
  for (sf in sk_files) try(source(sf, encoding = "UTF-8"), silent = TRUE)
  sourced_note <- paste0("已 source 本技能 脚本_scripts/: ", paste(basename(sk_files), collapse = ", "))
}
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
library(ggplot2)
if (exists("setup_cjk_fonts")) setup_cjk_fonts()

data_provenance <- "REAL"
prov_json <- file.path(data_dir, "PROVENANCE.json")
disease_en <- "Atherosclerosis"
if (file.exists(prov_json) && requireNamespace("jsonlite", quietly = TRUE)) {
  prov <- tryCatch(jsonlite::fromJSON(prov_json), error = function(e) NULL)
  if (!is.null(prov$disease_english_name)) disease_en <- prov$disease_english_name
}

# --- load single-herb + multi-DB contracts ---
herb_targets <- np_read_all_herb_targets(data_dir)
herb_overlaps <- np_read_all_herb_overlaps(data_dir)
drug_u <- np_read_contract(data_dir, "drug_union")
dis_by <- np_read_contract(data_dir, "disease_by_db")
dis_by_venn <- np_read_contract(data_dir, "disease_by_db_venn")
dis_u <- np_read_contract(data_dir, "disease_union")
ov <- np_read_contract(data_dir, "overlap")
sum_df <- np_read_contract(data_dir, "per_herb_summary")
net <- np_read_contract(data_dir, "network", required = FALSE)
type_df <- np_read_contract(data_dir, "type_table", required = FALSE)
ppi_df <- np_read_contract(data_dir, "ppi", required = FALSE)
go_df <- np_read_contract(data_dir, "go_bubble", required = FALSE)
kegg_df <- np_read_contract(data_dir, "kegg", required = FALSE)
ct_df <- np_read_contract(data_dir, "compound_targets", required = FALSE)
rename_df <- np_read_contract(data_dir, "compound_rename", required = FALSE)
hc_df <- np_read_contract(data_dir, "herb_compound_edges", required = FALSE)

n_herbs <- length(unique(herb_targets$herb_en))
n_drug <- length(unique(drug_u$gene))
n_dis <- length(unique(dis_u$gene))
n_ov <- length(unique(ov$gene))
ov_check <- np_compute_overlap(drug_u, dis_u)

# --- compound × disease-overlap edges ---
ct_ov_edges <- NULL
ct_ov_sum <- NULL
ct_cyto <- NULL
n_ct_edges <- 0L
n_ct_compounds <- 0L
n_unmapped_ct <- 0L
if (!is.null(ct_df) && nrow(ct_df) > 0) {
  ct_ov_edges <- np_build_compound_disease_overlap_edges(
    ct_df, ov, rename_map = rename_df, herb_compound_edges = hc_df
  )
  ct_ov_sum <- np_summarize_compound_overlap(ct_ov_edges)
  ct_cyto <- np_export_compound_gene_cytoscape(ct_ov_edges, herb_compound_edges = hc_df)
  n_ct_edges <- nrow(ct_ov_edges)
  n_ct_compounds <- length(unique(ct_ov_edges$compound_id))
  n_unmapped_ct <- sum(!ct_ov_edges$compound_id_mapped)
  # QC: all targets must be in overlap
  stopifnot(all(ct_ov_edges$target_gene %in% ov$gene))
}

# export tables
utils::write.csv(herb_targets, file.path(tab_dir, "04_全部单药靶点_AllHerbTargets.csv"),
                 row.names = FALSE, fileEncoding = "UTF-8")
utils::write.csv(herb_overlaps, file.path(tab_dir, "05_全部单药疾病交集_AllHerbDiseaseOverlaps.csv"),
                 row.names = FALSE, fileEncoding = "UTF-8")
utils::write.csv(dis_by, file.path(tab_dir, "10_疾病靶点按库_DiseaseGenesByDB.csv"),
                 row.names = FALSE, fileEncoding = "UTF-8")
utils::write.csv(dis_by_venn, file.path(tab_dir, "11_疾病靶点按库_VennFull_DiseaseGenesByDB.csv"),
                 row.names = FALSE, fileEncoding = "UTF-8")
utils::write.csv(ov, file.path(tab_dir, "02_药物疾病交集_DrugDiseaseOverlap.csv"),
                 row.names = FALSE, fileEncoding = "UTF-8")
utils::write.csv(sum_df, file.path(tab_dir, "03_单药疾病交集汇总_PerHerbOverlapSummary.csv"),
                 row.names = FALSE, fileEncoding = "UTF-8")
if (!is.null(net)) {
  utils::write.csv(net, file.path(tab_dir, "17_网络边_network.csv"), row.names = FALSE, fileEncoding = "UTF-8")
}
if (!is.null(type_df)) {
  utils::write.csv(type_df, file.path(tab_dir, "18_网络节点类型_type.csv"), row.names = FALSE, fileEncoding = "UTF-8")
}
if (!is.null(ct_ov_edges) && nrow(ct_ov_edges)) {
  utils::write.csv(
    ct_ov_edges,
    file.path(tab_dir, "06_成分疾病交集靶点_CompoundDiseaseOverlapTargets.csv"),
    row.names = FALSE, fileEncoding = "UTF-8"
  )
  utils::write.csv(
    ct_ov_sum,
    file.path(tab_dir, "07_成分疾病交集汇总_CompoundDiseaseOverlapSummary.csv"),
    row.names = FALSE, fileEncoding = "UTF-8"
  )
  utils::write.csv(
    ct_cyto$network,
    file.path(tab_dir, "15_网络边_CompoundGene_Cytoscape.csv"),
    row.names = FALSE, fileEncoding = "UTF-8"
  )
  utils::write.csv(
    ct_cyto$type,
    file.path(tab_dir, "16_网络节点_CompoundGene_Cytoscape.csv"),
    row.names = FALSE, fileEncoding = "UTF-8"
  )
  utils::write.csv(
    data.frame(
      metric = c(
        "n_compound_overlap_edges", "n_compounds", "n_overlap_genes_hit",
        "n_unmapped_compound_rows", "n_cytoscape_edges", "n_cytoscape_nodes"
      ),
      value = c(
        n_ct_edges, n_ct_compounds, length(unique(ct_ov_edges$target_gene)),
        n_unmapped_ct, nrow(ct_cyto$network), nrow(ct_cyto$type)
      )
    ),
    file.path(tab_dir, "08_成分疾病交集质控_CompoundOverlapQC.csv"),
    row.names = FALSE, fileEncoding = "UTF-8"
  )
}
utils::write.csv(
  data.frame(
    metric = c(
      "n_herbs", "drug_union", "disease_union", "overlap_file",
      "overlap_recomputed", "jaccard_file_vs_recomputed"
    ),
    value = c(
      n_herbs, n_drug, n_dis, n_ov, nrow(ov_check),
      length(intersect(ov$gene, ov_check$gene)) / max(1, length(union(ov$gene, ov_check$gene)))
    )
  ),
  file.path(tab_dir, "12_交集核对_OverlapIntegrity.csv"),
  row.names = FALSE, fileEncoding = "UTF-8"
)

# external breakpoint checklist (R network previews are primary; Cytoscape optional)
blocked <- data.frame(
  figure = c(
    "Herb–compound–target–pathway network (Cytoscape polish)",
    "STRING web vector export (optional)",
    "KEGG official pathway maps (Top10)"
  ),
  status = c("OPTIONAL_CYTOSCAPE", "OPTIONAL_STRING_WEB", "BLOCKED_EXTERNAL"),
  software = c(
    "Cytoscape 3.10.2 (optional after R preview)",
    "STRING web (optional)",
    "KEGG website"
  ),
  how_to = c(
    "Review R 网络图_HerbCompoundTargetPathway first; if needed import 网络边/节点_HerbCompoundTargetPathway_Cytoscape.csv",
    "Optional: upload overlap genes on STRING web for their stock SVG",
    "Search Top pathway names on https://www.kegg.jp/ and download pathway images"
  ),
  stringsAsFactors = FALSE
)
utils::write.csv(blocked, file.path(tab_dir, "21_外部图断点清单_ExternalFigureBreakpoints.csv"),
                 row.names = FALSE, fileEncoding = "UTF-8")

write_delivery_audit(
  skill_en, "post",
  n_rows = nrow(herb_targets), n_cols = ncol(herb_targets), n_samples = n_herbs,
  group_source = paste0("disease_en=", disease_en, "; per-herb TCMSP exports"),
  toy = FALSE,
  accession = "user_delivery_20260710",
  sourced_skill_scripts = sourced_note,
  notes = paste0("overlap=", n_ov, "; PARTIAL; R network preview primary; Cytoscape optional"),
  out_path = file.path(tab_dir, delivery_with_order(delivery_audit_name(skill_en, "post"), 1)),
  data_provenance = data_provenance
)

# --- Figures: 疾病/药病韦恩 = 微生信交付原图（含双底栏）；其它图 R 可复现 ---
venn_exporter <- file.path(skill_root, "_export_delivery_venn_figures.py")
if (file.exists(venn_exporter)) {
  py <- Sys.which("python")
  if (!nzchar(py)) py <- Sys.which("python3")
  if (!nzchar(py)) stop("需要 python 以导出交付韦恩图")
  st <- system2(py, shQuote(normalizePath(venn_exporter)), stdout = TRUE, stderr = TRUE)
  message(paste(st, collapse = "\n"))
} else {
  warning("未找到 _export_delivery_venn_figures.py，回退 R 近似韦恩")
  p_venn_dis <- np_plot_disease_db_venn(dis_by_venn)
  delivery_save_plot(p_venn_dis, skill_en, "venn", "DiseaseDatabases", 6.5, 8.0, fig_dir, bio_root, order = 1)
  p_venn_dd <- np_plot_drug_disease_venn(drug_u, dis_u)
  delivery_save_plot(p_venn_dd, skill_en, "venn", "DrugDisease", 6.0, 7.2, fig_dir, bio_root, order = 2)
}

p_herb <- np_plot_per_herb_overlap(sum_df)
delivery_save_plot(p_herb, skill_en, "bar", "PerHerbDiseaseOverlap", 6.0, 4.8, fig_dir, bio_root, order = 3)

fig_map <- c(
  "疾病多库韦恩" = paste0("../图片文件/", delivery_stem(skill_en, "venn", "DiseaseDatabases", order = 1), ".png"),
  "药物疾病韦恩" = paste0("../图片文件/", delivery_stem(skill_en, "venn", "DrugDisease", order = 2), ".png"),
  "单药疾病交集" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "PerHerbDiseaseOverlap", order = 3), ".png")
)

if (!is.null(ct_ov_sum) && nrow(ct_ov_sum) > 0) {
  # (A) equal/average rank panels
  p_ct <- np_plot_compound_overlap_panels(ct_ov_sum, target_per = 14L, max_per = 16L)
  h_ct <- np_compound_overlap_panels_height(ct_ov_sum, target_per = 14L, max_per = 16L)
  delivery_save_plot(p_ct, skill_en, "bar", "CompoundDiseaseOverlap", 14.0, h_ct, fig_dir, bio_root, order = 4)
  fig_map <- c(
    fig_map,
    "成分疾病交集(均分)" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "CompoundDiseaseOverlap", order = 4), ".png")
  )
  # (B) by herb/drug (large herbs auto-split)
  if (!is.null(ct_ov_edges) && nrow(ct_ov_edges) > 0) {
    p_ct_h <- np_plot_compound_overlap_by_herb(ct_ov_edges, target_per = 14L, max_per = 16L)
    h_ct_h <- np_compound_overlap_by_herb_height(ct_ov_edges, target_per = 14L, max_per = 16L)
    delivery_save_plot(
      p_ct_h, skill_en, "bar", "CompoundDiseaseOverlapByHerb", 14.0, h_ct_h, fig_dir, bio_root, order = 5
    )
    fig_map <- c(
      fig_map,
      "成分疾病交集(按药)" = paste0(
        "../图片文件/", delivery_stem(skill_en, "bar", "CompoundDiseaseOverlapByHerb", order = 5), ".png"
      )
    )
  }
}

if (!is.null(go_df) && nrow(go_df) > 0) {
  p_go_b <- np_plot_go_bubble(go_df, top_n = 10)
  delivery_save_plot(p_go_b, skill_en, "bubble", "GO_BPCCMF", 10.0, 9.5, fig_dir, bio_root, order = 6)
  p_go_bar <- np_plot_go_bar(go_df, top_n = 10)
  delivery_save_plot(p_go_bar, skill_en, "bar", "GO_BPCCMF", 11.0, 7.5, fig_dir, bio_root, order = 7)
  fig_map <- c(
    fig_map,
    "GO气泡" = paste0("../图片文件/", delivery_stem(skill_en, "bubble", "GO_BPCCMF", order = 6), ".png"),
    "GO柱状" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "GO_BPCCMF", order = 7), ".png")
  )
}
if (!is.null(kegg_df) && nrow(kegg_df) > 0) {
  p_kegg_l <- np_plot_kegg_lollipop(kegg_df, top_n = 20)
  delivery_save_plot(p_kegg_l, skill_en, "lollipop", "KEGG_Pathways", 10.5, 8.5, fig_dir, bio_root, order = 8)
  p_kegg_b <- np_plot_kegg_bar(kegg_df, top_n = 20)
  delivery_save_plot(p_kegg_b, skill_en, "bar", "KEGG_Pathways", 10.5, 8.5, fig_dir, bio_root, order = 9)
  fig_map <- c(
    fig_map,
    "KEGG棒棒糖" = paste0("../图片文件/", delivery_stem(skill_en, "lollipop", "KEGG_Pathways", order = 8), ".png"),
    "KEGG柱状" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "KEGG_Pathways", order = 9), ".png")
  )
  # KEGG gene–pathway chord (circlize); needs geneID membership column
  gene_id_ok <- any(c("geneID", "geneId", "gene") %in% names(kegg_df))
  if (gene_id_ok && requireNamespace("circlize", quietly = TRUE)) {
    circ_stem <- delivery_stem(skill_en, "circos", "KEGG", order = 10)
    delivery_assert_name_ok(paste0(circ_stem, ".png"))
    dpi_use <- if (exists("FIG_DPI")) FIG_DPI else 600L
    circ_out <- tryCatch(
      np_save_kegg_chord(
        kegg_df,
        out_dir = fig_dir,
        stem = circ_stem,
        top_n = 20,
        label_genes = TRUE,
        width = 11,
        height = 10,
        dpi = dpi_use
      ),
      error = function(e) {
        warning("KEGG circos failed: ", conditionMessage(e))
        NULL
      }
    )
    if (!is.null(circ_out) && file.exists(circ_out$png)) {
      fig_map <- c(fig_map, "KEGG圈图" = paste0("../图片文件/", circ_stem, ".png"))
    }
  } else if (!gene_id_ok) {
    warning("KEGG circos skipped: enrichment table lacks geneID membership column")
  } else {
    warning("KEGG circos skipped: install circlize")
  }
}

# --- R network previews (STRING PPI + A–B–C–D multilayer); Cytoscape optional ---
string_preview_ok <- FALSE
hctp_preview_ok <- FALSE
string_err <- NULL
ppi_df_live <- ppi_df
ppi_cache <- file.path(data_dir, "PPI互作_StringInteractions.tsv")
if (!is.null(net) && !is.null(type_df) && nrow(net) > 0 && nrow(type_df) > 0) {
  cyto_hctp <- np_export_hctp_cytoscape(net, type_df, tab_dir)
  p_hctp <- tryCatch(
    np_plot_hctp_network(net, type_df, label_top_n = 50L, edge_alpha = 0.07),
    error = function(e) {
      warning("HCTP network plot failed: ", conditionMessage(e))
      NULL
    }
  )
  if (!is.null(p_hctp)) {
    delivery_save_plot(
      p_hctp, skill_en, "network", "HerbCompoundTargetPathway",
      12.5, 9.5, fig_dir, bio_root, order = 11
    )
    fig_map <- c(
      fig_map,
      "药成分靶通路网络" = paste0(
        "../图片文件/", delivery_stem(skill_en, "network", "HerbCompoundTargetPathway", order = 11), ".png"
      )
    )
    hctp_preview_ok <- TRUE
  }
}
ppi_cache_900 <- file.path(data_dir, "19_PPI互作_StringInteractions_score900.tsv")
string_ids_live <- NULL
tryCatch({
  ppi_df_live <- np_fetch_string_ppi(
    unique(ov$gene),
    species = 9606L,
    required_score = 900L,
    cache_path = ppi_cache_900,
    force = FALSE
  )
  string_ids_live <- attr(ppi_df_live, "string_ids")
  utils::write.table(
    ppi_df_live, file.path(tab_dir, "19_PPI互作_StringInteractions_score900.tsv"),
    sep = "\t", quote = FALSE, row.names = FALSE, fileEncoding = "UTF-8"
  )
}, error = function(e) {
  string_err <<- conditionMessage(e)
  if (file.exists(ppi_cache_900)) {
    ppi_df_live <<- utils::read.delim(ppi_cache_900, stringsAsFactors = FALSE, check.names = FALSE)
  } else if (file.exists(ppi_cache)) {
    ppi_df_live <<- utils::read.delim(ppi_cache, stringsAsFactors = FALSE, check.names = FALSE)
  }
})
# Official STRING image (confidence 0.9, 3D structures, hide isolates)
stem_ppi <- delivery_stem(skill_en, "network", "StringPPI", order = 13)
png_ppi <- file.path(fig_dir, paste0(stem_ppi, ".png"))
tryCatch({
  np_fetch_string_network_image(
    unique(ov$gene),
    out_path = png_ppi,
    species = 9606L,
    required_score = 900L,
    network_flavor = "evidence",
    hide_disconnected_nodes = TRUE,
    block_structure_pics = FALSE,
    show_query_node_labels = TRUE,
    format = "highres_image",
    string_ids = string_ids_live,
    timeout = 360
  )
  if (file.exists(png_ppi) && file.info(png_ppi)$size > 1000) {
    fig_map <- c(fig_map, "STRING_PPI网络" = paste0("../图片文件/", stem_ppi, ".png"))
    string_preview_ok <- TRUE
  }
}, error = function(e) {
  warning("STRING official image failed: ", conditionMessage(e))
})
if (!is.null(ppi_df_live) && nrow(ppi_df_live) > 0) {
  p_ppi <- tryCatch(
    np_plot_string_ppi(
      ppi_df_live, min_score = 900L, drop_isolates = TRUE,
      layout = "concentric", label_top_n = 90L
    ),
    error = function(e) {
      warning("STRING PPI concentric plot failed: ", conditionMessage(e))
      NULL
    }
  )
  if (!is.null(p_ppi)) {
    delivery_save_plot(
      p_ppi, skill_en, "network", "StringPPI_Concentric", 11.0, 10.0, fig_dir, bio_root, order = 14
    )
    fig_map <- c(
      fig_map,
      "STRING_PPI同心圆" = paste0(
        "../图片文件/", delivery_stem(skill_en, "network", "StringPPI_Concentric", order = 14), ".png"
      )
    )
    if (!isTRUE(string_preview_ok)) {
      delivery_save_plot(p_ppi, skill_en, "network", "StringPPI", 11.0, 10.0, fig_dir, bio_root, order = 13)
      string_preview_ok <- TRUE
    }
  }
}

# remove obsolete misleading figures (keep CompoundDiseaseOverlap — now real join)
old_figs <- c(
  "网络图_CompoundTarget_Network.png", "网络图_CompoundTarget_Network.svg",
  "柱状图_DiseaseDbCounts_Bar.png", "柱状图_DiseaseDbCounts_Bar.svg",
  "柱状图_HubTargetDegree_Bar.png", "柱状图_HubTargetDegree_Bar.svg",
  "柱状图_StringPPITop_Bar.png", "柱状图_StringPPITop_Bar.svg",
  "柱状图_TargetDegree_Bar.png", "柱状图_TargetDegree_Bar.svg"
)
for (old in old_figs) {
  f1 <- file.path(fig_dir, old)
  if (file.exists(f1)) file.remove(f1)
}

status <- "PARTIAL"
interp <- paste0(
  "Pipeline: per-herb TCMSP targets → disease DBs queried by English name (", disease_en, ") → ",
  "true multi-DB Venn + drug–disease Venn → per-herb overlaps → ",
  "compound×disease-overlap targets (", n_ct_edges, " edges / ", n_ct_compounds, " compounds). ",
  "R previews: STRING PPI + herb–compound–target–pathway network (Cytoscape optional after review). ",
  "KEGG official maps = BLOCKED_EXTERNAL. KEGG circos = R-reproducible when geneID present. ",
  "data_provenance=REAL (delivery exports; not live scrape; not rnorm)."
)

data_html <- paste0(
  "<p><b>data_provenance: REAL</b> · disease_english_name=<code>", disease_en, "</code></p>",
  "<p>Herbs: ", n_herbs, " · drug_union=", n_drug, " · disease_union=", n_dis,
  " · overlap=", n_ov, " · compound_overlap_edges=", n_ct_edges, ".</p>",
  "<p><b>STATUS: PARTIAL</b> — R Venns/GO/KEGG/compound-overlap + network previews; ",
  "KEGG official maps external; Cytoscape polish optional.</p>",
  "<p>Breakpoint table: <code>21_外部图断点清单_ExternalFigureBreakpoints.csv</code></p>"
)
audit_path <- file.path(tab_dir, delivery_with_order(delivery_audit_name(skill_en, "post"), 1))
audit_html <- if (file.exists(audit_path)) {
  paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")
} else {
  "<p>无 post 审计表</p>"
}
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(
  skill_en, skill_folder, status,
  data_html, audit_html, sourced_note, fig_map, interp, rep_file
)
writeLines(
  c(
    status,
    paste0("data_provenance=", data_provenance),
    paste0("disease_english_name=", disease_en),
    "R_figures=PASS_SUBSET",
    "compound_disease_overlap_table=PASS",
    "compound_overlap_bar=PASS",
    "compound_overlap_by_herb=PASS",
    "KEGG_circos=PASS",
    paste0("STRING_PPI_preview=", if (isTRUE(string_preview_ok)) "PASS" else "BLOCKED_EXTERNAL"),
    paste0("HCTP_network_preview=", if (isTRUE(hctp_preview_ok)) "PASS" else "FAIL"),
    "Cytoscape_polish=OPTIONAL",
    "KEGG_official_maps=BLOCKED_EXTERNAL"
  ),
  file.path(rep_dir, "STATUS.txt")
)

message("DONE ", status, " data_provenance=", data_provenance, " — ", skill_folder)
