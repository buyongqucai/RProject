# GPU wild-type, then one knockout per gene. Enrichment figures use the netpharm geoms.
args <- commandArgs(trailingOnly = TRUE)
desk <- if (length(args) >= 1) args[[1]] else "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除"
algo <- "scTenifoldKnk_1.4.3_GPU"
wt_dir <- function(subtype) file.path(desk, "结果文件", subtype, algo, "_野生型", "数据文件")
wt_note_dir <- function(subtype) file.path(desk, "结果文件", subtype, algo, "_野生型", "报告文件")
ko_data_dir <- function(subtype, gene) file.path(desk, "结果文件", subtype, algo, gene, "数据文件")
ko_note_dir <- function(subtype, gene) file.path(desk, "结果文件", subtype, algo, gene, "报告文件")
enr_data_dir <- function(subtype, gene) file.path(desk, "结果文件", subtype, algo, gene, "数据文件")
enr_fig_dir <- function(subtype, gene) file.path(desk, "结果文件", subtype, algo, gene, "图片文件")
np_plots <- "e:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology/脚本_scripts/02_可视化_NetworkPharmPlots.R"
if (requireNamespace("RhpcBLASctl", quietly = TRUE)) {
  RhpcBLASctl::blas_set_num_threads(4L)
  RhpcBLASctl::omp_set_num_threads(4L)
}
Sys.setenv(OMP_NUM_THREADS = "4", OPENBLAS_NUM_THREADS = "4", MKL_NUM_THREADS = "4")
suppressPackageStartupMessages({
  library(scTenifoldNet)
  library(scTenifoldKnk)
  library(ggplot2)
})
source(np_plots, local = FALSE)

targets <- c("Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21")

read_wt <- function(folder) {
  genes <- readLines(file.path(folder, "genes.txt"), warn = FALSE, encoding = "UTF-8")
  n <- length(genes)
  raw <- readBin(file.path(folder, "gpu_wt_rounded.bin"), what = "double", n = n * n)
  wt <- matrix(raw, nrow = n, ncol = n, byrow = TRUE)
  rownames(wt) <- genes
  colnames(wt) <- genes
  diag(wt) <- 0
  t(wt)
}

gene_ratio <- function(text) {
  parts <- strsplit(as.character(text), "/", fixed = TRUE)
  vapply(parts, function(x) as.numeric(x[[1]]) / as.numeric(x[[2]]), numeric(1))
}

save_plot <- function(plot, path, width, height) {
  ggplot2::ggsave(path, plot, width = width, height = height, dpi = 300, bg = "white")
}

enrich_one <- function(symbols, data_dir, fig_dir) {
  dir.create(data_dir, recursive = TRUE, showWarnings = FALSE)
  dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)
  empty <- data.frame()
  if (!requireNamespace("clusterProfiler", quietly = TRUE) || !requireNamespace("org.Mm.eg.db", quietly = TRUE)) {
    writeLines("clusterProfiler or org.Mm.eg.db is not installed", file.path(data_dir, "富集_缺失.txt"))
    return(invisible(NULL))
  }
  symbols <- unique(symbols)
  if (length(symbols) < 2) {
    write.csv(empty, file.path(data_dir, "富集_GO.csv"), row.names = FALSE)
    write.csv(empty, file.path(data_dir, "富集_KEGG.csv"), row.names = FALSE)
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
  write.csv(go_df, file.path(data_dir, "富集_GO.csv"), row.names = FALSE)
  if (nrow(go_df)) {
    save_plot(np_plot_go_bubble(go_df, top_n = 10), file.path(fig_dir, "GO气泡.png"), 8.5, 9)
    save_plot(np_plot_go_bar(go_df, top_n = 10), file.path(fig_dir, "GO柱状.png"), 9, 7)
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
  write.csv(kegg_df, file.path(data_dir, "富集_KEGG.csv"), row.names = FALSE)
  if (nrow(kegg_df)) {
    save_plot(np_plot_kegg_lollipop(kegg_df, top_n = 20), file.path(fig_dir, "KEGG棒棒糖.png"), 8, 7)
    save_plot(np_plot_kegg_bar(kegg_df, top_n = 20), file.path(fig_dir, "KEGG柱状.png"), 8, 7)
  }
}

knock_one <- function(wt, subtype, gene) {
  data_dir <- ko_data_dir(subtype, gene)
  note_dir <- ko_note_dir(subtype, gene)
  dir.create(data_dir, recursive = TRUE, showWarnings = FALSE)
  dir.create(note_dir, recursive = TRUE, showWarnings = FALSE)
  if (max(abs(wt[gene, ])) == 0) {
    writeLines("这个基因在四舍五入后的野生型网里没有出边。敲除不改变网络，不再做富集。", file.path(note_dir, "说明_无出边.txt"))
    write.csv(data.frame(gene = character(), distance = numeric(), Z = numeric(), FC = numeric(), p.value = numeric(), p.adj = numeric()), file.path(data_dir, "响应基因_Responsive.csv"), row.names = FALSE)
    cat("KO", gene, "no outgoing edges\n")
    return(invisible(NULL))
  }
  ko <- wt
  ko[gene, ] <- 0
  started <- proc.time()[["elapsed"]]
  aligned <- scTenifoldNet::manifoldAlignment(wt, ko, d = 2)
  table <- scTenifoldKnk::dRegulation(aligned)
  elapsed <- proc.time()[["elapsed"]] - started
  write.csv(table, file.path(data_dir, "扰动_Dr.csv"), row.names = FALSE)
  responsive <- table[table$gene != gene & table$p.adj < 0.05, , drop = FALSE]
  write.csv(responsive, file.path(data_dir, "响应基因_Responsive.csv"), row.names = FALSE)
  writeLines(sprintf("seconds,%.3f\nn_responsive,%d", elapsed, nrow(responsive)), file.path(note_dir, "计时.txt"))
  enrich_one(responsive$gene, enr_data_dir(subtype, gene), enr_fig_dir(subtype, gene))
  cat("KO", gene, "responsive", nrow(responsive), sprintf("%.1f", elapsed), "\n")
}

for (subtype in c("PEP", "NF1")) {
  folder <- wt_dir(subtype)
  wt <- read_wt(folder)
  timing <- readLines(file.path(wt_note_dir(subtype), "timings.csv"), warn = FALSE, encoding = "UTF-8")
  control_line <- timing[grepl("^control,", timing)]
  control <- sub(".*gene=([^;]+).*", "\\1", control_line)
  genes <- c(targets, control)
  genes <- genes[genes %in% rownames(wt)]
  for (gene in genes) {
    knock_one(wt, subtype, gene)
  }
}
cat("KO_DONE\n")
