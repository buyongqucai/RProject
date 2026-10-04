# Formal Cplx2 virtual KO — max-CPU sequential subtypes.
# Root cause of prior under-utilization (scTenifoldNet 1.4):
#   pcNet(useRcpp=TRUE) uses a SERIAL C++ loop and IGNORES nCores.
#   makeNetworks builds nc_nNet networks with lapply (also serial).
# Prior 5-subtype × nCores=1 design therefore left most of Ultra 9 285K idle.
#
# This script:
#   - cannot inject cores into an already-running call (impossible) — restart required
#   - runs ONE subtype at a time (resume = per-subtype RDS+CSV)
#   - patches makeNetworks to build the 10 nets in parallel via future multisession
#   - each net keeps useRcpp=TRUE (fast C++) with BLAS=2 → ~20 threads when nNet=10
# GPU: scTenifoldKnk / scTenifoldNet have NO CUDA. See STATUS note for GenKI (Python).
options(stringsAsFactors = FALSE)
set.seed(20261001)

vko <- "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除"
root <- "C:/Users/10540/Desktop/琪乐无穷/五亚群留档"
raw_dir <- file.path(vko, "数据文件")
res_dir <- file.path(root, "结果文件", "_跨亚群", "scTenifoldKnk")
tab_dir <- file.path(res_dir, "数据文件")
fig_dir <- file.path(res_dir, "图片文件")
rep_dir <- file.path(res_dir, "报告文件")
obj_dir <- file.path(tab_dir, "敲除对象_KoObjects_Formal")
pilot_dir <- file.path(tab_dir, "_pilot_reduced_params_archive")
log_file <- file.path(rep_dir, "正式参数运行日志_FormalRun.log")
for (d in c(tab_dir, fig_dir, rep_dir, obj_dir, pilot_dir)) {
  dir.create(d, recursive = TRUE, showWarnings = FALSE)
}

log_con <- file(log_file, open = "at")
sink(log_con, type = "output", split = TRUE)
on.exit({
  try(sink(type = "output"), silent = TRUE)
  try(close(log_con), silent = TRUE)
}, add = TRUE)

message("=== Formal scTenifoldKnk MAXCPU start ", format(Sys.time()), " ===")
message("Strategy: sequential subtypes; parallelize nNet via patched makeNetworks + Rcpp")

n_logical <- max(1L, parallel::detectCores())
# Leave a few cores for OS/Cursor; use up to 20 for network workers.
n_net_workers <- as.integer(Sys.getenv("FORMAL_N_WORKERS", unset = "20"))
n_net_workers <- max(1L, min(n_net_workers, n_logical - 2L, 20L))
# With nNet=10, cap workers at 10 (one net per worker). Extra cores → BLAS.
blas_per_net <- max(1L, min(2L, n_logical %/% max(1L, min(10L, n_net_workers))))
Sys.setenv(
  OMP_NUM_THREADS = as.character(blas_per_net),
  OPENBLAS_NUM_THREADS = as.character(blas_per_net),
  MKL_NUM_THREADS = as.character(blas_per_net),
  VECLIB_MAXIMUM_THREADS = as.character(blas_per_net),
  R_PARALLELLY_AVAILABLECORES = as.character(n_logical)
)
options(mc.cores = n_logical, Ncpus = n_logical)

suppressPackageStartupMessages({
  library(Matrix)
  library(ggplot2)
  library(scTenifoldKnk)
  library(scTenifoldNet)
  library(future)
  library(furrr)
  if (requireNamespace("RhpcBLASctl", quietly = TRUE)) {
    RhpcBLASctl::blas_set_num_threads(blas_per_net)
    RhpcBLASctl::omp_set_num_threads(blas_per_net)
  }
})

# ---- Patch makeNetworks: parallelize the 10 GRNs; keep fast Rcpp inside each ----
patch_makeNetworks_parallel <- function(max_workers, blas_n) {
  ns <- asNamespace("scTenifoldNet")
  unlockBinding("makeNetworks", ns)
  makeNetworks_par <- function(X, nNet = 10, nCells = 500, nComp = 3,
                               scaleScores = TRUE, symmetric = FALSE, q = 0.95,
                               priorNetwork = NULL, nCores = parallel::detectCores(),
                               label = NULL) {
    geneList <- rownames(X)
    nGenes <- length(geneList)
    nCol <- ncol(X)
    if (nGenes == 0) stop("Gene names are required")
    if (nComp < 2 || nComp >= nGenes) stop("nComp should be >= 2 and < total number of genes")
    tag <- if (!is.null(label)) paste0("[", label, "] ") else ""
    n_workers <- max(1L, min(as.integer(nNet), as.integer(max_workers)))
    cli::cli_alert_info(
      "{tag}Building {nNet} GRNs in parallel (workers={n_workers}, cells={nCells}, Rcpp=TRUE, BLAS={blas_n})"
    )
    old_plan <- future::plan(future::multisession, workers = n_workers)
    on.exit(future::plan(old_plan), add = TRUE)
    networks <- furrr::future_map(seq_len(nNet), function(W) {
      if (requireNamespace("RhpcBLASctl", quietly = TRUE)) {
        RhpcBLASctl::blas_set_num_threads(as.integer(blas_n))
        RhpcBLASctl::omp_set_num_threads(as.integer(blas_n))
      }
      Sys.setenv(
        OMP_NUM_THREADS = as.character(blas_n),
        OPENBLAS_NUM_THREADS = as.character(blas_n),
        MKL_NUM_THREADS = as.character(blas_n)
      )
      Z <- sample(x = seq_len(nCol), size = nCells, replace = TRUE)
      Z <- as.matrix(X[, Z])
      Z <- Z[apply(Z, 1, sum) > 0, , drop = FALSE]
      # useRcpp=TRUE: fast serial C++; nCores ignored on this path (by design)
      Z <- scTenifoldNet::pcNet(
        Z, nComp = nComp, scaleScores = scaleScores, symmetric = symmetric,
        q = q, priorNetwork = priorNetwork, verbose = FALSE,
        nCores = 1L, useRcpp = TRUE
      )
      O <- matrix(0, nrow = nGenes, ncol = nGenes)
      rownames(O) <- colnames(O) <- geneList
      O[rownames(Z), colnames(Z)] <- as.matrix(Z)
      as(O, "dgCMatrix")
    }, .options = furrr::furrr_options(seed = TRUE))
    cli::cli_alert_success("{tag}Network construction complete: {nNet} networks")
    networks
  }
  assign("makeNetworks", makeNetworks_par, envir = ns)
  lockBinding("makeNetworks", ns)
  # scTenifoldKnk Imports makeNetworks — must rebind import env or patch is invisible
  knk <- asNamespace("scTenifoldKnk")
  knk_imp <- parent.env(knk)
  if (exists("makeNetworks", envir = knk_imp, inherits = FALSE)) {
    unlockBinding("makeNetworks", knk_imp)
    assign("makeNetworks", makeNetworks_par, envir = knk_imp)
    lockBinding("makeNetworks", knk_imp)
    message("Also rebound makeNetworks inside scTenifoldKnk imports")
  } else {
    warning("makeNetworks not found in scTenifoldKnk imports; patch may be ineffective")
  }
  message(sprintf(
    "Patched scTenifoldNet::makeNetworks → parallel nNet (workers<=%d, BLAS/OMP=%d)",
    max_workers, blas_n
  ))
}
patch_makeNetworks_parallel(n_net_workers, blas_per_net)

message(sprintf(
  "CPU plan: sequential subtypes | nNet parallel workers<=%d | BLAS/OMP=%d | logical=%d",
  n_net_workers, blas_per_net, n_logical
))

pilot_like <- list.files(tab_dir, pattern = "^04_扰动基因_.*\\.csv$", full.names = TRUE)
if (length(pilot_like)) {
  file.copy(pilot_like, file.path(pilot_dir, basename(pilot_like)), overwrite = FALSE)
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

prep_matrix_formal <- function(mat, soft_cap = 8000L) {
  rs <- Matrix::rowSums(mat > 0)
  mat <- mat[rs >= 25, , drop = FALSE]
  if (!"Cplx2" %in% rownames(mat)) stop("Cplx2 dropped by filter")
  n0 <- nrow(mat)
  if (n0 > soft_cap) {
    score <- Matrix::rowMeans(mat)
    score["Cplx2"] <- Inf
    mat <- mat[order(score, decreasing = TRUE)[seq_len(soft_cap)], , drop = FALSE]
    message("soft_cap applied: ", n0, " -> ", nrow(mat), " (top mean + Cplx2)")
  } else {
    message("genes after detection filter: ", n0, " (no soft_cap)")
  }
  as.matrix(mat)
}

force_env <- Sys.getenv("FORCE_RERUN", unset = "")
force_all <- tolower(force_env) %in% c("1", "true", "yes", "all")
force_set <- character(0)
if (!force_all && nzchar(force_env)) {
  force_set <- trimws(unlist(strsplit(force_env, "[,;\\s]+")))
  force_set <- force_set[nzchar(force_set)]
}
formal_paths <- function(subtype) {
  gene_data <- file.path(root, "结果文件", subtype, "scTenifoldKnk", "Cplx2", "数据文件")
  wt_rep <- file.path(root, "结果文件", subtype, "scTenifoldKnk", "_野生型", "报告文件")
  dir.create(gene_data, recursive = TRUE, showWarnings = FALSE)
  dir.create(wt_rep, recursive = TRUE, showWarnings = FALSE)
  list(
    rds = file.path(gene_data, paste0("正式_", subtype, "_Cplx2_formal.rds")),
    csv = file.path(gene_data, paste0("04_扰动基因_", subtype, "_Cplx2Dr_Formal.csv")),
    log = file.path(wt_rep, paste0("04_workerlog_", subtype, ".txt"))
  )
}
is_subtype_done <- function(subtype) {
  p <- formal_paths(subtype)
  file.exists(p$rds) && file.exists(p$csv) && file.info(p$rds)$size > 1000
}
load_done_dr <- function(subtype) {
  utils::read.csv(formal_paths(subtype)$csv, check.names = FALSE, stringsAsFactors = FALSE)
}

# Order by cell count ascending → earlier checkpoints on smaller subtypes
cell_n <- vapply(targets, function(s) sum(sub_meta$subtype == s), integer(1))
targets_ordered <- targets[order(cell_n, targets)]
message("subtype order (small→large cells): ", paste(sprintf("%s(%d)", targets_ordered, cell_n[targets_ordered]), collapse = ", "))

todo <- character(0)
skipped <- character(0)
for (s in targets_ordered) {
  must <- force_all || (s %in% force_set)
  if (!must && is_subtype_done(s)) skipped <- c(skipped, s) else todo <- c(todo, s)
}
message(sprintf(
  "Resume plan: skip=%s | run=%s | FORCE_RERUN='%s'",
  if (length(skipped)) paste(skipped, collapse = ",") else "(none)",
  if (length(todo)) paste(todo, collapse = ",") else "(none)",
  force_env
))
writeLines(c(
  paste0("time=", format(Sys.time())),
  paste0("mode=sequential_subtypes_parallel_nNet"),
  paste0("n_net_workers=", n_net_workers),
  paste0("blas_per_net=", blas_per_net),
  paste0("skip=", paste(skipped, collapse = ",")),
  paste0("run=", paste(todo, collapse = ",")),
  "unit=per_subtype (no mid-call percent resume)",
  "note=cannot add cores to a live scTenifoldKnk call"
), file.path(rep_dir, "RESUME_PLAN.txt"))

run_one_formal <- function(subtype, mat, gKO = "Cplx2") {
  n_cells <- ncol(mat)
  n_use <- min(500L, n_cells - 1L)
  p <- formal_paths(subtype)
  cat(sprintf(
    "[%s] START %s genes=%d cells=%d nc_nCells=%d nNetWorkers=%d BLAS=%d\n",
    format(Sys.time(), "%H:%M:%S"), subtype, nrow(mat), n_cells, n_use, n_net_workers, blas_per_net
  ), file = p$log, append = TRUE)
  writeLines(c(
    paste0("subtype=", subtype),
    paste0("phase=RUNNING"),
    paste0("time=", format(Sys.time())),
    paste0("genes=", nrow(mat)),
    paste0("cells=", n_cells)
  ), file.path(rep_dir, "CURRENT_SUBTYPE.txt"))
  t0 <- proc.time()
  res <- scTenifoldKnk(
    countMatrix = mat,
    gKO = gKO,
    qc = TRUE,
    qc_minLibSize = 1000,
    qc_minPCT = 0.05,
    nc_nNet = 10,
    nc_nCells = n_use,
    td_K = 3,
    # nCores is ignored by Rcpp pcNet; parallelism comes from patched makeNetworks
    nCores = 1L
  )
  elapsed <- (proc.time() - t0)[["elapsed"]]
  rds_tmp <- paste0(p$rds, ".tmp")
  saveRDS(res, rds_tmp)
  if (file.exists(p$rds)) file.remove(p$rds)
  file.rename(rds_tmp, p$rds)
  dr <- res$diffRegulation
  if (is.null(dr)) dr <- res[["dRegulation"]]
  if (is.null(dr)) stop("unexpected return for ", subtype)
  dr$subtype <- subtype
  dr$gKO <- gKO
  dr$elapsed_sec <- elapsed
  dr$n_genes_in <- nrow(mat)
  dr$n_cells_in <- n_cells
  dr$nc_nCells_used <- n_use
  dr$nc_nNet <- 10L
  dr$qc_minLibSize <- 1000L
  dr$run_mode <- "formal_maxcpu_sequential_parallel_nNet"
  utils::write.csv(dr, p$csv, row.names = FALSE)
  others <- dr[dr$gene != gKO & is.finite(dr$p.adj) & dr$p.adj < 0.05, , drop = FALSE]
  cat(sprintf(
    "[%s] DONE %s in %.1f min | FDR<0.05 excl KO: %d | checkpoint=%s\n",
    format(Sys.time(), "%H:%M:%S"), subtype, elapsed / 60, nrow(others), basename(p$rds)
  ), file = p$log, append = TRUE)
  message(sprintf("DONE %s in %.1f min | FDR<0.05 excl KO=%d", subtype, elapsed / 60, nrow(others)))
  dr
}

all_dr_list <- list()
for (s in skipped) {
  message("Loading checkpoint: ", s)
  all_dr_list[[s]] <- load_done_dr(s)
}

if (length(todo)) {
  for (subtype in todo) {
    message("==== subtype ", subtype, " ====")
    idx <- which(sub_meta$subtype == subtype)
    mat <- prep_matrix_formal(sub_counts[, idx, drop = FALSE])
    all_dr_list[[subtype]] <- run_one_formal(subtype, mat)
  }
} else {
  message("Nothing to run — all subtypes already checkpointed.")
}

all_dr <- do.call(rbind, all_dr_list[targets])
write.csv(all_dr, file.path(tab_dir, "04_扰动基因_五亚群_Cplx2DrAll_Formal.csv"), row.names = FALSE)
write.csv(all_dr, file.path(tab_dir, "04_扰动基因_五亚群_Cplx2DrAll.csv"), row.names = FALSE)

sig <- all_dr[all_dr$gene != "Cplx2" & is.finite(all_dr$p.adj) & all_dr$p.adj < 0.05, ]
write.csv(sig, file.path(tab_dir, "04_显著扰动_FDR05_Formal.csv"), row.names = FALSE)

rank_col <- "distance"
top <- do.call(rbind, lapply(split(all_dr, all_dr$subtype), function(df) {
  df <- df[order(df[[rank_col]], decreasing = TRUE), , drop = FALSE]
  head(df, 15)
}))
write.csv(top, file.path(tab_dir, "04_扰动基因_Top15_Cplx2DrTop_Formal.csv"), row.names = FALSE)

p2 <- ggplot(top, aes(.data[[rank_col]], reorder(gene, .data[[rank_col]]))) +
  geom_col(fill = "#F58518", width = 0.7) +
  facet_wrap(~ subtype, scales = "free_y") +
  labs(
    title = "Top predicted perturbed genes (formal defaults, max-CPU)",
    subtitle = "nc_nNet=10 parallelized; nc_nCells=min(500,n-1); qc_minLibSize=1000",
    x = rank_col, y = NULL
  ) +
  theme_bw()
ggplot2::ggsave(file.path(fig_dir, "04_柱状图_扰动基因_Cplx2DrBar_Formal.png"), p2, width = 10, height = 8, dpi = 600)
ggplot2::ggsave(file.path(fig_dir, "04_柱状图_扰动基因_Cplx2DrBar_Formal.svg"), p2, width = 10, height = 8)

si <- capture.output(sessionInfo())
writeLines(c(
  "STATUS=FORMAL_COMPLETE",
  "data_provenance=REAL",
  "accession=GSE197289",
  "model=Control",
  "subtypes=cLTMR,NF1,NP,PEP,TRPM8",
  "gKO=Cplx2",
  "run_mode=formal_maxcpu_sequential_parallel_nNet",
  "checkpoint=per_subtype_rds_and_csv",
  "mid_call_percent_resume=NO",
  "gpu=NOT_USED (scTenifoldKnk/scTenifoldNet CPU-only)",
  "python_gpu_alt=GenKI (PyTorch VGAE; different method, same WT-only input class)",
  "python_cpu_port=sctenifoldpy (scTenifoldKnk port; not CUDA-focused)",
  paste0("n_net_workers=", n_net_workers),
  paste0("blas_per_net=", blas_per_net),
  paste0("skipped_this_run=", paste(skipped, collapse = ",")),
  paste0("ran_this_run=", paste(todo, collapse = ",")),
  "qc_minLibSize=1000",
  "nc_nNet=10",
  "nc_nCells=min(500, n_cells-1)",
  "td_K=3",
  "gene_filter=detected_in_>=25_cells; soft_cap_8000_top_mean_if_needed; Cplx2_forced",
  "cpu=Intel_Core_Ultra_9_285K_24logical",
  "claim=computational prediction; not chronic TN model validation",
  paste0("n_FDR05_excl_KO=", nrow(sig)),
  "resume_hint=re-run same script to skip done subtypes; FORCE_RERUN=1 to redo all",
  si
), file.path(rep_dir, "STATUS_Formal.txt"))
writeLines("phase=ALL_DONE", file.path(rep_dir, "CURRENT_SUBTYPE.txt"))
message("=== FORMAL_KO_DONE ", format(Sys.time()), " ===")
