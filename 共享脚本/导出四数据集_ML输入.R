# 导出四数据集表达矩阵与元数据，供 Python ML 使用
# 输出：E:/PythonProject/差异分析与单细胞测序/共享数据/四数据集/{GSE}/

suppressPackageStartupMessages(library(tidyverse))

PROJECT_ROOT <- if (file.exists("RProject.Rproj")) normalizePath(".") else {
  p <- normalizePath(getwd(), winslash = "/")
  for (i in 1:6) {
    if (file.exists(file.path(p, "RProject.Rproj"))) break
    p <- dirname(p)
  }
  p
}
PY_ROOT <- "E:/PythonProject/差异分析与单细胞测序"
OUT_ROOT <- file.path(PY_ROOT, "共享数据", "四数据集")
MAMS_MOUSE <- file.path(PROJECT_ROOT, "sciadv_adz3266", "源数据", "MAMs_基因集_鼠.csv")

DATASETS <- tribble(
  ~id,          ~type,   ~case,     ~control,
  "GSE190856",  "scrna", "CLP",     "Steady",
  "GSE207363",  "scrna", "Sepsis",  "Sham",
  "GSE207177",  "scrna", "CLP",     "Control",
  "GSE267388",  "bulk",  "LPS",     "PBS"
)

source(file.path(PROJECT_ROOT, "共享脚本", "工具_富集与质控图.R"), encoding = "UTF-8")

export_one <- function(id, type, case, control) {
  ds <- id
  mid <- file.path(PROJECT_ROOT, ds, "源数据", "中间文件")
  out <- file.path(OUT_ROOT, ds)
  dir.create(out, recursive = TRUE, showWarnings = FALSE)

  if (type == "bulk") {
    mat <- readRDS(file.path(mid, paste0(ds, "_expr_matrix.rds")))
    si <- as.data.frame(readRDS(file.path(mid, paste0(ds, "_sample_info.rds"))))
  } else {
    suppressPackageStartupMessages(library(Seurat))
    obj <- readRDS(file.path(mid, paste0(ds, "_seurat.rds")))
    pb <- build_pseudobulk_matrix(obj)
    mat <- pb$expr
    si <- as.data.frame(pb$sample_info)
  }
  rownames(si) <- si$sample
  si <- si[colnames(mat), , drop = FALSE]
  # ML 仅用文档对比组（避免 Control/LLTS 等额外分组导致标签全为 0）
  si <- si[as.character(si$group) %in% c(control, case), , drop = FALSE]
  mat <- mat[, rownames(si), drop = FALSE]
  si$label <- ifelse(as.character(si$group) == case, 1L, 0L)
  if (ncol(mat) < 2 || length(unique(si$label)) < 2) {
    message(ds, ": 对比组样本不足或仅单类，跳过 ML 导出"); return(invisible(NULL))
  }
  if (max(mat, na.rm = TRUE) > 50) mat <- log2(mat + 1)

  deg_sig <- read.csv(file.path(PROJECT_ROOT, ds, "结果", "表格", paste0(ds, "_显著差异基因.csv")),
                      stringsAsFactors = FALSE)
  mams <- read.csv(MAMS_MOUSE, stringsAsFactors = FALSE)
  inter <- intersect(deg_sig$gene, mams$gene)
  if (length(inter) < 5) inter <- intersect(rownames(mat), mams$gene)
  if (length(inter) < 5) inter <- deg_sig$gene[1:min(50, nrow(deg_sig))]

  si$group <- factor(si$group, levels = c(control, case))

  write.csv(mat, file.path(out, "expr_matrix.csv"))
  write.csv(si, file.path(out, "sample_meta.csv"), row.names = FALSE)
  write.csv(data.frame(gene = inter), file.path(out, "feature_genes.csv"), row.names = FALSE)
  write.csv(deg_sig, file.path(out, "deg_significant.csv"), row.names = FALSE)
  write.csv(mams, file.path(out, "mams_geneset_mouse.csv"), row.names = FALSE)

  meta <- list(
    dataset = ds, type = type, contrast = paste(case, "vs", control),
    n_samples = ncol(mat), n_genes = nrow(mat), n_features = length(inter),
    r_deg = file.path(PROJECT_ROOT, ds, "结果", "表格", paste0(ds, "_显著差异基因.csv")),
    r_expr = file.path(mid, if (type == "bulk") paste0(ds, "_expr_matrix.rds") else paste0(ds, "_seurat.rds")),
    export_time = as.character(Sys.time())
  )
  writeLines(jsonlite::toJSON(meta, auto_unbox = TRUE, pretty = TRUE),
             file.path(out, "数据清单.json"))
  message(ds, ": ", ncol(mat), " 样本, ", length(inter), " 特征基因 -> ", out)
}

if (!requireNamespace("jsonlite", quietly = TRUE)) install.packages("jsonlite", repos = "https://cloud.r-project.org", quiet = TRUE)
for (i in seq_len(nrow(DATASETS))) {
  with(DATASETS[i, ], export_one(id, type, case, control))
}
message("完成: 导出四数据集_ML输入.R")
