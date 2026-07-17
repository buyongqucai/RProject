# 本轮：Mac vs DC 注释收紧 + GSE267388 bulk 清理
# 用法: Set-Location e:\RProject; Rscript 共享脚本/执行计划_本轮_MacDC与bulk清理.R

suppressPackageStartupMessages(library(tidyverse))
PROJECT_ROOT <- if (file.exists("RProject.Rproj")) normalizePath(".") else normalizePath("e:/RProject")
setwd(PROJECT_ROOT)

source(file.path(PROJECT_ROOT, "共享脚本", "工具_项目路径.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_统一出图.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA细胞注释.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA可视化.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "巨噬细胞差异分析与MAMs补全.R"), encoding = "UTF-8")

SCRNA_DS <- c("GSE190856", "GSE207363", "GSE207177")
ADJ <- file.path(PROJECT_ROOT, "调整计划")
dir.create(ADJ, showWarnings = FALSE)

# ---- C1: 重跑免疫亚群 ----
rows <- list()
for (ds in SCRNA_DS) {
  message("\n======== C1 ", ds, " ========")
  p <- init_dataset_paths(PROJECT_ROOT, ds)
  suppressPackageStartupMessages(library(Seurat))
  obj <- readRDS(file.path(p$中间数据, paste0(ds, "_seurat.rds")))
  DefaultAssay(obj) <- "RNA"
  if ("JoinLayers" %in% ls("package:Seurat")) {
    obj <- tryCatch(JoinLayers(obj, assay = "RNA"), error = function(e) obj)
  }
  n_mac_full <- sum(as.character(obj$celltype) == "Macrophages", na.rm = TRUE)
  immune_obj <- subset_immune_recluster(obj)
  if (is.null(immune_obj)) { message("失败: ", ds); next }
  saveRDS(immune_obj, file.path(p$中间数据, paste0(ds, "_immune.rds")))
  il <- sort(table(as.character(immune_obj$immune_lineage)), decreasing = TRUE)
  n_mac_imm <- as.integer(il["Macrophages"]); if (is.na(n_mac_imm)) n_mac_imm <- 0L
  n_dc <- as.integer(il["Dendritic"]); if (is.na(n_dc)) n_dc <- 0L
  plot_umap_by_col(immune_obj, "immune_lineage",
                   title = paste(ds, "免疫亚群（细胞类型）"),
                   out_path = file.path(p$图形, paste0(ds, "_UMAP_免疫聚类.pdf")))
  plot_umap_by_col(immune_obj, "immune_lineage",
                   title = paste(ds, "免疫谱系（淋巴系+髓系）"),
                   out_path = file.path(p$图形, paste0(ds, "_UMAP_免疫谱系.pdf")))
  write.csv(as.data.frame(il), file.path(p$表格, paste0(ds, "_免疫谱系组成.csv")), row.names = TRUE)
  rows[[ds]] <- tibble(dataset = ds, n_mac_full = n_mac_full, n_mac_immune = n_mac_imm,
                       n_dendritic = n_dc, n_immune = ncol(immune_obj),
                       labels = paste(names(il), collapse = ", "))
  message(ds, " full Mac=", n_mac_full, " | immune Mac=", n_mac_imm, " | DC=", n_dc)
  print(il)
  gc()
}
cmp <- bind_rows(rows)

# ---- C2: bulk 清理 ----
message("\n======== C2 GSE267388 清理 ========")
bulk_res <- cleanup_and_rename_gse267388_figures()

# ---- C3: 报告 ----
fmt_tbl <- function(df) {
  if (is.null(df) || !nrow(df)) return("_无_")
  hdr <- paste0("| ", paste(names(df), collapse = " | "), " |")
  sep <- paste0("|", paste(rep("---", ncol(df)), collapse = "|"), "|")
  rows <- apply(df, 1, function(r) paste0("| ", paste(r, collapse = " | "), " |"))
  paste(c(hdr, sep, rows), collapse = "\n")
}

lines <- c(
  "# 13 本轮执行：Mac/DC 注释收紧 + GSE267388 清理",
  "",
  paste0("**生成时间：** ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  paste0("**项目路径：** ", PROJECT_ROOT),
  "",
  "## C1 Macrophages vs Dendritic",
  "- Dendritic marker 改为 Flt3/Clec9a/Xcr1（去掉易交叉的 Itgax）",
  "- 全组织 celltype 为 Macrophages/Monocytes/Granulocytes/B/T 时优先锁定，禁止 Mac→DC 误标",
  "",
  fmt_tbl(as.data.frame(cmp)),
  "",
  "## C2 GSE267388",
  paste0("- 重命名：", length(bulk_res$renamed), " 个"),
  if (length(bulk_res$renamed)) paste(bulk_res$renamed, collapse = "\n") else "- （无待重命名文件或已处理）",
  "",
  paste0("- 删除冗余：", length(bulk_res$removed), " 个"),
  if (length(bulk_res$removed)) paste(head(bulk_res$removed, 40), collapse = "\n") else "",
  "",
  "## 验收",
  "- GSE207363 免疫谱系中 Macrophages 应接近全组织巨噬数量级，不再 DC >> Mac",
  "- GSE267388 无 CLP12h_vs_24h 文件名",
  ""
)
writeLines(lines, file.path(ADJ, "13_本轮执行_MacDC与bulk清理.md"), useBytes = TRUE)
message("报告: 调整计划/13_本轮执行_MacDC与bulk清理.md")
message("======== 本轮执行计划完成 ========")
