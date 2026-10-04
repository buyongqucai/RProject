# 步骤 1：亚群导出 + 质控 + 抽样 + 检出率 + 低相关对照。
# 用法: Rscript step1_export_qc.R <run_env.txt>
# 资源：线程数来自探测（R_THREADS），不写死。
options(stringsAsFactors = FALSE)

args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) >= 1)
env_path <- args[[1]]
kv <- list()
for (line in readLines(env_path, warn = FALSE, encoding = "UTF-8")) {
  if (!grepl("=", line) || grepl("^#", line)) next
  pos <- regexpr("=", line, fixed = TRUE)[1]
  key <- substr(line, 1, pos - 1)
  kv[[key]] <- substr(line, pos + 1, nchar(line))
}
get_int <- function(key) as.integer(kv[[key]])
get_num <- function(key) as.numeric(kv[[key]])

n_threads <- get_int("R_THREADS")
if (requireNamespace("RhpcBLASctl", quietly = TRUE)) {
  RhpcBLASctl::blas_set_num_threads(n_threads)
  RhpcBLASctl::omp_set_num_threads(n_threads)
}

suppressPackageStartupMessages({
  library(Matrix)
  library(scTenifoldNet)
})

raw_dir <- kv[["RAW_DIR"]]
result_dir <- kv[["RESULT_DIR"]]
subtypes <- strsplit(kv[["SUBTYPES"]], ",", fixed = TRUE)[[1]]
targets <- strsplit(kv[["KNOCK_GENES"]], ",", fixed = TRUE)[[1]]
n_net <- get_int("N_NET")
n_cells <- get_int("N_CELLS")
seed <- get_int("SEED")
min_detected <- get_int("MIN_DETECTED")

message("loading meta and counts")
meta <- read.csv(gzfile(file.path(raw_dir, kv[["META_FILE"]])), check.names = FALSE)
counts <- readRDS(gzcon(gzfile(file.path(raw_dir, kv[["COUNTS_FILE"]]), "rb")))
meta <- meta[match(colnames(counts), meta[[kv[["CELL_ID_COL"]]]]), , drop = FALSE]
stopifnot(!anyNA(meta[[kv[["CELL_ID_COL"]]]]))

export_one <- function(subtype) {
  out0 <- file.path(result_dir, subtype, "scTenifoldKnk_1.4.3_GPU", "_野生型", "数据文件")
  note0 <- file.path(result_dir, subtype, "scTenifoldKnk_1.4.3_GPU", "_野生型", "报告文件")
  if (file.exists(file.path(out0, "cpm.bin")) && file.exists(file.path(out0, "genes.txt")) &&
      file.exists(file.path(note0, "timings.csv"))) {
    message(subtype, " 已有导出结果，跳过")
    return(invisible(NULL))
  }
  keep <- meta[[kv[["MODEL_COL"]]]] == kv[["MODEL_VAL"]] & meta[[kv[["SUBTYPE_COL"]]]] == subtype
  mat <- counts[, keep, drop = FALSE]
  if (ncol(mat) < 2) stop(subtype, ": too few cells")
  detected <- Matrix::rowSums(mat > 0)
  present <- intersect(targets, names(detected)[detected > 0])
  missing <- setdiff(targets, present)
  keep_gene <- detected >= min_detected | (names(detected) %in% present)
  mat <- mat[keep_gene, , drop = FALSE]
  n_before <- nrow(mat)
  n_in <- ncol(mat)

  t0 <- proc.time()
  qc <- as.matrix(scTenifoldNet::scQC(
    mat,
    minLibSize = get_int("MIN_LIB_SIZE"),
    removeOutlierCells = TRUE,
    minPCT = get_num("MIN_PCT"),
    maxMTratio = get_num("MAX_MT_RATIO")
  ))
  qc_sec <- (proc.time() - t0)[["elapsed"]]
  dropped <- present[!present %in% rownames(qc)]
  if (length(dropped)) {
    # 强制补回被 scQC 掉的敲除靶基因（检出>0 才补）
    extra <- as.matrix(mat[dropped, colnames(qc), drop = FALSE])
    qc <- rbind(qc, extra)
  }
  t0 <- proc.time()
  cpm <- scTenifoldNet::cpmNormalization(qc)
  cpm_sec <- (proc.time() - t0)[["elapsed"]]

  n_draw <- min(n_cells, ncol(cpm) - 1L)
  set.seed(seed)
  draws <- replicate(n_net, sample.int(ncol(cpm), n_draw, replace = TRUE), simplify = FALSE)

  # 低相关对照：log1p(CPM) 上与 Cplx2 绝对 Pearson 相关最小、方差>0、不在敲除表
  expr <- log1p(cpm)
  if (!"Cplx2" %in% rownames(expr)) stop(subtype, ": Cplx2 missing after QC")
  cplx <- as.numeric(expr["Cplx2", ])
  others <- setdiff(rownames(expr), targets)
  cors <- vapply(others, function(gene) {
    x <- as.numeric(expr[gene, ])
    if (stats::sd(x) == 0) return(NA_real_)
    stats::cor(cplx, x, method = "pearson")
  }, numeric(1))
  cors <- cors[is.finite(cors)]
  control <- names(which.min(abs(cors)))

  out <- file.path(result_dir, subtype, "scTenifoldKnk_1.4.3_GPU", "_野生型", "数据文件")
  note <- file.path(result_dir, subtype, "scTenifoldKnk_1.4.3_GPU", "_野生型", "报告文件")
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
      sprintf("qc,%.3f,cells_in=%d;cells_qc=%d;genes_before=%d;genes=%d", qc_sec, n_in, ncol(cpm), n_before, nrow(cpm)),
      sprintf("cpm,%.3f,genes=%d", cpm_sec, nrow(cpm)),
      sprintf("indices,%.3f,n_draw=%d;n_net=%d;seed=%d;method=sample.int", 0, n_draw, n_net, seed),
      sprintf("control,0,gene=%s;abs_cor=%.6g;missing=%s", control, abs(cors[[control]]), paste(missing, collapse = "|"))
    ),
    file.path(note, "timings.csv"),
    useBytes = TRUE
  )
  cat(subtype, "genes", nrow(cpm), "cells", ncol(cpm), "control", control, "\n")
}

for (subtype in subtypes) export_one(subtype)
cat("STEP1_DONE\n")
