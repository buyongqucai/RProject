# 从 Step 4 续跑（DEG 已完成时使用）
suppressPackageStartupMessages(library(tidyverse))
PROJECT_ROOT <- if (file.exists("RProject.Rproj")) normalizePath(".") else normalizePath("e:/RProject")
setwd(PROJECT_ROOT)
ADJ_DIR <- file.path(PROJECT_ROOT, "调整计划")
source(file.path(PROJECT_ROOT, "共享脚本", "巨噬细胞差异分析与MAMs补全.R"), encoding = "UTF-8")

write_report <- function(filename, title, body_lines) {
  path <- file.path(ADJ_DIR, filename)
  hdr <- c(paste0("# ", title), "",
           paste0("**生成时间：** ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
           paste0("**项目路径：** ", PROJECT_ROOT), "")
  writeLines(c(hdr, body_lines), path, useBytes = TRUE)
  message("报告: ", path)
}
fmt_tbl <- function(df) {
  if (is.null(df) || !nrow(df)) return("_（无）_")
  hdr <- paste0("| ", paste(names(df), collapse = " | "), " |")
  sep <- paste0("|", paste(rep("---", ncol(df)), collapse = "|"), "|")
  rows <- apply(df, 1, function(r) paste0("| ", paste(r, collapse = " | "), " |"))
  paste(c(hdr, sep, rows), collapse = "\n")
}

message("=== Step 4: ER/线粒体热图 ===")
heat_log <- list()
for (ds in SCRNA_DS) heat_log[[ds]] <- run_macrophage_theme_heatmap(ds)
heat363 <- run_macrophage_theme_heatmap("GSE207363", suffix = "SepsisVsControl")
write_report("04_巨噬细胞专题热图_调整报告.md", "04 巨噬细胞专题热图 调整报告", c(
  "## Step 4", "ER stress / 线粒体功能障碍巨噬热图（含 Sirt2/Foxo1 HUB 标注）",
  paste(lapply(SCRNA_DS, function(ds) {
    h <- heat_log[[ds]]
    paste0("- **", ds, "**：ER ", h$n_genes_er, " / Mito ", h$n_genes_mito)
  }), collapse = "\n")
))

message("=== Step 3/5: GO/KEGG + MAMs ===")
enrich_log <- list(); mams_results <- list()
for (ds in SCRNA_DS) {
  enrich_log[[ds]] <- run_macrophage_enrichment(ds)
  plot_macrophage_hub_genes(ds)
  mams_results[[ds]] <- run_macrophage_mams_intersect(ds)
}
enrich363 <- run_macrophage_enrichment("GSE207363", suffix = "SepsisVsControl")
mams363 <- run_macrophage_mams_intersect("GSE207363", suffix = "SepsisVsControl")

mams_compare <- bind_rows(lapply(SCRNA_DS, function(ds) {
  tb <- collect_tissue_mams_stats(ds); mr <- mams_results[[ds]]
  tibble(dataset = ds, tissue_mams_n = tb$n_mams, macro_mams_n = mr$n_inter, macro_deg_n = mr$n_deg_sig)
}))
write_report("05_巨噬细胞GO_KEGG_调整报告.md", "05 巨噬细胞 GO/KEGG 调整报告",
             c("## Step 3", paste(lapply(SCRNA_DS, function(ds) {
               paste0("- **", ds, "** DEG ", enrich_log[[ds]]$n_sig %||% 0)
             }), collapse = "\n")))
write_report("06_巨噬细胞MAMs交集与HUB_调整报告.md", "06 巨噬细胞 MAMs 交集与 HUB 调整报告",
             c("## Step 5", fmt_tbl(as.data.frame(mams_compare)),
               paste(lapply(SCRNA_DS, function(ds) {
                 paste0("- **", ds, "**：", paste(mams_results[[ds]]$inter_genes, collapse = ", "))
               }), collapse = "\n")))

message("=== 清理冗余 PDF ===")
removed <- cleanup_redundant_scrna_figures()
baseline <- collect_baseline_snapshot()
after <- collect_baseline_snapshot()
write.csv(after, file.path(ADJ_DIR, "08_补全后快照.csv"), row.names = FALSE)
write_report("07_冗余图片清理_调整报告.md", "07 冗余图片清理 调整报告",
             c(paste0("已删除 ", length(removed), " 个冗余 PDF")))
write_report("08_补全路线执行汇总.md", "08 补全路线执行汇总", c(
  "## 5 步流程", "Step 1–5 已完成", "", fmt_tbl(as.data.frame(after))
))
message("续跑完成")
