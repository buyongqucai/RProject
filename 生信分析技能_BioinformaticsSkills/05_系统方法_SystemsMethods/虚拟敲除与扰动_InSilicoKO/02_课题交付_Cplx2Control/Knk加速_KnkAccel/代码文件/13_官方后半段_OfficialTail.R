# Official tensor through dRegulation on networks built outside Formal.
# Reads CSR binaries from out_dir. Does not write the Formal result directory.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) stop("out dir required")
out_dir <- args[[1]]

if (requireNamespace("RhpcBLASctl", quietly = TRUE)) {
  RhpcBLASctl::blas_set_num_threads(1L)
  RhpcBLASctl::omp_set_num_threads(1L)
}
Sys.setenv(OMP_NUM_THREADS = "1", OPENBLAS_NUM_THREADS = "1", MKL_NUM_THREADS = "1")

suppressPackageStartupMessages({
  library(Matrix)
  library(scTenifoldNet)
  library(scTenifoldKnk)
})

read_csr <- function(path) {
  con <- file(path, "rb")
  on.exit(close(con), add = TRUE)
  hdr <- readBin(con, "integer", n = 3L, size = 4)
  n_row <- hdr[[1]]
  n_col <- hdr[[2]]
  nnz <- hdr[[3]]
  indptr <- readBin(con, "integer", n = n_row + 1L, size = 4)
  cols <- readBin(con, "integer", n = nnz, size = 4)
  data <- readBin(con, "double", n = nnz, size = 8)
  rows <- rep(seq_len(n_row), diff(indptr))
  Matrix::sparseMatrix(i = rows, j = cols + 1L, x = data, dims = c(n_row, n_col))
}

genes <- readLines(file.path(out_dir, "genes.txt"), encoding = "UTF-8", warn = FALSE)
nets <- vector("list", 10L)
t0 <- proc.time()
for (i in seq_len(10L)) {
  nets[[i]] <- read_csr(file.path(out_dir, sprintf("net_%02d.csr", i)))
  rownames(nets[[i]]) <- colnames(nets[[i]]) <- genes
}
load_sec <- (proc.time() - t0)[["elapsed"]]

t0 <- proc.time()
set.seed(1)
wt <- scTenifoldNet::tensorDecomposition(
  xList = nets,
  K = 3,
  maxError = 1e-5,
  maxIter = 1000,
  nDecimal = 3
)
tensor_sec <- (proc.time() - t0)[["elapsed"]]
wt <- wt$X
t0 <- proc.time()
wt <- scTenifoldKnk:::strictDirection(wt, lambda = 0)
wt <- as.matrix(wt)
diag(wt) <- 0
wt <- t(wt)
direction_sec <- (proc.time() - t0)[["elapsed"]]

ko <- wt
ko["Cplx2", ] <- 0
t0 <- proc.time()
set.seed(1)
ma <- scTenifoldNet::manifoldAlignment(wt, ko, d = 2, nCores = 1L)
manifold_sec <- (proc.time() - t0)[["elapsed"]]
t0 <- proc.time()
dr <- scTenifoldKnk::dRegulation(ma, empiricalNull = FALSE)
dr_sec <- (proc.time() - t0)[["elapsed"]]
utils::write.csv(as.data.frame(dr), file.path(out_dir, "dr_optimized.csv"), row.names = FALSE)

official_rds <- "C:/Users/10540/Desktop/琪乐无穷/五亚群留档/结果文件/cLTMR/scTenifoldKnk/Cplx2/数据文件/正式_cLTMR_Cplx2_formal.rds"
official <- readRDS(official_rds)
off_wt <- as.matrix(official$tensorNetworks$WT)
if (!identical(rownames(off_wt), rownames(wt)) || !identical(colnames(off_wt), colnames(wt))) {
  stop("WT gene order does not match the official RDS")
}
wt_diff <- max(abs(wt - off_wt))
writeLines(
  c(
    "step,seconds,detail",
    sprintf("load_csr,%.3f,nets=10", load_sec),
    sprintf("tensor,%.3f,K=3;maxIter=1000;tol=1e-5", tensor_sec),
    sprintf("direction,%.3f,lambda=0", direction_sec),
    sprintf("manifold,%.3f,d=2", manifold_sec),
    sprintf("dRegulation,%.3f,empiricalNull=FALSE", dr_sec),
    sprintf("wt_max_abs,%.6e,versus_official_rds", wt_diff)
  ),
  file.path(out_dir, "timings_tail.csv")
)
cat(sprintf("tail ok tensor=%.3f direction=%.3f manifold=%.3f dr=%.3f wt_max_abs=%.6e\n",
            tensor_sec, direction_sec, manifold_sec, dr_sec, wt_diff))
