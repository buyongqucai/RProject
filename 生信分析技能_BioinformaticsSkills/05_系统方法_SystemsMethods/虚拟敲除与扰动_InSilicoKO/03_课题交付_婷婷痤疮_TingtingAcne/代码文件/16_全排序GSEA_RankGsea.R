# Project-specific: Tingting acne AHR virtual-knockout ranked GSEA.
options(stringsAsFactors = FALSE)
suppressPackageStartupMessages({
  library(clusterProfiler)
  library(org.Hs.eg.db)
  library(fgsea)
  library(qvalue)
  library(ggplot2)
})

DESKTOP <- "C:/Users/10540/Desktop/\u5a77\u5a77/\u865a\u62df\u6572\u9664"
RES <- file.path(DESKTOP, "\u7ed3\u679c\u6587\u4ef6")
GSEA_ROOT <- file.path(RES, "_\u8de8\u4e9a\u7fa4", "GSEA\u5168\u6392\u5e8f_RankedGSEA")
GSEA_DATA <- file.path(GSEA_ROOT, "\u6570\u636e\u6587\u4ef6")
GSEA_FIG <- file.path(GSEA_ROOT, "\u56fe\u7247\u6587\u4ef6")
GSEA_REP <- file.path(GSEA_ROOT, "\u62a5\u544a\u6587\u4ef6")
for (d in c(GSEA_DATA, GSEA_FIG, GSEA_REP)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

KEGG_LINK <- file.path(GSEA_DATA, "08_GSEA_KEGG\u57fa\u56e0\u5173\u8054_KEGGLink.txt")
KEGG_LIST <- file.path(GSEA_DATA, "08_GSEA_KEGG\u901a\u8def\u540d\u79f0_KEGGPathways.txt")
SEED <- 20261007
MIN_SIZE <- 10
MAX_SIZE <- 500
N_PERM_SIMPLE <- 1000
EPS <- 0
TARGET <- "AHR"

safe_qvalue <- function(p) {
  p <- as.numeric(p)
  out <- rep(NA_real_, length(p))
  ok <- is.finite(p)
  if (sum(ok) >= 2) {
    q <- tryCatch(qvalue::qvalue(p[ok], pi0 = NULL)$qvalues, error = function(e) NULL)
    if (!is.null(q)) out[ok] <- q
  }
  out
}

gson_sets <- function(g) split(as.character(g@gsid2gene$gene), as.character(g@gsid2gene$gsid))
gson_names <- function(g) setNames(as.character(g@gsid2name$name), as.character(g@gsid2name$gsid))

kegg_sets <- function() {
  link <- read.delim(KEGG_LINK, header = FALSE, col.names = c("pathway", "gene"), quote = "")
  nm <- read.delim(KEGG_LIST, header = FALSE, col.names = c("pathway", "name"), quote = "")
  link$pathway <- sub("^path:", "", link$pathway)
  link$gene <- sub("^hsa:", "", link$gene)
  nm$pathway <- sub("^path:", "", nm$pathway)
  list(sets = split(link$gene, link$pathway), names = setNames(nm$name, nm$pathway))
}

map_rank <- function(path, metric) {
  raw <- read.csv(path, check.names = FALSE)
  d <- raw[!is.na(raw$gene) & nzchar(raw$gene) & raw$gene != TARGET & is.finite(raw[[metric]]), , drop = FALSE]
  rows_before_mapping <- nrow(d)
  ids <- suppressMessages(bitr(d$gene, fromType = "SYMBOL", toType = "ENTREZID", OrgDb = org.Hs.eg.db))
  d$ENTREZID <- ids$ENTREZID[match(d$gene, ids$SYMBOL)]
  mapped_rows <- sum(!is.na(d$ENTREZID))
  mapped_symbols <- length(unique(d$gene[!is.na(d$ENTREZID)]))
  unmapped_symbols <- unique(d$gene[is.na(d$ENTREZID)])
  d <- d[!is.na(d$ENTREZID), , drop = FALSE]
  d <- d[order(d[[metric]], decreasing = TRUE), , drop = FALSE]
  dup_before <- sum(duplicated(d$ENTREZID))
  d <- d[!duplicated(d$ENTREZID), , drop = FALSE]
  stats <- setNames(as.numeric(d[[metric]]), as.character(d$ENTREZID))
  symbols <- setNames(as.character(d$gene), as.character(d$ENTREZID))
  audit <- data.frame(
    input_rows = nrow(raw),
    rows_after_target_and_metric_filter = rows_before_mapping,
    mapped_rows = mapped_rows,
    mapped_symbols = mapped_symbols,
    unmapped_symbol_count = length(unmapped_symbols),
    duplicate_entrez_removed = dup_before,
    final_rank_genes = length(stats),
    unmapped_symbols = paste(unmapped_symbols, collapse = ";"),
    stringsAsFactors = FALSE
  )
  list(stats = stats, symbols = symbols, audit = audit)
}

run_gsea <- function(sets, names_map, stats, collection, score_type, engine, subtype, metric, role, seed) {
  if (!length(sets) || !length(stats)) return(NULL)
  set.seed(seed)
  res <- tryCatch(
    fgseaMultilevel(
      pathways = sets, stats = stats, minSize = MIN_SIZE, maxSize = MAX_SIZE,
      scoreType = score_type, eps = EPS, nPermSimple = N_PERM_SIMPLE,
      gseaParam = 1, BPPARAM = BiocParallel::SerialParam()
    ),
    error = function(e) {
      message("GSEA ERROR ", engine, " ", subtype, " ", metric, " ", role, " ", collection, ": ", conditionMessage(e))
      NULL
    }
  )
  if (is.null(res) || !nrow(res)) return(NULL)
  x <- as.data.frame(res)
  if ("pval" %in% names(x) && !"pvalue" %in% names(x)) x$pvalue <- x$pval
  x$leading_edge <- vapply(res$leadingEdge, function(z) paste(z, collapse = ";"), character(1))
  x$leadingEdge <- NULL
  x$Description <- unname(names_map[x$pathway])
  x$Description[is.na(x$Description)] <- x$pathway[is.na(x$Description)]
  x$qvalue <- safe_qvalue(x$pvalue)
  x$engine <- engine
  x$subtype <- subtype
  x$rank_metric <- metric
  x$score_type <- score_type
  x$role <- role
  x$collection <- collection
  x$strict_pass <- !is.na(x$padj) & x$padj < 0.05 & !is.na(x$qvalue) & x$qvalue < 0.2
  x$broad_pass_fdr25 <- !is.na(x$padj) & x$padj < 0.25
  x$nominal_p05 <- !is.na(x$pvalue) & x$pvalue < 0.05
  x$interpretation <- ifelse(
    score_type == "pos",
    "positive NES = high perturbation/KL end; not expression direction",
    "positive NES = high relative perturbation Z; not biological up/down"
  )
  x[order(x$padj, x$pvalue, -abs(x$NES), na.last = TRUE), , drop = FALSE]
}

go <- lapply(c("BP", "CC", "MF"), function(ont) {
  g <- clusterProfiler:::get_GO_data(org.Hs.eg.db, ont, "ENTREZID")
  list(sets = gson_sets(g), names = gson_names(g))
})
names(go) <- c("GO-BP", "GO-CC", "GO-MF")
collections <- c(go, list("KEGG" = kegg_sets()))

p <- function(subtype, engine, gene, metric, score_type, role, filename) {
  base <- file.path(RES, subtype, engine, gene, "\u6570\u636e\u6587\u4ef6", filename)
  list(engine = engine, subtype = subtype, gene = gene, metric = metric,
       score_type = score_type, role = role, path = base)
}
inputs <- list(
  p("TREM2 macrophage", "scTenifoldKnk_1.4.3_GPU", "AHR", "distance", "pos", "target_primary", "\u6270\u52a8_Dr.csv"),
  p("TREM2 macrophage", "scTenifoldKnk_1.4.3_GPU", "AHR", "Z", "std", "target_sensitivity", "\u6270\u52a8_Dr.csv"),
  p("M2-like macrophage", "scTenifoldKnk_1.4.3_GPU", "AHR", "distance", "pos", "target_primary", "\u6270\u52a8_Dr.csv"),
  p("M2-like macrophage", "scTenifoldKnk_1.4.3_GPU", "AHR", "Z", "std", "target_sensitivity", "\u6270\u52a8_Dr.csv"),
  p("TREM2 macrophage", "GenKI", "AHR", "KL", "pos", "target_secondary", "KL\u6392\u5e8f_RankKL.csv"),
  p("M2-like macrophage", "GenKI", "AHR", "KL", "pos", "target_secondary", "KL\u6392\u5e8f_RankKL.csv"),
  p("TREM2 macrophage", "scTenifoldKnk_1.4.3_GPU", "MGAT4A", "distance", "pos", "control", "\u6270\u52a8_Dr.csv"),
  p("M2-like macrophage", "scTenifoldKnk_1.4.3_GPU", "BID", "distance", "pos", "control", "\u6270\u52a8_Dr.csv"),
  p("TREM2 macrophage", "GenKI", "DHRS9", "KL", "pos", "control", "KL\u6392\u5e8f_RankKL.csv"),
  p("M2-like macrophage", "GenKI", "FEN1", "KL", "pos", "control", "KL\u6392\u5e8f_RankKL.csv")
)

all_results <- list()
audit_rows <- list()
id_rows <- list()
stats_store <- list()
sets_store <- list()
seed_i <- 0
for (item in inputs) {
  mapped <- map_rank(item$path, item$metric)
  key <- paste(item$engine, item$subtype, item$gene, item$metric, item$role, sep = "|")
  a <- mapped$audit
  a$engine <- item$engine; a$subtype <- item$subtype; a$target_or_control <- item$gene
  a$rank_metric <- item$metric; a$score_type <- item$score_type; a$role <- item$role
  a$input_file <- item$path
  audit_rows[[key]] <- a
  id_rows[[key]] <- data.frame(
    engine = item$engine, subtype = item$subtype, target_or_control = item$gene,
    rank_metric = item$metric, role = item$role,
    entrez = names(mapped$stats), symbol = unname(mapped$symbols[names(mapped$stats)]),
    score = unname(mapped$stats), stringsAsFactors = FALSE
  )
  stats_store[[key]] <- mapped$stats
  sets_store[[key]] <- list()
  for (collection in names(collections)) {
    seed_i <- seed_i + 1
    rr <- run_gsea(collections[[collection]]$sets, collections[[collection]]$names, mapped$stats,
                   collection, item$score_type, item$engine, item$subtype, item$metric, item$role, SEED + seed_i)
    if (!is.null(rr)) {
      rr$target_or_control <- item$gene
      all_results[[paste(key, collection, sep = "|")]] <- rr
      sets_store[[key]][[collection]] <- collections[[collection]]$sets
    }
  }
}

results <- do.call(rbind, all_results)
audit <- do.call(rbind, audit_rows)
id_map <- do.call(rbind, id_rows)
rownames(results) <- NULL; rownames(audit) <- NULL; rownames(id_map) <- NULL
write.csv(results, file.path(GSEA_DATA, "08_GSEA\u5168\u91cf\u7ed3\u679c_AllRankedGsea.csv"), row.names = FALSE)
write.csv(results[results$strict_pass %in% TRUE, , drop = FALSE], file.path(GSEA_DATA, "08_GSEA\u901a\u8fc7\u6761\u76ee_PassedGsea.csv"), row.names = FALSE)
write.csv(results[results$broad_pass_fdr25 %in% TRUE, , drop = FALSE], file.path(GSEA_DATA, "08_GSEA\u5019\u9009\u6761\u76ee_BroadFdr25.csv"), row.names = FALSE)
write.csv(audit, file.path(GSEA_DATA, "08_GSEA\u57fa\u56e0\u6620\u5c04\u5ba1\u8ba1_IDMappingAudit.csv"), row.names = FALSE)
write.csv(id_map, file.path(GSEA_DATA, "08_GSEA\u6392\u540d\u57fa\u56e0\u8868_RankedGenes.csv"), row.names = FALSE)

split_key <- unique(results[c("engine", "subtype", "target_or_control", "rank_metric", "score_type", "role")])
summary_rows <- list()
for (i in seq_len(nrow(split_key))) {
  k <- split_key[i, ]
  for (collection in names(collections)) {
    x <- results[
      results$engine == k$engine & results$subtype == k$subtype &
      results$target_or_control == k$target_or_control & results$rank_metric == k$rank_metric &
      results$role == k$role & results$collection == collection, , drop = FALSE
    ]
    summary_rows[[length(summary_rows) + 1]] <- data.frame(
      k, collection = collection, tested_terms = nrow(x), finite_p = sum(is.finite(x$pvalue)),
      strict_pass = sum(x$strict_pass %in% TRUE), broad_fdr25 = sum(x$broad_pass_fdr25 %in% TRUE),
      nominal_p05 = sum(x$nominal_p05 %in% TRUE), stringsAsFactors = FALSE
    )
  }
}
summary <- do.call(rbind, summary_rows)
write.csv(summary, file.path(GSEA_DATA, "08_GSEA\u5206\u6790\u6458\u8981_GseaSummary.csv"), row.names = FALSE)

compare_pair <- function(engine, subtype, metric, target_gene, control_gene, target_path, control_path, target_resp, control_resp) {
  a <- read.csv(target_path, check.names = FALSE)
  b <- read.csv(control_path, check.names = FALSE)
  common <- intersect(a$gene, b$gene)
  aa <- a[match(common, a$gene), ]; bb <- b[match(common, b$gene), ]
  ta <- if (file.exists(target_resp)) read.csv(target_resp, check.names = FALSE)$gene else character()
  cb <- if (file.exists(control_resp)) read.csv(control_resp, check.names = FALSE)$gene else character()
  ta <- setdiff(ta, target_gene); cb <- setdiff(cb, control_gene)
  topa <- head(aa$gene[order(aa[[metric]], decreasing = TRUE)], 20)
  topb <- head(bb$gene[order(bb[[metric]], decreasing = TRUE)], 20)
  data.frame(
    engine = engine, subtype = subtype, target = target_gene, control = control_gene,
    rank_metric = metric, target_responsive = paste(ta, collapse = ";"), control_responsive = paste(cb, collapse = ";"),
    responsive_jaccard = length(intersect(ta, cb)) / max(1, length(union(ta, cb))),
    responsive_overlap = paste(intersect(ta, cb), collapse = ";"),
    rank_spearman = suppressWarnings(cor(aa[[metric]], bb[[metric]], method = "spearman")),
    top20_overlap = length(intersect(topa, topb)), stringsAsFactors = FALSE
  )
}
rdir <- function(subtype, engine, gene) file.path(RES, subtype, engine, gene)
spec <- list(
  compare_pair("scTenifoldKnk_1.4.3_GPU", "TREM2 macrophage", "distance", "AHR", "MGAT4A",
    file.path(rdir("TREM2 macrophage", "scTenifoldKnk_1.4.3_GPU", "AHR"), "\u6570\u636e\u6587\u4ef6", "\u6270\u52a8_Dr.csv"),
    file.path(rdir("TREM2 macrophage", "scTenifoldKnk_1.4.3_GPU", "MGAT4A"), "\u6570\u636e\u6587\u4ef6", "\u6270\u52a8_Dr.csv"),
    file.path(rdir("TREM2 macrophage", "scTenifoldKnk_1.4.3_GPU", "AHR"), "\u6570\u636e\u6587\u4ef6", "\u54cd\u5e94\u57fa\u56e0_Responsive.csv"),
    file.path(rdir("TREM2 macrophage", "scTenifoldKnk_1.4.3_GPU", "MGAT4A"), "\u6570\u636e\u6587\u4ef6", "\u54cd\u5e94\u57fa\u56e0_Responsive.csv")),
  compare_pair("scTenifoldKnk_1.4.3_GPU", "M2-like macrophage", "distance", "AHR", "BID",
    file.path(rdir("M2-like macrophage", "scTenifoldKnk_1.4.3_GPU", "AHR"), "\u6570\u636e\u6587\u4ef6", "\u6270\u52a8_Dr.csv"),
    file.path(rdir("M2-like macrophage", "scTenifoldKnk_1.4.3_GPU", "BID"), "\u6570\u636e\u6587\u4ef6", "\u6270\u52a8_Dr.csv"),
    file.path(rdir("M2-like macrophage", "scTenifoldKnk_1.4.3_GPU", "AHR"), "\u6570\u636e\u6587\u4ef6", "\u54cd\u5e94\u57fa\u56e0_Responsive.csv"),
    file.path(rdir("M2-like macrophage", "scTenifoldKnk_1.4.3_GPU", "BID"), "\u6570\u636e\u6587\u4ef6", "\u54cd\u5e94\u57fa\u56e0_Responsive.csv")),
  compare_pair("GenKI", "TREM2 macrophage", "KL", "AHR", "DHRS9",
    file.path(rdir("TREM2 macrophage", "GenKI", "AHR"), "\u6570\u636e\u6587\u4ef6", "KL\u6392\u5e8f_RankKL.csv"),
    file.path(rdir("TREM2 macrophage", "GenKI", "DHRS9"), "\u6570\u636e\u6587\u4ef6", "KL\u6392\u5e8f_RankKL.csv"),
    file.path(rdir("TREM2 macrophage", "GenKI", "AHR"), "\u6570\u636e\u6587\u4ef6", "\u54cd\u5e94\u57fa\u56e0_Responsive.csv"),
    file.path(rdir("TREM2 macrophage", "GenKI", "DHRS9"), "\u6570\u636e\u6587\u4ef6", "\u54cd\u5e94\u57fa\u56e0_Responsive.csv")),
  compare_pair("GenKI", "M2-like macrophage", "KL", "AHR", "FEN1",
    file.path(rdir("M2-like macrophage", "GenKI", "AHR"), "\u6570\u636e\u6587\u4ef6", "KL\u6392\u5e8f_RankKL.csv"),
    file.path(rdir("M2-like macrophage", "GenKI", "FEN1"), "\u6570\u636e\u6587\u4ef6", "KL\u6392\u5e8f_RankKL.csv"),
    file.path(rdir("M2-like macrophage", "GenKI", "AHR"), "\u6570\u636e\u6587\u4ef6", "\u54cd\u5e94\u57fa\u56e0_Responsive.csv"),
    file.path(rdir("M2-like macrophage", "GenKI", "FEN1"), "\u6570\u636e\u6587\u4ef6", "\u54cd\u5e94\u57fa\u56e0_Responsive.csv"))
)
specificity <- do.call(rbind, spec)
write.csv(specificity, file.path(GSEA_DATA, "08_GSEA\u7279\u5f02\u6027\u8bca\u65ad_AHR\u5bf9\u7167_Specificity.csv"), row.names = FALSE)

config <- data.frame(
  parameter = c("seed", "minGSSize", "maxGSSize", "nPermSimple", "eps", "target_removed",
                "primary", "sensitivity", "secondary", "controls", "go_source", "kegg_source", "org_db"),
  value = c(SEED, MIN_SIZE, MAX_SIZE, N_PERM_SIMPLE, EPS, TARGET,
            "Knk distance scoreType=pos", "Knk Z scoreType=std", "GenKI KL scoreType=pos",
            "Knk MGAT4A/BID; GenKI DHRS9/FEN1", "clusterProfiler get_GO_data",
            "KEGG REST link/hsa/pathway + list/pathway/hsa", paste0("org.Hs.eg.db ", packageVersion("org.Hs.eg.db"))),
  stringsAsFactors = FALSE
)
write.csv(config, file.path(GSEA_DATA, "08_GSEA\u8fd0\u884c\u53c2\u6570_GseaRunConfig.csv"), row.names = FALSE)
writeLines(capture.output(sessionInfo()), file.path(GSEA_REP, "08_GSEA\u8fd0\u884c\u73af\u5883_SessionInfo.txt"))

save_plot <- function(plot, stem) {
  ggsave(file.path(GSEA_FIG, paste0(stem, ".png")), plot, width = 9, height = 6, dpi = 600, bg = "white")
  ggsave(file.path(GSEA_FIG, paste0(stem, ".svg")), plot, width = 9, height = 6, bg = "white")
}
curve_pool <- results[is.finite(results$pvalue) & results$role != "control", , drop = FALSE]
curve_pool <- curve_pool[order(!curve_pool$strict_pass, curve_pool$padj, curve_pool$pvalue, na.last = TRUE), , drop = FALSE]
curve_pool <- curve_pool[!duplicated(paste(curve_pool$engine, curve_pool$subtype, curve_pool$target_or_control, curve_pool$rank_metric, curve_pool$collection, curve_pool$pathway)), , drop = FALSE]
curve_pool <- head(curve_pool, 8)
for (i in seq_len(nrow(curve_pool))) {
  r <- curve_pool[i, ]
  key <- paste(r$engine, r$subtype, r$target_or_control, r$rank_metric, r$role, sep = "|")
  gs <- sets_store[[key]][[r$collection]]
  if (is.null(gs) || !r$pathway %in% names(gs)) next
  plot <- fgsea::plotEnrichment(gs[[r$pathway]], stats_store[[key]]) +
    labs(title = paste0(r$collection, " | ", r$Description),
         subtitle = paste0(r$engine, " | ", r$subtype, " | ", r$rank_metric,
                           " | padj=", signif(r$padj, 3), " | NES=", signif(r$NES, 3),
                           if (isTRUE(r$strict_pass)) " | FDR-pass" else " | exploratory"),
         x = "Rank metric position", y = "Running enrichment score") +
    theme_bw(base_size = 11)
  stem <- sprintf("08_GSEA\u66f2\u7ebf_%02d_%s_%s_%s", i,
                  gsub("[^A-Za-z0-9]+", "_", r$engine), gsub("[^A-Za-z0-9]+", "_", r$subtype),
                  gsub("[^A-Za-z0-9]+", "_", r$pathway))
  save_plot(plot, stem)
}
message("RANKED_GSEA_DONE rows=", nrow(results), " strict=", sum(results$strict_pass %in% TRUE))