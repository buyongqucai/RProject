# Export one Control subtype count matrix for GenKI.
# Does not copy the GEO RDS and does not touch Knk result paths.
options(stringsAsFactors = FALSE)

args <- commandArgs(trailingOnly = TRUE)
requested <- if (length(args) >= 1) args[[1]] else "cLTMR"
subtypes <- if (requested == "all") {
  c("cLTMR", "NF1", "NP", "PEP", "TRPM8")
} else {
  requested
}

root <- "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除"
raw_dir <- file.path(root, "数据文件")

message("loading meta and counts once")
meta <- read.csv(
  gzfile(file.path(raw_dir, "01_细胞注释_CellMeta_GSE197289.csv.gz")),
  check.names = FALSE
)
counts <- readRDS(gzcon(gzfile(
  file.path(raw_dir, "02_表达矩阵_Counts_GSE197289.RDS.gz"),
  "rb"
)))
stopifnot(inherits(counts, "dgCMatrix"))
meta <- meta[match(colnames(counts), meta$V1), , drop = FALSE]
stopifnot(!anyNA(meta$V1))

for (subtype in subtypes) {
out_dir <- file.path(root, "结果文件", subtype, "GenKI", "_野生型", "数据文件")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
if (file.exists(file.path(out_dir, "counts.mtx")) && file.exists(file.path(out_dir, "EXPORT.txt"))) {
  message("skip existing ", subtype)
  next
}

keep <- meta$model == "Control" & meta$subtype == subtype
sub_meta <- meta[keep, , drop = FALSE]
sub <- counts[, keep, drop = FALSE]
if (ncol(sub) < 1) stop("no cells for subtype ", subtype)

rn <- rownames(sub)
if (anyDuplicated(rn)) {
  message("aggregating duplicated gene names: ", sum(duplicated(rn)))
  sub <- Matrix::Matrix(rowsum(as.matrix(sub), rn), sparse = TRUE)
}
cn <- colnames(sub)
if (anyDuplicated(cn)) cn <- make.unique(cn)
colnames(sub) <- cn
if (!"Cplx2" %in% rownames(sub)) stop("Cplx2 missing after export")

mtx <- file.path(out_dir, "counts.mtx")
Matrix::writeMM(sub, mtx)
writeLines(rownames(sub), file.path(out_dir, "genes.tsv"))
writeLines(colnames(sub), file.path(out_dir, "cells.tsv"))
write.csv(
  sub_meta,
  file.path(out_dir, "cell_meta.csv"),
  row.names = FALSE,
  quote = TRUE
)
note <- c(
  paste0("subtype=", subtype),
  "model=Control",
  "accession=GSE197289",
  "orientation=genes_x_cells",
  paste0("genes=", nrow(sub)),
  paste0("cells=", ncol(sub)),
  paste0("Cplx2_detected_cells=", sum(sub["Cplx2", ] > 0))
)
writeLines(note, file.path(out_dir, "EXPORT.txt"))
message(paste(note, collapse = " | "))
message("wrote ", out_dir)
}
