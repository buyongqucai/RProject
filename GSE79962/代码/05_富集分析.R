source("配置.R", encoding = "UTF-8")
setup_script_env()


suppressPackageStartupMessages({
  library(clusterProfiler)
  library(tidyverse)
  library(ggplot2)
  library(cfg$org_db, character.only = TRUE)
})

prefix <- file.path(PATHS$中间数据, DATASET)
deg_sig <- readRDS(paste0(prefix, "_deg_sig.rds"))

if (nrow(deg_sig) == 0) {
  stop("No significant DEGs found. Consider relaxing thresholds in config.R.")
}

genes_up <- deg_sig %>% filter(log2FC > 0) %>% pull(gene)
genes_down <- deg_sig %>% filter(log2FC < 0) %>% pull(gene)
genes_all <- deg_sig$gene

message("Enrichment input: ", length(genes_all), " DEGs (",
        length(genes_up), " up, ", length(genes_down), " down)")

# Convert gene symbols to Entrez IDs
map_to_entrez <- function(symbols) {
  org_pkg <- get(cfg$org_db, envir = asNamespace(cfg$org_db))
  suppressMessages(
    bitr(symbols, fromType = "SYMBOL", toType = "ENTREZID", OrgDb = org_pkg)
  )
}

entrez_all <- map_to_entrez(genes_all)
entrez_up <- map_to_entrez(genes_up)
entrez_down <- map_to_entrez(genes_down)

run_go <- function(entrez_ids, label) {
  if (nrow(entrez_ids) < 3) {
    message("Skipping GO for ", label, ": fewer than 3 mapped genes.")
    return(NULL)
  }
  enrichGO(
    gene = entrez_ids$ENTREZID,
    OrgDb = get(cfg$org_db, envir = asNamespace(cfg$org_db)),
    ont = "BP",
    pAdjustMethod = "BH",
    pvalueCutoff = 0.05,
    qvalueCutoff = 0.2,
    readable = TRUE
  )
}

run_kegg <- function(entrez_ids, label) {
  if (nrow(entrez_ids) < 3) {
    message("Skipping KEGG for ", label, ": fewer than 3 mapped genes.")
    return(NULL)
  }
  enrichKEGG(
    gene = entrez_ids$ENTREZID,
    organism = cfg$kegg_org,
    pAdjustMethod = "BH",
    pvalueCutoff = 0.05,
    qvalueCutoff = 0.2
  )
}

ego_all <- run_go(entrez_all, "all DEGs")
ekegg_all <- run_kegg(entrez_all, "all DEGs")

save_and_plot <- function(enrich_result, out_prefix, title) {
  if (is.null(enrich_result) || nrow(as.data.frame(enrich_result)) == 0) {
    message("No enrichment results for ", out_prefix)
    return(invisible(NULL))
  }

  df <- as.data.frame(enrich_result)
  write.csv(df, file.path(PATHS$tables, paste0(out_prefix, ".csv")), row.names = FALSE)

  n_show <- min(15, nrow(df))
  p <- dotplot(enrich_result, showCategory = n_show) +
    ggtitle(title) +
    theme(axis.text.y = element_text(size = 8))

  ggsave(
    file.path(PATHS$figures, paste0(out_prefix, ".pdf")),
    p, width = 10, height = max(5, n_show * 0.35)
  )
  message("Saved: ", out_prefix)
}

save_and_plot(ego_all, paste0(DATASET, "_GO生物过程"), paste(DATASET, "GO Biological Process"))
save_and_plot(ekegg_all, paste0(DATASET, "_KEGG通路"), paste(DATASET, "KEGG Pathways"))

# Separate up/down GO if enough genes
ego_up <- run_go(entrez_up, "upregulated")
ego_down <- run_go(entrez_down, "downregulated")
save_and_plot(ego_up, paste0(DATASET, "_GO生物过程_上调"), paste(DATASET, "GO BP - Upregulated"))
save_and_plot(ego_down, paste0(DATASET, "_GO生物过程_下调"), paste(DATASET, "GO BP - Downregulated"))

message("Done: 05_enrichment.R")