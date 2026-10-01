# Export pcNet() and pcNetCoreRcpp for a genes-by-cells count matrix.
# Args: input.csv (first column gene names), network.csv, core.csv
# One BLAS thread. Does not call scTenifoldKnk().
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3L) stop("need input.csv network.csv core.csv")
if (requireNamespace("RhpcBLASctl", quietly = TRUE)) {
  RhpcBLASctl::blas_set_num_threads(1L)
  RhpcBLASctl::omp_set_num_threads(1L)
}
Sys.setenv(OMP_NUM_THREADS = "1", MKL_NUM_THREADS = "1", OPENBLAS_NUM_THREADS = "1")
x <- as.matrix(read.csv(args[[1]], row.names = 1, check.names = FALSE))
storage.mode(x) <- "double"
if (nrow(x) > 200L) stop("refusing a large matrix")
net <- scTenifoldNet::pcNet(
  x, nComp = 3L, q = 0.95, scaleScores = TRUE, symmetric = FALSE,
  nCores = 1L, useRcpp = TRUE, verbose = FALSE
)
write.csv(as.matrix(net), args[[2]], row.names = TRUE)
x_std <- scale(t(x))
core <- scTenifoldNet:::pcNetCoreRcpp(as.matrix(x_std), 3L)
write.table(core, args[[3]], sep = ",", row.names = FALSE, col.names = FALSE)
