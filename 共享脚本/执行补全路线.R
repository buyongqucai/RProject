# 执行四数据集补全路线（对齐用户 5 步 snRNA 巨噬细胞主线）
# 用法: Set-Location e:\RProject; Rscript 共享脚本/执行补全路线.R

suppressPackageStartupMessages(library(tidyverse))

PROJECT_ROOT <- if (file.exists("RProject.Rproj")) normalizePath(".") else {
  p <- normalizePath(getwd(), winslash = "/")
  for (i in 1:6) { if (file.exists(file.path(p, "RProject.Rproj"))) break; p <- dirname(p) }
  p
}
setwd(PROJECT_ROOT)

ADJ_DIR <- file.path(PROJECT_ROOT, "调整计划")
EXEC_DIR <- file.path(PROJECT_ROOT, "执行计划")
dir.create(ADJ_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(EXEC_DIR, recursive = TRUE, showWarnings = FALSE)

source(file.path(PROJECT_ROOT, "共享脚本", "巨噬细胞差异分析与MAMs补全.R"), encoding = "UTF-8")

write_report <- function(filename, title, body_lines) {
  path <- file.path(ADJ_DIR, filename)
  hdr <- c(
    paste0("# ", title),
    "",
    paste0("**生成时间：** ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
    paste0("**项目路径：** ", PROJECT_ROOT),
    ""
  )
  writeLines(c(hdr, body_lines), path, useBytes = TRUE)
  message("报告已写入: ", path)
  path
}

fmt_tbl <- function(df) {
  if (is.null(df) || !nrow(df)) return("_（无数据）_")
  hdr <- paste0("| ", paste(names(df), collapse = " | "), " |")
  sep <- paste0("|", paste(rep("---", ncol(df)), collapse = "|"), "|")
  rows <- apply(df, 1, function(r) paste0("| ", paste(r, collapse = " | "), " |"))
  paste(c(hdr, sep, rows), collapse = "\n")
}
`%||%` <- function(x, y) if (is.null(x)) y else x

# ---- Step 00: 基线快照 ----
baseline <- collect_baseline_snapshot()
write.csv(baseline, file.path(ADJ_DIR, "00_调整前基线快照.csv"), row.names = FALSE)
write_report("00_调整前基线快照.md", "00 调整前基线快照", c(
  "## 目的",
  "记录补全前全组织 DEG 层与巨噬细胞 DEG 层基线。",
  "", "## 基线数据", "", fmt_tbl(as.data.frame(baseline))
))

# ---- Step 01: GSE207363 剔除 LLTS ----
message("\n=== Step 01: GSE207363 剔除 LLTS ===")
seurat363 <- file.path(PROJECT_ROOT, "GSE207363", "源数据", "中间文件", "GSE207363_seurat.rds")
need_reprocess363 <- TRUE
if (file.exists(seurat363)) {
  obj363 <- readRDS(seurat363)
  grps <- unique(as.character(obj363$group))
  need_reprocess363 <- "LLTS" %in% grps
}
if (need_reprocess363) {
  res363 <- reprocess_gse207363_no_llts()
} else {
  message("GSE207363 已剔除 LLTS，跳过重建")
  prop363 <- read.csv(file.path(PROJECT_ROOT, "GSE207363", "结果", "表格", "GSE207363_细胞类型比例.csv"))
  res363 <- list(after_cells = sum(prop363$n), after_groups = sort(unique(prop363$group)),
                 after_prop = prop363)
}
after_mac_pct <- res363$after_prop %>% group_by(group) %>%
  mutate(pct = round(100 * n / sum(n), 2)) %>%
  filter(celltype == "Macrophages") %>% select(group, pct)
write_report("01_GSE207363_剔除LLTS_调整报告.md", "01 GSE207363 剔除 LLTS 调整报告", c(
  "## 调整内容", "- 剔除 LLTS，仅保留 Control / Sham / Sepsis。",
  paste0("- 细胞数：", res363$after_cells),
  "", "### 各组巨噬细胞占比（%）", "", fmt_tbl(as.data.frame(after_mac_pct))
))

# ---- 用户 Step 1: UMAP + 免疫亚群 + 巨噬为核心 ----
message("\n=== 用户 Step 1: 细胞图谱与巨噬高亮 ===")
step1_log <- list()
for (ds in SCRNA_DS) {
  save_step1_scrna_figures(ds)
  step1_log[[ds]] <- plot_macrophage_umap_highlight(ds)
}
write_report("02_细胞图谱与巨噬核心_调整报告.md", "02 细胞图谱与巨噬核心 调整报告", c(
  "## 对应用户流程 Step 1",
  "snRNA-seq → UMAP 细胞类群 → 免疫亚群 → 明确巨噬细胞为核心免疫细胞。",
  "",
  "## 方法",
  "- `{GSE}_UMAP_细胞类型.pdf`、`_UMAP_免疫聚类.pdf`、`_UMAP_免疫谱系.pdf`",
  "- `{GSE}_分组细胞比例堆叠图.pdf`",
  "- `{GSE}_巨噬细胞_UMAP高亮.pdf`、`_巨噬细胞_分组UMAP.pdf`、`_巨噬细胞_分组比例.pdf`",
  "",
  "## 各数据集巨噬细胞数",
  "",
  paste(lapply(SCRNA_DS, function(ds) {
    paste0("- **", ds, "**：", step1_log[[ds]]$n_mac, " 个巨噬细胞")
  }), collapse = "\n")
))

# ---- 用户 Step 2: 巨噬细胞 DEG ----
message("\n=== 用户 Step 2: 巨噬细胞 DEG ===")
deg_results <- list()
for (ds in SCRNA_DS) {
  if (ds == "GSE190856" && file.exists(file.path(init_dataset_paths(PROJECT_ROOT, ds)$表格,
      paste0(ds, "_巨噬细胞_显著差异基因.csv")))) {
    sig_n <- nrow(read.csv(file.path(init_dataset_paths(PROJECT_ROOT, ds)$表格,
                                         paste0(ds, "_巨噬细胞_显著差异基因.csv"))))
    if (sig_n > 0) {
      message("跳过已完成 DEG: ", ds, " (n_sig=", sig_n, ")")
      deg_results[[ds]] <- list(dataset = ds, contrast = paste(MACRO_CONTRASTS[[ds]]$main, collapse = " vs "),
                                method = "macrophage_FindMarkers", n_macrophages = NA,
                                n_sig = sig_n, n_up = NA, n_down = NA,
                                sirt2 = data.frame(), foxo1 = data.frame())
      next
    }
  }
  deg_results[[ds]] <- run_macrophage_deg(ds, MACRO_CONTRASTS[[ds]]$main)
}
deg363_extra <- run_macrophage_deg("GSE207363", c("Sepsis", "Control"), suffix = "SepsisVsControl")

deg_summary <- bind_rows(lapply(deg_results, function(r) {
  tibble(dataset = r$dataset, contrast = r$contrast, method = r$method,
         n_macrophages = r$n_macrophages, n_sig = r$n_sig,
         n_up = r$n_up, n_down = r$n_down,
         Sirt2_sig = nrow(r$sirt2) > 0, Foxo1_sig = nrow(r$foxo1) > 0)
}))
write_report("03_巨噬细胞DEG_调整报告.md", "03 巨噬细胞 DEG 调整报告", c(
  "## 对应用户流程 Step 2",
  "对照/疾病组巨噬细胞差异基因（上调、下调）。",
  "",
  "## 方法",
  "- GSE207177：样本级巨噬 pseudobulk + edgeR-TMM + voom",
  "- GSE190856 / GSE207363：Seurat FindMarkers（低重复/功效不足）",
  "- 阈值：padj < 0.05，|log2FC| > 1",
  "",
  "## 主对比结果", "", fmt_tbl(as.data.frame(deg_summary)),
  "",
  paste0("## GSE207363 补充对比 Sepsis vs Control",
         "\n- 显著 DEG：", deg363_extra$n_sig,
         "（上调 ", deg363_extra$n_up, " / 下调 ", deg363_extra$n_down, "）"),
  "",
  "## 输出",
  "- `{GSE}_巨噬细胞_全部/显著差异基因.csv`",
  "- `{GSE}_巨噬细胞_火山图.pdf`"
))

# ---- 用户 Step 4: ER / 线粒体热图（在 GO/KEGG 之前执行，因不依赖富集）----
message("\n=== 用户 Step 4: ER/线粒体巨噬热图 ===")
heat_log <- list()
for (ds in SCRNA_DS) {
  heat_log[[ds]] <- run_macrophage_theme_heatmap(ds)
}
heat363 <- run_macrophage_theme_heatmap("GSE207363", suffix = "SepsisVsControl")
write_report("04_巨噬细胞专题热图_调整报告.md", "04 巨噬细胞专题热图 调整报告", c(
  "## 对应用户流程 Step 4",
  "内质网应激基因 / 线粒体功能障碍基因在巨噬细胞表达谱的变化。",
  "",
  "## 基因集",
  paste0("- ER stress（", length(ER_STRESS_GENES), "）：",
         paste(head(ER_STRESS_GENES, 8), collapse = ", "), " ..."),
  paste0("- Mito dysfunction（", length(MITO_DYSFUNCTION_GENES), "）：",
         paste(head(MITO_DYSFUNCTION_GENES, 8), collapse = ", "), " ..."),
  paste0("- HUB 候选（附加标注）：", paste(HUB_CANDIDATE_GENES, collapse = ", ")),
  "",
  "## 说明",
  "Sirt2 / Foxo1 为 MAMs 通路 HUB 候选，**不是** ER/线粒体 marker；热图中以「HUB候选」行标注。",
  "",
  paste(lapply(SCRNA_DS, function(ds) {
    h <- heat_log[[ds]]
    paste0("- **", ds, "**：ER ", h$n_genes_er, " 基因 / Mito ", h$n_genes_mito, " 基因")
  }), collapse = "\n"),
  "",
  "## 输出",
  "- `{GSE}_巨噬细胞_内质网应激热图.pdf` / `_线粒体功能障碍热图.pdf`",
  "- 对应 `{GSE}_巨噬细胞_*表达.csv`"
))

# ---- 用户 Step 3: GO/KEGG 上调/下调 ----
message("\n=== 用户 Step 3: GO/KEGG 富集 ===")
enrich_log <- list()
for (ds in SCRNA_DS) {
  enrich_log[[ds]] <- run_macrophage_enrichment(ds)
  plot_macrophage_hub_genes(ds)
}
enrich363 <- run_macrophage_enrichment("GSE207363", suffix = "SepsisVsControl")
write_report("05_巨噬细胞GO_KEGG_调整报告.md", "05 巨噬细胞 GO/KEGG 调整报告", c(
  "## 对应用户流程 Step 3",
  "对巨噬细胞显著 DEG 分别做 GO BP / KEGG（全体、上调、下调）。",
  "",
  paste(lapply(SCRNA_DS, function(ds) {
    e <- enrich_log[[ds]]
    if (!is.null(e$skipped) && e$skipped) {
      paste0("- **", ds, "**：DEG 不足，跳过")
    } else {
      paste0("- **", ds, "**：显著 DEG ", e$n_sig)
    }
  }), collapse = "\n"),
  "",
  "## 输出前缀",
  "- `{GSE}_巨噬细胞_GO生物过程_上调/下调*.csv/pdf`",
  "- `{GSE}_巨噬细胞_KEGG通路_上调/下调*.csv/pdf`"
))

# ---- 用户 Step 5: MAMs 交集 + GSEA → HUB ----
message("\n=== 用户 Step 5: MAMs 交集与 GSEA ===")
mams_results <- list()
for (ds in SCRNA_DS) mams_results[[ds]] <- run_macrophage_mams_intersect(ds)
mams363 <- run_macrophage_mams_intersect("GSE207363", suffix = "SepsisVsControl")

mams_compare <- bind_rows(lapply(SCRNA_DS, function(ds) {
  tb <- collect_tissue_mams_stats(ds)
  mr <- mams_results[[ds]]
  tibble(dataset = ds, tissue_mams_n = tb$n_mams, macro_mams_n = mr$n_inter,
         macro_deg_n = mr$n_deg_sig)
}))
write_report("06_巨噬细胞MAMs交集与HUB_调整报告.md", "06 巨噬细胞 MAMs 交集与 HUB 调整报告", c(
  "## 对应用户流程 Step 5",
  "巨噬细胞 DEG ∩ MAMs 基因集 → 筛核心 HUB（Sirt2 / Foxo1 等）。",
  "",
  "## 方法",
  "- MAMs 集：48 基因（sciadv MAMs）",
  "- 韦恩统计 + 交集火山图 + MAMs 分类 GSEA",
  "",
  "## 调整前后 MAMs 交集", "", fmt_tbl(as.data.frame(mams_compare)),
  "",
  "### 交集基因",
  paste(lapply(SCRNA_DS, function(ds) {
    g <- mams_results[[ds]]$inter_genes
    paste0("- **", ds, "**：", if (length(g)) paste(g, collapse = ", ") else "（无）")
  }), collapse = "\n"),
  "",
  paste0("- **GSE207363 SepsisVsControl**：",
         paste(mams363$inter_genes %||% character(0), collapse = ", "))
))

# ---- 清理冗余图片 ----
message("\n=== 清理冗余 PDF ===")
removed <- cleanup_redundant_scrna_figures()
write_report("07_冗余图片清理_调整报告.md", "07 冗余图片清理 调整报告", c(
  "## 原则",
  "保留 5 步主线必需图（UMAP/免疫/巨噬/DEG/GO-KEGG/热图/MAMs/HUB），删除全组织重复层与 ML/WGCNA/通讯等冗余图。",
  "",
  paste0("## 已删除 ", length(removed), " 个 PDF"),
  "",
  if (length(removed)) paste(head(basename(unlist(removed)), 30), collapse = "\n") else "_无_"
))

# ---- 汇总 ----
after <- collect_baseline_snapshot()
write.csv(after, file.path(ADJ_DIR, "08_补全后快照.csv"), row.names = FALSE)
write_report("08_补全路线执行汇总.md", "08 补全路线执行汇总", c(
  "## 用户 5 步流程执行状态",
  "",
  "| 步骤 | 内容 | 状态 | 报告 |",
  "|------|------|------|------|",
  "| Step 1 | UMAP/免疫/巨噬核心 | 完成 | 02_细胞图谱与巨噬核心 |",
  "| Step 2 | 巨噬 DEG 上/下调 | 完成 | 03_巨噬细胞DEG |",
  "| Step 3 | GO/KEGG 上/下调 | 完成 | 05_巨噬细胞GO_KEGG |",
  "| Step 4 | ER/线粒体巨噬热图 | 完成 | 04_巨噬细胞专题热图 |",
  "| Step 5 | MAMs 交集 + GSEA/HUB | 完成 | 06_巨噬细胞MAMs交集与HUB |",
  "",
  "## 补全前后快照", "",
  fmt_tbl(as.data.frame(baseline %>% rename(phase = layer) %>%
    left_join(after %>% select(dataset, layer, n_sig_deg, n_mams_inter) %>%
                rename(n_sig_deg_after = n_sig_deg, n_mams_inter_after = n_mams_inter),
              by = c("dataset", "layer")))),
  "",
  "## 主线",
  "**巨噬细胞 DEG → ER/Mito 热图 → GO/KEGG → MAMs 交集 → HUB（Sirt2/Foxo1）**",
  "",
  "## 未执行",
  "- 机器学习 / Nomogram（暂缓）"
))

message("\n======== 补全路线全部完成 ========")
