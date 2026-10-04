# Extra atlas figures from existing virtual-KO tables plus Control expression.
# English plot text. SVG+PNG. Computational prediction only.
options(stringsAsFactors = FALSE)
vko <- "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除"
arch <- "C:/Users/10540/Desktop/琪乐无穷/五亚群留档"
raw_dir <- file.path(vko, "数据文件")
tab_dir <- file.path(arch, "结果文件", "_跨亚群", "scTenifoldKnk", "数据文件")
fig_dir <- file.path(arch, "结果文件", "_跨亚群", "scTenifoldKnk", "图片文件")
viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
if (file.exists(viz)) source(viz, encoding = "UTF-8")
suppressPackageStartupMessages(library(ggplot2))
if (!exists("theme_journal")) theme_journal <- function(...) theme_bw()
fill1 <- if (exists("bioinfo_palette")) bioinfo_palette[1] else "#4C78A8"

save_plot <- function(p, stem, w = 7, h = 5) {
  ggplot2::ggsave(file.path(fig_dir, paste0(stem, ".png")), p, width = w, height = h, dpi = 600, limitsize = FALSE)
  ggplot2::ggsave(file.path(fig_dir, paste0(stem, ".svg")), p, width = w, height = h, limitsize = FALSE)
}

dr <- read.csv(file.path(tab_dir, "04_扰动基因_五亚群_Cplx2DrAll.csv"), check.names = FALSE)
dr <- dr[dr$gene != "Cplx2", , drop = FALSE]
subtypes <- c("cLTMR", "NF1", "NP", "PEP", "TRPM8")

# 02 expression
message("expression")
meta <- read.csv(gzfile(file.path(raw_dir, "01_细胞注释_CellMeta_GSE197289.csv.gz")), check.names = FALSE)
counts <- readRDS(gzcon(gzfile(file.path(raw_dir, "02_表达矩阵_Counts_GSE197289.RDS.gz"), "rb")))
meta <- meta[match(colnames(counts), meta$V1), , drop = FALSE]
keep <- meta$model == "Control" & meta$subtype %in% subtypes
expr <- data.frame(
  subtype = meta$subtype[keep],
  log1p_count = log1p(as.numeric(counts["Cplx2", keep])),
  stringsAsFactors = FALSE
)
expr$subtype <- factor(expr$subtype, levels = subtypes)
p2 <- ggplot(expr, aes(subtype, log1p_count)) +
  geom_violin(fill = fill1, color = NA, scale = "width") +
  geom_boxplot(width = 0.12, outlier.shape = NA, fill = "white") +
  labs(title = "Cplx2 expression in control TG subtypes", x = NULL, y = "log1p(count)") +
  theme_journal()
save_plot(p2, "02_小提琴图_对照亚群表达_Cplx2Violin")

# 07 top-100 overlap
topn <- lapply(subtypes, function(s) {
  d <- dr[dr$subtype == s, , drop = FALSE]
  d <- d[order(d$distance, decreasing = TRUE), , drop = FALSE]
  head(d$gene, 100)
})
names(topn) <- subtypes
jac <- matrix(NA_real_, length(subtypes), length(subtypes), dimnames = list(subtypes, subtypes))
for (i in subtypes) for (j in subtypes) {
  a <- topn[[i]]; b <- topn[[j]]
  jac[i, j] <- length(intersect(a, b)) / length(union(a, b))
}
write.csv(jac, file.path(tab_dir, "07_重叠_Top100Jaccard_Cplx2Overlap.csv"))
jac_df <- as.data.frame(as.table(jac))
names(jac_df) <- c("subtype_a", "subtype_b", "jaccard")
p7 <- ggplot(jac_df, aes(subtype_a, subtype_b, fill = jaccard)) +
  geom_tile(color = "white") +
  geom_text(aes(label = sprintf("%.2f", jaccard)), size = 3) +
  scale_fill_gradient(low = "white", high = fill1, limits = c(0, 1)) +
  labs(title = "Overlap of top 100 predicted genes", x = NULL, y = NULL, fill = "Jaccard") +
  theme_journal() +
  theme(axis.text.x = element_text(angle = 40, hjust = 1))
save_plot(p7, "07_热图_亚群重叠_Cplx2Jaccard", w = 7, h = 6)

# rank heatmap of genes that are in any subtype top 15
top15 <- unique(unlist(lapply(topn, head, 15)))
rank_mat <- sapply(subtypes, function(s) {
  d <- dr[dr$subtype == s, c("gene", "distance")]
  d <- d[order(d$distance, decreasing = TRUE), ]
  r <- match(top15, d$gene)
  setNames(r, top15)
})
rank_df <- as.data.frame(as.table(rank_mat))
names(rank_df) <- c("gene", "subtype", "rank")
rank_df$rank[!is.na(rank_df$rank) & rank_df$rank > 50] <- NA
p7b <- ggplot(rank_df, aes(subtype, gene, fill = rank)) +
  geom_tile() +
  scale_fill_gradient(low = fill1, high = "white", na.value = "grey92") +
  labs(title = "Rank of leading predicted genes", x = NULL, y = NULL, fill = "Rank") +
  theme_journal() +
  theme(axis.text.x = element_text(angle = 40, hjust = 1))
save_plot(p7b, "07_热图_基因排名_Cplx2Rank", w = 7, h = 8)

# 05 exploratory enrichR on top 50, not the FDR set
message("enrichment")
suppressPackageStartupMessages(library(enrichR))
focus <- c("synaptic vesicle", "SNARE", "neurotransmitter")
enr_rows <- list()
for (s in subtypes) {
  genes <- head(topn[[s]], 50)
  en <- try(enrichr(genes, "GO_Biological_Process_2023"), silent = TRUE)
  if (inherits(en, "try-error")) {
    message("enrichR failed ", s)
    next
  }
  tab <- en[["GO_Biological_Process_2023"]]
  if (is.null(tab) || !nrow(tab)) next
  hit <- grepl(paste(focus, collapse = "|"), tab$Term, ignore.case = TRUE)
  keep <- tab[hit | seq_len(nrow(tab)) <= 8, , drop = FALSE]
  keep$subtype <- s
  keep$gene_list <- "top50_by_distance_not_FDR"
  enr_rows[[s]] <- keep
}
if (length(enr_rows)) {
  enr <- do.call(rbind, enr_rows)
  write.csv(enr, file.path(tab_dir, "05_富集_Top50_Cplx2Enrich.csv"), row.names = FALSE)
  focus_df <- enr[grepl(paste(focus, collapse = "|"), enr$Term, ignore.case = TRUE), , drop = FALSE]
  if (nrow(focus_df)) {
    focus_df$neglog <- -log10(as.numeric(focus_df$Adjusted.P.value) + 1e-300)
    p5 <- ggplot(focus_df, aes(neglog, reorder(Term, neglog))) +
      geom_col(fill = fill1) +
      facet_wrap(~ subtype, scales = "free_y") +
      labs(
        title = "Rank-based GO terms (top 50 genes, not FDR set)",
        x = "-log10(adjusted P)", y = NULL
      ) +
      theme_journal()
    save_plot(p5, "05_柱状图_探索富集_Cplx2Enrich", w = 11, h = 7)
  } else {
    message("no focus terms in top enrichments")
  }
}

message("FIG_DONE")
