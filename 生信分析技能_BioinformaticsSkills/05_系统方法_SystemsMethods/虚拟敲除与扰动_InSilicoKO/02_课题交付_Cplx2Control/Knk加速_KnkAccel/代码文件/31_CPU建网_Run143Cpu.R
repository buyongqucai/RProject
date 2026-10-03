# Original 1.4.3 pcNet, q=0.9, 12 cores, one BLAS thread per process.
args <- commandArgs(trailingOnly = TRUE)
root <- args[[1]]
n_cores <- as.integer(args[[2]])
source(
  "e:/RProject/生信分析技能_BioinformaticsSkills/05_系统方法_SystemsMethods/虚拟敲除与扰动_InSilicoKO/02_课题交付_Cplx2Control/Knk加速_KnkAccel/代码文件/R_仓库公式/pcNet_1.4.3.R",
  local = TRUE
)
if (requireNamespace("RhpcBLASctl", quietly = TRUE)) {
  RhpcBLASctl::blas_set_num_threads(1L)
  RhpcBLASctl::omp_set_num_threads(1L)
}
Sys.setenv(OMP_NUM_THREADS = "1", OPENBLAS_NUM_THREADS = "1", MKL_NUM_THREADS = "1")

run_one <- function(subtype) {
  folder <- file.path(root, subtype, "scTenifoldKnk", "_野生型")
  out <- file.path(root, subtype, "scTenifoldKnk_CPU", "_野生型")
  dir.create(out, recursive = TRUE, showWarnings = FALSE)
  genes <- readLines(file.path(folder, "genes.txt"), warn = FALSE, encoding = "UTF-8")
  n_num <- file.info(file.path(folder, "cpm.bin"))$size / 8
  raw <- readBin(file.path(folder, "cpm.bin"), what = "double", n = n_num)
  n_cell <- length(raw) / length(genes)
  cpm <- matrix(raw, nrow = length(genes), ncol = n_cell)
  rownames(cpm) <- genes
  times <- c("net,seconds,genes")
  for (net_id in seq_len(10L)) {
    dest <- file.path(out, sprintf("net_%02d.rds", net_id))
    if (file.exists(dest) && file.info(dest)$size > 1000) {
      cat(subtype, "skip", net_id, "\n")
      next
    }
    idx <- as.integer(readLines(file.path(folder, sprintf("net_%02d_indices.txt", net_id)), warn = FALSE)) + 1L
    started <- proc.time()[["elapsed"]]
    network <- pcNet(cpm[, idx, drop = FALSE], nComp = 3L, scaleScores = TRUE, symmetric = FALSE, q = 0.9, nCores = n_cores, verbose = FALSE)
    elapsed <- proc.time()[["elapsed"]] - started
    saveRDS(network, dest)
    times <- c(times, sprintf("%d,%.3f,%d", net_id, elapsed, length(genes)))
    cat(subtype, "cpu net", net_id, sprintf("%.3f", elapsed), "\n")
    rm(network)
    gc()
  }
  writeLines(times, file.path(out, "cpu_network_times.csv"))
}

for (subtype in c("PEP", "NF1")) run_one(subtype)
cat("CPU_DONE\n")
