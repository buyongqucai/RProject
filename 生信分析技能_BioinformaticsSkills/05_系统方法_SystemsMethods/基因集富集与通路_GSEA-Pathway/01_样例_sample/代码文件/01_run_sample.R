# 样例分析脚本 — 基因集富集与通路_GSEA-Pathway
# 合规：统一交付规范_DeliveryStandards + 统一可视化规范_VizStandards
# analysis_kind=gsea  seed=19537
# data_provenance=REAL — GSE207177 (书清项目 macrophage DEG / MAMs / KEGG GSEA)
options(stringsAsFactors = FALSE)
set.seed(19537)

sample_root <- normalizePath("..", winslash = "/", mustWork = TRUE)
skill_root <- normalizePath("../..", winslash = "/", mustWork = TRUE)
bio_root <- normalizePath("../../..", winslash = "/", mustWork = TRUE)
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath("../../../..", winslash = "/", mustWork = TRUE)
}
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath(file.path(skill_root, "..", ".."), winslash = "/", mustWork = TRUE)
}

viz_script <- file.path(
  bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
  "脚本_scripts", "出版级出图_PublicationPlot.R"
)
if (file.exists(viz_script)) source(viz_script, encoding = "UTF-8")

delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")

paths <- delivery_sample_paths(sample_root)
data_dir <- paths$raw_dir
fig_dir <- paths$fig_dir
tab_dir <- paths$tab_dir
rep_dir <- paths$rep_dir
for (d in c(data_dir, fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)
source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")

skill_en <- "GSEA-Pathway"
skill_folder <- "基因集富集与通路_GSEA-Pathway"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- "未找到可 source 的技能脚本"
if (length(sk_files)) {
  for (sf in sk_files) {
    try(source(sf, encoding = "UTF-8"), silent = TRUE)
  }
  sourced_note <- paste0("已 source 本技能 脚本_scripts/: ", paste(basename(sk_files), collapse = ", "))
}
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")

# ---- REAL data roots (cache preferred; live 书清 fallback) ----
shuqing_root <- Sys.getenv("SHUQING_ROOT", "E:/RProject/书清项目")
sq_tab <- file.path(shuqing_root, "GSE207177", "结果", "表格")
accession <- "GSE207177"

resolve_real <- function(cache_name, live_name = NULL) {
  cache <- file.path(data_dir, cache_name)
  if (file.exists(cache)) return(list(path = cache, via = "cache"))
  if (!is.null(live_name)) {
    live <- file.path(sq_tab, live_name)
    if (file.exists(live)) return(list(path = live, via = "SHUQING_ROOT"))
  }
  stop("Missing REAL table: ", cache_name, " (and live fallback if any)")
}

src_deg <- resolve_real("real_GSE207177_macro_DEG.csv", "GSE207177_巨噬细胞_全部差异基因.csv")
src_mams <- resolve_real("real_GSE207177_MAMs_geneset.csv", "GSE207177_MAMs交集基因.csv")
src_kegg <- resolve_real("real_GSE207177_KEGG_GSEA_top20.csv", "GSE207177_GSEA_KEGG.csv")
src_hm <- resolve_real(
  "real_GSE207177_pathway_gene_heatmap.csv",
  "GSE207177_巨噬细胞_线粒体功能障碍热图表达.csv"
)
src_note <- paste0(
  "REAL GSE207177 via ",
  paste(unique(c(src_deg$via, src_mams$via, src_kegg$via, src_hm$via)), collapse = "+"),
  "; SHUQING_ROOT=", shuqing_root
)

deg <- read.csv(src_deg$path, check.names = FALSE, stringsAsFactors = FALSE)
mams <- read.csv(src_mams$path, check.names = FALSE, stringsAsFactors = FALSE)
kegg <- read.csv(src_kegg$path, check.names = FALSE, stringsAsFactors = FALSE)
if (!"Description" %in% names(kegg) && "ID" %in% names(kegg)) kegg$Description <- kegg$ID
kegg <- kegg[order(-abs(kegg$NES)), ]
pathways <- utils::head(kegg, 12)
pathways$pathway <- pathways$Description
pathways$size <- pathways$setSize
pathways$padj <- pathways$p.adjust
write.csv(
  pathways[, intersect(c("pathway", "NES", "size", "padj", "ID", "pvalue"), names(pathways))],
  file.path(tab_dir, delivery_table_name(skill_en, "GSEA", "NES")),
  row.names = FALSE
)
write_delivery_audit(
  skill_en, "post", nrow(deg), ncol(deg), NA, paste0(accession, " macrophage DEG + KEGG GSEA"),
  TRUE, NA, paste(sourced_note, src_note, sep = " | "),
  "GSEA NES + classic ES + pathway gene heatmap; data_provenance=REAL",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "REAL"
)

library(ggplot2)
pathways$pathway <- factor(pathways$pathway, levels = pathways$pathway[order(pathways$NES)])
nes_fill <- c("FALSE" = unname(bioinfo_volcano[["down"]]), "TRUE" = unname(bioinfo_volcano[["up"]]))
p <- ggplot(pathways, aes(NES, pathway, fill = NES > 0)) +
  geom_col(width = 0.7) +
  geom_vline(xintercept = 0, linewidth = 0.4, color = "grey40") +
  scale_fill_manual(values = nes_fill, guide = "none") +
  labs(
    title = paste0("GSEA NES by pathway — ", accession),
    x = "NES", y = NULL
  )
delivery_save_plot(p, skill_en, "bar", "NES_Pathways", 5.5, 4.5, fig_dir, bio_root, order = 1)

pb <- plot_enrich_lollipop_journal(
  data.frame(
    Description = as.character(pathways$pathway),
    Count = pathways$size,
    p.adjust = pathways$padj,
    stringsAsFactors = FALSE
  ),
  title = paste0("Pathway enrichment — ", accession)
)
delivery_save_plot(pb, skill_en, "lollipop", "PathwayEnrich", 6.2, 5.2, fig_dir, bio_root, order = 2)

# Classic GSEA: ranked by log2FC; gene set = MAMs intersection genes present in DEG
ranked <- deg$log2FC
names(ranked) <- as.character(deg$gene)
ranked <- sort(ranked[!is.na(ranked) & names(ranked) != "" & !duplicated(names(ranked))], decreasing = TRUE)
gene_set <- unique(as.character(mams$gene))
gene_set <- gene_set[gene_set %in% names(ranked)]
gsea_nes <- gsea_p <- gsea_padj <- NULL
mams_gsea_cache <- file.path(data_dir, "real_GSE207177_macro_MAMs_GSEA.csv")
mams_gsea_live <- file.path(sq_tab, "GSE207177_巨噬细胞_MAMs通路GSEA.csv")
mams_gsea_path <- if (file.exists(mams_gsea_cache)) mams_gsea_cache else if (file.exists(mams_gsea_live)) mams_gsea_live else NA_character_
if (!is.na(mams_gsea_path)) {
  mg <- read.csv(mams_gsea_path, check.names = FALSE, stringsAsFactors = FALSE)
  if (nrow(mg) >= 1L) {
    gsea_nes <- mg$NES[1]
    gsea_p <- mg$pvalue[1]
    gsea_padj <- mg$p.adjust[1]
  }
}
if (length(gene_set) < 3L) {
  le <- pathways$core_enrichment[1]
  if (!is.null(le) && !is.na(le) && nzchar(le)) {
    gene_set <- intersect(unlist(strsplit(as.character(le), "/")), names(ranked))
  }
}
p_gsea <- plot_gsea_classic_journal(
  ranked_metric = ranked,
  gene_set = gene_set,
  title = paste0("GSEA enrichment — MAMs (", accession, ")"),
  es_color = "#1B7A4A",
  nes = gsea_nes,
  pvalue = gsea_p,
  p.adjust = gsea_padj
)
delivery_save_plot(p_gsea, skill_en, "gsea", "ClassicEnrichment", 5.5, 6.2, fig_dir, bio_root, order = 3)

# Pathway gene activity heatmap from REAL mito dysfunction + ER stress matrices
hm_path <- src_hm$path
if (basename(hm_path) == "GSE207177_巨噬细胞_线粒体功能障碍热图表达.csv") {
  hm1 <- read.csv(hm_path, check.names = FALSE, stringsAsFactors = FALSE)
  hm2_live <- file.path(sq_tab, "GSE207177_巨噬细胞_内质网应激热图表达.csv")
  hm2 <- if (file.exists(hm2_live)) {
    read.csv(hm2_live, check.names = FALSE, stringsAsFactors = FALSE)
  } else {
    hm1[0, ]
  }
  hm <- rbind(hm1, hm2)
} else {
  hm <- read.csv(hm_path, check.names = FALSE, stringsAsFactors = FALSE)
}
# genes × samples (CLP / Control); annotate panel in row names if present
sample_cols <- intersect(c("CLP", "Control"), names(hm))
if (length(sample_cols) < 2L) {
  sample_cols <- setdiff(names(hm), c("gene", "panel", "Gene", "Pathway"))
}
gene_col <- if ("gene" %in% names(hm)) "gene" else names(hm)[1]
rn <- as.character(hm[[gene_col]])
if ("panel" %in% names(hm)) {
  rn <- paste0(as.character(hm$panel), ":", rn)
}
act <- as.matrix(hm[, sample_cols, drop = FALSE])
storage.mode(act) <- "numeric"
rownames(act) <- make.unique(rn)
# z-score rows for diverging display when values are expression means
act_z <- t(scale(t(act)))
act_z[is.na(act_z)] <- 0
p_hm <- plot_pathway_activity_heatmap_journal(
  act_z,
  title = paste0("Pathway gene activity — mito/ER (", accession, ")"),
  cluster_rows = TRUE,
  cluster_cols = FALSE
)
delivery_save_plot(p_hm, skill_en, "heatmap", "PathwayActivity", 5.5, 5.2, fig_dir, bio_root, order = 4)

fig_map <- c(
  "通路 NES" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "NES_Pathways", order = 1), ".png"),
  "富集棒棒糖" = paste0("../图片文件/", delivery_stem(skill_en, "lollipop", "PathwayEnrich", order = 2), ".png"),
  "GSEA经典曲线" = paste0("../图片文件/", delivery_stem(skill_en, "gsea", "ClassicEnrichment", order = 3), ".png"),
  "通路活性热图" = paste0("../图片文件/", delivery_stem(skill_en, "heatmap", "PathwayActivity", order = 4), ".png")
)
interp <- paste0(
  "REAL ", accession, "：期刊 Fig3-C 棒棒糖 + Fig2/3 GSEA（绿 ES + 红蓝 rank bar + 嵌字统计）",
  " + mito/ER 通路基因热图。data_provenance=REAL。"
)
status <- "PASS"

data_html <- paste0(
  "<p><b>data_provenance: REAL</b> — accession <code>", accession, "</code>（书清项目）。</p>",
  "<p>缓存表见 <code>数据文件/real_GSE207177_*.csv</code>；完整树 <code>SHUQING_ROOT</code>=",
  shuqing_root, "。</p>",
  "<p>详见 <code>数据文件/DATA_SOURCE.md</code> / <code>PROVENANCE.md</code>。</p>"
)
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- if (file.exists(audit_path)) {
  paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")
} else {
  "<p>无 post 审计表</p>"
}
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(
  skill_en, skill_folder, status,
  data_html, audit_html, paste(sourced_note, src_note, sep = " | "), fig_map, interp, rep_file,
  blocked_reason = if (exists("blocked_reason")) blocked_reason else ""
)
writeLines(c(status, "data_provenance=REAL", paste0("accession=", accession)), file.path(rep_dir, "STATUS.txt"))
for (old in c("sample_pca.png", "sample_volcano.png", "样例报告.html")) {
  f1 <- file.path(fig_dir, old); if (file.exists(f1)) file.remove(f1)
  f2 <- file.path(rep_dir, old); if (file.exists(f2)) file.remove(f2)
}
message("DONE ", status, " — ", skill_folder, " REAL ", accession, " report=", basename(rep_file))
