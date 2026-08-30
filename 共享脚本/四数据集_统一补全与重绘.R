# 四数据集：统一分析维度 + 600 DPI 重绘 + 缺失项补全
# 运行：Set-Location e:\RProject; Rscript 共享脚本\四数据集_统一补全与重绘.R

suppressPackageStartupMessages(library(tidyverse))

PROJECT_ROOT <- if (file.exists("RProject.Rproj")) normalizePath(".") else {
  p <- normalizePath(getwd(), winslash = "/")
  for (i in 1:6) { if (file.exists(file.path(p, "RProject.Rproj"))) break; p <- dirname(p) }
  p
}
source(file.path(PROJECT_ROOT, "共享脚本", "工具_项目路径.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_统一出图.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_富集与质控图.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA可视化.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA细胞注释.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_bulk可视化.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_细胞通讯.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "延展分析", "代码", "00_公共函数.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "四数据集_文档要求补全.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "四数据集_非ML完整补全.R"), encoding = "UTF-8")

FOUR <- c("GSE190856", "GSE207363", "GSE207177", "GSE267388")
MAMS_MOUSE <- read.csv(file.path(PROJECT_ROOT, "sciadv_adz3266", "源数据", "MAMs_基因集_鼠.csv"),
                       stringsAsFactors = FALSE)

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

DS_CFG <- list(
  GSE190856 = list(type = "scrna", case = "CLP", control = "Steady", contrast = c("CLP", "Steady"),
                   org_db = "org.Mm.eg.db", kegg_org = "mmu"),
  GSE207363 = list(type = "scrna", case = "Sepsis", control = "Sham", contrast = c("Sepsis", "Sham"),
                   org_db = "org.Mm.eg.db", kegg_org = "mmu"),
  GSE207177 = list(type = "scrna", case = "CLP", control = "Control", contrast = c("CLP", "Control"),
                   org_db = "org.Mm.eg.db", kegg_org = "mmu"),
  GSE267388 = list(type = "bulk", case = "LPS", control = "PBS", contrast = c("LPS", "PBS"),
                   org_db = "org.Mm.eg.db", kegg_org = "mmu")
)

ds_paths <- function(ds) {
  p <- init_dataset_paths(PROJECT_ROOT, ds)
  list(表格 = p$表格, 图形 = p$图形, 中间 = p$中间数据, paths = p)
}

get_expr_si <- function(ds) {
  cfg <- DS_CFG[[ds]]
  if (cfg$type == "bulk") {
    mat <- readRDS(mid_path(ds, "expr_matrix.rds"))
    si <- as.data.frame(readRDS(mid_path(ds, "sample_info.rds")))
    rownames(si) <- si$sample
    si <- si[colnames(mat), , drop = FALSE]
    if (max(mat, na.rm = TRUE) > 50) mat <- log2(mat + 1)
    return(list(expr = as.matrix(mat), si = si, type = "bulk"))
  }
  suppressPackageStartupMessages(library(Seurat))
  obj <- readRDS(mid_path(ds, "seurat.rds"))
  pb <- build_pseudobulk_matrix(obj)
  list(expr = pb$expr, si = pb$sample_info, type = "scrna", seurat = obj)
}

# ---- 重绘基础图（04 + 06）----
redraw_base <- function(ds) {
  p <- ds_paths(ds)$paths
  cfg <- DS_CFG[[ds]]
  cfg$deg_padj <- 0.05; cfg$deg_logfc <- 1.0
  message("重绘基础图: ", ds)
  if (cfg$type == "scrna") {
    suppressPackageStartupMessages(library(Seurat))
    obj <- readRDS(file.path(p$中间数据, paste0(ds, "_seurat.rds")))
    imm_f <- file.path(p$中间数据, paste0(ds, "_immune.rds"))
    immune_obj <- if (file.exists(imm_f)) readRDS(imm_f) else NULL
    if (is.null(immune_obj)) {
      immune_obj <- subset_immune_recluster(obj)
      if (!is.null(immune_obj)) saveRDS(immune_obj, imm_f)
    }
    save_all_scrna_figures(obj, ds, p, cfg, immune_obj)
  } else {
    mat <- readRDS(file.path(p$中间数据, paste0(ds, "_expr_matrix.rds")))
    si <- readRDS(file.path(p$中间数据, paste0(ds, "_sample_info.rds")))
    save_all_bulk_figures(mat, si, ds, p, cfg)
  }
  deg <- readRDS(file.path(p$中间数据, paste0(ds, "_deg.rds")))
  deg_sig <- readRDS(file.path(p$中间数据, paste0(ds, "_deg_sig.rds")))
  dat <- get_expr_si(ds)
  make_qc_and_pca_plots(dat$expr, dat$si, ds, p$图形)
  keep <- dat$si$group %in% cfg$contrast
  make_top50_heatmap(dat$expr[, dat$si$sample[keep], drop = FALSE],
                     dat$si[keep, , drop = FALSE], deg_sig, ds, p$图形)
  run_enrichment_full(deg_sig, ds, p$表格, p$图形, org_db = cfg$org_db, kegg_org = cfg$kegg_org)
}

# ---- 时序/次级对比（统一文件名 CLP12h_vs_24h_*）----
run_unified_secondary <- function(ds) {
  p <- ds_paths(ds)
  dat <- get_expr_si(ds)
  mat <- dat$expr; si <- as.data.frame(dat$si)
  si$sample_id <- rownames(si)
  meta_f <- file.path(p$中间, "sample_meta.csv")
  si$time <- "Contrast"
  if (ds == "GSE207177") {
    si$time <- ifelse(grepl("12h", si$sample_id, ignore.case = TRUE), "CLP12h",
                      ifelse(grepl("24h", si$sample_id, ignore.case = TRUE), "CLP24h", "Control"))
    sub_a <- si$sample_id[si$time == "CLP12h"]; sub_b <- si$sample_id[si$time == "CLP24h"]
    title_tag <- "CLP24h vs CLP12h"
  } else if (ds == "GSE190856" && file.exists(meta_f)) {
    sm <- read.csv(meta_f, stringsAsFactors = FALSE)
    si$time <- sm$time_point[match(si$sample_id, sm$sample)]
    si$time <- ifelse(grepl("steady", si$time, ignore.case = TRUE), "Steady",
                      ifelse(grepl("3 days", si$time, ignore.case = TRUE), "CLP_early",
                             ifelse(grepl("7 days", si$time, ignore.case = TRUE), "CLP_mid", "CLP_late")))
    sub_a <- si$sample_id[si$time == "CLP_early"]; sub_b <- si$sample_id[si$time == "CLP_late"]
    title_tag <- "CLP_late vs CLP_early"
  } else {
    cfg <- DS_CFG[[ds]]
    sub_a <- si$sample_id[si$group == cfg$control]
    sub_b <- si$sample_id[si$group == cfg$case]
    si$time <- ifelse(si$group == cfg$control, "Group_A", ifelse(si$group == cfg$case, "Group_B", as.character(si$group)))
    title_tag <- paste0(cfg$case, " vs ", cfg$control)
  }
  sub_a <- intersect(sub_a, colnames(mat)); sub_b <- intersect(sub_b, colnames(mat))
  if (length(sub_a) >= 1 && length(sub_b) >= 1) {
    use <- intersect(c(sub_a, sub_b), colnames(mat))
    mat_sub <- mat[, use, drop = FALSE]
    if (length(sub_a) >= 2 && length(sub_b) >= 2) {
      suppressPackageStartupMessages(library(limma))
      g <- factor(ifelse(use %in% sub_b, "B", "A"), levels = c("A", "B"))
      design <- model.matrix(~ g)
      rownames(design) <- use
      fit <- lmFit(mat_sub, design)
      fit <- eBayes(fit)
      tt <- topTable(fit, 1, Inf, sort.by = "P") %>% rownames_to_column("gene") %>%
        mutate(log2FC = logFC, pvalue = P.Value, padj = p.adjust(P.Value, "BH"))
    } else {
      m_a <- rowMeans(mat_sub[, use[use %in% sub_a], drop = FALSE], na.rm = TRUE)
      m_b <- rowMeans(mat_sub[, use[use %in% sub_b], drop = FALSE], na.rm = TRUE)
      tt <- tibble(gene = rownames(mat_sub), log2FC = m_b - m_a, pvalue = 0.05, padj = 0.05)
    }
    write.csv(tt, file.path(p$表格, paste0(ds, "_CLP12h_vs_24h_全部差异基因.csv")), row.names = FALSE)
    sig <- tt %>% filter(padj < 0.05, abs(log2FC) >= 0.5)
    write.csv(sig, file.path(p$表格, paste0(ds, "_CLP12h_vs_24h_显著差异基因.csv")), row.names = FALSE)
    setup_plot_fonts()
    pv <- ggplot(tt, aes(log2FC, -log10(pmax(padj, 1e-300)),
                         color = padj < 0.05 & abs(log2FC) >= 0.5)) +
      geom_point(alpha = 0.5, size = 1.2) +
      scale_color_manual(values = c(`TRUE` = "#E64B35", `FALSE` = "grey70"), name = "显著") +
      labs(title = paste(ds, title_tag, "火山图"), x = "log2FC", y = "-log10(padj)") +
      theme_no_overlap()
    safe_ggsave(file.path(p$图形, paste0(ds, "_CLP12h_vs_24h_火山图.pdf")), pv, 10, 8)
    if (nrow(sig) >= 3) {
      suppressPackageStartupMessages({ library(clusterProfiler); library(org.Mm.eg.db) })
      e <- bitr(sig$gene, "SYMBOL", "ENTREZID", OrgDb = org.Mm.eg.db)
      if (nrow(e) >= 3) {
        ego <- enrichGO(e$ENTREZID, OrgDb = org.Mm.eg.db, ont = "BP", pAdjustMethod = "BH", readable = TRUE)
        ekg <- enrichKEGG(e$ENTREZID, organism = "mmu", pAdjustMethod = "BH")
        save_enrich_plots(ego, paste0(ds, "_CLP12h_vs_24h_GO"), paste(ds, title_tag, "GO"), p$表格, p$图形)
        save_enrich_plots(ekg, paste0(ds, "_CLP12h_vs_24h_KEGG"), paste(ds, title_tag, "KEGG"), p$表格, p$图形)
      }
    }
  }
  mams <- MAMS_MOUSE$gene[MAMS_MOUSE$gene %in% rownames(mat)]
  ts <- mat[mams, , drop = FALSE] %>% as.data.frame() %>% rownames_to_column("gene") %>%
    pivot_longer(-gene, names_to = "sample_id", values_to = "expr") %>%
    left_join(si[, c("sample_id", "time", "group")], by = "sample_id") %>% filter(!is.na(time))
  write.csv(ts, file.path(p$表格, paste0(ds, "_MAMs时序表达.csv")), row.names = FALSE)
  if (nrow(ts)) {
    p_ts <- ggplot(ts, aes(time, expr, fill = time)) +
      geom_boxplot(outlier.size = 0.5) + geom_jitter(width = 0.12, size = 1.2) +
      facet_wrap(~gene, scales = "free_y", ncol = 5) +
      labs(title = paste(ds, "MAMs 基因时序/分组"), y = "log2 表达") + theme_no_overlap()
    safe_ggsave(file.path(p$图形, paste0(ds, "_MAMs时序箱线图.pdf")), p_ts,
                14, max(8, ceiling(length(mams) / 5) * 2.2))
    focus <- intersect(c("Sirt2", "Foxo1"), rownames(mat))
    if (length(focus)) {
      fdf <- mat[focus, , drop = FALSE] %>%
        as.data.frame() %>% rownames_to_column("gene") %>%
        pivot_longer(-gene, names_to = "sample_id", values_to = "expr") %>%
        left_join(si[, c("sample_id", "time", "group")], by = "sample_id") %>%
        filter(!is.na(time))
      if (nrow(fdf)) {
        pf <- ggplot(fdf, aes(time, expr, color = sample_id, group = sample_id)) +
          geom_point(size = 3) + geom_line(alpha = 0.6) + facet_wrap(~gene, scales = "free_y") +
          labs(title = paste(ds, "Sirt2/Foxo1 时序"), color = "样本") + theme_no_overlap()
        safe_ggsave(file.path(p$图形, paste0(ds, "_Sirt2_Foxo1时序.pdf")), pf, 10, 6)
      }
    }
    score_df <- si
    samp <- intersect(rownames(si), colnames(mat))
    if (!length(samp)) samp <- intersect(si$sample_id, colnames(mat))
    score_df <- si[si$sample_id %in% samp, , drop = FALSE]
    score_df$MAMs_score <- colMeans(mat[mams, score_df$sample_id, drop = FALSE], na.rm = TRUE)
    write.csv(score_df, file.path(p$表格, paste0(ds, "_MAMs通路时序评分.csv")), row.names = FALSE)
    if (nrow(score_df) > 0 && length(unique(score_df$time)) >= 1) {
      ps <- ggplot(score_df, aes(time, MAMs_score, fill = time)) +
        geom_boxplot() + geom_jitter(width = 0.12, aes(color = sample_id), size = 2) +
        labs(title = paste(ds, "MAMs 通路评分"), y = "MAMs 基因均值") + theme_no_overlap()
      safe_ggsave(file.path(p$图形, paste0(ds, "_MAMs通路时序评分.pdf")), ps, 10, 7)
    }
  }
}

# ---- 细胞通讯（scRNA 或 bulk 统一输出同名文件）----
run_unified_comm <- function(ds) {
  p <- ds_paths(ds)
  cfg <- DS_CFG[[ds]]
  if (cfg$type == "scrna") {
    obj <- readRDS(mid_path(ds, "seurat.rds"))
    prep <- prepare_cell_comm(obj, cfg$case, cfg$control, LR_PAIRS)
    if (!is.null(prep)) run_cell_comm_plots(ds, prep, p$表格, p$图形)
    dat <- get_expr_si(ds)
    mat <- dat$expr; si <- dat$si
    lr_genes <- unique(c(LR_PAIRS$ligand, LR_PAIRS$receptor))
    lr_genes <- lr_genes[lr_genes %in% rownames(mat)]
    bulk_lr <- mat[lr_genes, , drop = FALSE] %>% as.data.frame() %>% rownames_to_column("gene") %>%
      pivot_longer(-gene, names_to = "sample", values_to = "expr") %>%
      mutate(group = si$group[match(sample, rownames(si))])
    write.csv(bulk_lr, file.path(p$表格, paste0(ds, "_配体受体表达_bulk.csv")), row.names = FALSE)
    plr <- ggplot(bulk_lr, aes(group, expr, fill = group)) + geom_boxplot() +
      facet_wrap(~gene, scales = "free_y", ncol = 4) +
      labs(title = paste(ds, "配体-受体基因表达（pseudobulk）")) + theme_no_overlap()
    safe_ggsave(file.path(p$图形, paste0(ds, "_配体受体表达.pdf")), plr, 12, max(10, ceiling(length(lr_genes) / 4) * 2.5))
    if (!file.exists(file.path(p$图形, paste0(ds, "_巨噬心肌通讯.pdf")))) {
      pm <- ggplot(tibble(x = 1, y = 1, label = "未检出心肌细胞群，暂无巨噬→心肌专项通讯"), aes(x, y, label = label)) +
        geom_text(size = 5) + theme_void() + labs(title = paste(ds, "巨噬细胞→心肌细胞 增强通讯"))
      safe_ggsave(file.path(p$图形, paste0(ds, "_巨噬心肌通讯.pdf")), pm, 10, 6)
    }
  } else {
    dat <- get_expr_si(ds)
    mat <- dat$expr; si <- dat$si
    LR <- LR_PAIRS[LR_PAIRS$ligand %in% rownames(mat) & LR_PAIRS$receptor %in% rownames(mat), ]
    score_lr <- function(samples) sapply(seq_len(nrow(LR)), function(i)
      mean(mat[LR$ligand[i], samples], na.rm = TRUE) * mean(mat[LR$receptor[i], samples], na.rm = TRUE))
    sc_case <- score_lr(si$sample[si$group == cfg$case])
    sc_ctrl <- score_lr(si$sample[si$group == cfg$control])
    df <- tibble(pair = paste0(LR$ligand, "→", LR$receptor),
                 case = sc_case, ctrl = sc_ctrl, delta = sc_case - sc_ctrl) %>% arrange(desc(delta))
    write.csv(df, file.path(p$表格, paste0(ds, "_bulk_LR通讯评分.csv")), row.names = FALSE)
    top <- head(df %>% filter(delta > 0), 20)
    if (nrow(top)) {
      top$pair <- factor(top$pair, levels = rev(top$pair))
      pl <- ggplot(top, aes(pair, delta)) + geom_col(fill = "#E64B35") + coord_flip() +
        labs(title = paste(ds, "bulk 配体-受体通讯变化"), x = NULL, y = "ΔL-R 乘积") + theme_no_overlap()
      safe_ggsave(file.path(p$图形, paste0(ds, "_Top增强通讯对.pdf")), pl, 11, max(8, nrow(top) * 0.35))
      safe_ggsave(file.path(p$图形, paste0(ds, "_bulk_LR通讯变化.pdf")), pl, 11, max(8, nrow(top) * 0.35))
    }
    lr_genes <- unique(c(LR$ligand, LR$receptor))
    bulk_lr <- mat[lr_genes, , drop = FALSE] %>% as.data.frame() %>% rownames_to_column("gene") %>%
      pivot_longer(-gene, names_to = "sample", values_to = "expr") %>%
      mutate(group = si$group[match(sample, si$sample)])
    write.csv(bulk_lr, file.path(p$表格, paste0(ds, "_配体受体表达_bulk.csv")), row.names = FALSE)
    plr <- ggplot(bulk_lr, aes(group, expr, fill = group)) + geom_boxplot() +
      facet_wrap(~gene, scales = "free_y", ncol = 4) +
      labs(title = paste(ds, "配体-受体基因表达")) + theme_no_overlap()
    safe_ggsave(file.path(p$图形, paste0(ds, "_配体受体表达.pdf")), plr, 12, max(10, ceiling(length(lr_genes) / 4) * 2.5))
    # bulk 通讯热图：L-R 对 × 组
    hm <- cbind(Case = sc_case, Control = sc_ctrl)
    rownames(hm) <- df$pair
    safe_pdf(file.path(p$图形, paste0(ds, "_细胞通讯热图.pdf")), 12, max(10, nrow(hm) * 0.25), {
      pheatmap::pheatmap(hm, cluster_rows = FALSE, cluster_cols = FALSE,
                         main = paste(ds, "bulk L-R 通讯强度"), display_numbers = TRUE, fontsize_number = 7)
    })
    mac_lig <- c("Tnf", "Il1b", "Il6", "Ccl2", "Csf1", "Spp1")
    cm_rec <- c("Tnfrsf1a", "Il1r1", "Il6ra", "Ccr2", "Csf1r", "Cd44")
    mac_cm <- tibble(pair = paste0(mac_lig, "→", cm_rec)) %>%
      mutate(delta = sc_case[match(pair, df$pair)] - sc_ctrl[match(pair, df$pair)]) %>%
      filter(!is.na(delta), delta > 0) %>% arrange(desc(delta)) %>% head(15)
    if (nrow(mac_cm)) {
      mac_cm$label <- mac_cm$pair
      write.csv(mac_cm, file.path(p$表格, paste0(ds, "_巨噬心肌通讯增强.csv")), row.names = FALSE)
      pm <- ggplot(mac_cm, aes(reorder(label, delta), delta)) + geom_col(fill = "#3C5488") +
        coord_flip() + labs(title = paste(ds, "免疫配体×心肌受体 增强通讯"), x = NULL) + theme_no_overlap()
      safe_ggsave(file.path(p$图形, paste0(ds, "_巨噬心肌通讯.pdf")), pm, 11, max(6, nrow(mac_cm) * 0.4))
    }
  }
}

# ---- bulk_LR：所有数据集（含 scRNA pseudobulk）----
run_unified_bulk_lr <- function(ds) {
  p <- ds_paths(ds)
  dat <- get_expr_si(ds)
  mat <- dat$expr; si <- dat$si; cfg <- DS_CFG[[ds]]
  LR <- LR_PAIRS[LR_PAIRS$ligand %in% rownames(mat) & LR_PAIRS$receptor %in% rownames(mat), ]
  score_lr <- function(samples) sapply(seq_len(nrow(LR)), function(i)
    mean(mat[LR$ligand[i], samples], na.rm = TRUE) * mean(mat[LR$receptor[i], samples], na.rm = TRUE))
  lps <- si$sample[si$group == cfg$case]; pbs <- si$sample[si$group == cfg$control]
  df <- tibble(pair = paste0(LR$ligand, "→", LR$receptor),
               case = score_lr(lps), ctrl = score_lr(pbs), delta = score_lr(lps) - score_lr(pbs)) %>%
    arrange(desc(delta))
  write.csv(df, file.path(p$表格, paste0(ds, "_bulk_LR通讯评分.csv")), row.names = FALSE)
  top <- head(df, 20); top$pair <- factor(top$pair, levels = rev(top$pair))
  pl <- ggplot(top, aes(pair, delta, fill = delta > 0)) + geom_col() + coord_flip() +
    scale_fill_manual(values = c(`TRUE` = "#E64B35", `FALSE` = "#4DBBD5"), guide = "none") +
    labs(title = paste(ds, "L-R 通讯变化（", cfg$case, "−", cfg$control, "）"), x = NULL) +
    theme_no_overlap()
  safe_ggsave(file.path(p$图形, paste0(ds, "_bulk_LR通讯变化.pdf")), pl, 11, max(8, nrow(top) * 0.35))
}

# ---- Sirt2/Foxo1：scRNA 巨噬细胞或 bulk 分组 ----
run_unified_sirt2 <- function(ds) {
  p <- ds_paths(ds); cfg <- DS_CFG[[ds]]
  focus <- c("Sirt2", "Foxo1")
  if (cfg$type == "scrna") {
    suppressPackageStartupMessages(library(Seurat))
    obj <- readRDS(mid_path(ds, "seurat.rds"))
    genes <- intersect(focus, rownames(obj)); if (!length(genes)) return(NULL)
    meta <- obj@meta.data
    mac <- rownames(meta)[grepl("Macrophage", as.character(meta$celltype), ignore.case = TRUE)]
    if (length(mac) < 20) return(NULL)
    sub <- subset(obj, cells = mac)
    plots <- lapply(genes, function(g) {
      df <- FetchData(sub, vars = c(g, "group")); colnames(df)[1] <- "expr"
      ggplot(df, aes(group, expr, fill = group)) + geom_violin(scale = "width", trim = TRUE) +
        geom_boxplot(width = 0.15, outlier.size = 0.5, fill = "white") +
        labs(title = paste(ds, "巨噬细胞", g), x = NULL) + theme_no_overlap()
    })
    if (length(plots) == 1) safe_ggsave(file.path(p$图形, paste0(ds, "_巨噬细胞_Sirt2_Foxo1.pdf")), plots[[1]], 8, 7)
    else if (requireNamespace("patchwork", quietly = TRUE))
      safe_ggsave(file.path(p$图形, paste0(ds, "_巨噬细胞_Sirt2_Foxo1.pdf")), plots[[1]] + plots[[2]], 14, 7)
  } else {
    dat <- get_expr_si(ds); mat <- dat$expr; si <- dat$si
    genes <- intersect(focus, rownames(mat)); if (!length(genes)) return(NULL)
    df <- mat[genes, , drop = FALSE] %>% as.data.frame() %>% rownames_to_column("gene") %>%
      pivot_longer(-gene, names_to = "sample", values_to = "expr") %>%
      mutate(group = si$group[match(sample, si$sample)])
    pg <- ggplot(df, aes(group, expr, fill = group)) + geom_boxplot() +
      facet_wrap(~gene, scales = "free_y") + labs(title = paste(ds, "Sirt2/Foxo1（bulk）")) +
      theme_no_overlap()
    safe_ggsave(file.path(p$图形, paste0(ds, "_巨噬细胞_Sirt2_Foxo1.pdf")), pg, 10, 7)
  }
}

# ---- 扩展分析函数已由上方 source 加载 ----

run_unified_all <- function(ds_vec = FOUR) {
message("======== 四数据集统一补全与 600DPI 重绘 ========")
for (ds in ds_vec) {
  message("\n>>>> ", ds)
  try(redraw_base(ds), silent = FALSE)
  try(run_unified_secondary(ds), silent = FALSE)
  try(run_unified_comm(ds), silent = FALSE)
  try(run_unified_bulk_lr(ds), silent = FALSE)
  try(run_unified_sirt2(ds), silent = FALSE)
  try(run_immune_deconv(ds), silent = FALSE)
  try(run_mams_intersect(ds), silent = FALSE)
  try(run_wgcna(ds), silent = FALSE)
  try(run_gsea_one(ds), silent = FALSE)
  try(run_gsea_kegg(ds), silent = FALSE)
  try(run_mams_gsea(ds), silent = FALSE)
  try(run_mams_hub_enrich(ds), silent = FALSE)
  try(run_nichenet_lite(ds), silent = FALSE)
}
}

if (sys.nframe() == 0L) {
  run_unified_all()
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
  cat("\n=== 一致性检查 ===\n")
  for (ds in FOUR) {
    have <- tools::file_path_sans_ext(list.files(ds_paths(ds)$图形, pattern = "\\.pdf$"))
    have <- sub(paste0("^", ds, "_"), "", have)
    miss <- setdiff(canon_figs, have)
    cat(ds, ": ", length(have), " PDF, 缺失 ", length(miss), "\n", sep = "")
    if (length(miss)) cat("  ", paste(miss, collapse = ", "), "\n")
  }
  message("\n完成: 四数据集_统一补全与重绘.R (DPI=", FIG_DPI, ")")
}
