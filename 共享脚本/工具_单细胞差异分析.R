# 单细胞 RNA-seq 差异分析（pseudobulk / Seurat）

check_scrna_dependencies <- function() {
  needed <- c("Seurat", "DESeq2", "Matrix")
  missing <- needed[!vapply(needed, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
  if (length(missing)) stop("单细胞分析还需安装: ", paste(missing, collapse = ", "))
}

build_seurat_from_10x <- function(counts, project = "scRNA", min_cells = 3, min_features = 200) {
  check_scrna_dependencies()
  obj <- Seurat::CreateSeuratObject(counts = counts, project = project,
                                    min.cells = min_cells, min.features = min_features)
  obj[["percent.mt"]] <- Seurat::PercentageFeatureSet(obj, pattern = "^mt-|^MT-")
  obj
}

run_seurat_qc_cluster <- function(obj, resolution = 0.5) {
  check_scrna_dependencies()
  obj <- Seurat::NormalizeData(obj, verbose = FALSE)
  obj <- Seurat::FindVariableFeatures(obj, verbose = FALSE)
  obj <- Seurat::ScaleData(obj, verbose = FALSE)
  obj <- Seurat::RunPCA(obj, verbose = FALSE)
  obj <- Seurat::FindNeighbors(obj, dims = 1:20, verbose = FALSE)
  obj <- Seurat::FindClusters(obj, resolution = resolution, verbose = FALSE)
  obj <- Seurat::RunUMAP(obj, dims = 1:20, verbose = FALSE)
  obj
}

run_scrna_pseudobulk_deg <- function(count_matrix, sample_meta, celltype_col = "celltype",
                                     group_col = "group", contrast = c("Case", "Control"),
                                     sample_col = "sample") {
  check_scrna_dependencies()
  if (!requireNamespace("DESeq2", quietly = TRUE)) stop("需要 DESeq2")

  meta <- sample_meta
  meta <- meta[colnames(count_matrix), , drop = FALSE]
  if (nrow(meta) == 0) stop("meta 与 count 列名不匹配")
  meta$pb_id <- paste(meta[[sample_col]], meta[[celltype_col]], sep = "__")

  idx_list <- split(seq_len(ncol(count_matrix)), meta$pb_id)
  if (length(idx_list) == 0) stop("无法构建 pseudobulk 分组")
  pb_list <- lapply(idx_list, function(idx) {
    Matrix::rowSums(count_matrix[, idx, drop = FALSE])
  })
  pb_mat <- do.call(cbind, pb_list)
  if (is.null(dim(pb_mat))) {
    pb_mat <- matrix(pb_list[[1]], ncol = 1, dimnames = list(rownames(count_matrix), names(idx_list)))
  }
  colnames(pb_mat) <- names(idx_list)

  pb_meta <- meta[!duplicated(meta$pb_id), c("pb_id", sample_col, celltype_col, group_col)]
  rownames(pb_meta) <- pb_meta$pb_id
  pb_meta <- pb_meta[colnames(pb_mat), , drop = FALSE]

  keep <- pb_meta[[group_col]] %in% contrast
  pb_mat <- pb_mat[, keep, drop = FALSE]
  pb_meta <- pb_meta[keep, , drop = FALSE]
  pb_meta[[group_col]] <- factor(pb_meta[[group_col]], levels = contrast)

  dds <- DESeq2::DESeqDataSetFromMatrix(
    countData = round(as.matrix(pb_mat)),
    colData = pb_meta,
    design = stats::as.formula(paste("~", group_col))
  )
  dds <- DESeq2::DESeq(dds, quiet = TRUE)
  res <- DESeq2::results(dds, contrast = c(group_col, contrast[1], contrast[2]))
  res_df <- as.data.frame(res)
  res_df$gene <- rownames(res_df)
  res_df
}

aggregate_pseudobulk_matrix <- function(count_matrix, meta, sample_col = "sample") {
  ids <- split(seq_len(ncol(count_matrix)), meta[[sample_col]])
  mat <- sapply(ids, function(idx) Matrix::rowSums(count_matrix[, idx, drop = FALSE]))
  mat <- as.matrix(mat)
  rownames(mat) <- rownames(count_matrix)
  mat
}
