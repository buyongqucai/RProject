# 小鼠心肌 scRNA 细胞类型注释（canonical markers）
#
# 关键设计约束（历史错误已修复，勿回退）：
# 1. annotate_by_markers 只使用「本次」打分列，禁止 grep("^score_") 读取全部分数
# 2. 免疫子集必须硬过滤淋巴系+髓系，禁止仅靠 immune_score>0 软筛选
# 3. IMMUNE_LINEAGE 不含内皮/成纤维/心肌等基质细胞

CARDIAC_MARKERS <- list(
  Cardiomyocytes = c("Myh6", "Tnnt2", "Rbm20"),
  Endothelial = c("Pecam1", "Cdh5", "Kdr"),
  Fibroblasts = c("Col1a1", "Dcn", "Pdgfra"),
  Fibroblasts_activated = c("Postn", "Acta2", "Cthrc1"),
  Macrophages = c("Adgre1", "Cd68", "Csf1r"),
  Monocytes = c("Ly6c2", "Ccr2"),
  Granulocytes = c("S100a8", "Ly6g"),
  T_cells = c("Cd3d", "Trbc2"),
  NK_cells = c("Nkg7", "Klrb1c"),
  B_cells = c("Cd79a", "Ms4a1"),
  Smooth_muscle = c("Myh11", "Tagln"),
  Pericytes = c("Rgs5", "Pdgfrb")
)

# 仅淋巴系 + 髓系（+ 增殖）；不含内皮/成纤维等基质细胞
# Dendritic 用较特异 marker（避免 Itgax 与巨噬交叉导致 DC 过度标注）
IMMUNE_LINEAGE <- list(
  Macrophages = c("Adgre1", "Cd68", "Csf1r"),
  Granulocytes = c("S100a8", "Ly6g"),
  Monocytes = c("Ly6c2", "Ccr2"),
  Dendritic = c("Flt3", "Clec9a", "Xcr1"),
  T_cells = c("Cd3d", "Trbc2"),
  NK_cells = c("Nkg7", "Klrb1c"),
  B_cells = c("Cd79a", "Ms4a1"),
  Cycling = c("Mki67", "Top2a")
)

IMMUNE_CELLTYPES_KEEP <- c(
  "Macrophages", "Monocytes", "Granulocytes", "Neutrophils",
  "Dendritic", "T_cells", "NK_cells", "B_cells", "Cycling", "T_NK"
)

NON_IMMUNE_CELLTYPES <- c(
  "Endothelial", "Fibroblasts", "Fibroblasts_activated",
  "Cardiomyocytes", "Pericytes", "Smooth_muscle"
)

filter_genes_present <- function(genes, obj) {
  genes[genes %in% rownames(obj)]
}

is_immune_celltype_label <- function(ct) {
  ct <- as.character(ct)
  ct %in% IMMUNE_CELLTYPES_KEEP |
    grepl("^(Macrophage|Monocyte|Granulocyte|Neutrophil|Dendritic|T_cell|NK_cell|B_cell|Cycling|T_NK)",
          ct, ignore.case = TRUE)
}

# 使用调用方指定的唯一前缀；禁止与历史 score_* 混用
score_celltypes <- function(obj, marker_list, prefix) {
  stopifnot(is.character(prefix), nchar(prefix) > 0)
  for (ct in names(marker_list)) {
    genes <- filter_genes_present(marker_list[[ct]], obj)
    if (length(genes) < 1) next
    # AddModuleScore 会在 name 后追加数字；用临时名再重命名为 prefix+ct
    tmp <- paste0(prefix, ct, "_")
    obj <- Seurat::AddModuleScore(obj, features = list(genes), name = tmp, assay = "RNA")
    cn <- paste0(tmp, "1")
    if (cn %in% colnames(obj@meta.data)) {
      colnames(obj@meta.data)[colnames(obj@meta.data) == cn] <- paste0(prefix, ct)
    }
  }
  obj
}

annotate_by_markers <- function(obj, marker_list = CARDIAC_MARKERS, label_col = "celltype",
                                score_prefix = NULL) {
  # 每次注释使用独立前缀，只根据本次 marker_list 打分，避免泄漏旧 CARDIAC score_*
  if (is.null(score_prefix)) {
    score_prefix <- paste0("ann_", gsub("[^A-Za-z0-9]", "", label_col), "_")
  }
  expected <- paste0(score_prefix, names(marker_list))
  # 清除同前缀旧列
  drop_cols <- intersect(expected, colnames(obj@meta.data))
  if (length(drop_cols)) {
    obj@meta.data <- obj@meta.data[, setdiff(colnames(obj@meta.data), drop_cols), drop = FALSE]
  }
  obj <- score_celltypes(obj, marker_list, prefix = score_prefix)
  score_cols <- intersect(paste0(score_prefix, names(marker_list)), colnames(obj@meta.data))
  if (length(score_cols) == 0) {
    obj[[label_col]] <- "Unknown"
    return(obj)
  }
  mat <- as.matrix(obj@meta.data[, score_cols, drop = FALSE])
  best <- apply(mat, 1, function(x) {
    if (all(is.na(x))) return("Unknown")
    score_cols[which.max(x)]
  })
  labels <- sub(paste0("^", score_prefix), "", best)
  obj[[label_col]] <- factor(labels)
  obj
}

annotate_clusters_by_markers <- function(obj, marker_list = CARDIAC_MARKERS, label_col = "celltype") {
  obj <- annotate_by_markers(obj, marker_list, label_col)
  if (!"seurat_clusters" %in% colnames(obj@meta.data)) return(obj)
  cluster_map <- obj@meta.data %>%
    tibble::as_tibble(rownames = "cell") %>%
    dplyr::group_by(seurat_clusters) %>%
    dplyr::summarise(celltype = names(sort(table(.data[[label_col]]), decreasing = TRUE))[1],
                     .groups = "drop")
  map_vec <- setNames(cluster_map$celltype, cluster_map$seurat_clusters)
  obj[[label_col]] <- factor(unname(map_vec[as.character(obj$seurat_clusters)]))
  obj
}

# 免疫谱系注释：marker 打分 + 全组织 celltype 优先（避免 Mac 被误标 DC）
annotate_immune_lineage <- function(obj) {
  obj <- annotate_clusters_by_markers(obj, IMMUNE_LINEAGE, "immune_lineage_marker")
  marker <- as.character(obj$immune_lineage_marker)
  out <- marker

  if ("celltype" %in% colnames(obj@meta.data)) {
    parent <- as.character(obj$celltype)
    parent[parent == "Neutrophils"] <- "Granulocytes"
    # 全组织已明确为巨噬/单核/粒/B/T 的细胞，优先保留，避免 DC/Cycling 抢标
    lock <- parent %in% c("Macrophages", "Monocytes", "Granulocytes", "B_cells", "T_cells")
    out[lock] <- parent[lock]
    # 全组织 NK → NK；否则 marker 为 NK 也可
    out[parent == "NK_cells"] <- "NK_cells"
    # 明确禁止：全组织 Macrophages 不得被标成 Dendritic
    out[parent == "Macrophages" & marker == "Dendritic"] <- "Macrophages"
  }

  # 仅允许 IMMUNE_LINEAGE 合法名
  out[!out %in% names(IMMUNE_LINEAGE)] <- marker[!out %in% names(IMMUNE_LINEAGE)]
  out[!out %in% names(IMMUNE_LINEAGE)] <- "Cycling"
  obj$immune_lineage <- factor(out, levels = names(IMMUNE_LINEAGE))
  obj
}

# 选取免疫细胞：优先全组织 celltype 硬过滤；无 celltype 时才回退到 marker score / Ptprc
select_immune_cells <- function(obj, assay = "RNA") {
  meta <- obj@meta.data
  cells_all <- rownames(meta)

  if ("celltype" %in% colnames(meta)) {
    ct <- as.character(meta$celltype)
    keep <- is_immune_celltype_label(ct) & !(ct %in% NON_IMMUNE_CELLTYPES)
    cells <- cells_all[keep]
    message("免疫子集：按 celltype 硬过滤 n=", length(cells),
            " / 全细胞 ", length(cells_all))
    return(cells)
  }

  # 无 celltype 时的兜底（少见）
  immune_genes <- unique(c(unlist(IMMUNE_LINEAGE), "Ptprc"))
  present <- filter_genes_present(immune_genes, obj)
  if (length(present) == 0) return(character(0))
  obj2 <- Seurat::AddModuleScore(obj, features = list(present), name = "immune_score_", assay = assay)
  immune_col <- grep("^immune_score_", colnames(obj2@meta.data), value = TRUE)[1]
  cells <- rownames(obj2@meta.data)[obj2@meta.data[[immune_col]] > 0]
  if (length(cells) < 50 && "Ptprc" %in% rownames(obj)) {
    expr <- Seurat::FetchData(obj, vars = "Ptprc")
    cells <- rownames(expr)[expr[[1]] > 0]
  }
  message("免疫子集：无 celltype，回退 score/Ptprc n=", length(cells))
  cells
}

subset_immune_recluster <- function(obj, assay = "RNA") {
  cells <- select_immune_cells(obj, assay = assay)
  if (length(cells) < 50) return(NULL)

  sub <- subset(obj, cells = cells)
  # 合并 v5 多层，避免 ScaleData/PCA 在多 layer 子集上崩溃
  if ("JoinLayers" %in% ls("package:Seurat")) {
    sub <- try(Seurat::JoinLayers(sub, assay = assay), silent = TRUE)
  }
  if (inherits(sub, "try-error")) return(NULL)

  # 清除历史 CARDIAC score_*，避免下游再被误用
  stale <- grep("^score_|^ann_", colnames(sub@meta.data), value = TRUE)
  if (length(stale)) {
    sub@meta.data <- sub@meta.data[, setdiff(colnames(sub@meta.data), stale), drop = FALSE]
  }

  gc()
  sub <- Seurat::NormalizeData(sub, verbose = FALSE)
  sub <- Seurat::FindVariableFeatures(sub, verbose = FALSE)
  sub <- Seurat::ScaleData(sub, verbose = FALSE)
  sub <- Seurat::RunPCA(sub, verbose = FALSE)
  sub <- Seurat::FindNeighbors(sub, dims = 1:15, verbose = FALSE)
  sub <- Seurat::FindClusters(sub, resolution = 0.4, verbose = FALSE)
  sub <- Seurat::RunUMAP(sub, dims = 1:15, verbose = FALSE)
  sub <- annotate_immune_lineage(sub)

  # 最终保险：剔除任何误标为非免疫的簇
  il <- as.character(sub$immune_lineage)
  bad <- il %in% NON_IMMUNE_CELLTYPES
  if (any(bad)) {
    message("剔除误标非免疫细胞: ", sum(bad))
    sub <- subset(sub, cells = colnames(sub)[!bad])
  }
  # 断言：图例只能是 IMMUNE_LINEAGE 名称
  unexpected <- setdiff(unique(as.character(sub$immune_lineage)), names(IMMUNE_LINEAGE))
  if (length(unexpected)) {
    warning("immune_lineage 出现非预期标签: ", paste(unexpected, collapse = ", "))
  }
  sub
}

filter_seurat_by_groups <- function(obj, keep_groups) {
  if (is.null(keep_groups) || length(keep_groups) == 0) return(obj)
  cells <- rownames(obj@meta.data)[obj$group %in% keep_groups]
  subset(obj, cells = cells)
}
