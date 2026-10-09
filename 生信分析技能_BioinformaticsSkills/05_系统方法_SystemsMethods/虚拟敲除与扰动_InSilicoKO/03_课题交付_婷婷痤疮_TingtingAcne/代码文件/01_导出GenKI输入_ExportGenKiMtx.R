# 导出 GenKI 用 mtx：皮损 × 指定 celltype
# Usage: Rscript 01_...R "TREM2 macrophage"
options(stringsAsFactors = FALSE)
args <- commandArgs(trailingOnly = TRUE)
subtype <- if (length(args) >= 1) args[[1]] else "TREM2 macrophage"
stim_keep <- "Lesional"

raw <- "C:/Users/10540/Desktop/婷婷/虚拟敲除/数据文件"
out <- file.path(
  "C:/Users/10540/Desktop/婷婷/虚拟敲除/结果文件", subtype, "GenKI", "_野生型", "数据文件"
)
dir.create(out, recursive = TRUE, showWarnings = FALSE)
done <- file.path(out, "counts.mtx")
if (file.exists(done) && file.exists(file.path(out, "genes.tsv")) && file.exists(file.path(out, "cells.tsv"))) {
  message("skip existing ", subtype)
  quit(save = "no", status = 0)
}

suppressPackageStartupMessages(library(Matrix))
meta <- read.csv(gzfile(file.path(raw, "01_细胞注释_CellMeta_GSE175817.csv.gz")), check.names = FALSE)
counts <- readRDS(gzcon(gzfile(file.path(raw, "02_表达矩阵_Counts_GSE175817.RDS.gz"), "rb")))
meta <- meta[match(colnames(counts), meta$cell_id), , drop = FALSE]
keep <- meta$stim == stim_keep & meta$celltype == subtype
mat <- counts[, keep, drop = FALSE]
if (ncol(mat) < 2) stop("too few cells for ", subtype)

# GenKI / scanpy expect cells × genes mtx (mmread then .T in Python reader expects genes×cells file then transpose)
# 与琪乐无穷一致：写 genes×cells，Python 端 mmread().T
Matrix::writeMM(mat, done)
writeLines(rownames(mat), file.path(out, "genes.tsv"), useBytes = TRUE)
writeLines(colnames(mat), file.path(out, "cells.tsv"), useBytes = TRUE)
writeLines(
  c(
    paste0("subtype=", subtype),
    paste0("stim=", stim_keep),
    paste0("n_genes=", nrow(mat)),
    paste0("n_cells=", ncol(mat)),
    paste0("AHR_detected=", if ("AHR" %in% rownames(mat)) sum(mat["AHR", ] > 0) else 0)
  ),
  file.path(out, "export_note.txt"),
  useBytes = TRUE
)
message("EXPORT_GENKI ", subtype, " genes=", nrow(mat), " cells=", ncol(mat))
