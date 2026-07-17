# 按《生物信息学分析.docx》补全四数据集缺失分析
# 输出写入各数据集 结果/表格 与 结果/图形

suppressPackageStartupMessages({
  library(tidyverse)
  library(ggplot2)
})

PROJECT_ROOT <- if (file.exists("RProject.Rproj")) normalizePath(".") else {
  p <- normalizePath(getwd(), winslash = "/")
  for (i in 1:6) { if (file.exists(file.path(p, "RProject.Rproj"))) break; p <- dirname(p) }
  p
}
source(file.path(PROJECT_ROOT, "共享脚本", "工具_富集与质控图.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA可视化.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_统一出图.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA细胞注释.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_细胞通讯.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "延展分析", "代码", "00_公共函数.R"), encoding = "UTF-8")

MAMS_MOUSE <- read.csv(file.path(PROJECT_ROOT, "sciadv_adz3266", "源数据", "MAMs_基因集_鼠.csv"),
                       stringsAsFactors = FALSE)
FOUR <- c("GSE190856", "GSE207363", "GSE207177", "GSE267388")

LR_PAIRS <- tribble(
  ~ligand, ~receptor,
  "Tnf", "Tnfrsf1a", "Tnf", "Tnfrsf1b", "Il1b", "Il1r1", "Il1b", "Il1rap",
  "Il6", "Il6ra", "Il6", "Il6st", "Ccl2", "Ccr2", "Ccl3", "Ccr1", "Ccl4", "Ccr5",
  "Ccl5", "Ccr5", "Cxcl2", "Cxcr2", "Cxcl1", "Cxcr2", "Cxcl10", "Cxcr3",
  "Csf1", "Csf1r", "Csf2", "Csf2ra", "Csf3", "Csf3r", "Tgfb1", "Tgfbr1", "Tgfb1", "Tgfbr2",
  "Spp1", "Cd44", "Spp1", "Itgav", "Icam1", "Itgal", "Icam1", "Itgb2",
  "Apoe", "Trem2", "Apoe", "Ldlr", "Vegfa", "Flt1", "Vegfa", "Kdr",
  "Pdgfb", "Pdgfrb", "Angpt1", "Tek", "Il10", "Il10ra", "Ifng", "Ifngr1",
  "Cxcl12", "Cxcr4", "Ccl7", "Ccr2", "Il18", "Il18r1", "Nampt", "Insr"
)

ds_paths <- function(ds) {
  list(
    表格 = file.path(PROJECT_ROOT, ds, "结果", "表格"),
    图形 = file.path(PROJECT_ROOT, ds, "结果", "图形"),
    中间 = file.path(PROJECT_ROOT, ds, "源数据", "中间文件")
  )
}

get_seurat_data_mat <- function(obj) {
  DefaultAssay(obj) <- "RNA"
  if ("JoinLayers" %in% ls("package:Seurat")) {
    obj <- tryCatch(JoinLayers(obj, assay = "RNA"), error = function(e) obj)
  }
  tryCatch(
    as.matrix(GetAssayData(obj, assay = "RNA", layer = "data")),
    error = function(e) as.matrix(LayerData(obj, assay = "RNA", layer = "data"))
  )
}

get_expr_sample <- function(ds) {
  info <- DATASETS[DATASETS$id == ds, ]
  if (info$type == "bulk") {
    mat <- readRDS(mid_path(ds, "expr_matrix.rds"))
    si <- as.data.frame(readRDS(mid_path(ds, "sample_info.rds")))
    rownames(si) <- si$sample
    si <- si[colnames(mat), , drop = FALSE]
    if (max(mat, na.rm = TRUE) > 50) mat <- log2(mat + 1)
    return(list(expr = as.matrix(mat), sample_info = si, type = "bulk"))
  }
  suppressPackageStartupMessages(library(Seurat))
  obj <- readRDS(mid_path(ds, "seurat.rds"))
  pb <- build_pseudobulk_matrix(obj)
  list(expr = pb$expr, sample_info = pb$sample_info, type = "scrna", seurat = obj)
}

# ---- 1. CIBERSORT 式免疫浸润（immunedeconv::mcp_counter，小鼠兼容）----
run_immune_deconv <- function(ds) {
  p <- ds_paths(ds)
  dat <- get_expr_sample(ds)
  mat <- dat$expr
  # immunedeconv 需要 gene × sample
  imm <- NULL
  if (requireNamespace("immunedeconv", quietly = TRUE)) {
    imm <- tryCatch(
      immunedeconv::deconvolute(mat, method = "mcp_counter", tumor = FALSE),
      error = function(e) { message("immunedeconv 失败 ", ds, ": ", conditionMessage(e)); NULL }
    )
  }
  if (is.null(imm)) {
    # 兜底：IMMUNE_LINEAGE marker 平均表达
    score_one <- function(vec, genes) {
      g <- genes[genes %in% names(vec)]; if (!length(g)) return(0); mean(vec[g], na.rm = TRUE)
    }
    rows <- lapply(colnames(mat), function(s) {
      vec <- mat[, s]; names(vec) <- rownames(mat)
      sc <- vapply(IMMUNE_LINEAGE, score_one, numeric(1), vec = vec)
      tibble(sample = s, cell_type = names(sc), fraction = sc / sum(sc))
    })
    imm <- bind_rows(rows) %>% pivot_wider(names_from = cell_type, values_from = fraction)
    imm$method <- "marker_fallback"
  } else {
    imm$method <- "mcp_counter"
  }
  write.csv(imm, file.path(p$表格, paste0(ds, "_CIBERSORT免疫浸润.csv")), row.names = FALSE)
  # 堆叠柱图
  ext_setup_font()
  long <- imm %>% pivot_longer(-c(sample, method), names_to = "cell_type", values_to = "fraction")
  si <- dat$sample_info; long$group <- si$group[match(long$sample, rownames(si))]
  p_bar <- ggplot(long, aes(sample, fraction, fill = cell_type)) +
    geom_col(position = "fill") +
    facet_wrap(~group, scales = "free_x", nrow = 1) +
    scale_y_continuous(labels = scales::percent_format()) +
    theme(axis.text.x = element_text(angle = 45, hjust = 1, size = 7)) +
    labs(title = paste(ds, "免疫细胞浸润比例（CIBERSORT/mcp_counter）"),
         x = NULL, y = "比例", fill = "细胞类型")
  safe_ggsave(file.path(p$图形, paste0(ds, "_CIBERSORT免疫浸润.pdf")), p_bar, width = 12, height = 7)
  message("CIBERSORT: ", ds)
}

# ---- 2. MAMs ∩ DEG + 火山图 ----
run_mams_intersect <- function(ds) {
  p <- ds_paths(ds)
  deg <- read.csv(file.path(p$表格, paste0(ds, "_显著差异基因.csv")), stringsAsFactors = FALSE)
  inter <- deg %>% filter(gene %in% MAMS_MOUSE$gene) %>%
    left_join(MAMS_MOUSE, by = "gene")
  write.csv(inter, file.path(p$表格, paste0(ds, "_MAMs交集基因.csv")), row.names = FALSE)
  deg_all <- readRDS(mid_path(ds, "deg.rds"))
  deg_all$is_mams <- deg_all$gene %in% MAMS_MOUSE$gene
  setup_plot_fonts()
  fam <- ""  # 避免 showtext 与 ggrepel 组合导致 invalid font type
  p <- ggplot(deg_all, aes(log2FC, -log10(pmax(padj, 1e-300)), color = is_mams)) +
    geom_point(alpha = 0.6, size = 1.2) +
    scale_color_manual(values = c(`TRUE` = "#E64B35", `FALSE` = "grey70"),
                       labels = c(`TRUE` = "MAMs相关", `FALSE` = "其他"), name = NULL) +
    labs(title = paste(ds, "MAMs 交集火山图"), x = "log2FC", y = "-log10(padj)")
  if (requireNamespace("ggrepel", quietly = TRUE)) {
    lab <- deg_all %>% filter(is_mams, padj < 0.05) %>% arrange(padj) %>% head(15)
    if (nrow(lab)) {
      has_st <- "showtext" %in% loadedNamespaces()
      if (has_st) try(showtext::showtext_auto(FALSE), silent = TRUE)
      p <- p + ggrepel::geom_text_repel(data = lab, aes(label = gene),
        size = 3.2, max.overlaps = 20, show.legend = FALSE)
      if (has_st) try(showtext::showtext_auto(TRUE), silent = TRUE)
    }
  }
  if (requireNamespace("Cairo", quietly = TRUE)) {
    safe_ggsave(file.path(p$图形, paste0(ds, "_MAMs交集火山图.pdf")), p, width = 10, height = 8)
  } else {
    safe_pdf(file.path(p$图形, paste0(ds, "_MAMs交集火山图.pdf")), 10, 8, print(p))
  }
  message("MAMs交集: ", ds, " (", nrow(inter), " 基因)")
}

# ---- 3. WGCNA（样本级；轻量实现，避免 Windows 上 blockwiseModules 崩溃）----
run_wgcna <- function(ds) {
  tryCatch({
  p <- ds_paths(ds)
  dat <- get_expr_sample(ds)
  mat <- dat$expr; si <- dat$sample_info
  info <- DATASETS[DATASETS$id == ds, ]
  vars <- apply(mat, 1, var)
  sel <- names(sort(vars, decreasing = TRUE))[1:min(2000, sum(vars > 0))]
  datExpr <- t(mat[sel, , drop = FALSE])
  if (nrow(datExpr) < 4) { message("样本过少，跳过 WGCNA: ", ds); return(NULL) }
  trait <- as.numeric(factor(si$group, levels = c(info$control, info$case))) - 1
  trait <- trait[match(rownames(datExpr), rownames(si))]
  gene_cor <- apply(datExpr, 2, function(x) stats::cor(x, trait, use = "pairwise.complete.obs"))
  gene_cor[is.na(gene_cor)] <- 0
  top_n <- min(1200, ncol(datExpr))
  use_genes <- names(sort(abs(gene_cor), decreasing = TRUE))[seq_len(top_n)]
  hc <- hclust(dist(t(datExpr[, use_genes, drop = FALSE])), method = "average")
  k <- min(8, max(3, nrow(datExpr) - 1))
  moduleLabels <- cutree(hc, k = k)
  moduleColors <- paste0("M", moduleLabels)
  ME_list <- lapply(split(use_genes, moduleColors), function(g) rowMeans(datExpr[, g, drop = FALSE]))
  MEs <- do.call(cbind, ME_list)
  colnames(MEs) <- paste0("ME", names(ME_list))
  corME <- matrix(stats::cor(MEs, trait, use = "pairwise.complete.obs"), ncol = 1,
                  dimnames = list(colnames(MEs), info$case))
  mt <- data.frame(module = rownames(corME), cor_case = corME[, 1])
  mt <- mt[order(-abs(mt$cor_case)), ]
  write.csv(mt, file.path(p$表格, paste0(ds, "_WGCNA模块表型相关.csv")), row.names = FALSE)
  ext_setup_font()
  if (requireNamespace("pheatmap", quietly = TRUE)) {
    safe_pdf(file.path(p$图形, paste0(ds, "_WGCNA模块表型相关.pdf")), width = 7, height = max(5, nrow(mt) * 0.45), {
      pheatmap::pheatmap(corME, cluster_rows = FALSE, cluster_cols = FALSE,
                         color = colorRampPalette(c("#4DBBD5", "white", "#E64B35"))(50),
                         main = paste(ds, "WGCNA 模块-表型"))
    })
  }
  top_mod <- mt$module[1]
  mod_tag <- sub("^ME", "", top_mod)
  mod_genes <- use_genes[moduleColors == mod_tag]
  kME <- vapply(mod_genes, function(g) stats::cor(datExpr[, g], MEs[, top_mod], use = "p"), numeric(1))
  hub <- names(sort(abs(kME), decreasing = TRUE))[seq_len(min(30, length(kME)))]
  hub_df <- tibble(gene = hub, module = mod_tag, kME = kME[hub])
  write.csv(hub_df, file.path(p$表格, paste0(ds, "_WGCNA_Hub基因.csv")), row.names = FALSE)
  message("WGCNA: ", ds, " (hub n=", nrow(hub_df), ", Sirt2=", "Sirt2" %in% hub,
          ", Foxo1=", "Foxo1" %in% hub, ")")
  }, error = function(e) message("WGCNA 失败 ", ds, ": ", conditionMessage(e)))
}

# ---- 4. GSEA（扩展至四数据集）----
run_gsea_one <- function(ds) {
  p <- ds_paths(ds)
  deg <- load_deg(ds); if (is.null(deg)) return(invisible(NULL))
  suppressPackageStartupMessages(library(clusterProfiler))
  suppressPackageStartupMessages(library(org.Mm.eg.db))
  ranks <- deg_rank_vector(deg)
  ego <- tryCatch(gseGO(geneList = ranks, OrgDb = org.Mm.eg.db, ont = "BP", keyType = "SYMBOL",
                        minGSSize = 10, maxGSSize = 500, pvalueCutoff = 0.25, eps = 0, verbose = FALSE),
                  error = function(e) NULL)
  if (!is.null(ego) && nrow(as.data.frame(ego)) > 0) {
    write.csv(as.data.frame(ego), file.path(p$表格, paste0(ds, "_GSEA_GO.csv")), row.names = FALSE)
    ext_setup_font()
    p_dot <- clusterProfiler::dotplot(ego, showCategory = 15, label_format = enrich_full_labels) +
      ggtitle(paste(ds, "GSEA GO-BP")) +
      scale_y_discrete(labels = enrich_full_labels)
    sz <- enrich_plot_size(15, head(as.data.frame(ego)$Description, 15))
    safe_ggsave(file.path(p$图形, paste0(ds, "_GSEA_GO.pdf")), p_dot, sz$width, sz$height)
  }
  message("GSEA: ", ds)
}

# ---- 5. GSE207177 时间序列（CLP12h vs CLP24h）----
run_timeseries_207177 <- function() {
  ds <- "GSE207177"; p <- ds_paths(ds)
  suppressPackageStartupMessages(library(Seurat))
  obj <- readRDS(mid_path(ds, "seurat.rds"))
  pb <- build_pseudobulk_matrix(obj)
  si <- as.data.frame(pb$sample_info)
  si$sample_id <- rownames(si)
  si$time <- ifelse(grepl("12h", si$sample_id, ignore.case = TRUE), "CLP12h",
                    ifelse(grepl("24h", si$sample_id, ignore.case = TRUE), "CLP24h", "Control"))
  mams_genes <- MAMS_MOUSE$gene[MAMS_MOUSE$gene %in% rownames(pb$expr)]
  if (!length(mams_genes)) return(invisible(NULL))
  ts <- pb$expr[mams_genes, , drop = FALSE] %>%
    as.data.frame() %>% rownames_to_column("gene") %>%
    pivot_longer(-gene, names_to = "sample_id", values_to = "expr") %>%
    left_join(si[, c("sample_id", "time", "group")], by = "sample_id")
  ts <- ts %>% filter(!is.na(time))
  write.csv(ts, file.path(p$表格, paste0(ds, "_MAMs时序表达.csv")), row.names = FALSE)
  ext_setup_font()
  ts_clp <- ts %>% filter(time %in% c("CLP12h", "CLP24h"))
  if (nrow(ts_clp) > 0) {
    p_ts <- ggplot(ts_clp, aes(time, expr, fill = time)) +
      geom_boxplot(outlier.size = 0.5) + geom_jitter(width = 0.12, size = 1) +
      facet_wrap(~gene, scales = "free_y", ncol = 5) +
      labs(title = paste(ds, "MAMs 基因 CLP 时序（12h vs 24h）"), y = "log2CPM")
    safe_ggsave(file.path(p$图形, paste0(ds, "_MAMs时序箱线图.pdf")), p_ts,
                width = 14, height = max(8, ceiling(length(mams_genes) / 5) * 2.2))
  }
  focus <- intersect(c("Sirt2", "Foxo1"), rownames(pb$expr))
  if (length(focus)) {
    fdf <- pb$expr[focus, , drop = FALSE] %>%
      as.data.frame() %>% rownames_to_column("gene") %>%
      pivot_longer(-gene, names_to = "sample_id", values_to = "expr") %>%
      left_join(si[, c("sample_id", "time", "group")], by = "sample_id") %>%
      filter(!is.na(time))
    if (nrow(fdf)) {
      p_f <- ggplot(fdf, aes(time, expr, color = sample_id, group = sample_id)) +
        geom_point(size = 3) + geom_line(alpha = 0.6) + facet_wrap(~gene, scales = "free_y") +
        labs(title = paste(ds, "Sirt2/Foxo1 时序趋势"), color = "样本")
      safe_ggsave(file.path(p$图形, paste0(ds, "_Sirt2_Foxo1时序.pdf")), p_f, width = 10, height = 6)
    }
  }
  message("时序分析: GSE207177")
}

# ---- 6. 细胞通讯（scRNA 四数据集 + bulk GSE267388 配体-受体表达）----
run_cell_comm <- function(ds) {
  p <- ds_paths(ds)
  info <- DATASETS[DATASETS$id == ds, ]
  LR <- LR_PAIRS
  if (info$type == "scrna") {
    suppressPackageStartupMessages(library(Seurat))
    obj <- readRDS(mid_path(ds, "seurat.rds"))
    prep <- prepare_cell_comm(obj, info$case, info$control, LR_PAIRS)
    if (!is.null(prep)) {
      run_cell_comm_plots(ds, prep, p$表格, p$图形)
      comm_df <- tibble(group = c(info$control, info$case),
                        comm_score = c(sum(comm_matrix_from_prep(prep, info$control)),
                                       sum(comm_matrix_from_prep(prep, info$case))))
      write.csv(comm_df, file.path(p$表格, paste0(ds, "_细胞通讯评分.csv")), row.names = FALSE)
    }
  } else {
    mat <- readRDS(mid_path(ds, "expr_matrix.rds"))
    if (max(mat, na.rm = TRUE) > 50) mat <- log2(mat + 1)
    lr_genes <- unique(c(LR$ligand, LR$receptor))
    lr_genes <- lr_genes[lr_genes %in% rownames(mat)]
    si <- readRDS(mid_path(ds, "sample_info.rds"))
    bulk_lr <- mat[lr_genes, , drop = FALSE] %>% as.data.frame() %>%
      rownames_to_column("gene") %>% pivot_longer(-gene, names_to = "sample", values_to = "expr") %>%
      mutate(group = si$group[match(sample, si$sample)])
    write.csv(bulk_lr, file.path(p$表格, paste0(ds, "_配体受体表达_bulk.csv")), row.names = FALSE)
    ext_setup_font()
    p_lr <- ggplot(bulk_lr, aes(group, expr, fill = group)) + geom_boxplot() +
      facet_wrap(~gene, scales = "free_y", ncol = 4) +
      labs(title = paste(ds, "bulk 配体-受体基因表达（CellPhoneDB 前置）"))
    safe_ggsave(file.path(p$图形, paste0(ds, "_配体受体表达.pdf")), p_lr, width = 12, height = max(10, ceiling(length(lr_genes) / 4) * 2.5))
  }
  message("细胞通讯: ", ds)
}

run_doc_completion_all <- function(ds_vec = FOUR) {
for (ds in ds_vec) {
  message("\n======== ", ds, " ========")
  try(run_immune_deconv(ds), silent = FALSE)
  try(run_mams_intersect(ds), silent = FALSE)
  try(run_wgcna(ds), silent = FALSE)
  try(run_gsea_one(ds), silent = FALSE)
  try(run_cell_comm(ds), silent = FALSE)
}
try(run_timeseries_207177(), silent = FALSE)
}
if (sys.nframe() == 0L) {
  run_doc_completion_all()
  message("\n完成: 四数据集_文档要求补全.R")
}
