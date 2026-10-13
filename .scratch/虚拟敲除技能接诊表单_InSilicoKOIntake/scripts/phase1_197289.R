options(stringsAsFactors = FALSE)
data_dir <- "E:/RProject/.scratch/虚拟敲除技能接诊表单_InSilicoKOIntake/data"
out_dir <- "E:/RProject/.scratch/虚拟敲除技能接诊表单_InSilicoKOIntake/phase1"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

meta <- read.csv(gzfile(file.path(data_dir, "GSE197289_snRNA-seq_mouse_barcode_meta.csv.gz")), check.names = FALSE)
message("meta ", nrow(meta), " cols ", paste(colnames(meta), collapse = ","))

obj <- readRDS(gzcon(gzfile(file.path(data_dir, "GSE197289_snRNA-seq_mouse_raw_counts.RDS.gz"), "rb")))
message("class ", paste(class(obj), collapse = ","))
if (inherits(obj, "Seurat")) {
  counts <- obj@assays$RNA@counts
  if (is.null(counts)) counts <- SeuratObject::LayerData(obj, layer = "counts")
} else if (is.list(obj) && !is.null(obj$counts)) {
  counts <- obj$counts
} else {
  counts <- obj
}
message("dim ", paste(dim(counts), collapse = " x "))
message("rownames head ", paste(head(rownames(counts), 3), collapse = ","))
message("colnames head ", paste(head(colnames(counts), 2), collapse = ","))

gene <- "Cplx2"
if (!gene %in% rownames(counts)) stop("Cplx2 missing")
x <- as.numeric(counts[gene, ])
names(x) <- colnames(counts)

# meta V1 is barcode
ids <- as.character(meta$V1)
if (!"V1" %in% colnames(meta)) ids <- as.character(meta[[1]])
m <- match(names(x), ids)
message("matched ", sum(!is.na(m)), " / ", length(x))
meta2 <- meta[m, , drop = FALSE]
ok <- !is.na(m)

summarise <- function(group) {
  g <- as.character(group)
  g[!ok] <- NA
  ug <- sort(unique(g[!is.na(g)]))
  rows <- lapply(ug, function(one) {
    idx <- which(g == one)
    v <- x[idx]
    data.frame(
      group = one,
      n_cells = length(v),
      n_detected = sum(v > 0),
      detection_rate = mean(v > 0),
      mean_count = mean(v),
      stringsAsFactors = FALSE
    )
  })
  df <- do.call(rbind, rows)
  df$pass_H5 <- df$detection_rate >= 0.10 & df$n_detected >= 25
  df$pass_H6 <- df$n_cells >= 300
  df$pass_knock <- df$pass_H5 & df$pass_H6
  df
}

by_sub <- summarise(meta2$subtype)
by_sub$split <- "subtype"
by_model <- summarise(paste(meta2$model, meta2$subtype, sep = "|"))
by_model$split <- "model_subtype"
by_class <- summarise(meta2$class)
by_class$split <- "class"
out <- rbind(by_sub, by_model, by_class)
write.csv(out, file.path(out_dir, "GSE197289_Cplx2_detection.csv"), row.names = FALSE)
message("wrote ", nrow(out), " rows")
print(by_sub[order(-by_sub$n_cells), ])
message("PHASE1_197289_DONE")
