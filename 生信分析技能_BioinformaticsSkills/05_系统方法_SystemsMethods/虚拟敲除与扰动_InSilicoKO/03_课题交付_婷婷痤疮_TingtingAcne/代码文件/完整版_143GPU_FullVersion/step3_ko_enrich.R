# 步骤 3：虚拟敲除 + 流形对齐 + dRegulation + GO/KEGG 富集。
# 用法: Rscript step3_ko_enrich.R <run_env.txt>
# 每个基因一个目录：<亚群>/scTenifoldKnk_1.4.3_GPU/<基因>/{数据文件,图片文件,报告文件}
options(stringsAsFactors = FALSE)

args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) >= 1)
kv <- list()
for (line in readLines(args[[1]], warn = FALSE, encoding = "UTF-8")) {
  if (!grepl("=", line) || grepl("^#", line)) next
  pos <- regexpr("=", line, fixed = TRUE)[1]
  kv[[substr(line, 1, pos - 1)]] <- substr(line, pos + 1, nchar(line))
}
get_int <- function(key) as.integer(kv[[key]])
get_num <- function(key) as.numeric(kv[[key]])

if (requireNamespace("RhpcBLASctl", quietly = TRUE)) {
  RhpcBLASctl::blas_set_num_threads(get_int("R_THREADS"))
  RhpcBLASctl::omp_set_num_threads(get_int("R_THREADS"))
}

org_db_name <- if (!is.null(kv[["ORG_DB"]]) && nzchar(kv[["ORG_DB"]])) kv[["ORG_DB"]] else "org.Mm.eg.db"
kegg_org <- if (!is.null(kv[["KEGG_ORGANISM"]]) && nzchar(kv[["KEGG_ORGANISM"]])) kv[["KEGG_ORGANISM"]] else "mmu"
suppressPackageStartupMessages({
  library(scTenifoldNet)
  library(scTenifoldKnk)
  library(clusterProfiler)
  if (!requireNamespace(org_db_name, quietly = TRUE)) {
    stop("missing OrgDb package: ", org_db_name)
  }
  library(org_db_name, character.only = TRUE)
})
org_db <- get(org_db_name)

result_dir <- kv[["RESULT_DIR"]]
subtypes <- strsplit(kv[["SUBTYPES"]], ",", fixed = TRUE)[[1]]
targets <- strsplit(kv[["KNOCK_GENES"]], ",", fixed = TRUE)[[1]]
algo <- "scTenifoldKnk_1.4.3_GPU"
fdr_cut <- get_num("FDR_CUT")
align_d <- get_int("KO_ALIGN_D")

gene_ratio <- function(text) {
  parts <- strsplit(as.character(text), "/", fixed = TRUE)
  vapply(parts, function(x) as.numeric(x[[1]]) / as.numeric(x[[2]]), numeric(1))
}

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

enrich_one <- function(symbols, data_dir, note_dir) {
  dir.create(data_dir, recursive = TRUE, showWarnings = FALSE)
  dir.create(note_dir, recursive = TRUE, showWarnings = FALSE)
  empty <- data.frame()
  symbols <- unique(symbols)
  if (length(symbols) < 2) {
    write.csv(empty, file.path(data_dir, "富集_GO.csv"), row.names = FALSE)
    write.csv(empty, file.path(data_dir, "富集_KEGG.csv"), row.names = FALSE)
    writeLines(sprintf("too_few_genes n=%d", length(symbols)), file.path(note_dir, "富集_EnrichNote.txt"))
    return(invisible(NULL))
  }
  parts <- list()
  for (ont in c("BP", "CC", "MF")) {
    ego <- tryCatch(
      clusterProfiler::enrichGO(
        symbols, OrgDb = org_db, keyType = "SYMBOL", ont = ont,
        pAdjustMethod = "BH", pvalueCutoff = get_num("ENRICH_P"), qvalueCutoff = get_num("ENRICH_Q"), readable = FALSE
      ),
      error = function(e) NULL
    )
    if (is.null(ego) || nrow(as.data.frame(ego)) == 0) next
    frame <- as.data.frame(ego)
    frame$ontology <- ont
    frame$term <- frame$Description
    frame$enrichment <- gene_ratio(frame$GeneRatio)
    frame$count <- frame$Count
    parts[[ont]] <- frame
  }
  go_df <- if (length(parts)) do.call(rbind, parts) else empty
  write.csv(go_df, file.path(data_dir, "富集_GO.csv"), row.names = FALSE)

  mapped <- tryCatch(
    clusterProfiler::bitr(symbols, fromType = "SYMBOL", toType = "ENTREZID", OrgDb = org_db),
    error = function(e) NULL
  )
  kegg_df <- empty
  if (!is.null(mapped) && nrow(mapped) >= 2) {
    kegg <- tryCatch(
      clusterProfiler::enrichKEGG(
        unique(mapped$ENTREZID), organism = kegg_org,
        pAdjustMethod = "BH", pvalueCutoff = get_num("ENRICH_P"), qvalueCutoff = get_num("ENRICH_Q")
      ),
      error = function(e) NULL
    )
    if (!is.null(kegg) && nrow(as.data.frame(kegg))) {
      kegg_df <- as.data.frame(kegg)
      kegg_df$term <- kegg_df$Description
      kegg_df$count <- kegg_df$Count
    }
  }
  write.csv(kegg_df, file.path(data_dir, "富集_KEGG.csv"), row.names = FALSE)
  writeLines(
    sprintf("genes=%d\ngo_terms=%d\nkegg_terms=%d", length(symbols), nrow(go_df), nrow(kegg_df)),
    file.path(note_dir, "富集_EnrichNote.txt")
  )
}

knock_one <- function(wt, subtype, gene, control_gene) {
  base <- file.path(result_dir, subtype, algo, gene)
  data_dir <- file.path(base, "数据文件")
  note_dir <- file.path(base, "报告文件")
  dir.create(data_dir, recursive = TRUE, showWarnings = FALSE)
  dir.create(note_dir, recursive = TRUE, showWarnings = FALSE)
  if (file.exists(file.path(data_dir, "扰动_Dr.csv"))) {
    message(subtype, " ", gene, " 已有扰动表，跳过")
    return(invisible(NULL))
  }
  if (max(abs(wt[gene, ])) == 0) {
    writeLines("这个基因在四舍五入后的野生型网里没有出边。敲除不改变网络，不再做富集。", file.path(note_dir, "说明_无出边.txt"))
    write.csv(
      data.frame(gene = character(), distance = numeric(), Z = numeric(), FC = numeric(), p.value = numeric(), p.adj = numeric()),
      file.path(data_dir, "扰动_Dr.csv"),
      row.names = FALSE
    )
    write.csv(
      data.frame(gene = character(), distance = numeric(), Z = numeric(), FC = numeric(), p.value = numeric(), p.adj = numeric()),
      file.path(data_dir, "响应基因_Responsive.csv"),
      row.names = FALSE
    )
    message(subtype, " ", gene, " no outgoing edges")
    return(invisible(NULL))
  }
  ko <- wt
  ko[gene, ] <- 0
  started <- proc.time()[["elapsed"]]
  aligned <- scTenifoldNet::manifoldAlignment(wt, ko, d = align_d)
  table <- scTenifoldKnk::dRegulation(aligned)
  elapsed <- proc.time()[["elapsed"]] - started
  write.csv(table, file.path(data_dir, "扰动_Dr.csv"), row.names = FALSE)
  responsive <- table[table$gene != gene & table$p.adj < fdr_cut, , drop = FALSE]
  write.csv(responsive, file.path(data_dir, "响应基因_Responsive.csv"), row.names = FALSE)
  writeLines(
    sprintf("seconds,%.3f\nn_responsive,%d\ncontrol,%s\nis_control,%s", elapsed, nrow(responsive), control_gene, gene == control_gene),
    file.path(note_dir, "计时.txt")
  )
  enrich_one(responsive$gene, data_dir, note_dir)
  message(subtype, " ", gene, " responsive ", nrow(responsive), " ", sprintf("%.1fs", elapsed))
}

for (subtype in subtypes) {
  wt_folder <- file.path(result_dir, subtype, algo, "_野生型", "数据文件")
  note_folder <- file.path(result_dir, subtype, algo, "_野生型", "报告文件")
  wt <- read_wt(wt_folder)
  timing <- readLines(file.path(note_folder, "timings.csv"), warn = FALSE, encoding = "UTF-8")
  control_line <- timing[grepl("control,", timing)]
  control <- sub(".*gene=([^;]+).*", "\\1", control_line)
  genes <- c(targets, control)
  genes <- genes[genes %in% rownames(wt)]
  for (gene in genes) knock_one(wt, subtype, gene, control)
}
cat("STEP3_DONE\n")
