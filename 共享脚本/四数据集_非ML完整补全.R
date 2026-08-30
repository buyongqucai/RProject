# 按《生物信息学分析.docx》补全非 ML/DL 分析（细胞通讯热图、MAMs GSEA、Hub 富集、时序 DEG 等）
# 依赖各数据集 源数据/中间文件/*_seurat.rds 或 bulk expr_matrix.rds；缺失时请先运行各数据集 运行全部分析.R

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
source(file.path(PROJECT_ROOT, "共享脚本", "工具_细胞通讯.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "延展分析", "代码", "00_公共函数.R"), encoding = "UTF-8")

MAMS_MOUSE <- read.csv(file.path(PROJECT_ROOT, "sciadv_adz3266", "源数据", "MAMs_基因集_鼠.csv"),
                       stringsAsFactors = FALSE)
FOUR <- c("GSE190856", "GSE207363", "GSE207177", "GSE267388")
SCRNA <- c("GSE190856", "GSE207363", "GSE207177")

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

# curated 配体-受体（免疫→心肌串扰；小鼠）
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

# Hub 基因上游配体（NicheNet 简化版；文献 curated）
HUB_LIGAND_TARGET <- tribble(
  ~ligand, ~target,
  "Csf1", "Csf1r", "Il1b", "Sirt2", "Tnf", "Foxo1", "Ifng", "Sirt2",
  "Il6", "Foxo1", "Tgfb1", "Mfn2", "Tgfb1", "Opa1", "Ccl2", "Ccr2",
  "Spp1", "Cd44", "Vegfa", "Kdr", "Cxcl10", "Cxcr3", "Il18", "Il18r1"
)

nes_barplot <- function(df, title, out_path) {
  if (is.null(df) || nrow(df) == 0) return(invisible(NULL))
  top <- rbind(head(df[order(-df$NES), ], 12), head(df[order(df$NES), ], 12))
  top <- top[!duplicated(top$ID), ]
  p <- ggplot(top, aes(reorder(Description, NES), NES, fill = NES > 0)) +
    geom_col() + coord_flip() +
    scale_fill_manual(values = c(`TRUE` = "#E64B35", `FALSE` = "#4DBBD5"),
                      labels = c(`TRUE` = "激活", `FALSE` = "抑制"), name = NULL) +
    theme_bw(base_size = 11) + theme(axis.text.y = element_text(size = 9)) +
    scale_y_discrete(labels = function(x) as.character(x)) +
    labs(title = title, x = NULL, y = "NES")
  safe_ggsave(out_path, p, width = max(12, max(nchar(top$Description)) * 0.15), height = max(9, nrow(top) * 0.45))
}

ora_enrich_save <- function(genes, ds, prefix, title_base) {
  if (length(genes) < 3) return(invisible(NULL))
  suppressPackageStartupMessages({ library(clusterProfiler); library(org.Mm.eg.db) })
  p <- ds_paths(ds)
  e <- suppressMessages(tryCatch(
    bitr(unique(genes), "SYMBOL", "ENTREZID", OrgDb = org.Mm.eg.db), error = function(er) NULL))
  if (is.null(e) || nrow(e) < 3) return(invisible(NULL))
  ego <- tryCatch(enrichGO(e$ENTREZID, OrgDb = org.Mm.eg.db, ont = "BP", pAdjustMethod = "BH",
                           pvalueCutoff = 0.05, readable = TRUE), error = function(er) NULL)
  save_enrich_plots(ego, paste0(ds, "_", prefix, "GO"), paste(ds, title_base, "GO-BP"), p$表格, p$图形)
  ekegg <- tryCatch(enrichKEGG(e$ENTREZID, organism = "mmu", pAdjustMethod = "BH",
                               pvalueCutoff = 0.05), error = function(er) NULL)
  save_enrich_plots(ekegg, paste0(ds, "_", prefix, "KEGG"), paste(ds, title_base, "KEGG"), p$表格, p$图形)
}

# ---- 1. scRNA 细胞通讯热图 + Top L-R（调用共享工具）----
run_cell_comm_heatmap <- function(ds) {
  info <- DATASETS[DATASETS$id == ds, ]
  if (info$type != "scrna") return(invisible(NULL))
  seurat_f <- mid_path(ds, "seurat.rds")
  if (!file.exists(seurat_f)) { message("跳过细胞通讯热图（无 seurat）: ", ds); return(NULL) }
  p <- ds_paths(ds)
  suppressPackageStartupMessages(library(Seurat))
  obj <- readRDS(seurat_f)
  prep <- prepare_cell_comm(obj, info$case, info$control, LR_PAIRS)
  if (is.null(prep)) { message("细胞通讯准备失败: ", ds); return(NULL) }
  run_cell_comm_plots(ds, prep, p$表格, p$图形)
  message("细胞通讯热图: ", ds)
}

# ---- 2. GSEA KEGG ----
run_gsea_kegg <- function(ds) {
  deg <- load_deg(ds); if (is.null(deg)) return(invisible(NULL))
  p <- ds_paths(ds)
  suppressPackageStartupMessages({ library(clusterProfiler); library(org.Mm.eg.db) })
  ranks_sym <- deg_rank_vector(deg)
  map <- suppressMessages(bitr(names(ranks_sym), "SYMBOL", "ENTREZID", OrgDb = org.Mm.eg.db))
  map <- map[!duplicated(map$SYMBOL), ]
  ranks_ent <- ranks_sym[map$SYMBOL]; names(ranks_ent) <- map$ENTREZID
  ranks_ent <- sort(ranks_ent[!is.na(names(ranks_ent))], decreasing = TRUE)
  if (length(ranks_ent) < 100) return(invisible(NULL))
  set.seed(42)
  ekegg <- tryCatch(gseKEGG(geneList = ranks_ent, organism = "mmu",
                            minGSSize = 10, maxGSSize = 500, pvalueCutoff = 0.25, eps = 0, verbose = FALSE),
                    error = function(e) NULL)
  if (!is.null(ekegg) && nrow(as.data.frame(ekegg)) > 0) {
    write.csv(as.data.frame(ekegg), file.path(p$表格, paste0(ds, "_GSEA_KEGG.csv")), row.names = FALSE)
    nes_barplot(as.data.frame(ekegg), paste0(ds, " GSEA KEGG（NES）"),
                file.path(p$图形, paste0(ds, "_GSEA_KEGG.pdf")))
    message("GSEA KEGG: ", ds)
  }
}

# ---- 3. MAMs 分类基因集 GSEA ----
run_mams_gsea <- function(ds) {
  deg <- load_deg(ds); if (is.null(deg)) return(invisible(NULL))
  p <- ds_paths(ds)
  ranks <- deg_rank_vector(deg)
  gs_list <- split(MAMS_MOUSE$gene, MAMS_MOUSE$category)
  gs_list$inflammasome <- c("Nlrp3", "Casp1", "Casp4", "Gsdmd", "Il1b", "Il18", "Pycard", "Txnip")
  gs_list$mtDNA_release <- c("Tlr9", "Tlr4", "Myd88", "Irf7", "Ifnb1", "Sting1", "Tbk1", "Irf3")
  term2gene <- bind_rows(lapply(names(gs_list), function(nm) {
    tibble(gs_name = nm, gene_name = unique(gs_list[[nm]]))
  })) %>% filter(gene_name %in% names(ranks))
  if (nrow(term2gene) < 10) return(invisible(NULL))
  suppressPackageStartupMessages(library(clusterProfiler))
  set.seed(42)
  fg <- tryCatch(
    GSEA(ranks, TERM2GENE = term2gene, minGSSize = 5, maxGSSize = 500,
         pvalueCutoff = 0.25, verbose = FALSE),
    error = function(e) NULL)
  if (is.null(fg) || nrow(as.data.frame(fg)) == 0) return(invisible(NULL))
  df <- as.data.frame(fg)
  write.csv(df, file.path(p$表格, paste0(ds, "_MAMs通路GSEA.csv")), row.names = FALSE)
  nes_barplot(df, paste0(ds, " MAMs/炎症/mtDNA GSEA"), file.path(p$图形, paste0(ds, "_MAMs通路GSEA.pdf")))
  message("MAMs GSEA: ", ds)
}

# ---- 4. MAMs 交集 & WGCNA Hub ORA ----
run_mams_hub_enrich <- function(ds) {
  p <- ds_paths(ds)
  mams_f <- file.path(p$表格, paste0(ds, "_MAMs交集基因.csv"))
  if (file.exists(mams_f)) {
    mams <- read.csv(mams_f, stringsAsFactors = FALSE)$gene
    ora_enrich_save(unique(mams), ds, "MAMs交集", "MAMs交集基因")
  }
  hub_f <- file.path(p$表格, paste0(ds, "_WGCNA_Hub基因.csv"))
  if (file.exists(hub_f)) {
    hub <- read.csv(hub_f, stringsAsFactors = FALSE)$gene
    ora_enrich_save(unique(hub), ds, "WGCNA_Hub", "WGCNA Hub 模块")
  }
}

# ---- 5. 巨噬细胞 Sirt2/Foxo1 表达 ----
run_macro_sirt2_foxo1 <- function(ds) {
  seurat_f <- mid_path(ds, "seurat.rds")
  if (!file.exists(seurat_f)) return(invisible(NULL))
  focus <- c("Sirt2", "Foxo1")
  suppressPackageStartupMessages(library(Seurat))
  obj <- readRDS(seurat_f)
  genes <- intersect(focus, rownames(obj))
  if (!length(genes)) return(invisible(NULL))
  meta <- obj@meta.data
  mac_cells <- rownames(meta)[grepl("Macrophage", as.character(meta$celltype), ignore.case = TRUE)]
  if (length(mac_cells) < 20) return(invisible(NULL))
  sub <- subset(obj, cells = mac_cells)
  p <- ds_paths(ds)
  ext_setup_font()
  plots <- lapply(genes, function(g) {
    df <- FetchData(sub, vars = c(g, "group"))
    colnames(df)[1] <- "expr"
    ggplot(df, aes(group, expr, fill = group)) + geom_violin(scale = "width", trim = TRUE) +
      geom_boxplot(width = 0.15, outlier.size = 0.5, fill = "white") +
      theme_bw() + labs(title = paste(ds, "巨噬细胞", g), x = NULL, y = "表达")
  })
  if (length(plots) == 1) {
    safe_ggsave(file.path(p$图形, paste0(ds, "_巨噬细胞_Sirt2_Foxo1.pdf")), plots[[1]], width = 8, height = 7)
  } else {
    suppressPackageStartupMessages(library(patchwork))
    safe_ggsave(file.path(p$图形, paste0(ds, "_巨噬细胞_Sirt2_Foxo1.pdf")),
           plots[[1]] + plots[[2]], width = 14, height = 7)
  }
  message("巨噬细胞 Sirt2/Foxo1: ", ds)
}

# ---- 6. NicheNet 简化：Hub 配体-靶标网络 ----
run_nichenet_lite <- function(ds) {
  p <- ds_paths(ds)
  hub <- character(0)
  hub_f <- file.path(p$表格, paste0(ds, "_WGCNA_Hub基因.csv"))
  if (file.exists(hub_f)) hub <- c(hub, read.csv(hub_f)$gene)
  mams_f <- file.path(p$表格, paste0(ds, "_MAMs交集基因.csv"))
  if (file.exists(mams_f)) hub <- c(hub, read.csv(mams_f)$gene)
  hub <- unique(hub)
  if (!length(hub)) return(invisible(NULL))
  edges <- HUB_LIGAND_TARGET %>% filter(target %in% hub)
  if (!nrow(edges)) edges <- HUB_LIGAND_TARGET %>% filter(target %in% c("Sirt2", "Foxo1", "Mfn2", "Opa1"))
  write.csv(edges, file.path(p$表格, paste0(ds, "_Hub配体靶标网络.csv")), row.names = FALSE)
  ext_setup_font()
  edges$edge <- paste0(edges$ligand, " → ", edges$target)
  pg <- ggplot(edges, aes(reorder(edge, target), 1, fill = ligand)) +
    geom_tile() + coord_flip() + theme_bw() +
    theme(axis.text.y = element_text(size = 9), axis.text.x = element_blank(), axis.ticks.x = element_blank()) +
    labs(title = paste0(ds, " Hub 基因配体-靶标（NicheNet 简化）"), x = NULL, y = NULL, fill = "配体")
  safe_ggsave(file.path(p$图形, paste0(ds, "_Hub配体靶标网络.pdf")), pg, width = 11, height = max(6, nrow(edges) * 0.4))
  message("NicheNet 简化: ", ds)
}

# ---- 7. GSE207177 CLP12h vs CLP24h 时序 DEG ----
run_timeseries_deg <- function() {
  ds <- "GSE207177"; p <- ds_paths(ds)
  seurat_f <- mid_path(ds, "seurat.rds")
  if (!file.exists(seurat_f)) { message("跳过时序 DEG（无 seurat）"); return(NULL) }
  suppressPackageStartupMessages({ library(Seurat); library(edgeR); library(limma) })
  obj <- readRDS(seurat_f)
  pb <- build_pseudobulk_matrix(obj)
  si <- pb$sample_info
  si$time <- ifelse(grepl("12h", si$sample), "CLP12h",
                    ifelse(grepl("24h", si$sample), "CLP24h", "Control"))
  si <- si[si$time %in% c("CLP12h", "CLP24h"), , drop = FALSE]
  if (nrow(si) < 3) { message("CLP12h/24h 样本不足"); return(NULL) }
  mat <- pb$expr[, rownames(si), drop = FALSE]
  design <- model.matrix(~ 0 + si$time)
  colnames(design) <- levels(factor(si$time))
  fit <- lmFit(mat, design)
  cont <- makeContrasts(CLP24h_vs_12h = CLP24h - CLP12h, levels = design)
  fit2 <- contrasts.fit(fit, cont) %>% eBayes()
  tt <- topTable(fit2, coef = 1, number = Inf, sort.by = "P")
  deg <- tt %>% rownames_to_column("gene") %>%
    mutate(log2FC = logFC, pvalue = P.Value, padj = p.adjust(P.Value, "BH")) %>%
    dplyr::select(gene, log2FC, pvalue, padj, everything())
  write.csv(deg, file.path(p$表格, paste0(ds, "_CLP12h_vs_24h_全部差异基因.csv")), row.names = FALSE)
  deg_sig <- deg %>% filter(padj < 0.05, abs(log2FC) >= 0.5)
  write.csv(deg_sig, file.path(p$表格, paste0(ds, "_CLP12h_vs_24h_显著差异基因.csv")), row.names = FALSE)
  ext_setup_font()
  pv <- ggplot(deg, aes(log2FC, -log10(pmax(padj, 1e-300)),
                        color = padj < 0.05 & abs(log2FC) >= 0.5)) +
    geom_point(alpha = 0.5, size = 1) +
    scale_color_manual(values = c(`TRUE` = "#E64B35", `FALSE` = "grey70"), name = "显著") +
    labs(title = paste0(ds, " CLP24h vs CLP12h 火山图"), x = "log2FC", y = "-log10(padj)")
  safe_ggsave(file.path(p$图形, paste0(ds, "_CLP12h_vs_24h_火山图.pdf")), pv, width = 10, height = 8)
  if (nrow(deg_sig) >= 3) {
    ora_enrich_save(deg_sig$gene, ds, "CLP12h_vs_24h_", "CLP24h vs CLP12h")
  }
  # MAMs 通路时序评分（模块均值）
  mams <- MAMS_MOUSE$gene[MAMS_MOUSE$gene %in% rownames(mat)]
  score_df <- si
  score_df$MAMs_score <- colMeans(mat[mams, , drop = FALSE], na.rm = TRUE)
  write.csv(score_df, file.path(p$表格, paste0(ds, "_MAMs通路时序评分.csv")), row.names = FALSE)
  pts <- ggplot(score_df, aes(time, MAMs_score, fill = time)) +
    geom_boxplot() + geom_jitter(width = 0.1, aes(color = sample), size = 2) +
    labs(title = paste0(ds, " MAMs 通路评分时序（12h→24h）"), y = "MAMs 基因均值 log2CPM")
  safe_ggsave(file.path(p$图形, paste0(ds, "_MAMs通路时序评分.pdf")), pts, width = 10, height = 7)
  message("时序 DEG: GSE207177")
}

# ---- 8. GSE267388 bulk 免疫-心肌 L-R 热图 ----
run_bulk_lr_heatmap <- function(ds = "GSE267388") {
  expr_f <- mid_path(ds, "expr_matrix.rds")
  if (!file.exists(expr_f)) return(invisible(NULL))
  p <- ds_paths(ds)
  mat <- readRDS(expr_f)
  if (max(mat, na.rm = TRUE) > 50) mat <- log2(mat + 1)
  si <- readRDS(mid_path(ds, "sample_info.rds"))
  LR <- LR_PAIRS[LR_PAIRS$ligand %in% rownames(mat) & LR_PAIRS$receptor %in% rownames(mat), ]
  score_lr <- function(samples) {
    sapply(seq_len(nrow(LR)), function(i) {
      mean(mat[LR$ligand[i], samples], na.rm = TRUE) * mean(mat[LR$receptor[i], samples], na.rm = TRUE)
    })
  }
  info <- DATASETS[DATASETS$id == ds, ]
  lps <- si$sample[si$group == info$case]
  pbs <- si$sample[si$group == info$control]
  sc_lps <- score_lr(lps); sc_pbs <- score_lr(pbs)
  df <- tibble(pair = paste0(LR$ligand, "→", LR$receptor), LPS = sc_lps, PBS = sc_pbs,
               delta = sc_lps - sc_pbs) %>% arrange(desc(delta))
  write.csv(df, file.path(p$表格, paste0(ds, "_bulk_LR通讯评分.csv")), row.names = FALSE)
  ext_setup_font()
  top <- head(df, 20)
  top$pair <- factor(top$pair, levels = rev(top$pair))
  pl <- ggplot(top, aes(pair, delta, fill = delta > 0)) +
    geom_col() + coord_flip() +
    scale_fill_manual(values = c(`TRUE` = "#E64B35", `FALSE` = "#4DBBD5"), guide = "none") +
    theme_bw() + labs(title = paste0(ds, " bulk 配体-受体通讯变化（LPS−PBS）"), x = NULL, y = "L-R 乘积差")
  safe_ggsave(file.path(p$图形, paste0(ds, "_bulk_LR通讯变化.pdf")), pl, width = 11, height = max(8, nrow(top) * 0.35))
  message("bulk L-R: ", ds)
}

run_nonml_completion_all <- function(ds_vec = FOUR) {
for (ds in ds_vec) {
  message("\n======== 非ML补全 ", ds, " ========")
  try(run_cell_comm_heatmap(ds), silent = FALSE)
  try(run_gsea_kegg(ds), silent = FALSE)
  try(run_mams_gsea(ds), silent = FALSE)
  try(run_mams_hub_enrich(ds), silent = FALSE)
  try(run_macro_sirt2_foxo1(ds), silent = FALSE)
  try(run_nichenet_lite(ds), silent = FALSE)
}
try(run_timeseries_deg(), silent = FALSE)
try(run_bulk_lr_heatmap(), silent = FALSE)
}
if (sys.nframe() == 0L) {
  run_nonml_completion_all()
  message("\n完成: 四数据集_非ML完整补全.R")
}
