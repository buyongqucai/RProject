# 重跑三 scRNA 免疫子集：剔除非免疫污染 + 细胞名 UMAP
# 用法: Set-Location e:\RProject; Rscript 共享脚本/重跑免疫亚群UMAP.R

suppressPackageStartupMessages(library(tidyverse))

PROJECT_ROOT <- if (file.exists("RProject.Rproj")) normalizePath(".") else {
  p <- normalizePath(getwd(), winslash = "/")
  for (i in 1:6) { if (file.exists(file.path(p, "RProject.Rproj"))) break; p <- dirname(p) }
  p
}
setwd(PROJECT_ROOT)

source(file.path(PROJECT_ROOT, "共享脚本", "工具_项目路径.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_统一出图.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA细胞注释.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA可视化.R"), encoding = "UTF-8")

SCRNA_DS <- c("GSE190856", "GSE207363", "GSE207177")
NON_IMM <- c("Endothelial", "Fibroblasts", "Fibroblasts_activated",
             "Cardiomyocytes", "Pericytes", "Smooth_muscle")

before_after <- list()

for (ds in SCRNA_DS) {
  message("\n======== ", ds, " ========")
  p <- init_dataset_paths(PROJECT_ROOT, ds)
  seu_f <- file.path(p$中间数据, paste0(ds, "_seurat.rds"))
  imm_f <- file.path(p$中间数据, paste0(ds, "_immune.rds"))

  before_tab <- NULL
  if (file.exists(imm_f)) {
    old <- tryCatch(readRDS(imm_f), error = function(e) NULL)
    if (!is.null(old) && "immune_lineage" %in% colnames(old@meta.data)) {
      before_tab <- as.data.frame(sort(table(as.character(old$immune_lineage)), decreasing = TRUE))
      names(before_tab) <- c("celltype", "n_before")
      before_n_nonimm <- sum(before_tab$n_before[before_tab$celltype %in% NON_IMM])
    } else {
      before_n_nonimm <- NA
    }
  } else {
    before_n_nonimm <- NA
  }

  suppressPackageStartupMessages(library(Seurat))
  obj <- readRDS(seu_f)
  DefaultAssay(obj) <- "RNA"
  if ("JoinLayers" %in% ls("package:Seurat")) {
    obj <- tryCatch(JoinLayers(obj, assay = "RNA"), error = function(e) obj)
  }

  immune_obj <- subset_immune_recluster(obj)
  if (is.null(immune_obj)) {
    message("免疫子集失败: ", ds)
    next
  }
  saveRDS(immune_obj, imm_f)

  after_tab <- as.data.frame(sort(table(as.character(immune_obj$immune_lineage)), decreasing = TRUE))
  names(after_tab) <- c("celltype", "n_after")
  after_n_nonimm <- sum(after_tab$n_after[after_tab$celltype %in% NON_IMM], na.rm = TRUE)

  cfg <- list(deg_padj = 0.05, deg_logfc = 1.0, run_immune_subset = TRUE)
  # 仅重绘免疫相关与细胞类型 UMAP（不全量重跑 DEG 图）
  plot_umap_celltype(obj, title = paste(ds, "UMAP 细胞类型"),
                     out_path = file.path(p$图形, paste0(ds, "_UMAP.pdf")))
  plot_umap_celltype(obj, title = paste(ds, "UMAP 细胞类型"),
                     out_path = file.path(p$图形, paste0(ds, "_UMAP_细胞类型.pdf")))
  plot_umap_by_col(immune_obj, "immune_lineage",
                   title = paste(ds, "免疫亚群（细胞类型）"),
                   out_path = file.path(p$图形, paste0(ds, "_UMAP_免疫聚类.pdf")))
  plot_umap_by_col(immune_obj, "immune_lineage",
                   title = paste(ds, "免疫谱系（淋巴系+髓系）"),
                   out_path = file.path(p$图形, paste0(ds, "_UMAP_免疫谱系.pdf")))

  merged <- if (!is.null(before_tab)) {
    dplyr::full_join(before_tab, after_tab, by = "celltype")
  } else after_tab
  write.csv(merged, file.path(p$表格, paste0(ds, "_免疫谱系_修正前后对比.csv")), row.names = FALSE)

  before_after[[ds]] <- list(
    n_immune = ncol(immune_obj),
    before_n_nonimm = before_n_nonimm,
    after_n_nonimm = after_n_nonimm,
    after_tab = after_tab,
    labels = paste(after_tab$celltype, collapse = ", ")
  )
  message(ds, " 免疫细胞 n=", ncol(immune_obj),
          " | 非免疫标签: ", before_n_nonimm, " → ", after_n_nonimm)
  print(after_tab)
  gc()
}

# ---- 调整报告 ----
ADJ <- file.path(PROJECT_ROOT, "调整计划")
dir.create(ADJ, showWarnings = FALSE)

fmt_tbl <- function(df) {
  if (is.null(df) || !nrow(df)) return("_（无）_")
  hdr <- paste0("| ", paste(names(df), collapse = " | "), " |")
  sep <- paste0("|", paste(rep("---", ncol(df)), collapse = "|"), "|")
  rows <- apply(df, 1, function(r) paste0("| ", paste(r, collapse = " | "), " |"))
  paste(c(hdr, sep, rows), collapse = "\n")
}

lines <- c(
  "# 11 免疫亚群 UMAP 修正调整报告",
  "",
  paste0("**生成时间：** ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  paste0("**项目路径：** ", PROJECT_ROOT),
  "",
  "## 调整内容",
  "1. 免疫亚群 UMAP **数字簇 → 细胞名称**（`immune_lineage`）",
  "2. 剔除非免疫污染（内皮 / 成纤维 / 心肌 / 周细胞等）",
  "3. 修复 `annotate_by_markers` 误用旧 `score_*` 列导致的错误标注",
  "4. `IMMUNE_LINEAGE` 统一：T_cells / NK_cells 分列；Granulocytes 替代 Neutrophils",
  "",
  "## 原因",
  "- 原 `_UMAP_免疫聚类.pdf` 按 `seurat_clusters` 着色，故为 0–15 数字",
  "- `immune_score > 0` 过松，基质细胞混入免疫子集",
  "- `annotate_by_markers` 用 `grep('^score_')` 读到全组织 CARDIAC 分数，误标 Endothelial/Fibroblasts",
  "",
  "## 各数据集修正前后",
  ""
)

for (ds in names(before_after)) {
  r <- before_after[[ds]]
  lines <- c(lines,
    paste0("### ", ds),
    paste0("- 免疫细胞数：", r$n_immune),
    paste0("- 非免疫标签细胞数：", r$before_n_nonimm, " → **", r$after_n_nonimm, "**"),
    paste0("- 修正后谱系：", r$labels),
    "",
    fmt_tbl(as.data.frame(r$after_tab)),
    ""
  )
}

lines <- c(lines,
  "## 输出文件",
  "- `{GSE}_UMAP_免疫聚类.pdf`（细胞名）",
  "- `{GSE}_UMAP_免疫谱系.pdf`（淋巴系+髓系）",
  "- `{GSE}_免疫谱系_修正前后对比.csv`",
  "- 更新 `{GSE}_immune.rds`",
  "",
  "## 验收",
  "- 免疫图图例为细胞名，无 0–15 主图例",
  "- `immune_lineage` 不含 Endothelial / Fibroblasts / Cardiomyocytes / Pericytes",
  ""
)

writeLines(lines, file.path(ADJ, "11_免疫亚群UMAP修正_调整报告.md"), useBytes = TRUE)
message("\n报告已写入: 调整计划/11_免疫亚群UMAP修正_调整报告.md")
message("======== 全部完成 ========")
