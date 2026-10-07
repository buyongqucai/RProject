# -*- coding: utf-8 -*-
args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args)) normalizePath(args[1]) else normalizePath(file.path(getwd()))
skill <- "E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology"
viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
delivery <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一交付规范_DeliveryStandards/脚本_scripts/规范_出图与命名_PlotNaming.R"
source(viz)
source(delivery)
source(file.path(skill, "脚本_scripts/03_STRING与网络图_StringNetwork.R"))
source(file.path(skill, "脚本_scripts/04_交付网络布局_DeliveryNetworkLayouts.R"))

data_dir <- file.path(root, "数据")
met_dir <- file.path(data_dir, "代谢物")
ppi_dir <- file.path(data_dir, "PPI")
enrich_dir <- file.path(data_dir, "富集分析")
fig_dir <- file.path(root, "图片")
dir.create(ppi_dir, recursive=TRUE, showWarnings=FALSE)
dir.create(enrich_dir, recursive=TRUE, showWarnings=FALSE)
dir.create(fig_dir, recursive=TRUE, showWarnings=FALSE)

read_genes <- function(path) {
  x <- read.csv(path, stringsAsFactors=FALSE, check.names=FALSE, fileEncoding="UTF-8")
  sort(unique(toupper(trimws(as.character(x$gene)))))
}
main_genes <- read_genes(file.path(data_dir, "C_main_evidence_priority_H_plus_M.csv"))
full_genes <- read_genes(file.path(data_dir, "C_full_gutmgene_human_H_plus_M.csv"))
disease <- read.csv("E:/RProject/努力学习项目/交付文件/数据/疾病/疾病靶点合并.csv", stringsAsFactors=FALSE, check.names=FALSE, fileEncoding="UTF-8")
disease_genes <- sort(unique(toupper(trimws(as.character(disease$gene)))))

fetch_and_plot_ppi <- function(genes, label, cache_name, plot_stem=NULL) {
  cache <- file.path(ppi_dir, cache_name)
  ppi <- np_fetch_string_ppi(genes, required_score=900L, cache_path=cache, force=FALSE)
  write.csv(ppi, file.path(ppi_dir, paste0(label, "_STRING原始边.csv")), row.names=FALSE, fileEncoding="UTF-8")
  if (!is.null(plot_stem) && nrow(ppi)) {
    p <- np_plot_string_ppi(ppi, title=if (label=="Main") "STRING PPI of shared targets" else "STRING PPI sensitivity network", label_top_n=NULL, min_score=900L, drop_isolates=TRUE, layout="concentric", max_nodes=200L)
    save_plot_pub(p, stem=plot_stem, width=7.2, height=7.2, dpi=600, out_dir=fig_dir)
  }
  ppi
}
ppi_main <- fetch_and_plot_ppi(main_genes, "Main", "STRING_Main_score900.tsv", "01_PPI网络_核心三源靶点_PpiCoreNetwork")
ppi_full <- fetch_and_plot_ppi(full_genes, "Full", "STRING_Full_score900.tsv", NULL)

suppressPackageStartupMessages({
  library(clusterProfiler)
  library(org.Hs.eg.db)
})
map_entrez <- function(genes) {
  x <- suppressWarnings(bitr(genes, fromType="SYMBOL", toType="ENTREZID", OrgDb=org.Hs.eg.db))
  unique(x$ENTREZID)
}
run_enrich <- function(genes, prefix) {
  q <- map_entrez(genes)
  u <- map_entrez(disease_genes)
  go <- enrichGO(gene=q, universe=u, OrgDb=org.Hs.eg.db, ont="ALL", pAdjustMethod="BH", pvalueCutoff=0.05, qvalueCutoff=0.20, readable=TRUE)
  godf <- as.data.frame(go)
  if (nrow(godf)) {
    godf$ONTOLOGY <- factor(godf$ONTOLOGY, levels=c("BP","CC","MF"))
    godf <- godf[order(godf$ONTOLOGY, godf$p.adjust), ]
  }
  kegg <- tryCatch(enrichKEGG(gene=q, universe=u, organism="hsa", pAdjustMethod="BH", pvalueCutoff=0.05, qvalueCutoff=0.20), error=function(e) NULL)
  kedf <- if (is.null(kegg)) data.frame() else as.data.frame(kegg)
  write.csv(godf, file.path(enrich_dir, paste0(prefix, "_GO富集全表.csv")), row.names=FALSE, fileEncoding="UTF-8")
  write.csv(kedf, file.path(enrich_dir, paste0(prefix, "_KEGG富集全表.csv")), row.names=FALSE, fileEncoding="UTF-8")
  write.csv(data.frame(set=c("input","universe"), n=c(length(q), length(u))), file.path(enrich_dir, paste0(prefix, "_富集背景审计.csv")), row.names=FALSE, fileEncoding="UTF-8")
  list(go=godf, kegg=kedf, n_query=length(q), n_universe=length(u))
}
en_main <- run_enrich(main_genes, "Main")
en_full <- run_enrich(full_genes, "Full")

if (nrow(en_main$go)) {
  pg <- plot_enrich_hbar_facet(en_main$go, top_n=8, title="GO enrichment of shared targets")
  save_plot_pub(pg, stem="02_GO富集_核心三源靶点_GoEnrichment", width=7.2, height=8.2, dpi=600, out_dir=fig_dir)
}
if (nrow(en_main$kegg)) {
  pk <- plot_enrich_dot_journal(en_main$kegg, top_n=20, title="KEGG pathway enrichment of shared targets")
  save_plot_pub(pk, stem="03_KEGG富集_核心三源靶点_KeggEnrichment", width=7.2, height=7.2, dpi=600, out_dir=fig_dir)
}

summary <- data.frame(
  analysis=c("Main","Full"),
  input_genes=c(length(main_genes), length(full_genes)),
  ppi_edges=c(nrow(ppi_main), nrow(ppi_full)),
  entrez_query=c(en_main$n_query, en_full$n_query),
  universe_entrez=c(en_main$n_universe, en_full$n_universe),
  go_terms=c(nrow(en_main$go), nrow(en_full$go)),
  kegg_terms=c(nrow(en_main$kegg), nrow(en_full$kegg))
)
write.csv(summary, file.path(data_dir, "机制层_PPI富集摘要.csv"), row.names=FALSE, fileEncoding="UTF-8")
print(summary)
