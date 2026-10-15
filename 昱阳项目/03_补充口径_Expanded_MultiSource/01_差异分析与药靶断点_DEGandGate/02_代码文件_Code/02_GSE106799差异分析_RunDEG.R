# 昱阳项目专用：GSE106799 limma DEG + PCA + 火山图 + 热图
# 已引用：RNA-seq + DataAuthenticity + VizStandards + DeliveryStandards
# 阈值（计划锁定）：|logFC|>=1 且 P.Value<0.05（主阈值；adj 一并输出）

suppressPackageStartupMessages({
  library(GEOquery)
  library(Biobase)
  library(limma)
  library(ggplot2)
})

root <- "E:/RProject/昱阳项目/02_差异分析与药靶断点_DEGandGate"
raw_geo <- file.path(root, "01_数据文件_Data/01_初始数据_RawInitial/01_GEO_GSE106799")
tab_dir <- file.path(root, "01_数据文件_Data/02_结果数据_ResultTables")
fig_dir <- file.path(root, "03_图片文件_Figures")
rep_dir <- file.path(root, "04_报告文件_Reports")
dir.create(tab_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
del <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一交付规范_DeliveryStandards/脚本_scripts/规范_出图与命名_PlotNaming.R"
source(viz, encoding = "UTF-8")
source(del, encoding = "UTF-8")

matrix_gz <- file.path(raw_geo, "GSE106799_series_matrix.txt.gz")
stopifnot(file.exists(matrix_gz))

# ---- load GEO from local matrix (no remote GPL fetch) ----
gse <- getGEO(filename = matrix_gz, GSEMatrix = TRUE, getGPL = FALSE)
es <- if (is.list(gse)) gse[[1]] else gse
expr <- exprs(es)
pdata <- pData(es)

title <- as.character(pdata$title)
grp <- ifelse(grepl("^Propofol", title, ignore.case = TRUE), "Propofol",
              ifelse(grepl("^Control", title, ignore.case = TRUE), "Control", NA_character_))

meta <- data.frame(
  sample = colnames(expr),
  geo_accession = as.character(pdata$geo_accession),
  title = title,
  source_name = as.character(pdata$source_name_ch1),
  group = grp,
  stringsAsFactors = FALSE
)
write.csv(meta, file.path(tab_dir, "01_样本元数据_SampleMeta_GSE106799.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

# authenticity checks
n_ok <- !any(is.na(meta$group)) && length(unique(meta$group)) == 2L
n_per <- table(meta$group)
auth <- data.frame(
  check = c("accession", "n_samples", "groups_parsed", "n_Control", "n_Propofol", "matrix_genes", "matrix_samples"),
  value = c("GSE106799", nrow(meta), n_ok, unname(n_per["Control"]), unname(n_per["Propofol"]),
            nrow(expr), ncol(expr)),
  stringsAsFactors = FALSE
)
write.csv(auth, file.path(tab_dir, "02_真实性核对_AuthenticityCheck.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")
stopifnot(n_ok)
stopifnot(all(c("Control", "Propofol") %in% names(n_per)))
stopifnot(all(n_per >= 3))

# gene symbols: local GPL24261 soft or supplementary xls
parse_gpl_soft <- function(path) {
  # NCBI sometimes serves soft as plain text even with .gz suffix
  magic <- readBin(path, what = "raw", n = 2)
  con <- if (length(magic) >= 2 && magic[1] == as.raw(0x1f) && magic[2] == as.raw(0x8b)) {
    gzfile(path, open = "rt")
  } else {
    file(path, open = "rt", encoding = "UTF-8")
  }
  on.exit(close(con))
  lines <- readLines(con, warn = FALSE)
  i0 <- grep("^!platform_table_begin", lines)[1]
  i1 <- grep("^!platform_table_end", lines)[1]
  if (is.na(i0) || is.na(i1)) stop("GPL table markers not found: ", path)
  tab <- utils::read.delim(text = lines[(i0 + 1):(i1 - 1)], stringsAsFactors = FALSE, check.names = FALSE)
  id_col <- names(tab)[1]
  sym_col <- NULL
  for (cand in c("GeneSymbol", "Gene Symbol", "GENE_SYMBOL", "Symbol", "gene_symbol", "ORF", "GENE_NAME")) {
    if (cand %in% names(tab)) { sym_col <- cand; break }
  }
  if (is.null(sym_col)) {
    # fuzzy
    hit <- grep("symbol|gene", names(tab), ignore.case = TRUE, value = TRUE)
    if (length(hit)) sym_col <- hit[1]
  }
  if (is.null(sym_col)) {
    message("GPL columns: ", paste(names(tab), collapse = ", "))
    stop("No gene symbol column in GPL")
  }
  data.frame(ID = as.character(tab[[id_col]]), symbol = as.character(tab[[sym_col]]),
             stringsAsFactors = FALSE)
}

gpl_candidates <- c(
  file.path(raw_geo, "GPL24261.soft"),
  file.path(raw_geo, "GPL24261.soft.gz")
)
xls_gz <- file.path(raw_geo, "GSE106799_mRNA.xls.gz")
annot <- NULL
for (gpl_path in gpl_candidates) {
  if (file.exists(gpl_path) && file.info(gpl_path)$size > 1000) {
    message("Annotating from ", basename(gpl_path))
    annot <- parse_gpl_soft(gpl_path)
    break
  }
}
if (is.null(annot) && file.exists(xls_gz) && file.info(xls_gz)$size > 1000) {
  message("Annotating from supplementary xls.gz")
  xls_tmp <- tempfile(fileext = ".xls")
  R.utils::gunzip(xls_gz, destname = xls_tmp, remove = FALSE, overwrite = TRUE)
  if (requireNamespace("readxl", quietly = TRUE)) {
    x <- as.data.frame(readxl::read_excel(xls_tmp))
  } else if (requireNamespace("xlsx", quietly = TRUE)) {
    x <- xlsx::read.xlsx(xls_tmp, sheetIndex = 1)
  } else {
    # try CSV-like via gdata or skip
    stop("Need readxl to parse xls; install.packages('readxl')")
  }
  message("xls columns: ", paste(names(x), collapse = ", "))
  id_col <- names(x)[grepl("ID|Probe|ASMM", names(x), ignore.case = TRUE)][1]
  sym_col <- names(x)[grepl("Gene.?Symbol|Symbol|GeneName", names(x), ignore.case = TRUE)][1]
  annot <- data.frame(ID = as.character(x[[id_col]]), symbol = as.character(x[[sym_col]]),
                      stringsAsFactors = FALSE)
}
stopifnot(!is.null(annot))

annot$symbol <- vapply(annot$symbol, function(s) {
  s <- as.character(s)
  if (is.na(s) || !nzchar(s) || s %in% c("---", "NA", "N/A")) return(NA_character_)
  s <- sub("//.*$", "", s)
  s <- strsplit(s, " /// |;|\\|", perl = TRUE)[[1]][1]
  trimws(s)
}, character(1))

probe_ids <- rownames(expr)
sym_map <- annot$symbol[match(probe_ids, annot$ID)]
# collapse probes -> gene by max AveExpr later; first keep best variance probe
ok <- !is.na(sym_map) & nzchar(sym_map)
expr_ok <- expr[ok, , drop = FALSE]
syms <- sym_map[ok]
# pick probe with highest mean expression per gene
ave <- rowMeans(expr_ok)
ord <- order(ave, decreasing = TRUE)
expr_ok <- expr_ok[ord, , drop = FALSE]
syms <- syms[ord]
keep <- !duplicated(syms)
expr2 <- expr_ok[keep, , drop = FALSE]
rownames(expr2) <- syms[keep]
message("Mapped genes: ", nrow(expr2), " / probes kept ", sum(ok))

# series matrix already quantile-normalized log-scale intensities (~5–15)
message("expr range: ", paste(round(range(expr2, na.rm = TRUE), 2), collapse = " .. "))

# ---- PCA ----
pca <- prcomp(t(expr2), center = TRUE, scale. = TRUE)
var_exp <- summary(pca)$importance[2, 1:2] * 100
pca_df <- data.frame(
  sample = rownames(pca$x),
  PC1 = pca$x[, 1],
  PC2 = pca$x[, 2],
  group = meta$group[match(rownames(pca$x), meta$sample)],
  stringsAsFactors = FALSE
)
write.csv(pca_df, file.path(tab_dir, "03_PCA坐标_PcaCoordinates.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

p_pca <- plot_pca_journal(
  pca_df, title = sprintf("PCA (PC1 %.1f%%, PC2 %.1f%%)", var_exp[1], var_exp[2])
)
ggsave(file.path(fig_dir, "01_PCA质控_PcaQc.png"), p_pca, width = 5, height = 4, dpi = 600)
ggsave(file.path(fig_dir, "01_PCA质控_PcaQc.svg"), p_pca, width = 5, height = 4)

# ---- limma DEG ----
group <- factor(meta$group, levels = c("Control", "Propofol"))
design <- model.matrix(~ 0 + group)
colnames(design) <- levels(group)
fit <- lmFit(expr2, design)
contrast <- makeContrasts(Propofol - Control, levels = design)
fit2 <- eBayes(contrasts.fit(fit, contrast))
tt <- topTable(fit2, number = Inf, sort.by = "P")
tt$gene <- rownames(tt)
tt <- tt[, c("gene", "logFC", "AveExpr", "t", "P.Value", "adj.P.Val", "B")]

write.csv(tt, file.path(tab_dir, "04_全基因差异_AllGenes_limma.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

# main threshold per plan: |logFC|>=1 & P.Value<0.05
deg <- tt[abs(tt$logFC) >= 1 & tt$P.Value < 0.05, , drop = FALSE]
deg$direction <- ifelse(deg$logFC > 0, "up", "down")
write.csv(deg, file.path(tab_dir, "05_差异基因_DEG_mainThreshold.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

# volcano: journal helper expects adj.P.Val column name; use raw P to match main DEG cut
vol_df <- data.frame(
  gene = tt$gene,
  logFC = tt$logFC,
  adj.P.Val = tt$P.Value,
  stringsAsFactors = FALSE
)
p_vol <- plot_volcano_journal(
  vol_df,
  logfc_cut = 1, p_cut = 0.05,
  title = "Propofol vs Control (P7 hippocampus)"
) + ggplot2::labs(y = expression(-log[10]~italic(P)))
ggsave(file.path(fig_dir, "02_火山图_Volcano.png"), p_vol, width = 5.5, height = 4.5, dpi = 600)
ggsave(file.path(fig_dir, "02_火山图_Volcano.svg"), p_vol, width = 5.5, height = 4.5)

# heatmap top DEGs by |logFC| among significant
top_n <- min(50L, nrow(deg))
if (top_n >= 2) {
  deg_ord <- deg[order(abs(deg$logFC), decreasing = TRUE), , drop = FALSE]
  genes_hm <- utils::head(deg_ord$gene, top_n)
  mat <- expr2[genes_hm, , drop = FALSE]
  # z-score rows
  mat_z <- t(scale(t(mat)))
  mat_z[is.na(mat_z)] <- 0
  # order samples Control then Propofol
  ord <- order(meta$group, meta$sample)
  mat_z <- mat_z[, ord, drop = FALSE]
  ann <- data.frame(Group = meta$group[ord])
  rownames(ann) <- colnames(mat_z)
  png(file.path(fig_dir, "03_差异基因热图_DegHeatmap.png"), width = 2200, height = 2600, res = 300)
  pheatmap::pheatmap(
    mat_z,
    annotation_col = ann,
    cluster_cols = FALSE,
    cluster_rows = TRUE,
    show_colnames = TRUE,
    fontsize_row = 7,
    fontsize_col = 8,
    color = colorRampPalette(c("#2166AC", "#F7F7F7", "#B2182B"))(100),
    border_color = NA,
    main = "Top DEGs (z-score)"
  )
  # force black labels via grid - pheatmap uses gpar; set cex
  dev.off()
  # svg via pdf device not ideal; save csv of matrix for audit
  write.csv(cbind(gene = rownames(mat_z), mat_z),
            file.path(tab_dir, "06_热图矩阵_HeatmapMatrix_zscore.csv"),
            row.names = FALSE, fileEncoding = "UTF-8")
} else {
  message("Too few DEGs for heatmap")
}

summ <- data.frame(
  n_genes_tested = nrow(tt),
  n_deg = nrow(deg),
  n_up = sum(deg$direction == "up"),
  n_down = sum(deg$direction == "down"),
  threshold = "|logFC|>=1 & P.Value<0.05",
  accession = "GSE106799",
  stringsAsFactors = FALSE
)
write.csv(summ, file.path(tab_dir, "07_DEG数量摘要_DegSummary.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

status <- sprintf(paste(
  "STATUS: DEG_DONE",
  "accession: GSE106799",
  "data_provenance: REAL",
  "n_Control: %s",
  "n_Propofol: %s",
  "n_deg: %s (up %s / down %s)",
  "threshold: |logFC|>=1 & P.Value<0.05",
  "figures: 01_PCA 02_Volcano 03_Heatmap",
  "updated: %s",
  sep = "\n"
), n_per["Control"], n_per["Propofol"], nrow(deg), summ$n_up, summ$n_down, format(Sys.time(), "%Y-%m-%d %H:%M"))
writeLines(status, file.path(rep_dir, "01_STATUS.txt"))
message(status)
