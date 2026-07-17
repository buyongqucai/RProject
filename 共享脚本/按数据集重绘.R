# 按数据集逐个重绘（避免一次性跑四个卡住）
# 用法: Rscript 共享脚本/按数据集重绘.R [GSE190856|GSE207363|GSE207177|GSE267388|all]

args <- commandArgs(trailingOnly = TRUE)
target <- if (length(args)) args[[1]] else "all"
FOUR <- c("GSE190856", "GSE207363", "GSE207177", "GSE267388")
if (!identical(target, "all") && !target %in% FOUR) stop("未知数据集: ", target)

suppressPackageStartupMessages(library(tidyverse))
PROJECT_ROOT <- if (file.exists("RProject.Rproj")) normalizePath(".") else {
  p <- normalizePath(getwd(), winslash = "/")
  for (i in 1:6) { if (file.exists(file.path(p, "RProject.Rproj"))) break; p <- dirname(p) }
  p
}
setwd(PROJECT_ROOT)
source(file.path(PROJECT_ROOT, "共享脚本", "四数据集_统一补全与重绘.R"), encoding = "UTF-8")

run_one <- function(ds) {
  message("\n========== ", ds, " 开始 ", format(Sys.time()), " ==========")
  gc()
  steps <- list(
    redraw_base = function() redraw_base(ds),
    secondary = function() run_unified_secondary(ds),
    comm = function() run_unified_comm(ds),
    bulk_lr = function() run_unified_bulk_lr(ds),
    sirt2 = function() run_unified_sirt2(ds),
    cibersort = function() run_immune_deconv(ds),
    mams = function() run_mams_intersect(ds),
    wgcna = function() run_wgcna(ds),
    gsea_go = function() run_gsea_one(ds),
    gsea_kegg = function() run_gsea_kegg(ds),
    mams_gsea = function() run_mams_gsea(ds),
    hub_enrich = function() run_mams_hub_enrich(ds),
    nichenet = function() run_nichenet_lite(ds)
  )
  for (nm in names(steps)) {
    message("  [", ds, "] ", nm, " ...")
    tryCatch(steps[[nm]](), error = function(e) message("  !! ", nm, " 失败: ", conditionMessage(e)))
    gc()
  }
  n <- length(list.files(ds_paths(ds)$图形, pattern = "\\.pdf$"))
  message("========== ", ds, " 完成, PDF=", n, " ==========\n")
}

ds_list <- if (identical(target, "all")) FOUR else target
for (ds in ds_list) run_one(ds)

canon_figs <- c(
  "质控箱线图", "质控PCA", "PCA", "Top50热图", "火山图", "UMAP", "UMAP_细胞类型",
  "UMAP_免疫聚类", "UMAP_免疫谱系", "细胞比例环图", "分组细胞比例堆叠图",
  "GO生物过程", "GO生物过程图", "GO生物过程_上调", "GO生物过程_上调图",
  "GO生物过程_下调", "GO生物过程_下调图", "KEGG通路", "KEGG通路图",
  "CIBERSORT免疫浸润", "MAMs交集火山图", "WGCNA模块表型相关",
  "GSEA_GO", "GSEA_KEGG", "MAMs通路GSEA", "MAMs交集GO", "WGCNA_HubGO",
  "Hub配体靶标网络", "细胞通讯热图", "Top增强通讯对", "巨噬心肌通讯",
  "配体受体表达", "bulk_LR通讯变化", "巨噬细胞_Sirt2_Foxo1",
  "CLP12h_vs_24h_火山图", "MAMs时序箱线图", "Sirt2_Foxo1时序", "MAMs通路时序评分"
)
cat("\n=== parity check ===\n")
for (ds in ds_list) {
  have <- sub(paste0("^", ds, "_"), "", tools::file_path_sans_ext(list.files(ds_paths(ds)$图形, "\\.pdf$")))
  miss <- setdiff(canon_figs, have)
  cat(ds, ": PDF=", length(have), " missing=", length(miss), "\n", sep = "")
  if (length(miss)) cat("  ", paste(miss, collapse = ", "), "\n")
}
message("ALL DONE DPI=", FIG_DPI)
