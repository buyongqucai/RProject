# 单细胞/空转骨架：GEO 自动流水线阶段 + 出版级出图 + 书清工具
# 流程参考：https://mp.weixin.qq.com/s/Z8x1a1Q8A5uQq3qAzBpDpg
# status = "skeleton"（GEO 下载/DoubletFinder/注释等阶段仍为 TODO；
# 四参数主链已实现：scrna_qc_filter / scrna_resolution_grid / scrna_find_markers，议题 08）

find_project_root <- function(start = getwd()) {
  p <- normalizePath(start, winslash = "/", mustWork = FALSE)
  for (i in 1:8) {
    if (file.exists(file.path(p, "RProject.Rproj"))) return(p)
    parent <- dirname(p)
    if (identical(parent, p)) break
    p <- parent
  }
  stop("未找到 RProject.Rproj")
}

check_r_packages <- function(pkgs) {
  missing <- pkgs[!vapply(pkgs, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
  if (length(missing)) {
    stop("缺少 R 包（请先安装）: ", paste(missing, collapse = ", "), call. = FALSE)
  }
  invisible(TRUE)
}

source_pub_viz <- function(project_root = find_project_root()) {
  f <- file.path(
    project_root, "生信分析技能_BioinformaticsSkills", "00_基础_Foundation",
    "统一可视化规范_VizStandards", "脚本_scripts", "出版级出图_PublicationPlot.R"
  )
  stopifnot("缺少出版级出图_PublicationPlot.R" = file.exists(f))
  source(f, encoding = "UTF-8")
}

#' 推荐依赖（与技能说明 §5 对齐；按阶段按需检查）
scrna_recommended_packages <- function() {
  list(
    essential = c("Seurat", "SeuratObject", "Matrix", "ggplot2", "dplyr", "patchwork"),
    geo_auto = c("GEOquery", "data.table", "stringr", "hdf5r"),
    qc_doublet = c("DoubletFinder"),
    integrate = c("harmony", "clustree"),
    annotate = c("SingleR", "celldex"),
    deg = c("edgeR"),
    enrich = c("clusterProfiler", "enrichplot", "org.Hs.eg.db", "org.Mm.eg.db", "ggrepel")
  )
}

#' 创建 GEO 自动模式目录树
ensure_geo_project_dirs <- function(geo_id, base_dir = getwd()) {
  geo_id <- toupper(trimws(geo_id))
  stopifnot(grepl("^GSE[0-9]+$", geo_id))
  root <- file.path(base_dir, paste0(geo_id, "_auto_scRNA"))
  dirs <- c(
    "00_download", "01_extracted", "02_figures",
    "03_tables", "04_objects", "05_reports"
  )
  for (d in dirs) dir.create(file.path(root, d), recursive = TRUE, showWarnings = FALSE)
  invisible(list(
    PROJECT_DIR = root,
    DL_DIR = file.path(root, "00_download"),
    EX_DIR = file.path(root, "01_extracted"),
    FIG_DIR = file.path(root, "02_figures"),
    TAB_DIR = file.path(root, "03_tables"),
    OBJ_DIR = file.path(root, "04_objects"),
    REP_DIR = file.path(root, "05_reports")
  ))
}

record_decision_stub <- function(rep_dir, stage, decision, reason = "", confidence = "NA") {
  dir.create(rep_dir, recursive = TRUE, showWarnings = FALSE)
  f <- file.path(rep_dir, "automatic_decisions.csv")
  row <- data.frame(
    stage = stage, decision = decision, reason = reason,
    confidence = confidence, stringsAsFactors = FALSE
  )
  if (file.exists(f)) {
    old <- utils::read.csv(f, stringsAsFactors = FALSE)
    utils::write.csv(rbind(old, row), f, row.names = FALSE)
  } else {
    utils::write.csv(row, f, row.names = FALSE)
  }
  invisible(row)
}

#' 原始计数快速校验（原则：拒绝 TPM/CPM/log / 过少细胞）
validate_raw_counts_stub <- function(mat, min_cells = 80L, min_genes = 200L, min_int_frac = 0.90) {
  if (is.null(mat)) return(list(ok = FALSE, reason = "矩阵为空"))
  ng <- nrow(mat); nc <- ncol(mat)
  if (nc < min_cells) return(list(ok = FALSE, reason = sprintf("细胞数 %d < %d（疑似 bulk）", nc, min_cells)))
  if (ng < min_genes) return(list(ok = FALSE, reason = sprintf("基因数 %d < %d", ng, min_genes)))
  vals <- if (inherits(mat, "sparseMatrix")) mat@x else as.numeric(mat)
  vals <- vals[is.finite(vals) & vals != 0]
  if (!length(vals)) return(list(ok = FALSE, reason = "无非零值"))
  if (any(vals < 0)) return(list(ok = FALSE, reason = "含负值（疑似标准化）"))
  if (length(vals) > 2e5) vals <- sample(vals, 2e5)
  fi <- mean(abs(vals - round(vals)) < 1e-8)
  if (fi < min_int_frac) {
    return(list(ok = FALSE, reason = sprintf("整数比 %.2f < %.2f（疑似 TPM/CPM/log）", fi, min_int_frac)))
  }
  list(ok = TRUE, reason = sprintf("通过：基因=%d 细胞=%d 整数比=%.3f", ng, nc, fi))
}

#' 差异方法选择：每组样本数 ≥ pb_min → pseudobulk；否则 exploratory
choose_de_method <- function(n_case, n_control, pb_min = 2L) {
  if (n_case >= pb_min && n_control >= pb_min) {
    list(method = "edgeR_pseudobulk", exploratory = FALSE)
  } else {
    list(method = "cell_level_exploratory", exploratory = TRUE)
  }
}

#' QC 过滤（QC_MIN_FEATURE_FLOOR）：保留 nFeature_RNA >= min_feature_floor 的细胞
scrna_qc_filter <- function(obj, min_feature_floor = 200) {
  if (!inherits(obj, "Seurat")) stop("scrna_qc_filter 需要 Seurat 对象", call. = FALSE)
  subset(obj, subset = nFeature_RNA >= min_feature_floor)
}

#' 分辨率网格聚类（RES_GRID）：Normalize → HVG → PCA → neighbors → 每个分辨率一列 RNA_snn_res.*
scrna_resolution_grid <- function(obj,
                                  res_grid = seq(0.1, 1.2, by = 0.1),
                                  npcs = 30,
                                  verbose = FALSE) {
  if (!inherits(obj, "Seurat")) stop("scrna_resolution_grid 需要 Seurat 对象", call. = FALSE)
  npcs <- min(npcs, ncol(obj) - 1L)
  obj <- NormalizeData(obj, verbose = verbose)
  obj <- FindVariableFeatures(obj, verbose = verbose)
  obj <- ScaleData(obj, verbose = verbose)
  obj <- RunPCA(obj, npcs = npcs, verbose = verbose)
  obj <- FindNeighbors(obj, dims = seq_len(npcs), verbose = verbose)
  obj <- FindClusters(obj, resolution = res_grid, verbose = verbose)
  obj
}

#' 标记基因（DE_LOGFC / DE_FDR）：FindAllMarkers 后按阈值精确过滤
scrna_find_markers <- function(obj, logfc = 1, fdr = 0.05, ...) {
  if (!inherits(obj, "Seurat")) stop("scrna_find_markers 需要 Seurat 对象", call. = FALSE)
  mk <- FindAllMarkers(obj, logfc.threshold = logfc, ...)
  if (!nrow(mk) || !all(c("p_val_adj", "avg_log2FC") %in% names(mk))) return(mk)
  mk[mk$p_val_adj <= fdr & abs(mk$avg_log2FC) >= logfc, , drop = FALSE]
}

#' Harmony 是否安全：单组或每组均有 ≥2 样本
harmony_design_safe <- function(group_table) {
  # group_table: named integer counts per group
  if (is.null(group_table) || !length(group_table)) return(FALSE)
  k <- length(group_table)
  k == 1L || (k >= 2L && all(group_table >= 2L))
}

source_shuqing_scrna <- function(project_root = find_project_root()) {
  scripts <- file.path(project_root, "书清项目", "共享脚本")
  tools <- c(
    "工具_单细胞对象.R", "工具_scRNA细胞注释.R",
    "工具_scRNA可视化.R", "工具_统一出图.R", "工具_富集与质控图.R"
  )
  loaded <- character()
  for (t in tools) {
    f <- file.path(scripts, t)
    if (file.exists(f)) {
      source(f, encoding = "UTF-8")
      loaded <- c(loaded, t)
    }
  }
  list(tools_dir = scripts, loaded = loaded)
}

#' 主入口：本地 Seurat 或 GEO 自动模式骨架
#'
#' @param geo_id 若提供 GSE 号则走 GEO 自动目录与阶段清单（下载/分析 TODO）
#' @param seurat_rds 已有对象路径（跳过下载）
#' @param out_dir DeliveryStandards 结果根目录（样例模式）
#' @param qc_min_feature_floor QC_MIN_FEATURE_FLOOR：基因数硬下限（默认 200）
#' @param pb_min_samples PB_MIN_SAMPLES：启用伪 bulk 的每组最小样本数（默认 2）
#' @param de_logfc DE_LOGFC：差异倍数阈值（默认 1）
#' @param de_fdr DE_FDR：FDR 阈值（默认 0.05）
#' @param res_grid RES_GRID：分辨率扫描网格（默认 0.1–1.2 step 0.1）
run_scrna_pipeline <- function(seurat_rds = NULL,
                               geo_id = NULL,
                               dataset = NULL,
                               out_dir = NULL,
                               qc_min_feature_floor = 200,
                               pb_min_samples = 2,
                               de_logfc = 1,
                               de_fdr = 0.05,
                               res_grid = seq(0.1, 1.2, by = 0.1),
                               project_root = find_project_root()) {
  pkgs <- scrna_recommended_packages()$essential
  check_r_packages(pkgs)
  source_pub_viz(project_root)
  sq <- source_shuqing_scrna(project_root)
  if (length(sq$loaded)) {
    message("【书清】已 source: ", paste(sq$loaded, collapse = ", "))
  } else {
    message("【提示】未找到书清 scRNA 工具，期望目录: ", sq$tools_dir)
  }

  stages <- c(
    "01_download_or_load",
    "02_validate_raw_counts",
    "03_infer_species_groups",
    "04_per_sample_QC_MAD",
    "05_per_sample_DoubletFinder",
    "06_merge_normalize_PCA",
    "07_Harmony_if_safe",
    "08_resolution_grid_clustree",
    "09_UMAP_markers_SingleR",
    "10_proportions",
    "11_DEG_pseudobulk_or_exploratory",
    "12_GO_KEGG",
    "13_save_Seurat_and_decisions"
  )

  geo_dirs <- NULL
  if (!is.null(geo_id) && nzchar(geo_id)) {
    geo_dirs <- ensure_geo_project_dirs(geo_id, base_dir = if (is.null(out_dir)) getwd() else dirname(out_dir))
    record_decision_stub(
      geo_dirs$REP_DIR, "pipeline", "skeleton_started",
      paste0("GEO_ID=", toupper(geo_id), "; 参考微信 GEO 自动流水线"), "high"
    )
    message("【GEO 模式】项目目录: ", geo_dirs$PROJECT_DIR)
    message("【TODO】GEOquery 下载补充文件 → 格式判别 → 填入各阶段实现")
  }

  if (!is.null(out_dir)) {
    dir.create(file.path(out_dir, "图片文件"), recursive = TRUE, showWarnings = FALSE)
    dir.create(file.path(out_dir, "数据文件"), recursive = TRUE, showWarnings = FALSE)
    dir.create(file.path(out_dir, "报告文件"), recursive = TRUE, showWarnings = FALSE)
  }

  message("【骨架】dataset=", dataset, " geo_id=", geo_id, " seurat=", seurat_rds, " out=", out_dir)
  message("【骨架】阶段: ", paste(stages, collapse = " → "))
  message(sprintf(
    "【参数】QC_MIN_FEATURE_FLOOR=%d PB_MIN_SAMPLES=%d DE_LOGFC=%s DE_FDR=%s RES_GRID=%s",
    as.integer(qc_min_feature_floor), as.integer(pb_min_samples),
    de_logfc, de_fdr, paste(range(res_grid), collapse = "-")
  ))
  message("【原则】按样本 DoubletFinder；有重复→edgeR pseudobulk；无重复→探索性 Wilcoxon 并写 DEG_method_note")
  message("【出图】DPI>=600 SVG+PNG；对齐 VizStandards Fig3；禁纯数字簇号当最终类型")

  invisible(list(
    status = "skeleton",
    stages = stages,
    params = list(
      qc_min_feature_floor = qc_min_feature_floor,
      pb_min_samples = pb_min_samples,
      de_logfc = de_logfc,
      de_fdr = de_fdr,
      res_grid = res_grid
    ),
    pkgs_ok = pkgs,
    tools_dir = sq$tools_dir,
    loaded = sq$loaded,
    geo_dirs = geo_dirs,
    helpers = list(
      validate_raw_counts_stub = validate_raw_counts_stub,
      choose_de_method = choose_de_method,
      harmony_design_safe = harmony_design_safe,
      scrna_qc_filter = scrna_qc_filter,
      scrna_resolution_grid = scrna_resolution_grid,
      scrna_find_markers = scrna_find_markers
    )
  ))
}

if (sys.nframe() == 0L && !interactive()) message("加载 run_scrna_pipeline() / GEO 骨架")
