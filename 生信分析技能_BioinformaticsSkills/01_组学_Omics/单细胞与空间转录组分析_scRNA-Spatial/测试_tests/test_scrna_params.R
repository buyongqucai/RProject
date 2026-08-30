# 议题 08：scRNA 骨架四参数接缝测试（红 → 绿）
# 接缝：run_scrna_pipeline 签名默认值 + scrna_qc_filter / scrna_resolution_grid / scrna_find_markers
library(testthat)
library(Seurat)

this_file <- tryCatch(
  normalizePath(sys.frame(1)$ofile, winslash = "/"),
  error = function(e) normalizePath("test_scrna_params.R", winslash = "/", mustWork = TRUE)
)
skill_dir <- dirname(dirname(this_file))
source(file.path(skill_dir, "脚本_scripts", "运行单细胞空转骨架_runScrnaSkeleton.R"), encoding = "UTF-8")

#' 小合成 Seurat 对象：200 细胞 × 500 基因
#' - 细胞 1–50：低质量（仅 100 基因低表达）→ 应被 QC floor 滤除
#' - 细胞 51–125 / 126–200：两个表达谱截然不同的群体 → 应可聚类并产生 marker
make_toy_seurat <- function() {
  set.seed(42)
  counts <- matrix(rpois(500 * 200, lambda = 1), nrow = 500,
                   dimnames = list(paste0("Gene", 1:500), paste0("Cell", 1:200)))
  counts[, 1:50] <- 0
  counts[1:100, 1:50] <- matrix(rpois(100 * 50, lambda = 1), nrow = 100)
  counts[101:300, 51:125] <- matrix(rpois(200 * 75, lambda = 20), nrow = 200)
  counts[301:500, 126:200] <- matrix(rpois(200 * 75, lambda = 20), nrow = 200)
  CreateSeuratObject(counts = counts, min.cells = 0, min.features = 0)
}

test_that("run_scrna_pipeline 签名含技能说明 §4 四个参数及默认值", {
  fml <- formals(run_scrna_pipeline)
  expect_equal(eval(fml$qc_min_feature_floor), 200)
  expect_equal(eval(fml$pb_min_samples), 2)
  expect_equal(eval(fml$de_logfc), 1)
  expect_equal(eval(fml$de_fdr), 0.05)
  expect_equal(eval(fml$res_grid), seq(0.1, 1.2, by = 0.1))
})

test_that("scrna_qc_filter 按 QC_MIN_FEATURE_FLOOR 过滤低质量细胞", {
  obj <- make_toy_seurat()
  filtered <- scrna_qc_filter(obj, min_feature_floor = 200)
  expect_lt(ncol(filtered), ncol(obj))
  expect_true(all(filtered$nFeature_RNA >= 200))
  expect_equal(ncol(filtered), 150)
})

test_that("scrna_resolution_grid 按 RES_GRID 每个分辨率产出一列聚类", {
  obj <- make_toy_seurat()
  obj <- scrna_qc_filter(obj, min_feature_floor = 200)
  grid <- seq(0.1, 0.3, by = 0.1)  # 测试用小网格，E2E 用全网格
  obj <- scrna_resolution_grid(obj, res_grid = grid, verbose = FALSE)
  cols <- grep("^RNA_snn_res\\.", colnames(obj@meta.data), value = TRUE)
  expect_true(all(paste0("RNA_snn_res.", grid) %in% cols))
})

test_that("scrna_find_markers 按 DE_LOGFC / DE_FDR 过滤", {
  obj <- make_toy_seurat()
  obj <- scrna_qc_filter(obj, min_feature_floor = 200)
  obj <- scrna_resolution_grid(obj, res_grid = c(0.1), verbose = FALSE)
  mk <- scrna_find_markers(obj, logfc = 1, fdr = 0.05)
  expect_true(is.data.frame(mk))
  if (nrow(mk)) {
    expect_true(all(mk$avg_log2FC >= 1 | mk$avg_log2FC <= -1))
    expect_true(all(mk$p_val_adj <= 0.05))
  }
})
