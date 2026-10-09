# 从作者 myeloid.Rdata（Seurat）导出 Knk 用 counts + meta。
# 输出到桌面婷婷/虚拟敲除/数据文件/
options(stringsAsFactors = FALSE)
suppressPackageStartupMessages({
  library(Seurat)
  library(Matrix)
})

rdata <- "C:/Users/10540/Desktop/婷婷/虚拟敲除/数据文件/_作者注释Rdata/myeloid.Rdata"
out_dir <- "C:/Users/10540/Desktop/婷婷/虚拟敲除/数据文件"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

message("loading ", rdata)
env <- new.env()
loaded <- load(rdata, envir = env)
message("objects: ", paste(loaded, collapse = ", "))
obj <- NULL
for (nm in loaded) {
  cand <- env[[nm]]
  if (inherits(cand, "Seurat")) {
    obj <- cand
    message("using Seurat object: ", nm)
    break
  }
}
if (is.null(obj)) stop("no Seurat object in myeloid.Rdata")

# 旧版 Seurat 对象在新 SeuratObject 上可能缺 images 槽；优先升级，失败则裸槽读取
obj <- tryCatch(UpdateSeuratObject(obj), error = function(e) {
  message("UpdateSeuratObject failed: ", conditionMessage(e), "; use raw slots")
  obj
})

meta <- obj@meta.data
# 常见列名兜底
if (!"celltype" %in% colnames(meta)) {
  if ("cell_type" %in% colnames(meta)) meta$celltype <- meta$cell_type
  else if ("CellType" %in% colnames(meta)) meta$celltype <- meta$CellType
  else if ("ident" %in% colnames(meta)) meta$celltype <- as.character(meta$ident)
  else stop("cannot find celltype; colnames=", paste(colnames(meta), collapse = ","))
}
if (!"stim" %in% colnames(meta)) {
  for (cand in c("stim", "Stim", "condition", "lesional", "group", "orig.ident")) {
    if (cand %in% colnames(meta)) {
      meta$stim <- meta[[cand]]
      break
    }
  }
}
if (!"stim" %in% colnames(meta)) stop("cannot find stim/lesional column; colnames=", paste(colnames(meta), collapse = ","))

# 统一皮损取值：含 lesion（忽略大小写）的写成 Lesional，否则 Nonlesional（若已是两类则保留）
stim_chr <- as.character(meta$stim)
stim_l <- tolower(stim_chr)
meta$stim_raw <- stim_chr
if (any(grepl("lesion", stim_l))) {
  meta$stim <- ifelse(grepl("non", stim_l), "Nonlesional",
                      ifelse(grepl("lesion", stim_l), "Lesional", stim_chr))
}

counts <- NULL
counts <- tryCatch(
  GetAssayData(obj, assay = DefaultAssay(obj), layer = "counts"),
  error = function(e) NULL
)
if (is.null(counts)) {
  counts <- tryCatch(
    GetAssayData(obj, assay = DefaultAssay(obj), slot = "counts"),
    error = function(e) NULL
  )
}
if (is.null(counts)) {
  assay_name <- if (length(obj@assays)) names(obj@assays)[[1]] else "RNA"
  assay <- obj@assays[[assay_name]]
  if (!is.null(assay@counts) && length(assay@counts)) {
    counts <- assay@counts
  } else if (!is.null(assay@data) && length(assay@data)) {
    message("counts slot empty; using data slot (may already be normalized)")
    counts <- assay@data
  } else {
    stop("cannot extract expression matrix from myeloid object")
  }
}
if (!inherits(counts, "dgCMatrix")) counts <- as(as(counts, "CsparseMatrix"), "dgCMatrix")
cell_ids <- colnames(counts)
if (is.null(cell_ids) || any(!nzchar(cell_ids))) cell_ids <- rownames(meta)
if (nrow(meta) != length(cell_ids)) {
  # 尝试按行名对齐
  if (!is.null(rownames(meta)) && all(cell_ids %in% rownames(meta))) {
    meta <- meta[cell_ids, , drop = FALSE]
  } else {
    stop("meta rows (", nrow(meta), ") != cells (", length(cell_ids), ")")
  }
}
meta$cell_id <- cell_ids
colnames(counts) <- meta$cell_id

meta_out <- meta[, intersect(c("cell_id", "stim", "stim_raw", "celltype", "donor"), colnames(meta)), drop = FALSE]
# 保证 stim/celltype 在
meta_out$stim <- meta$stim
meta_out$celltype <- meta$celltype

meta_path <- file.path(out_dir, "01_细胞注释_CellMeta_GSE175817.csv.gz")
counts_path <- file.path(out_dir, "02_表达矩阵_Counts_GSE175817.RDS.gz")
gz <- gzfile(meta_path, "w")
write.csv(meta_out, gz, row.names = FALSE)
close(gz)
con <- gzfile(counts_path, "wb")
saveRDS(counts, con)
close(con)

# 摘要：亚群 × stim、AHR 检出
ahr <- if ("AHR" %in% rownames(counts)) as.numeric(counts["AHR", ]) else rep(0, ncol(counts))
det <- tapply(ahr > 0, list(meta_out$stim, meta_out$celltype), sum)
ncell <- table(stim = meta_out$stim, celltype = meta_out$celltype)
summary_path <- file.path(out_dir, "00_导出摘要_ExportSummary.txt")
lines <- c(
  paste0("n_cells=", ncol(counts)),
  paste0("n_genes=", nrow(counts)),
  paste0("assay=", DefaultAssay(obj)),
  paste0("stim_levels=", paste(unique(meta_out$stim), collapse = "|")),
  paste0("celltypes=", paste(sort(unique(meta_out$celltype)), collapse = "|")),
  "n_cells_by_stim_celltype:",
  capture.output(print(ncell)),
  "AHR_detected_cells_by_stim_celltype:",
  capture.output(print(det)),
  paste0("meta=", meta_path),
  paste0("counts=", counts_path)
)
writeLines(lines, summary_path, useBytes = TRUE)
message(paste(lines, collapse = "\n"))
message("EXPORT_DONE")
