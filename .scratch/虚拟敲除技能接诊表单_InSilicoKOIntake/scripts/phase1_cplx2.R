# M4 Phase1: Cplx2 detection. No knockout.
options(stringsAsFactors = FALSE)
data_dir <- "E:/RProject/.scratch/虚拟敲除技能接诊表单_InSilicoKOIntake/data"
out_dir <- "E:/RProject/.scratch/虚拟敲除技能接诊表单_InSilicoKOIntake/phase1"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

det_table <- function(mat, groups, gene = "Cplx2") {
  rn <- rownames(mat)
  hit <- which(rn == gene)
  if (length(hit) != 1L) {
    hit <- which(tolower(rn) == tolower(gene))
  }
  if (length(hit) != 1L) stop("gene not found: ", gene)
  x <- mat[hit[1], ]
  x <- as.numeric(x)
  groups <- as.character(groups)
  if (length(groups) != length(x)) stop("group length mismatch")
  spl <- split(x, groups)
  rows <- lapply(names(spl), function(g) {
    v <- spl[[g]]
    data.frame(
      group = g,
      n_cells = length(v),
      n_detected = sum(v > 0, na.rm = TRUE),
      detection_rate = mean(v > 0, na.rm = TRUE),
      mean_count = mean(v, na.rm = TRUE),
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, rows)
}

pass_h <- function(df) {
  df$pass_H5 <- df$detection_rate >= 0.10 & df$n_detected >= 25
  df$pass_H6 <- df$n_cells >= 300
  df$pass_knock <- df$pass_H5 & df$pass_H6
  df
}

message("packages")
suppressPackageStartupMessages({
  library(Matrix)
})

# --- GSE197289 meta first (always) ---
meta_path <- file.path(data_dir, "GSE197289_snRNA-seq_mouse_barcode_meta.csv.gz")
meta <- read.csv(gzfile(meta_path), check.names = FALSE)
message("197289 meta cols: ", paste(colnames(meta), collapse = " | "))
message("197289 meta rows: ", nrow(meta))
writeLines(capture.output(str(meta[, seq_len(min(12, ncol(meta)))])), file.path(out_dir, "GSE197289_meta_str.txt"))

rds_path <- file.path(data_dir, "GSE197289_snRNA-seq_mouse_raw_counts.RDS.gz")
if (file.exists(rds_path)) {
  message("reading 197289 RDS")
  con <- gzcon(file(rds_path, "rb"))
  on.exit(close(con), add = TRUE)
  counts <- readRDS(con)
  message("class ", paste(class(counts), collapse = ","), " dim ", paste(dim(counts), collapse = "x"))
  # gene x cell expected
  if (nrow(counts) < ncol(counts) && "Cplx2" %in% colnames(counts) && !("Cplx2" %in% rownames(counts))) {
    counts <- t(counts)
  }
  bc <- colnames(counts)
  # match meta
  idcol <- NULL
  for (cand in c("barcode", "Barcode", "cell", "Cell", colnames(meta)[1])) {
    if (cand %in% colnames(meta)) { idcol <- cand; break }
  }
  message("idcol ", idcol)
  meta_id <- as.character(meta[[idcol]])
  # try rownames
  if (is.null(rownames(meta)) || all(rownames(meta) == seq_len(nrow(meta)))) {
    rownames(meta) <- meta_id
  }
  common <- intersect(bc, rownames(meta))
  if (length(common) < 100) {
    common <- intersect(bc, meta_id)
    rownames(meta) <- meta_id
    common <- intersect(bc, rownames(meta))
  }
  message("matched cells ", length(common), " / ", length(bc))
  group_col <- NULL
  for (cand in c("celltype", "cell_type", "CellType", "cluster", "annotation", "ident")) {
    if (cand %in% colnames(meta)) { group_col <- cand; break }
  }
  if (is.null(group_col)) {
    # pick a character column with modest unique count
    nunq <- sapply(meta, function(z) length(unique(z)))
    chars <- nunq[nunq > 2 & nunq < 40]
    message("candidate group cols: ", paste(names(chars), chars, sep = "=", collapse = "; "))
    group_col <- names(chars)[1]
  }
  message("group_col ", group_col)
  sub <- meta[common, , drop = FALSE]
  tab <- pass_h(det_table(counts[, common, drop = FALSE], sub[[group_col]]))
  tab$dataset <- "GSE197289"
  tab$group_col <- group_col
  write.csv(tab, file.path(out_dir, "GSE197289_Cplx2_by_group.csv"), row.names = FALSE)
  message("wrote 197289 table")
} else {
  message("RDS missing")
}

message("PHASE1_PARTIAL_DONE")
