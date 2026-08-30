# 数据真实性核对：扫描各数据集，核对"数据从哪来、是否被编造/污染、矩阵与元数据是否一致"
# 目标：避免 AI 幻觉/瞎编。发现问题会以 [FAIL]/[WARN] 标注并写入报告 CSV。
# 用法：Rscript 数据真实性核对.R   （在项目根目录或本目录均可）

suppressPackageStartupMessages({ library(tidyverse) })

PROJECT_ROOT <- if (file.exists("RProject.Rproj")) normalizePath(".") else {
  p <- normalizePath(getwd(), winslash = "/")
  while (!file.exists(file.path(p, "RProject.Rproj")) && dirname(p) != p) p <- dirname(p)
  p
}
setwd(PROJECT_ROOT)

# ---- GEO 官方样本数登记表（须人工/AI 从 GEO 页面核对后填写，作为"真值"）----
# 未登记者标 NA，脚本只做本地一致性检查，不做 GEO 比对。
GEO_TRUTH <- tibble::tribble(
  ~dataset,     ~geo_samples, ~note,
  "GSE79962",   31L,  "20 SCM + 11 Control（人心肌芯片）",
  "GSE267388",  10L,  "5 LPS + 5 PBS（不含 average 汇总列）",
  "GSE207363",  4L,   "control/sham/sepsis/sepsis+LLTS 各1（scRNA）",
  "GSE207177",  6L,   "2 control + 4 CLP（scRNA）",
  "GSE190856",  7L,   "CLP + Steady（scRNA）",
  "GSE229925",  NA_integer_, "待核对",
  "GSE171546",  NA_integer_, "待核对"
)

mid <- function(ds, sfx) file.path(PROJECT_ROOT, ds, "源数据/中间文件", paste0(ds, "_", sfx))
issues <- list()
add <- function(ds, level, item, detail) issues[[length(issues) + 1]] <<-
  tibble(dataset = ds, level = level, item = item, detail = detail)

check_dataset <- function(ds) {
  cat("\n==============", ds, "==============\n")
  # 1) 下载清单（数据来源可溯源）
  man <- file.path(PROJECT_ROOT, ds, "源数据", "下载清单.json")
  if (file.exists(man)) cat("[OK]   下载清单存在（来源可溯源）:", basename(man), "\n")
  else { cat("[WARN] 缺少下载清单.json（无法溯源下载来源）\n"); add(ds, "WARN", "manifest", "缺少下载清单.json") }

  # 2) 样本数与分组
  seu <- mid(ds, "seurat.rds")
  n_proc <- NA_integer_; groups <- NULL; sample_names <- NULL
  if (file.exists(seu)) {
    suppressPackageStartupMessages(library(Seurat))
    obj <- readRDS(seu); m <- obj@meta.data
    scol <- intersect(c("sample", "orig.ident"), colnames(m))[1]
    sample_names <- unique(as.character(m[[scol]]))
    n_proc <- length(sample_names)
    if ("group" %in% colnames(m)) groups <- as.character(m$group)
    rm(obj); gc()
  } else {
    si <- mid(ds, "sample_info_final.rds"); if (!file.exists(si)) si <- mid(ds, "sample_info.rds")
    em <- mid(ds, "expr_matrix.rds")
    if (file.exists(si)) {
      s <- as.data.frame(readRDS(si))
      matcols <- if (file.exists(em)) colnames(readRDS(em)) else NULL
      # 选出与表达矩阵列最匹配的样本 ID 列（兼容 sample/geo_accession/其它命名/行名）
      cand <- c(list(rownames(s)), lapply(s, as.character))
      names(cand) <- c(".rownames", colnames(s))
      pick <- names(cand)[1]; best <- -1
      if (!is.null(matcols)) {
        for (nm in names(cand)) {
          ov <- length(intersect(cand[[nm]], matcols))
          if (ov > best) { best <- ov; pick <- nm }
        }
        sample_names <- cand[[pick]]
        if (setequal(colnames_v <- matcols, sample_names)) cat("[OK]   表达矩阵列与 sample_info 一致（ID列:", pick, "）\n")
        else { cat("[FAIL] 表达矩阵列与 sample_info 不一致（最佳ID列:", pick, "命中", best, "/", length(matcols), "）\n")
          add(ds, "FAIL", "matrix_meta", paste0("矩阵列 != sample_info（", pick, " 命中 ", best, "/", length(matcols), "）")) }
      } else {
        id_col <- intersect(c("sample", "geo_accession", "sample_id", "id"), colnames(s))[1]
        sample_names <- if (!is.na(id_col)) as.character(s[[id_col]]) else rownames(s)
      }
      n_proc <- nrow(s); groups <- as.character(s$group)
    }
  }
  cat("     处理后样本数:", n_proc, "| 样本:", paste(head(sample_names, 12), collapse = ", "), "\n")

  # 3) 与 GEO 真值比对
  truth <- GEO_TRUTH$geo_samples[GEO_TRUTH$dataset == ds]
  if (length(truth) && !is.na(truth)) {
    if (!is.na(n_proc) && n_proc == truth) cat("[OK]   样本数与 GEO 官方一致 (", truth, ")\n")
    else { cat("[FAIL] 样本数与 GEO 官方不一致：处理", n_proc, " vs GEO", truth, "\n")
      add(ds, "FAIL", "geo_count", paste0("处理 ", n_proc, " vs GEO ", truth)) }
  } else cat("[WARN] 未登记 GEO 真值，跳过样本数比对（请从 GEO 页面核对）\n")

  # 4) 编造/污染分组检查
  if (!is.null(sample_names)) {
    bad <- grep("average|mean|summary|汇总", sample_names, ignore.case = TRUE, value = TRUE)
    if (length(bad)) { cat("[FAIL] 疑似汇总/非真实样本列:", paste(bad, collapse = ", "), "\n")
      add(ds, "FAIL", "fake_sample", paste(bad, collapse = ", ")) }
  }
  if (!is.null(groups) && any(is.na(groups))) {
    cat("[FAIL] 存在 NA 分组（分组映射失败/被编造风险）\n"); add(ds, "FAIL", "na_group", "存在 NA 分组")
  }

  # 5) DEG 合理性（全上调/全下调 = 归一化伪影；中位 log2FC 应≈0）
  degf <- mid(ds, "deg.rds")
  if (file.exists(degf)) {
    deg <- readRDS(degf)
    up <- sum(deg$log2FC > 0 & deg$padj < 0.05, na.rm = TRUE)
    dn <- sum(deg$log2FC < 0 & deg$padj < 0.05, na.rm = TRUE)
    med <- median(deg$log2FC, na.rm = TRUE)
    cat(sprintf("     DEG: 上调 %d / 下调 %d, 中位 log2FC=%.2f\n", up, dn, med))
    if ((up + dn) > 50 && (up == 0 || dn == 0)) {
      cat("[FAIL] DEG 全部单向（疑似未做组成归一化的伪影）\n"); add(ds, "FAIL", "deg_onesided", "DEG 全部单向") }
    if (abs(med) > 1) { cat("[WARN] DEG 中位 log2FC 偏离 0 较大：", round(med, 2), "\n")
      add(ds, "WARN", "deg_shift", paste0("median log2FC=", round(med, 2))) }
  }
  invisible(NULL)
}

datasets <- GEO_TRUTH$dataset
datasets <- datasets[dir.exists(file.path(PROJECT_ROOT, datasets))]
for (ds in datasets) try(check_dataset(ds), silent = FALSE)

report <- if (length(issues)) bind_rows(issues) else tibble(dataset = character(), level = character(), item = character(), detail = character())
outdir <- file.path(PROJECT_ROOT, "校验"); dir.create(outdir, showWarnings = FALSE)
write.csv(report, file.path(outdir, "数据真实性核对报告.csv"), row.names = FALSE)
cat("\n================ 汇总 ================\n")
cat("FAIL:", sum(report$level == "FAIL"), " WARN:", sum(report$level == "WARN"), "\n")
if (nrow(report)) print(report)
cat("\n报告已保存: 校验/数据真实性核对报告.csv\n")
