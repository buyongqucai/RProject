# PEP and NF1 for the current plan. No 8000 cap. Does not write the old Formal tree.
args <- commandArgs(trailingOnly = TRUE)
desk <- if (length(args) >= 1 && !grepl("scTenifold", args[[1]])) args[[1]] else "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除"

if (requireNamespace("RhpcBLASctl", quietly = TRUE)) {
  RhpcBLASctl::blas_set_num_threads(1L)
  RhpcBLASctl::omp_set_num_threads(1L)
}
Sys.setenv(OMP_NUM_THREADS = "1", OPENBLAS_NUM_THREADS = "1", MKL_NUM_THREADS = "1")

suppressPackageStartupMessages({
  library(Matrix)
  library(scTenifoldNet)
  library(future)
  library(furrr)
})

targets <- c("Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21")
raw_dir <- "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除/数据文件"
meta <- read.csv(gzfile(file.path(raw_dir, "01_细胞注释_CellMeta_GSE197289.csv.gz")), check.names = FALSE)
counts <- readRDS(gzcon(gzfile(file.path(raw_dir, "02_表达矩阵_Counts_GSE197289.RDS.gz"), "rb")))
meta <- meta[match(colnames(counts), meta$V1), , drop = FALSE]
stopifnot(!anyNA(meta$V1))

draw_once <- function(n_col, n_draw) {
  set.seed(1)
  old <- future::plan(future::sequential)
  on.exit(future::plan(old), add = TRUE)
  furrr::future_map(seq_len(10L), function(w) {
    sample(x = seq_len(n_col), size = n_draw, replace = TRUE)
  }, .options = furrr::furrr_options(seed = TRUE))
}

export_one <- function(subtype) {
  keep <- meta$model == "Control" & meta$subtype == subtype
  mat <- counts[, keep, drop = FALSE]
  detected <- Matrix::rowSums(mat > 0)
  present <- intersect(targets, names(detected)[detected > 0])
  missing <- setdiff(targets, present)
  keep_gene <- detected >= 25 | (names(detected) %in% present)
  mat <- mat[keep_gene, , drop = FALSE]
  n_before_qc <- nrow(mat)
  t0 <- proc.time()
  qc <- as.matrix(scTenifoldNet::scQC(mat, minLibSize = 1000, removeOutlierCells = TRUE, minPCT = 0.05, maxMTratio = 0.1))
  qc_sec <- (proc.time() - t0)[["elapsed"]]
  dropped <- present[!present %in% rownames(qc)]
  if (length(dropped)) {
    extra <- as.matrix(mat[dropped, colnames(qc), drop = FALSE])
    qc <- rbind(qc, extra)
  }
  t0 <- proc.time()
  cpm <- scTenifoldNet::cpmNormalization(qc)
  cpm_sec <- (proc.time() - t0)[["elapsed"]]
  n_gene <- nrow(cpm)
  dense_gb <- n_gene * n_gene * 10 * 8 / 1024^3
  n_in <- ncol(mat)
  n_draw <- min(500L, ncol(cpm) - 1L)
  t0 <- proc.time()
  draws <- draw_once(ncol(cpm), n_draw)
  again <- draw_once(ncol(cpm), n_draw)
  index_sec <- (proc.time() - t0)[["elapsed"]]
  if (!identical(draws, again)) stop("cell-index draws are not stable")

  expr <- log1p(cpm)
  cplx <- as.numeric(expr["Cplx2", ])
  others <- setdiff(rownames(expr), targets)
  cors <- vapply(others, function(gene) {
    x <- as.numeric(expr[gene, ])
    if (stats::sd(x) == 0) return(NA_real_)
    stats::cor(cplx, x, method = "pearson")
  }, numeric(1))
  cors <- cors[is.finite(cors)]
  control <- names(which.min(abs(cors)))

  out <- file.path(
    desk, "结果文件", subtype, "scTenifoldKnk_1.4.3_GPU", "_野生型", "数据文件"
  )
  note <- file.path(desk, "结果文件", subtype, "scTenifoldKnk_1.4.3_GPU", "_野生型", "报告文件")
  dir.create(out, recursive = TRUE, showWarnings = FALSE)
  dir.create(note, recursive = TRUE, showWarnings = FALSE)
  con <- file(file.path(out, "cpm.bin"), "wb")
  writeBin(as.numeric(cpm), con, size = 8)
  close(con)
  writeLines(rownames(cpm), file.path(out, "genes.txt"), useBytes = TRUE)
  for (i in seq_along(draws)) {
    writeLines(as.character(draws[[i]] - 1L), file.path(out, sprintf("net_%02d_indices.txt", i)))
  }
  det_lines <- c("gene,detected_cells,cells,forced_back")
  for (gene in targets) {
    n_det <- if (gene %in% names(detected)) unname(detected[[gene]]) else 0L
    det_lines <- c(det_lines, sprintf("%s,%d,%d,%d", gene, n_det, n_in, as.integer(gene %in% dropped)))
  }
  writeLines(det_lines, file.path(out, "检出_Detection.csv"), useBytes = TRUE)
  writeLines(
    c(
      "step,seconds,detail",
      sprintf("qc,%.3f,cells_in=%d;cells_qc=%d;genes_before=%d;genes=%d;dense_gb=%.2f", qc_sec, n_in, ncol(cpm), n_before_qc, n_gene, dense_gb),
      sprintf("cpm,%.3f,genes=%d", cpm_sec, n_gene),
      sprintf("indices,%.3f,n_draw=%d;n_net=10;q=0.9;stable=yes", index_sec, n_draw),
      sprintf("control,0,gene=%s;abs_cor=%.6g;missing=%s", control, abs(cors[[control]]), paste(missing, collapse = "|"))
    ),
    file.path(note, "timings.csv")
  )
  cat(subtype, "genes", n_gene, "cells", ncol(cpm), "dense_gb", sprintf("%.2f", dense_gb), "control", control, "forced", paste(dropped, collapse = ","), "\n")
}

for (subtype in c("PEP", "NF1")) export_one(subtype)
cat("EXPORT_DONE\n")
