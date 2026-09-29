# CPLX2 virtual KO — Control TG sensory subtypes that passed H5/H6
# data_provenance=REAL GSE197289 mouse snRNA
# Claim: computational prediction, not a trigeminal-neuralgia KO experiment.
options(stringsAsFactors = FALSE)
set.seed(20260929)

root <- "C:/Users/10540/Desktop/琪乐无穷/CPLX2虚拟敲除_Cplx2VirtualKO"
raw_dir <- file.path(root, "数据文件")
code_dir <- file.path(root, "代码文件")
res_dir <- file.path(root, "结果文件")
tab_dir <- file.path(res_dir, "数据文件")
fig_dir <- file.path(res_dir, "图片文件")
rep_dir <- file.path(res_dir, "报告文件")
for (d in c(tab_dir, fig_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
if (file.exists(viz)) source(viz, encoding = "UTF-8")

suppressPackageStartupMessages({
  library(Matrix)
  library(ggplot2)
  library(scTenifoldKnk)
})

save_plot <- function(p, stem, w = 7, h = 5) {
  ggplot2::ggsave(file.path(fig_dir, paste0(stem, ".png")), p, width = w, height = h, dpi = 600)
  ggplot2::ggsave(file.path(fig_dir, paste0(stem, ".svg")), p, width = w, height = h)
}

message("loading counts")
meta <- read.csv(gzfile(file.path(raw_dir, "01_细胞注释_CellMeta_GSE197289.csv.gz")), check.names = FALSE)
counts <- readRDS(gzcon(gzfile(file.path(raw_dir, "02_表达矩阵_Counts_GSE197289.RDS.gz"), "rb")))
stopifnot(inherits(counts, "dgCMatrix"))
meta <- meta[match(colnames(counts), meta$V1), , drop = FALSE]
stopifnot(!anyNA(meta$V1))

targets <- c("cLTMR", "NF1", "NP", "PEP", "TRPM8")
keep <- meta$model == "Control" & meta$subtype %in% targets
sub_meta <- meta[keep, , drop = FALSE]
sub_counts <- counts[, keep, drop = FALSE]
message("control target cells ", ncol(sub_counts))

det <- do.call(rbind, lapply(targets, function(g) {
  idx <- sub_meta$subtype == g
  v <- as.numeric(sub_counts["Cplx2", idx])
  data.frame(
    subtype = g, n_cells = length(v), n_detected = sum(v > 0),
    detection_rate = mean(v > 0), mean_count = mean(v),
    stringsAsFactors = FALSE
  )
}))
write.csv(det, file.path(tab_dir, "03_检出率_对照五亚群_Cplx2DetectionControl.csv"), row.names = FALSE)

if (exists("theme_journal")) {
  p <- ggplot(det, aes(detection_rate, reorder(subtype, detection_rate))) +
    geom_col(fill = if (exists("bioinfo_palette")) bioinfo_palette[1] else "#4C78A8", width = 0.72) +
    labs(title = "Cplx2 detection in control TG subtypes", x = "Detection rate", y = NULL) +
    theme_journal()
} else {
  p <- ggplot(det, aes(detection_rate, reorder(subtype, detection_rate))) +
    geom_col(width = 0.72) +
    labs(title = "Cplx2 detection in control TG subtypes", x = "Detection rate", y = NULL) +
    theme_bw()
}
save_plot(p, "03_柱状图_对照亚群检出率_Cplx2DetectionBar")

prep_matrix <- function(mat, max_genes = 1000) {
  rs <- Matrix::rowSums(mat > 0)
  mat <- mat[rs >= 25, , drop = FALSE]
  if (!"Cplx2" %in% rownames(mat)) stop("Cplx2 dropped by filter")
  if (nrow(mat) > max_genes) {
    score <- Matrix::rowMeans(mat)
    score["Cplx2"] <- Inf
    mat <- mat[order(score, decreasing = TRUE)[seq_len(max_genes)], , drop = FALSE]
  }
  as.matrix(mat)
}

run_one <- function(subtype, gKO) {
  idx <- which(sub_meta$subtype == subtype)
  mat <- prep_matrix(sub_counts[, idx, drop = FALSE])
  n_cells <- ncol(mat)
  n_use <- min(200L, n_cells - 1L)
  message("KO ", subtype, " ", gKO, " genes ", nrow(mat), " cells ", n_cells, " nCells ", n_use)
  t0 <- proc.time()
  res <- scTenifoldKnk(
    countMatrix = mat,
    gKO = gKO,
    qc = TRUE,
    qc_minLibSize = 500,
    qc_minPCT = 0.05,
    nc_nNet = 3,
    nc_nCells = n_use,
    td_K = 3,
    nCores = max(1L, parallel::detectCores() - 1L)
  )
  elapsed <- (proc.time() - t0)[["elapsed"]]
  dr <- res$diffRegulation
  if (is.null(dr)) dr <- res[["dRegulation"]]
  if (is.null(dr)) {
    saveRDS(res, file.path(tab_dir, paste0("debug_", subtype, "_", gKO, ".rds")))
    stop("unexpected scTenifoldKnk return for ", subtype)
  }
  dr$subtype <- subtype
  dr$gKO <- gKO
  dr$elapsed_sec <- elapsed
  dr$n_genes_in <- nrow(mat)
  dr$n_cells_in <- n_cells
  dr
}

all_dr <- list()
for (g in targets) {
  dr <- run_one(g, "Cplx2")
  all_dr[[g]] <- dr
  write.csv(dr, file.path(tab_dir, paste0("04_扰动基因_", g, "_Cplx2Dr.csv")), row.names = FALSE)
  message("saved ", g)
}

dr_all <- do.call(rbind, all_dr)
write.csv(dr_all, file.path(tab_dir, "04_扰动基因_五亚群_Cplx2DrAll.csv"), row.names = FALSE)

rank_col <- intersect(c("distance", "FC", "statistic", "d"), colnames(dr_all))[1]
if (is.na(rank_col)) rank_col <- colnames(dr_all)[2]
top <- do.call(rbind, lapply(split(dr_all, dr_all$subtype), function(df) {
  df <- df[order(df[[rank_col]], decreasing = TRUE), , drop = FALSE]
  head(df, 15)
}))
write.csv(top, file.path(tab_dir, "04_扰动基因_Top15_Cplx2DrTop.csv"), row.names = FALSE)

if (exists("theme_journal")) {
  p2 <- ggplot(top, aes(.data[[rank_col]], reorder(gene, .data[[rank_col]]))) +
    geom_col(fill = if (exists("bioinfo_palette")) bioinfo_palette[2] else "#F58518", width = 0.7) +
    facet_wrap(~ subtype, scales = "free_y") +
    labs(title = "Top predicted perturbed genes after Cplx2 virtual KO", x = rank_col, y = NULL) +
    theme_journal()
} else {
  p2 <- ggplot(top, aes(.data[[rank_col]], reorder(gene, .data[[rank_col]]))) +
    geom_col(width = 0.7) +
    facet_wrap(~ subtype, scales = "free_y") +
    labs(title = "Top predicted perturbed genes after Cplx2 virtual KO", x = rank_col, y = NULL) +
    theme_bw()
}
save_plot(p2, "04_柱状图_扰动基因_Cplx2DrBar", w = 10, h = 8)

si <- capture.output(sessionInfo())
writeLines(c(
  "STATUS=PARTIAL",
  "data_provenance=REAL",
  "accession=GSE197289",
  "model=Control",
  "subtypes=cLTMR,NF1,NP,PEP,TRPM8",
  "gKO=Cplx2",
  "qc_minLibSize=500",
  "nc_nNet=3",
  "nc_nCells=min(200, n-1)",
  "max_genes=1000 top mean, Cplx2 forced in",
  "note=reduced from package defaults (nNet=10, nCells=500) so five subtypes finish; not a hidden change of biology",
  "Sp5C GSE322600 not knocked: n=51 < 300",
  "GSE131272 not subtype-knocked: no author labels in supplement",
  "claim=computational prediction; not chronic TN model validation",
  si
), file.path(rep_dir, "STATUS.txt"))
message("KO_DONE")
