# 03 代谢重编程：bulk GSVA（样本级）+ scRNA AUCell（细胞类型级）
# 数据来源：GSE79962 表达矩阵（人）、GSE207177 Seurat（鼠）；KEGG 代谢通路（KEGG REST）
# 意义：GSEA 提示 OXPHOS/TCA 整体受抑；此处量化“哪些代谢通路、在哪些样本/细胞类型”改变
source("00_公共函数.R", encoding = "UTF-8")
suppressPackageStartupMessages({ library(clusterProfiler); library(limma)
  library(pheatmap); library(RColorBrewer) })

# 构建 KEGG 代谢通路的 symbol 基因集（缓存）
get_kegg_metabolic_sets <- function(kegg_org, orgdb_name) {
  cache <- file.path(EXT$中间, paste0("kegg_metabolic_", kegg_org, ".rds"))
  if (file.exists(cache)) return(readRDS(cache))
  suppressPackageStartupMessages(library(orgdb_name, character.only = TRUE))
  orgdb <- get(orgdb_name, envir = asNamespace(orgdb_name))
  kg <- clusterProfiler::download_KEGG(kegg_org)
  p2e <- kg$KEGGPATHID2EXTID; p2n <- kg$KEGGPATHID2NAME
  colnames(p2e) <- c("pid", "entrez"); colnames(p2n) <- c("pid", "name")
  # 代谢类通路：KEGG 编号 < 02000（00010–01100）
  code <- suppressWarnings(as.integer(sub(kegg_org, "", p2e$pid)))
  p2e <- p2e[!is.na(code) & code < 2000, ]
  map <- suppressMessages(bitr(unique(p2e$entrez), "ENTREZID", "SYMBOL", OrgDb = orgdb))
  sym <- setNames(map$SYMBOL, map$ENTREZID)
  p2e$symbol <- sym[p2e$entrez]
  p2e <- p2e[!is.na(p2e$symbol), ]
  nm <- setNames(p2n$name, p2n$pid)
  sets <- split(p2e$symbol, p2e$pid)
  names(sets) <- paste0(sub(paste0(".*", kegg_org), kegg_org, names(sets)), "|", nm[names(sets)])
  sets <- sets[lengths(sets) >= 10]
  saveRDS(sets, cache); sets
}

# ---------- 3A. bulk GSVA (GSE79962) ----------
run_bulk_gsva <- function(ds = "GSE79962") {
  expr <- load_bulk_expr(ds); meta <- load_bulk_meta(ds)
  if (is.null(expr) || is.null(meta)) { message("缺 bulk 数据: ", ds); return(invisible(NULL)) }
  grp <- factor(meta$group)
  sets <- get_kegg_metabolic_sets("hsa", "org.Hs.eg.db")
  expr <- as.matrix(expr)
  gsva_res <- tryCatch({
    param <- GSVA::gsvaParam(expr, sets, kcdf = "Gaussian")
    GSVA::gsva(param)
  }, error = function(e) GSVA::gsva(expr, sets, method = "gsva", kcdf = "Gaussian", verbose = FALSE))

  design <- model.matrix(~ 0 + grp); colnames(design) <- levels(grp)
  cm <- makeContrasts(contrasts = paste0(levels(grp)[2], "-", levels(grp)[1]), levels = design)
  # 保证 case-control 方向：contrast = case - control
  case <- DATASETS$case[DATASETS$id == ds]; ctrl <- DATASETS$control[DATASETS$id == ds]
  cm <- makeContrasts(contrasts = paste0(case, "-", ctrl), levels = design)
  fit <- eBayes(contrasts.fit(lmFit(gsva_res, design), cm))
  tt <- topTable(fit, number = Inf, sort.by = "t")
  tt$pathway <- rownames(tt)
  save_tab(tt, paste0("03_代谢GSVA_", ds, ".csv"))

  top <- tt[order(tt$t), ]; top <- rbind(head(top, 15), tail(top, 15))
  mat <- gsva_res[rownames(top), , drop = FALSE]
  rownames(mat) <- substr(sub("^[^|]*\\|", "", rownames(mat)), 1, 40)
  ann <- data.frame(Group = grp); rownames(ann) <- colnames(mat)
  ord <- order(grp)
  pdf(file.path(EXT$图形, paste0("03_代谢GSVA热图_", ds, ".pdf")), width = 10, height = 9)
  pheatmap(mat[, ord], annotation_col = ann, cluster_cols = FALSE, fontsize_row = 8,
           main = paste0(ds, " 代谢通路活性(GSVA) ", case, " vs ", ctrl),
           color = colorRampPalette(c("#4DBBD5", "white", "#E64B35"))(100))
  dev.off()
  message("完成 bulk GSVA: ", ds)
}

# ---------- 3B. scRNA AUCell (GSE207177) ----------
run_sc_aucell <- function(ds = "GSE207177", max_cells = 15000) {
  suppressPackageStartupMessages({ library(Seurat); library(AUCell) })
  obj <- load_seurat(ds); if (is.null(obj)) { message("缺 Seurat: ", ds); return(invisible(NULL)) }
  DefaultAssay(obj) <- "RNA"; obj <- JoinLayers(obj, assay = "RNA")
  set.seed(42)
  if (ncol(obj) > max_cells) obj <- subset(obj, cells = sample(colnames(obj), max_cells))
  expr <- GetAssayData(obj, layer = "data")
  sets <- get_kegg_metabolic_sets("mmu", "org.Mm.eg.db")

  rankings <- AUCell_buildRankings(expr, plotStats = FALSE, verbose = FALSE)
  auc <- AUCell_calcAUC(sets, rankings, verbose = FALSE)
  auc_mat <- AUCell::getAUC(auc)                       # sets x cells

  meta <- obj@meta.data
  ct <- as.character(meta$celltype); gp <- as.character(meta$group)
  # 细胞类型 × 通路平均 AUC
  ct_levels <- names(sort(table(ct), decreasing = TRUE))
  ct_levels <- ct_levels[ct_levels %in% ct]
  mean_by_ct <- sapply(ct_levels, function(c) rowMeans(auc_mat[, ct == c, drop = FALSE]))
  # 取按细胞类型间方差最大的 25 条通路
  v <- apply(mean_by_ct, 1, var); sel <- names(sort(v, decreasing = TRUE))[1:min(25, length(v))]
  m <- mean_by_ct[sel, , drop = FALSE]
  rownames(m) <- substr(sub("^[^|]*\\|", "", rownames(m)), 1, 40)
  pdf(file.path(EXT$图形, paste0("03_代谢AUCell_细胞类型_", ds, ".pdf")), width = 10, height = 9)
  pheatmap(t(scale(t(m))), fontsize_row = 8, main = paste0(ds, " 细胞类型代谢活性(AUCell)"),
           color = colorRampPalette(c("#4DBBD5", "white", "#E64B35"))(100))
  dev.off()

  # 关键通路 OXPHOS：疾病 vs 对照，按细胞类型
  oxphos <- grep("Oxidative phosphorylation", rownames(auc_mat), ignore.case = TRUE, value = TRUE)[1]
  if (!is.na(oxphos)) {
    df <- tibble(celltype = ct, group = gp, OXPHOS = auc_mat[oxphos, ])
    case <- DATASETS$case[DATASETS$id == ds]; ctrl <- DATASETS$control[DATASETS$id == ds]
    df <- df %>% filter(group %in% c(case, ctrl)) %>%
      mutate(group = factor(group, levels = c(ctrl, case)))
    keep_ct <- names(which(table(df$celltype) > 50))
    df <- df %>% filter(celltype %in% keep_ct)
    p <- ggplot(df, aes(x = celltype, y = OXPHOS, fill = group)) +
      geom_boxplot(outlier.size = 0.2) + ext_theme() +
      theme(axis.text.x = element_text(angle = 30, hjust = 1)) +
      labs(title = paste0(ds, " 氧化磷酸化活性 ", case, " vs ", ctrl), x = NULL, y = "OXPHOS AUC")
    save_fig(p, paste0("03_代谢AUCell_OXPHOS_", ds, ".pdf"), width = 9, height = 5)
    save_tab(df %>% group_by(celltype, group) %>%
               summarise(mean_OXPHOS = mean(OXPHOS), .groups = "drop"),
             paste0("03_代谢AUCell_OXPHOS_", ds, ".csv"))
  }
  message("完成 scRNA AUCell: ", ds)
}

run_bulk_gsva("GSE79962")
run_sc_aucell("GSE207177")
message("完成: 03_代谢重编程.R")
