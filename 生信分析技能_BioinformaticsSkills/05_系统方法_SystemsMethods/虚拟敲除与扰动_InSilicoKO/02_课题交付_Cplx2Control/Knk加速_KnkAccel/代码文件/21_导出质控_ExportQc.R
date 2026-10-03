# Read-only QC extract for one finished subtype. Does not write Formal results.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) stop("out dir and subtype required")
out_dir <- args[[1]]
subtype <- args[[2]]
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

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

raw_dir <- "C:/Users/10540/Desktop/琪乐无穷/CPLX2虚拟敲除_Cplx2VirtualKO/数据文件"
meta <- read.csv(gzfile(file.path(raw_dir, "01_细胞注释_CellMeta_GSE197289.csv.gz")), check.names = FALSE)
counts <- readRDS(gzcon(gzfile(file.path(raw_dir, "02_表达矩阵_Counts_GSE197289.RDS.gz"), "rb")))
meta <- meta[match(colnames(counts), meta$V1), , drop = FALSE]
stopifnot(!anyNA(meta$V1))
keep <- meta$model == "Control" & meta$subtype == subtype
mat <- counts[, keep, drop = FALSE]
rm(counts)
gc()

rs <- Matrix::rowSums(mat > 0)
mat <- mat[rs >= 25, , drop = FALSE]
if (!"Cplx2" %in% rownames(mat)) stop("Cplx2 dropped by filter")
if (nrow(mat) > 8000L) {
  score <- Matrix::rowMeans(mat)
  score["Cplx2"] <- Inf
  mat <- mat[order(score, decreasing = TRUE)[seq_len(8000L)], , drop = FALSE]
}
mat <- as.matrix(mat)
n_in <- ncol(mat)
n_draw <- min(500L, n_in - 1L)

t0 <- proc.time()
qc <- scTenifoldNet::scQC(mat, minLibSize = 1000, removeOutlierCells = TRUE, minPCT = 0.05, maxMTratio = 0.1)
qc_sec <- (proc.time() - t0)[["elapsed"]]
t0 <- proc.time()
cpm <- scTenifoldNet::cpmNormalization(qc)
cpm_sec <- (proc.time() - t0)[["elapsed"]]
if (!"Cplx2" %in% rownames(cpm)) stop("Cplx2 dropped by scQC")

draw_once <- function() {
  n_col <- ncol(cpm)
  set.seed(1)
  old <- future::plan(future::sequential)
  on.exit(future::plan(old), add = TRUE)
  furrr::future_map(seq_len(10L), function(w) {
    sample(x = seq_len(n_col), size = n_draw, replace = TRUE)
  }, .options = furrr::furrr_options(seed = TRUE))
}
t0 <- proc.time()
draws <- draw_once()
again <- draw_once()
index_sec <- (proc.time() - t0)[["elapsed"]]
if (!identical(draws, again)) stop("cell-index draws are not stable")

con <- file(file.path(out_dir, "cpm.bin"), "wb")
writeBin(as.numeric(cpm), con, size = 8)
close(con)
writeLines(rownames(cpm), file.path(out_dir, "genes.txt"), useBytes = TRUE)
for (i in seq_along(draws)) {
  writeLines(as.character(draws[[i]] - 1L), file.path(out_dir, sprintf("net_%02d_indices.txt", i)))
}
writeLines(
  c(
    "step,seconds,detail",
    sprintf("qc,%.3f,cells_in=%d;cells_qc=%d;genes=%d", qc_sec, n_in, ncol(cpm), nrow(cpm)),
    sprintf("cpm,%.3f,genes=%d", cpm_sec, nrow(cpm)),
    sprintf("indices,%.3f,n_draw=%d;n_net=10;q=0.9;stable=yes", index_sec, n_draw)
  ),
  file.path(out_dir, "timings.csv")
)
cat(sprintf("export_ok subtype=%s genes=%d cells_qc=%d n_draw=%d\n", subtype, nrow(cpm), ncol(cpm), n_draw))
