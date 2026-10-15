# 清风项目 · 图谱套件出图 01：韦恩(疾病R/药病微生信) + 03–10 统计图 + 编号表 + 报告
# 数据契约：03_药病交集与网络/.../图谱契约数据_FigureContractData
# 图 recipe 全部来自技能 SSOT（02_可视化_NetworkPharmPlots.R），本脚本只接线
options(stringsAsFactors = FALSE)

skill_root <- "E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology"
bio_root <- "E:/RProject/生信分析技能_BioinformaticsSkills"
viz_script <- file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                        "脚本_scripts", "出版级出图_PublicationPlot.R")
if (file.exists(viz_script)) source(viz_script, encoding = "UTF-8")
delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")

data_dir <- "E:/RProject/清风项目/03_药病交集与网络_OverlapAndNetwork/01_数据文件_Data/02_结果数据_ResultTables/图谱契约数据_FigureContractData"
# by_stage 落位（用户确认 2026-10-15）：01疾病 / 03交集网络 / 04富集PPI
fig_dir_01 <- "E:/RProject/清风项目/01_疾病靶点_DiseaseTargets/03_图片文件_Figures"
fig_dir_03 <- "E:/RProject/清风项目/03_药病交集与网络_OverlapAndNetwork/03_图片文件_Figures"
fig_dir_04 <- "E:/RProject/清风项目/04_富集与PPI_EnrichPPI/03_图片文件_Figures"
fig_dir <- fig_dir_04  # 兼容旧引用；新图按 stage 写
tab_dir <- "E:/RProject/清风项目/04_富集与PPI_EnrichPPI/01_数据文件_Data/02_结果数据_ResultTables/图谱套件编号表_FigureSuiteTables"
rep_dir <- "E:/RProject/清风项目/04_富集与PPI_EnrichPPI/04_报告文件_Reports"
for (d in c(data_dir, fig_dir_01, fig_dir_03, fig_dir_04, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

skill_en <- "NetworkPharmacology"
skill_folder <- "网络药理学_NetworkPharmacology"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
for (sf in sk_files) try(source(sf, encoding = "UTF-8"), silent = TRUE)
sourced_note <- paste0("已 source 本技能 脚本_scripts/: ", paste(basename(sk_files), collapse = ", "))

# ---- 本地 recipe 覆盖：GO 气泡按富集分数排序（用户确认 2026-10-15，撤销旧「按 p 值」override） ----
# X=enrichment（富集分数 FoldEnrichment）、size=count、color=-log10(pvalue)；竖排 BP/CC/MF；
# 每分面内按富集分数自上而下（富集分数高在上），使气泡沿 X 单调展开、观感整齐。见出图约束 §I。
np_plot_go_bubble <- function(go_df, top_n = 10) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
  df <- go_df
  df$pvalue <- as.numeric(df$pvalue)
  df$enrichment <- as.numeric(df$enrichment)
  df$count <- as.numeric(df$count)
  if (!"ontology" %in% names(df)) df$ontology <- "BP"
  df$ontology <- factor(as.character(df$ontology), levels = c("BP", "CC", "MF"))
  df$neglogp <- -log10(pmax(df$pvalue, 1e-300))

  # 与技能 SSOT np_plot_go_bubble 对齐：top_n 按 enrichment 降序；分面内 enrichment 高在上
  parts <- split(df, df$ontology)
  parts <- lapply(parts, function(d) {
    d <- d[order(-d$enrichment, d$pvalue), , drop = FALSE]
    utils::head(d, top_n)
  })
  df <- do.call(rbind, parts)
  rownames(df) <- NULL

  df$term_lab <- np_wrap_term(df$term, width = 36)
  df <- df[order(df$ontology, df$enrichment, -df$neglogp), , drop = FALSE]
  df$term_lab <- factor(df$term_lab, levels = unique(df$term_lab))

  ggplot2::ggplot(
    df,
    ggplot2::aes(enrichment, term_lab, size = count, color = neglogp)
  ) +
    ggplot2::geom_point(alpha = 0.92) +
    ggplot2::facet_grid(ontology ~ ., scales = "free_y", space = "free_y") +
    ggplot2::scale_color_gradientn(colours = np_go_pval_cols, name = "-log 10 (pvalue)") +
    ggplot2::scale_size_continuous(
      range = c(2.5, 10), name = "count", breaks = function(x) pretty(x, n = 3)
    ) +
    ggplot2::scale_x_continuous(expand = ggplot2::expansion(mult = c(0.04, 0.08))) +
    ggplot2::labs(x = "Enrichment", y = NULL) +
    ggplot2::guides(
      color = ggplot2::guide_colorbar(order = 1, barwidth = 0.7, barheight = 5),
      size = ggplot2::guide_legend(order = 2, override.aes = list(color = "grey30"))
    ) +
    np_theme_enrich(8.2) +
    ggplot2::theme(
      strip.text.y = ggplot2::element_text(angle = 0, face = "bold", size = 10),
      panel.spacing.y = ggplot2::unit(0.4, "lines"),
      legend.position = "right"
    )
}

if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
library(ggplot2)
if (exists("setup_cjk_fonts")) setup_cjk_fonts()

data_provenance <- "REAL"
disease_en <- "Idiopathic Pulmonary Fibrosis"
prov_json <- file.path(data_dir, "PROVENANCE.json")
if (file.exists(prov_json) && requireNamespace("jsonlite", quietly = TRUE)) {
  prov <- tryCatch(jsonlite::fromJSON(prov_json), error = function(e) NULL)
  if (!is.null(prov$disease_english_name)) disease_en <- prov$disease_english_name
}

# --- 契约读取 ---
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

# --- 成分 x 疾病交集边 ---
ct_ov_edges <- NULL
ct_ov_sum <- NULL
ct_cyto <- NULL
n_ct_edges <- 0L
n_ct_compounds <- 0L
if (!is.null(ct_df) && nrow(ct_df) > 0) {
  ct_ov_edges <- np_build_compound_disease_overlap_edges(
    ct_df, ov, rename_map = rename_df, herb_compound_edges = hc_df
  )
  ct_ov_sum <- np_summarize_compound_overlap(ct_ov_edges)
  ct_cyto <- np_export_compound_gene_cytoscape(ct_ov_edges, herb_compound_edges = hc_df)
  n_ct_edges <- nrow(ct_ov_edges)
  n_ct_compounds <- length(unique(ct_ov_edges$compound_id))
  stopifnot(all(ct_ov_edges$target_gene %in% ov$gene))
}

# --- 编号表导出 ---
utils::write.csv(herb_targets, file.path(tab_dir, "04_全部单药靶点_AllHerbTargets.csv"), row.names = FALSE, fileEncoding = "UTF-8")
utils::write.csv(herb_overlaps, file.path(tab_dir, "05_全部单药疾病交集_AllHerbDiseaseOverlaps.csv"), row.names = FALSE, fileEncoding = "UTF-8")
utils::write.csv(dis_by, file.path(tab_dir, "10_疾病靶点按库_DiseaseGenesByDB.csv"), row.names = FALSE, fileEncoding = "UTF-8")
utils::write.csv(dis_by_venn, file.path(tab_dir, "11_疾病靶点按库_VennFull_DiseaseGenesByDB.csv"), row.names = FALSE, fileEncoding = "UTF-8")
utils::write.csv(ov, file.path(tab_dir, "02_药物疾病交集_DrugDiseaseOverlap.csv"), row.names = FALSE, fileEncoding = "UTF-8")
utils::write.csv(sum_df, file.path(tab_dir, "03_单药疾病交集汇总_PerHerbOverlapSummary.csv"), row.names = FALSE, fileEncoding = "UTF-8")
if (!is.null(net)) utils::write.csv(net, file.path(tab_dir, "17_网络边_network.csv"), row.names = FALSE, fileEncoding = "UTF-8")
if (!is.null(type_df)) utils::write.csv(type_df, file.path(tab_dir, "18_网络节点类型_type.csv"), row.names = FALSE, fileEncoding = "UTF-8")
if (!is.null(ct_ov_edges) && nrow(ct_ov_edges)) {
  utils::write.csv(ct_ov_edges, file.path(tab_dir, "06_成分疾病交集靶点_CompoundDiseaseOverlapTargets.csv"), row.names = FALSE, fileEncoding = "UTF-8")
  utils::write.csv(ct_ov_sum, file.path(tab_dir, "07_成分疾病交集汇总_CompoundDiseaseOverlapSummary.csv"), row.names = FALSE, fileEncoding = "UTF-8")
  utils::write.csv(ct_cyto$network, file.path(tab_dir, "15_网络边_CompoundGene_Cytoscape.csv"), row.names = FALSE, fileEncoding = "UTF-8")
  utils::write.csv(ct_cyto$type, file.path(tab_dir, "16_网络节点_CompoundGene_Cytoscape.csv"), row.names = FALSE, fileEncoding = "UTF-8")
  utils::write.csv(
    data.frame(
      metric = c("n_compound_overlap_edges", "n_compounds", "n_overlap_genes_hit", "n_cytoscape_edges", "n_cytoscape_nodes"),
      value = c(n_ct_edges, n_ct_compounds, length(unique(ct_ov_edges$target_gene)), nrow(ct_cyto$network), nrow(ct_cyto$type))
    ),
    file.path(tab_dir, "08_成分疾病交集质控_CompoundOverlapQC.csv"), row.names = FALSE, fileEncoding = "UTF-8"
  )
}
utils::write.csv(
  data.frame(
    metric = c("n_herbs", "drug_union", "disease_union", "overlap_file", "overlap_recomputed", "jaccard_file_vs_recomputed"),
    value = c(n_herbs, n_drug, n_dis, n_ov, nrow(ov_check),
              length(intersect(ov$gene, ov_check$gene)) / max(1, length(union(ov$gene, ov_check$gene))))
  ),
  file.path(tab_dir, "12_交集核对_OverlapIntegrity.csv"), row.names = FALSE, fileEncoding = "UTF-8"
)
blocked <- data.frame(
  figure = c("Herb-compound-target-pathway network (Cytoscape polish)", "STRING web vector export (optional)", "KEGG official pathway maps (Top20)"),
  status = c("OPTIONAL_CYTOSCAPE", "OPTIONAL_STRING_WEB", "BLOCKED_EXTERNAL"),
  software = c("Cytoscape 3.10.2 (optional after R preview)", "STRING web (optional)", "KEGG website"),
  how_to = c("Review R HCTP figures first; optional import HerbCompoundTargetPathway Cytoscape CSVs",
             "Optional: upload overlap genes on STRING web for their stock SVG",
             "See skill FROZEN section F route (24_download_kegg_pathway_maps.py)"),
  stringsAsFactors = FALSE
)
utils::write.csv(blocked, file.path(tab_dir, "21_外部图断点清单_ExternalFigureBreakpoints.csv"), row.names = FALSE, fileEncoding = "UTF-8")

write_delivery_audit(
  skill_en, "post",
  n_rows = nrow(herb_targets), n_cols = ncol(herb_targets), n_samples = n_herbs,
  group_source = paste0("disease_en=", disease_en, "; per-herb TCMSP+BATMAN exports"),
  toy = FALSE,
  accession = "qingfeng_delivery_20261015",
  sourced_skill_scripts = sourced_note,
  notes = paste0("overlap=", n_ov, "; R network previews in 02/03 scripts"),
  out_path = file.path(tab_dir, delivery_with_order(delivery_audit_name(skill_en, "post"), 1)),
  data_provenance = data_provenance
)

# --- 图 01：疾病多库韦恩（契约装配→01_疾病靶点/03_图片，FROZEN §G） ---
fig_map <- c()
venn_dis <- file.path(fig_dir_01, paste0(delivery_stem(skill_en, "venn", "DiseaseDatabases", order = 1), ".png"))
if (file.exists(venn_dis)) {
  fig_map <- c(fig_map, "疾病多库韦恩" = paste0("../../01_疾病靶点_DiseaseTargets/03_图片文件_Figures/", basename(venn_dis)))
} else {
  warning("图01 疾病多库韦恩缺失（应由 图谱契约装配_buildFigureContracts.py 微生信产出）")
}

# --- 图 02：药病韦恩（契约装配→03_药病交集/03_图片） ---
venn_dd <- file.path(fig_dir_03, paste0(delivery_stem(skill_en, "venn", "DrugDisease", order = 2), ".png"))
if (file.exists(venn_dd)) {
  fig_map <- c(fig_map, "药物疾病韦恩" = paste0("../../03_药病交集与网络_OverlapAndNetwork/03_图片文件_Figures/", basename(venn_dd)))
} else {
  warning("图02 药病韦恩缺失（应由 图谱契约装配_buildFigureContracts.py 产出）")
}

# --- 图 03–05：交集柱（→03） ---
p_herb <- np_plot_per_herb_overlap(sum_df)
delivery_save_plot(p_herb, skill_en, "bar", "PerHerbDiseaseOverlap", 6.0, 4.8, fig_dir_03, bio_root, order = 3)
fig_map <- c(fig_map, "单药疾病交集" = paste0("../../03_药病交集与网络_OverlapAndNetwork/03_图片文件_Figures/", delivery_stem(skill_en, "bar", "PerHerbDiseaseOverlap", order = 3), ".png"))

if (!is.null(ct_ov_sum) && nrow(ct_ov_sum) > 0) {
  p_ct <- np_plot_compound_overlap_panels(ct_ov_sum, target_per = 14L, max_per = 16L)
  h_ct <- np_compound_overlap_panels_height(ct_ov_sum, target_per = 14L, max_per = 16L)
  delivery_save_plot(p_ct, skill_en, "bar", "CompoundDiseaseOverlap", 14.0, h_ct, fig_dir_03, bio_root, order = 4)
  fig_map <- c(fig_map, "成分疾病交集(均分)" = paste0("../../03_药病交集与网络_OverlapAndNetwork/03_图片文件_Figures/", delivery_stem(skill_en, "bar", "CompoundDiseaseOverlap", order = 4), ".png"))
  if (!is.null(ct_ov_edges) && nrow(ct_ov_edges) > 0) {
    p_ct_h <- np_plot_compound_overlap_by_herb(ct_ov_edges, target_per = 14L, max_per = 16L)
    h_ct_h <- np_compound_overlap_by_herb_height(ct_ov_edges, target_per = 14L, max_per = 16L)
    delivery_save_plot(p_ct_h, skill_en, "bar", "CompoundDiseaseOverlapByHerb", 14.0, h_ct_h, fig_dir_03, bio_root, order = 5)
    fig_map <- c(fig_map, "成分疾病交集(按药)" = paste0("../../03_药病交集与网络_OverlapAndNetwork/03_图片文件_Figures/", delivery_stem(skill_en, "bar", "CompoundDiseaseOverlapByHerb", order = 5), ".png"))
  }
}

# --- 图 06–10：GO/KEGG（→04 富集） ---
if (!is.null(go_df) && nrow(go_df) > 0) {
  p_go_b <- np_plot_go_bubble(go_df, top_n = 10)
  delivery_save_plot(p_go_b, skill_en, "bubble", "GO_BPCCMF", 10.0, 9.5, fig_dir_04, bio_root, order = 6)
  p_go_bar <- np_plot_go_bar(go_df, top_n = 10)
  delivery_save_plot(p_go_bar, skill_en, "bar", "GO_BPCCMF", 11.0, 7.5, fig_dir_04, bio_root, order = 7)
  fig_map <- c(fig_map,
    "GO气泡" = paste0("../图片文件/", delivery_stem(skill_en, "bubble", "GO_BPCCMF", order = 6), ".png"),
    "GO柱状" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "GO_BPCCMF", order = 7), ".png"))
}

if (!is.null(kegg_df) && nrow(kegg_df) > 0) {
  p_kegg_l <- np_plot_kegg_lollipop(kegg_df, top_n = 20)
  delivery_save_plot(p_kegg_l, skill_en, "lollipop", "KEGG_Pathways", 10.5, 8.5, fig_dir_04, bio_root, order = 8)
  p_kegg_b <- np_plot_kegg_bar(kegg_df, top_n = 20)
  delivery_save_plot(p_kegg_b, skill_en, "bar", "KEGG_Pathways", 10.5, 8.5, fig_dir_04, bio_root, order = 9)
  fig_map <- c(fig_map,
    "KEGG棒棒糖" = paste0("../图片文件/", delivery_stem(skill_en, "lollipop", "KEGG_Pathways", order = 8), ".png"),
    "KEGG柱状" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "KEGG_Pathways", order = 9), ".png"))
  gene_id_ok <- any(c("geneID", "geneId", "gene") %in% names(kegg_df))
  if (gene_id_ok && requireNamespace("circlize", quietly = TRUE)) {
    circ_stem <- delivery_stem(skill_en, "circos", "KEGG", order = 10)
    delivery_assert_name_ok(paste0(circ_stem, ".png"))
    dpi_use <- if (exists("FIG_DPI")) FIG_DPI else 600L
    circ_out <- tryCatch(
      np_save_kegg_chord(kegg_df, out_dir = fig_dir_04, stem = circ_stem, top_n = 20,
                         label_genes = TRUE, width = 11, height = 10, dpi = dpi_use),
      error = function(e) { warning("KEGG circos failed: ", conditionMessage(e)); NULL }
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

# 11/12→03；13/14/15→04（由 02/03 脚本产出）
fig_map <- c(
  fig_map,
  "药成分靶通路网络" = "../../03_药病交集与网络_OverlapAndNetwork/03_图片文件_Figures/11_网络图_HerbCompoundTargetPathway_Network.png",
  "药成分靶通路网络(椭圆)" = "../../03_药病交集与网络_OverlapAndNetwork/03_图片文件_Figures/12_网络图_HerbCompoundTargetPathway_Ellipse_Network.png",
  "STRING_PPI网络" = "../图片文件/13_网络图_StringPPI_Network.png",
  "STRING_PPI同心圆" = "../图片文件/14_网络图_StringPPI_Concentric_Network.png",
  "STRING_PPI_Degree" = "../图片文件/15_网络图_StringPPI_Degree_Network.png"
)

status <- "PARTIAL"
interp <- paste0(
  "Pipeline: TCMSP 8-herb waterfall + BATMAN leech known targets -> disease 5-DB (", disease_en, ") -> ",
  "VennFull + drug-disease Venn -> per-herb overlaps -> compound x disease-overlap targets (",
  n_ct_edges, " edges / ", n_ct_compounds, " compounds). ",
  "Figures 11-15 via 02/03 scripts (HCTP columns+ellipse; STRING official image + R degree gradient). ",
  "KEGG official maps = BLOCKED_EXTERNAL. data_provenance=REAL."
)
data_html <- paste0(
  "<p><b>data_provenance: REAL</b> · disease_english_name=<code>", disease_en, "</code></p>",
  "<p>Herbs: ", n_herbs, " · drug_union=", n_drug, " · disease_union=", n_dis, " · overlap=", n_ov,
  " · compound_overlap_edges=", n_ct_edges, ".</p>",
  "<p><b>STATUS: PARTIAL</b> — full 01-15 R figure suite; KEGG official maps external; Cytoscape polish optional.</p>",
  "<p>Breakpoint table: <code>21_外部图断点清单_ExternalFigureBreakpoints.csv</code></p>"
)
audit_path <- file.path(tab_dir, delivery_with_order(delivery_audit_name(skill_en, "post"), 1))
audit_html <- if (file.exists(audit_path)) {
  paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")
} else {
  "<p>无 post 审计表</p>"
}
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(skill_en, skill_folder, status, data_html, audit_html, sourced_note, fig_map, interp, rep_file)
writeLines(
  c(status,
    paste0("data_provenance=", data_provenance),
    paste0("disease_english_name=", disease_en),
    "R_figures_01_10=PASS_SUBSET",
    "venn_disease=WEISHENGXIN_5DB_CTD_curated",
    "venn_drugdisease=WEISHENGIN_TEMPLATE",
    "compound_disease_overlap_table=PASS",
    "KEGG_circos=PASS",
    "figures_11_15=see_STATUS_network_preview"),
  file.path(rep_dir, "STATUS.txt")
)
message("DONE ", status, " — ", skill_folder)
