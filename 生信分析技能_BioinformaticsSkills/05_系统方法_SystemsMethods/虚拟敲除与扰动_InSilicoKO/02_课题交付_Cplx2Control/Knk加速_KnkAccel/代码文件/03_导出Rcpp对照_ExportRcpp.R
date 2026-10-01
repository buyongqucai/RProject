# Export pcNetCoreRcpp coefficients for a small standardized matrix.
# Args: input csv (samples x genes), output csv.
# One BLAS thread. Does not call scTenifoldKnk().
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) stop("need input.csv output.csv")
if (requireNamespace("RhpcBLASctl", quietly = TRUE)) {
  RhpcBLASctl::blas_set_num_threads(1L)
  RhpcBLASctl::omp_set_num_threads(1L)
}
x <- as.matrix(read.csv(args[[1]], header = FALSE))
storage.mode(x) <- "double"
if (ncol(x) > 200L) stop("refusing a large matrix")
coef <- scTenifoldNet:::pcNetCoreRcpp(x, 3L)
write.table(coef, args[[2]], sep = ",", row.names = FALSE, col.names = FALSE)
