# Official CPU tensor, knockout, dRegulation, and enrichment from the saved 1.4.3 networks.
args <- commandArgs(trailingOnly = TRUE)
root <- args[[1]]
np_plots <- "e:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology/脚本_scripts/02_可视化_NetworkPharmPlots.R"
if (requireNamespace("RhpcBLASctl", quietly = TRUE)) {
  RhpcBLASctl::blas_set_num_threads(4L)
  RhpcBLASctl::omp_set_num_threads(4L)
}
Sys.setenv(OMP_NUM_THREADS = "4", OPENBLAS_NUM_THREADS = "4", MKL_NUM_THREADS = "4")
suppressPackageStartupMessages({
  library(Matrix)
  library(scTenifoldNet)
  library(scTenifoldKnk)
  library(ggplot2)
})
source(np_plots, local = FALSE)

targets <- c("Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21")

gene_ratio <- function(text) {
  parts <- strsplit(as.character(text), "/", fixed = TRUE)
  vapply(parts, function(x) as.numeric(x[[1]]) / as.numeric(x[[2]]), numeric(1))
}

save_plot <- function(plot, path, width, height) {
  ggplot2::ggsave(path, plot, width = width, height = height, dpi = 300, bg = "white")
}

enrich_one <- function(symbols, out_dir) {
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  empty <- data.frame()
  symbols <- unique(symbols)
  if (length(symbols) < 2) {
    write.csv(empty, file.path(out_dir, "富集_GO.csv"), row.names = FALSE)
    write.csv(empty, file.path(out_dir, "富集_KEGG.csv"), row.names = FALSE)
    return(invisible(NULL))
  }
  go_parts <- list()
  for (ont in c("BP", "CC", "MF")) {
    ego <- tryCatch(
      clusterProfiler::enrichGO(symbols, OrgDb = org.Mm.eg.db::org.Mm.eg.db, keyType = "SYMBOL", ont = ont, pAdjustMethod = "BH", pvalueCutoff = 0.05, qvalueCutoff = 0.2, readable = FALSE),
      error = function(e) NULL
    )
    if (is.null(ego) || nrow(as.data.frame(ego)) == 0) next
    frame <- as.data.frame(ego)
    frame$ontology <- ont
    frame$term <- frame$Description
    frame$enrichment <- gene_ratio(frame$GeneRatio)
    frame$count <- frame$Count
    go_parts[[ont]] <- frame
  }
  go_df <- if (length(go_parts)) do.call(rbind, go_parts) else empty
  write.csv(go_df, file.path(out_dir, "富集_GO.csv"), row.names = FALSE)
  if (nrow(go_df)) {
    save_plot(np_plot_go_bubble(go_df, top_n = 10), file.path(out_dir, "GO气泡.png"), 8.5, 9)
    save_plot(np_plot_go_bar(go_df, top_n = 10), file.path(out_dir, "GO柱状.png"), 9, 7)
  }
  mapped <- tryCatch(
    clusterProfiler::bitr(symbols, fromType = "SYMBOL", toType = "ENTREZID", OrgDb = org.Mm.eg.db::org.Mm.eg.db),
    error = function(e) NULL
  )
  kegg <- NULL
  if (!is.null(mapped) && nrow(mapped) >= 2) {
    kegg <- tryCatch(
      clusterProfiler::enrichKEGG(unique(mapped$ENTREZID), organism = "mmu", pAdjustMethod = "BH", pvalueCutoff = 0.05, qvalueCutoff = 0.2),
      error = function(e) NULL
    )
  }
  kegg_df <- if (is.null(kegg)) empty else as.data.frame(kegg)
  if (nrow(kegg_df)) {
    kegg_df$term <- kegg_df$Description
    kegg_df$count <- kegg_df$Count
  }
  write.csv(kegg_df, file.path(out_dir, "富集_KEGG.csv"), row.names = FALSE)
  if (nrow(kegg_df)) {
    save_plot(np_plot_kegg_lollipop(kegg_df, top_n = 20), file.path(out_dir, "KEGG棒棒糖.png"), 8, 7)
    save_plot(np_plot_kegg_bar(kegg_df, top_n = 20), file.path(out_dir, "KEGG柱状.png"), 8, 7)
  }
}

knock_one <- function(wt, gene, out_dir) {
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  if (max(abs(wt[gene, ])) == 0) {
    writeLines("这个基因在四舍五入后的野生型网里没有出边。敲除不改变网络，不再做富集。", file.path(out_dir, "说明_无出边.txt"))
    write.csv(data.frame(gene = character(), distance = numeric(), Z = numeric(), FC = numeric(), p.value = numeric(), p.adj = numeric()), file.path(out_dir, "响应基因_Responsive.csv"), row.names = FALSE)
    cat("KO", gene, "no outgoing edges\n")
    return(invisible(NULL))
  }
  ko <- wt
  ko[gene, ] <- 0
  started <- proc.time()[["elapsed"]]
  aligned <- scTenifoldNet::manifoldAlignment(wt, ko, d = 2, nCores = 1L)
  table <- scTenifoldKnk::dRegulation(aligned, empiricalNull = FALSE)
  elapsed <- proc.time()[["elapsed"]] - started
  write.csv(table, file.path(out_dir, "扰动_Dr.csv"), row.names = FALSE)
  responsive <- table[table$gene != gene & table$p.adj < 0.05, , drop = FALSE]
  write.csv(responsive, file.path(out_dir, "响应基因_Responsive.csv"), row.names = FALSE)
  writeLines(sprintf("seconds,%.3f\nn_responsive,%d", elapsed, nrow(responsive)), file.path(out_dir, "计时.txt"))
  enrich_one(responsive$gene, out_dir)
  cat("KO", gene, "responsive", nrow(responsive), sprintf("%.1f", elapsed), "\n")
}

read_gpu_wt <- function(folder) {
  genes <- readLines(file.path(folder, "genes.txt"), warn = FALSE, encoding = "UTF-8")
  n <- length(genes)
  raw <- readBin(file.path(folder, "gpu_wt_rounded.bin"), what = "double", n = n * n)
  wt <- matrix(raw, nrow = n, ncol = n, byrow = TRUE)
  rownames(wt) <- colnames(wt) <- genes
  diag(wt) <- 0
  t(wt)
}

for (subtype in c("PEP", "NF1")) {
  gpu_dir <- file.path(root, subtype, "scTenifoldKnk", "_野生型")
  cpu_dir <- file.path(root, subtype, "scTenifoldKnk_CPU", "_野生型")
  genes <- readLines(file.path(gpu_dir, "genes.txt"), warn = FALSE, encoding = "UTF-8")
  nets <- vector("list", 10L)
  t0 <- proc.time()
  for (i in seq_len(10L)) {
    nets[[i]] <- readRDS(file.path(cpu_dir, sprintf("net_%02d.rds", i)))
    nets[[i]] <- as(nets[[i]], "dgCMatrix")
    rownames(nets[[i]]) <- colnames(nets[[i]]) <- genes
  }
  load_sec <- (proc.time() - t0)[["elapsed"]]
  t0 <- proc.time()
  set.seed(1)
  decomposed <- scTenifoldNet::tensorDecomposition(xList = nets, K = 3, maxError = 1e-5, maxIter = 1000, nDecimal = 3)
  tensor_sec <- (proc.time() - t0)[["elapsed"]]
  rm(nets)
  gc()
  wt <- decomposed$X
  rm(decomposed)
  t0 <- proc.time()
  wt <- scTenifoldKnk:::strictDirection(wt, lambda = 0)
  wt <- as.matrix(wt)
  diag(wt) <- 0
  wt <- t(wt)
  direction_sec <- (proc.time() - t0)[["elapsed"]]
  gpu_wt <- read_gpu_wt(gpu_dir)
  wt_gap <- max(abs(wt - gpu_wt))
  rm(gpu_wt)
  writeLines(
    c(
      "step,seconds,detail",
      sprintf("load_rds,%.3f,nets=10", load_sec),
      sprintf("tensor,%.3f,K=3;maxIter=1000;tol=1e-5", tensor_sec),
      sprintf("direction,%.3f,lambda=0", direction_sec),
      sprintf("wt_max_abs_vs_gpu,%.6e,after_round_diag_transpose", wt_gap)
    ),
    file.path(cpu_dir, "timings_tail.csv")
  )
  cat(subtype, "tensor", sprintf("%.3f", tensor_sec), "wt_vs_gpu", sprintf("%.6e", wt_gap), "\n")
  timing <- readLines(file.path(gpu_dir, "timings.csv"), warn = FALSE, encoding = "UTF-8")
  control <- sub(".*gene=([^;]+).*", "\\1", timing[grepl("^control,", timing)])
  for (gene in c(targets, control)) {
    if (!gene %in% rownames(wt)) next
    knock_one(wt, gene, file.path(root, subtype, "scTenifoldKnk_CPU", gene))
  }
  rm(wt)
  gc()
}
cat("CPU_TAIL_DONE\n")
