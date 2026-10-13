# 用 clusterProfiler 重算 GO/KEGG（对齐技能契约），再用 NetworkPharmacology 技能脚本重绘
# 禁止 Enrichr 乱标 Group / 带 GO:ID 的脏 term
options(stringsAsFactors = FALSE)

project_root <- "E:/RProject"
bio_root <- file.path(project_root, "生信分析技能_BioinformaticsSkills")
skill_root <- file.path(bio_root, "03_药物计算_DrugDiscovery", "网络药理学_NetworkPharmacology")
work_root <- file.path(project_root, "努力学习项目", "网络药理学")
data_dir <- file.path(work_root, "数据文件")
fig_dir <- file.path(work_root, "代码文件", "结果文件", "图片文件")
tab_dir <- file.path(work_root, "代码文件", "结果文件", "数据文件")
rep_dir <- file.path(work_root, "代码文件", "结果文件", "报告文件")

stopifnot(requireNamespace("clusterProfiler", quietly = TRUE))
stopifnot(requireNamespace("org.Hs.eg.db", quietly = TRUE))
library(clusterProfiler)
library(org.Hs.eg.db)
library(ggplot2)

source(file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                 "脚本_scripts", "出版级出图_PublicationPlot.R"), encoding = "UTF-8")
source(file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards",
                 "脚本_scripts", "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
for (sf in list.files(file.path(skill_root, "脚本_scripts"), pattern = "[.][Rr]$", full.names = TRUE)) {
  source(sf, encoding = "UTF-8")
}
if (exists("setup_cjk_fonts")) setup_cjk_fonts()

skill_en <- "NetworkPharmacology"
ov <- utils::read.csv(file.path(data_dir, "药物疾病交集_DrugDiseaseOverlap.csv"),
                      stringsAsFactors = FALSE, fileEncoding = "UTF-8")
genes <- unique(as.character(ov$gene))
genes <- genes[!is.na(genes) & nzchar(genes)]
message("overlap genes: ", length(genes))

idmap <- bitr(genes, fromType = "SYMBOL", toType = "ENTREZID", OrgDb = org.Hs.eg.db)
message("mapped entrez: ", nrow(idmap))
entrez <- unique(idmap$ENTREZID)

# ---------- GO BP/CC/MF → 富集GO_BPCCMF_Bubble.csv（Metascape/clusterProfiler 契约）----------
go_list <- list()
for (ont in c("BP", "CC", "MF")) {
  eg <- enrichGO(
    gene = entrez,
    OrgDb = org.Hs.eg.db,
    keyType = "ENTREZID",
    ont = ont,
    pAdjustMethod = "BH",
    pvalueCutoff = 0.05,
    qvalueCutoff = 0.2,
    readable = TRUE
  )
  if (is.null(eg) || nrow(as.data.frame(eg)) == 0) next
  df <- as.data.frame(eg)
  # enrichment ≈ FoldEnrichment if present, else GeneRatio/BgRatio
  if ("FoldEnrichment" %in% names(df)) {
    enrich <- as.numeric(df$FoldEnrichment)
  } else {
    gr <- vapply(strsplit(as.character(df$GeneRatio), "/"), function(x) as.numeric(x[1]) / as.numeric(x[2]), 1)
    br <- vapply(strsplit(as.character(df$BgRatio), "/"), function(x) as.numeric(x[1]) / as.numeric(x[2]), 1)
    enrich <- gr / br
  }
  # term: plain English, lowercase (对齐样例，无 GO:ID)
  term <- tolower(as.character(df$Description))
  go_list[[ont]] <- data.frame(
    term = term,
    enrichment = enrich,
    pvalue = as.numeric(df$pvalue),
    count = as.integer(df$Count),
    ontology = ont,
    stringsAsFactors = FALSE
  )
}
go_df <- do.call(rbind, go_list)
rownames(go_df) <- NULL
# 每 ontology 先按 enrichment 留足候选，出图函数再 top_n
utils::write.csv(go_df, file.path(data_dir, "富集GO_BPCCMF_Bubble.csv"),
                 row.names = FALSE, fileEncoding = "UTF-8")
utils::write.csv(go_df, file.path(tab_dir, "13_富集GO_BPCCMF.csv"),
                 row.names = FALSE, fileEncoding = "UTF-8")
message("GO rows: ", nrow(go_df))

# ---------- KEGG → 富集KEGG_TopPathways.csv（含 one_type Group）----------
kk <- enrichKEGG(
  gene = entrez,
  organism = "hsa",
  keyType = "kegg",
  pAdjustMethod = "BH",
  pvalueCutoff = 0.05,
  qvalueCutoff = 0.2
)
kk <- setReadable(kk, OrgDb = org.Hs.eg.db, keyType = "ENTREZID")
kdf <- as.data.frame(kk)
# category / subcategory from clusterProfiler
one_type <- if ("category" %in% names(kdf)) as.character(kdf$category) else NA_character_
# map to np_kegg_group_levels names used by skill
map_group <- function(x) {
  x <- as.character(x)
  out <- rep("Cellular Processes", length(x))
  out[grepl("Environmental Information", x, ignore.case = TRUE)] <- "Environmental Information Processing"
  out[grepl("Human Diseases", x, ignore.case = TRUE)] <- "Human Diseases"
  out[grepl("Organismal Systems", x, ignore.case = TRUE)] <- "Organismal Systems"
  out[grepl("Cellular Processes", x, ignore.case = TRUE)] <- "Cellular Processes"
  out[grepl("Metabolism", x, ignore.case = TRUE)] <- "Cellular Processes"
  out[grepl("Genetic Information", x, ignore.case = TRUE)] <- "Cellular Processes"
  out
}
kegg_out <- data.frame(
  ID = kdf$ID,
  term = as.character(kdf$Description),
  Description = as.character(kdf$Description),
  GeneRatio = as.character(kdf$GeneRatio),
  BgRatio = as.character(kdf$BgRatio),
  pvalue = as.numeric(kdf$pvalue),
  padj = as.numeric(kdf$p.adjust),
  `p.adjust` = as.numeric(kdf$p.adjust),
  geneID = gsub("/", "/", as.character(kdf$geneID), fixed = TRUE),
  count = as.integer(kdf$Count),
  Count = as.integer(kdf$Count),
  one_type = map_group(one_type),
  Group = map_group(one_type),
  check.names = FALSE,
  stringsAsFactors = FALSE
)
utils::write.csv(kegg_out, file.path(data_dir, "富集KEGG_TopPathways.csv"),
                 row.names = FALSE, fileEncoding = "UTF-8")
utils::write.csv(kegg_out, file.path(tab_dir, "14_富集KEGG_TopPathways.csv"),
                 row.names = FALSE, fileEncoding = "UTF-8")
message("KEGG rows: ", nrow(kegg_out))

# ---------- 重绘：技能函数 + delivery_save_plot ----------
# 先清旧 GO/KEGG 图，避免混淆
old_pat <- c("06_气泡图_GO_BPCCMF_Bubble", "07_柱状图_GO_BPCCMF_Bar",
             "08_棒棒糖图_KEGG_Pathways_Lollipop", "09_柱状图_KEGG_Pathways_Bar")
for (stem in old_pat) {
  for (ext in c(".png", ".svg", ".pdf")) {
    f <- file.path(fig_dir, paste0(stem, ext))
    if (file.exists(f)) file.remove(f)
  }
}

p_go_b <- np_plot_go_bubble(go_df, top_n = 10)
delivery_save_plot(p_go_b, skill_en, "bubble", "GO_BPCCMF", 10.0, 9.5, fig_dir, bio_root, order = 6)
p_go_bar <- np_plot_go_bar(go_df, top_n = 10)
delivery_save_plot(p_go_bar, skill_en, "bar", "GO_BPCCMF", 11.0, 7.5, fig_dir, bio_root, order = 7)

p_kegg_l <- np_plot_kegg_lollipop(kegg_out, top_n = 20)
delivery_save_plot(p_kegg_l, skill_en, "lollipop", "KEGG_Pathways", 10.5, 8.5, fig_dir, bio_root, order = 8)
p_kegg_b <- np_plot_kegg_bar(kegg_out, top_n = 20)
delivery_save_plot(p_kegg_b, skill_en, "bar", "KEGG_Pathways", 10.5, 8.5, fig_dir, bio_root, order = 9)

# 韦恩/单药柱已是技能函数；疾病韦恩按规范用 VennFull。再跑一遍保证主题一致。
dis_by_venn <- np_read_contract(data_dir, "disease_by_db_venn")
drug_u <- np_read_contract(data_dir, "drug_union")
dis_u <- np_read_contract(data_dir, "disease_union")
sum_df <- np_read_contract(data_dir, "per_herb_summary")

for (stem in c("01_韦恩图_DiseaseDatabases_Venn", "02_韦恩图_DrugDisease_Venn",
               "03_柱状图_PerHerbDiseaseOverlap_Bar")) {
  for (ext in c(".png", ".svg", ".pdf")) {
    f <- file.path(fig_dir, paste0(stem, ext))
    if (file.exists(f)) file.remove(f)
  }
}
p_venn_dis <- np_plot_disease_db_venn(dis_by_venn)
delivery_save_plot(p_venn_dis, skill_en, "venn", "DiseaseDatabases", 6.5, 8.0, fig_dir, bio_root, order = 1)
p_venn_dd <- np_plot_drug_disease_venn(drug_u, dis_u)
delivery_save_plot(p_venn_dd, skill_en, "venn", "DrugDisease", 6.0, 7.2, fig_dir, bio_root, order = 2)
p_herb <- np_plot_per_herb_overlap(sum_df)
delivery_save_plot(p_herb, skill_en, "bar", "PerHerbDiseaseOverlap", 6.5, 5.2, fig_dir, bio_root, order = 3)

writeLines(c(
  "STATUS: PARTIAL",
  "enrichment: clusterProfiler (GO+KEGG) — NOT Enrichr",
  "plotting: NetworkPharmacology skill np_plot_* + delivery_save_plot",
  "GO terms: lowercase, no GO:ID (sample contract)",
  "KEGG Group: from clusterProfiler category mapped to delivery Group levels",
  paste0("fig_dir: ", fig_dir)
), file.path(rep_dir, "STATUS.txt"), useBytes = TRUE)

message("DONE — figures refreshed in ", fig_dir)
