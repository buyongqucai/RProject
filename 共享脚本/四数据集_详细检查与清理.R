# 四数据集详细检查 + 统一清理冗余图
# 用法: Set-Location e:\RProject; Rscript 共享脚本/四数据集_详细检查与清理.R

suppressPackageStartupMessages(library(tidyverse))
PROJECT_ROOT <- if (file.exists("RProject.Rproj")) normalizePath(".") else normalizePath("e:/RProject")
setwd(PROJECT_ROOT)

source(file.path(PROJECT_ROOT, "共享脚本", "工具_项目路径.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "巨噬细胞差异分析与MAMs补全.R"), encoding = "UTF-8")

ADJ <- file.path(PROJECT_ROOT, "调整计划")
dir.create(ADJ, showWarnings = FALSE)

SCRNA <- c("GSE190856", "GSE207363", "GSE207177")
NON_IMM <- c("Endothelial", "Fibroblasts", "Fibroblasts_activated",
             "Cardiomyocytes", "Pericytes", "Smooth_muscle")

# ---- 1. 清理图 ----
message("=== 清理三 scRNA 冗余 PDF ===")
removed_sc <- cleanup_redundant_scrna_figures(SCRNA)
message("=== 清理 GSE267388 ===")
bulk_res <- cleanup_and_rename_gse267388_figures()

# ---- 2. 逐数据集核查 ----
audit_rows <- list()
missing_rows <- list()
immune_rows <- list()

scrna_required_core <- function(ds) {
  c(
    paste0(ds, "_UMAP_细胞类型.pdf"),
    paste0(ds, "_UMAP_免疫聚类.pdf"),
    paste0(ds, "_UMAP_免疫谱系.pdf"),
    paste0(ds, "_分组细胞比例堆叠图.pdf"),
    paste0(ds, "_巨噬细胞_UMAP高亮.pdf"),
    paste0(ds, "_巨噬细胞_火山图.pdf"),
    paste0(ds, "_巨噬细胞_内质网应激热图.pdf"),
    paste0(ds, "_巨噬细胞_线粒体功能障碍热图.pdf"),
    paste0(ds, "_巨噬细胞_GO生物过程_上调.pdf"),
    paste0(ds, "_巨噬细胞_GO生物过程_下调.pdf"),
    paste0(ds, "_巨噬细胞_MAMs韦恩图.pdf"),
    paste0(ds, "_巨噬细胞_MAMs交集火山图.pdf"),
    paste0(ds, "_巨噬细胞_Sirt2_Foxo1.pdf")
  )
}

scrna_required_tables <- function(ds) {
  c(
    paste0(ds, "_巨噬细胞_显著差异基因.csv"),
    paste0(ds, "_巨噬细胞_全部差异基因.csv"),
    paste0(ds, "_巨噬细胞_MAMs交集基因.csv"),
    paste0(ds, "_细胞类型比例.csv")
  )
}

bulk_required <- function(ds) {
  c(
    paste0(ds, "_火山图.pdf"),
    paste0(ds, "_质控箱线图.pdf"),
    paste0(ds, "_PCA.pdf"),
    paste0(ds, "_Top50热图.pdf"),
    paste0(ds, "_GO生物过程.pdf"),
    paste0(ds, "_KEGG通路.pdf"),
    paste0(ds, "_MAMs交集火山图.pdf"),
    paste0(ds, "_巨噬细胞_Sirt2_Foxo1.pdf")
  )
}

for (ds in SCRNA) {
  message("核查: ", ds)
  p <- init_dataset_paths(PROJECT_ROOT, ds)
  pdfs <- list.files(p$图形, pattern = "\\.pdf$", full.names = FALSE)
  keep <- SCRNA_FIGURE_KEEP(ds)
  extras <- setdiff(pdfs, keep)
  req <- scrna_required_core(ds)
  miss_fig <- setdiff(req, pdfs)
  req_tab <- scrna_required_tables(ds)
  miss_tab <- req_tab[!file.exists(file.path(p$表格, req_tab))]

  # immune
  imm_f <- file.path(p$中间数据, paste0(ds, "_immune.rds"))
  n_nonimm <- NA_integer_; n_mac_imm <- NA_integer_; n_mac_full <- NA_integer_
  labels <- ""
  if (file.exists(imm_f)) {
    md <- readRDS(imm_f)@meta.data
    il <- table(as.character(md$immune_lineage))
    n_nonimm <- sum(il[intersect(names(il), NON_IMM)], na.rm = TRUE)
    n_mac_imm <- as.integer(il["Macrophages"]); if (is.na(n_mac_imm)) n_mac_imm <- 0L
    labels <- paste(names(sort(il, decreasing = TRUE)), collapse = ", ")
  }
  seu_f <- file.path(p$中间数据, paste0(ds, "_seurat.rds"))
  if (file.exists(seu_f)) {
    sm <- readRDS(seu_f)@meta.data
    n_mac_full <- sum(as.character(sm$celltype) == "Macrophages", na.rm = TRUE)
  }

  # deg / mams
  deg_f <- file.path(p$表格, paste0(ds, "_巨噬细胞_显著差异基因.csv"))
  mams_f <- file.path(p$表格, paste0(ds, "_巨噬细胞_MAMs交集基因.csv"))
  n_deg <- if (file.exists(deg_f)) nrow(read.csv(deg_f)) else NA
  n_mams <- if (file.exists(mams_f)) nrow(read.csv(mams_f)) else NA

  audit_rows[[ds]] <- tibble(
    dataset = ds, type = "scRNA", n_pdf = length(pdfs), n_extra = length(extras),
    n_miss_fig = length(miss_fig), n_miss_tab = length(miss_tab),
    n_mac_full = n_mac_full, n_mac_immune = n_mac_imm, n_nonimm_in_immune = n_nonimm,
    n_macro_deg = n_deg, n_mams_inter = n_mams,
    ok_immune = isTRUE(n_nonimm == 0), ok_mac_align = isTRUE(n_mac_full == n_mac_imm)
  )
  immune_rows[[ds]] <- tibble(dataset = ds, immune_labels = labels)
  if (length(miss_fig) || length(miss_tab) || length(extras)) {
    missing_rows[[length(missing_rows) + 1]] <- tibble(
      dataset = ds,
      missing_figures = paste(miss_fig, collapse = "; "),
      missing_tables = paste(miss_tab, collapse = "; "),
      leftover_extras = paste(extras, collapse = "; ")
    )
  }
}

# bulk
ds <- "GSE267388"
p <- init_dataset_paths(PROJECT_ROOT, ds)
pdfs <- list.files(p$图形, pattern = "\\.pdf$", full.names = FALSE)
keep <- BULK_FIGURE_KEEP(ds)
extras <- setdiff(pdfs, keep)
req <- bulk_required(ds)
miss_fig <- setdiff(req, pdfs)
clp_left <- grep("CLP12h", pdfs, value = TRUE)
deg_f <- file.path(p$表格, paste0(ds, "_显著差异基因.csv"))
mams_f <- file.path(p$表格, paste0(ds, "_MAMs交集基因.csv"))
audit_rows[[ds]] <- tibble(
  dataset = ds, type = "bulk", n_pdf = length(pdfs), n_extra = length(extras),
  n_miss_fig = length(miss_fig), n_miss_tab = as.integer(!file.exists(deg_f)) + as.integer(!file.exists(mams_f)),
  n_mac_full = NA_integer_, n_mac_immune = NA_integer_, n_nonimm_in_immune = NA_integer_,
  n_macro_deg = if (file.exists(deg_f)) nrow(read.csv(deg_f)) else NA,
  n_mams_inter = if (file.exists(mams_f)) nrow(read.csv(mams_f)) else NA,
  ok_immune = NA, ok_mac_align = NA
)
missing_rows[[length(missing_rows) + 1]] <- tibble(
  dataset = ds,
  missing_figures = paste(c(miss_fig, if (length(clp_left)) paste0("CLP残留:", clp_left)), collapse = "; "),
  missing_tables = "",
  leftover_extras = paste(extras, collapse = "; ")
)

audit <- bind_rows(audit_rows)
imm_lab <- bind_rows(immune_rows)
miss <- bind_rows(missing_rows)
write.csv(audit, file.path(ADJ, "14_四数据集检查快照.csv"), row.names = FALSE)

fmt_tbl <- function(df) {
  if (is.null(df) || !nrow(df)) return("_无_")
  hdr <- paste0("| ", paste(names(df), collapse = " | "), " |")
  sep <- paste0("|", paste(rep("---", ncol(df)), collapse = "|"), "|")
  rows <- apply(df, 1, function(r) paste0("| ", paste(r, collapse = " | "), " |"))
  paste(c(hdr, sep, rows), collapse = "\n")
}

# 清理后最终 PDF 列表
final_lists <- lapply(c(SCRNA, "GSE267388"), function(ds) {
  p <- init_dataset_paths(PROJECT_ROOT, ds)
  paste0("- **", ds, "**（", length(list.files(p$图形, "\\.pdf$")), "）：",
         paste(list.files(p$图形, "\\.pdf$"), collapse = ", "))
})

lines <- c(
  "# 14 四数据集详细检查与清理报告",
  "",
  paste0("**生成时间：** ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  paste0("**项目路径：** ", PROJECT_ROOT),
  "",
  "## 清理动作",
  paste0("- scRNA 删除冗余 PDF：", length(removed_sc), " 个"),
  paste0("- GSE267388 重命名：", length(bulk_res$renamed), "；删除：", length(bulk_res$removed)),
  "",
  "## 四数据集总览",
  "",
  fmt_tbl(as.data.frame(audit)),
  "",
  "## 免疫谱系标签（三 scRNA）",
  "",
  fmt_tbl(as.data.frame(imm_lab)),
  "",
  "## 缺失 / 残留明细",
  "",
  fmt_tbl(as.data.frame(miss)),
  "",
  "## 清理后保留的 PDF",
  "",
  paste(final_lists, collapse = "\n"),
  "",
  "## 判定",
  "- scRNA：免疫非免疫污染应为 0；Mac 全组织与免疫谱系应对齐",
  "- bulk：不应残留 CLP12h 文件名；图集应为验证相关主图",
  "- 主线必需图缺失见上表 n_miss_fig",
  ""
)
writeLines(lines, file.path(ADJ, "14_四数据集详细检查与清理报告.md"), useBytes = TRUE)
message("报告: 调整计划/14_四数据集详细检查与清理报告.md")
print(audit)
message("======== 完成 ========")
