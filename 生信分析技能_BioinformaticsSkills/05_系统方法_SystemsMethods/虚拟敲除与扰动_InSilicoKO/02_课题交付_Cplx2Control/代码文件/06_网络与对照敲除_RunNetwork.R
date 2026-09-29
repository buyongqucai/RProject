# Re-run the same reduced virtual KO and save objects for plotKO networks.
# Also knock one negative-control gene (Rplp0) in the same five subtypes.
options(stringsAsFactors = FALSE)
set.seed(20260929)
root <- "C:/Users/10540/Desktop/琪乐无穷/CPLX2虚拟敲除_Cplx2VirtualKO"
raw_dir <- file.path(root, "数据文件")
tab_dir <- file.path(root, "结果文件", "数据文件")
fig_dir <- file.path(root, "结果文件", "图片文件")
obj_dir <- file.path(root, "结果文件", "数据文件", "敲除对象_KoObjects")
dir.create(obj_dir, recursive = TRUE, showWarnings = FALSE)
suppressPackageStartupMessages({
  library(Matrix)
  library(scTenifoldKnk)
})

meta <- read.csv(gzfile(file.path(raw_dir, "01_细胞注释_CellMeta_GSE197289.csv.gz")), check.names = FALSE)
counts <- readRDS(gzcon(gzfile(file.path(raw_dir, "02_表达矩阵_Counts_GSE197289.RDS.gz"), "rb")))
meta <- meta[match(colnames(counts), meta$V1), , drop = FALSE]
targets <- c("cLTMR", "NF1", "NP", "PEP", "TRPM8")
keep <- meta$model == "Control" & meta$subtype %in% targets
sub_meta <- meta[keep, , drop = FALSE]
sub_counts <- counts[, keep, drop = FALSE]

prep_matrix <- function(mat, max_genes = 1000) {
  rs <- Matrix::rowSums(mat > 0)
  mat <- mat[rs >= 25, , drop = FALSE]
  if (nrow(mat) > max_genes) {
    score <- Matrix::rowMeans(mat)
    if ("Cplx2" %in% names(score)) score["Cplx2"] <- Inf
    if ("Rplp0" %in% names(score)) score["Rplp0"] <- max(score[is.finite(score)]) + 1
    mat <- mat[order(score, decreasing = TRUE)[seq_len(max_genes)], , drop = FALSE]
  }
  as.matrix(mat)
}

run_one <- function(subtype, gKO) {
  idx <- which(sub_meta$subtype == subtype)
  mat <- prep_matrix(sub_counts[, idx, drop = FALSE])
  if (!gKO %in% rownames(mat)) stop(gKO, " missing in ", subtype)
  n_use <- min(200L, ncol(mat) - 1L)
  message("KO ", subtype, " ", gKO)
  res <- scTenifoldKnk(
    countMatrix = mat, gKO = gKO, qc = TRUE,
    qc_minLibSize = 500, qc_minPCT = 0.05,
    nc_nNet = 3, nc_nCells = n_use, td_K = 3,
    nCores = max(1L, parallel::detectCores() - 1L)
  )
  saveRDS(res, file.path(obj_dir, paste0(subtype, "_", gKO, ".rds")))
  dr <- res$diffRegulation
  dr$subtype <- subtype
  dr$gKO <- gKO
  write.csv(dr, file.path(tab_dir, paste0("04_扰动基因_", subtype, "_", gKO, "Dr.csv")), row.names = FALSE)
  png(file.path(fig_dir, paste0("06_网络图_", subtype, "_", gKO, "Network.png")), width = 2400, height = 1800, res = 300)
  try(plotKO(res, gKO = gKO), silent = FALSE)
  dev.off()
  dr
}

for (g in targets) {
  run_one(g, "Cplx2")
  run_one(g, "Rplp0")
}
message("NET_DONE")
