# 巨噬细胞差异分析 + MAMs 交集/韦恩/富集（四数据集 scRNA 补全）

suppressPackageStartupMessages(library(tidyverse))

if (!exists("PROJECT_ROOT")) {
  PROJECT_ROOT <- if (file.exists("RProject.Rproj")) normalizePath(".") else {
    p <- normalizePath(getwd(), winslash = "/")
    for (i in 1:6) { if (file.exists(file.path(p, "RProject.Rproj"))) break; p <- dirname(p) }
    p
  }
}
source(file.path(PROJECT_ROOT, "共享脚本", "工具_项目路径.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_统一出图.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_富集与质控图.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA可视化.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "延展分析", "代码", "00_公共函数.R"), encoding = "UTF-8")

MAMS_MOUSE <- read.csv(file.path(PROJECT_ROOT, "sciadv_adz3266", "源数据", "MAMs_基因集_鼠.csv"),
                       stringsAsFactors = FALSE)

SCRNA_DS <- c("GSE190856", "GSE207363", "GSE207177")
MACRO_CONTRASTS <- list(
  GSE190856 = list(main = c("CLP", "Steady")),
  GSE207177 = list(main = c("CLP", "Control")),
  GSE207363 = list(main = c("Sepsis", "Sham"), extra = c("Sepsis", "Control"))
)

# 低生物学重复 / 已知 pseudobulk 功效不足时，与全细胞层一致走 FindMarkers
FORCE_CELL_LEVEL_DS <- c("GSE190856", "GSE207363")

ER_STRESS_GENES <- c(
  "Hspa5", "Atf4", "Xbp1", "Ddit3", "Hspa1a", "Eif2ak3", "Herpud1", "Ern1",
  "Atf6", "Manf", "Dnajb9", "Calr", "Canx", "Ppp1r15a", "Wfs1", "Edem1"
)
MITO_DYSFUNCTION_GENES <- c(
  "Pink1", "Prkn", "Mfn1", "Mfn2", "Dnm1l", "Tomm40", "Ndufs1", "Cox5a",
  "Ucp2", "Opa1", "Fis1", "Fundc1", "Bnip3", "Hspa9", "Slc25a4", "Ndufa1",
  "Atp5f1a", "Sod2", "Pgam5", "Gpx1"
)
HUB_CANDIDATE_GENES <- c("Sirt2", "Foxo1")

ensure_joined_layers <- function(obj, assay = "RNA") {
  suppressPackageStartupMessages(library(Seurat))
  DefaultAssay(obj) <- assay
  if ("JoinLayers" %in% ls("package:Seurat")) {
    lyr <- tryCatch(Layers(obj[[assay]]), error = function(e) character(0))
    multi <- length(lyr) > 3 || any(grepl("^(counts|data)\\.", lyr))
    if (multi) obj <- JoinLayers(obj, assay = assay)
  }
  obj
}

get_joined_expr <- function(obj, assay = "RNA", layer = "data") {
  obj <- ensure_joined_layers(obj, assay)
  tryCatch(
    as.matrix(GetAssayData(obj, assay = assay, layer = layer)),
    error = function(e) {
      lyr <- Layers(obj[[assay]])
      pat <- if (layer == "counts") "^counts" else "^data"
      dl <- lyr[grepl(pat, lyr)]
      if (length(dl) == 0) stop("无法获取表达矩阵: ", conditionMessage(e))
      mats <- lapply(dl, function(l) as.matrix(LayerData(obj, assay = assay, layer = l)))
      all_genes <- Reduce(union, lapply(mats, rownames))
      mats <- lapply(mats, function(m) {
        out <- matrix(0, nrow = length(all_genes), ncol = ncol(m),
                      dimnames = list(all_genes, colnames(m)))
        out[rownames(m), ] <- m
        out
      })
      do.call(cbind, mats)
    }
  )
}

rebuild_single_layer_seurat <- function(obj, assay = "RNA") {
  suppressPackageStartupMessages(library(Seurat))
  lyr <- Layers(obj[[assay]])
  count_layers <- lyr[grepl("^counts", lyr)]
  if (length(count_layers)) {
    counts <- get_joined_expr(obj, assay, "counts")
  } else {
    dat <- get_joined_expr(obj, assay, "data")
    counts <- round(expm1(pmax(dat, 0)))
  }
  counts <- round(pmax(counts, 0))
  meta <- obj@meta.data[colnames(counts), , drop = FALSE]
  CreateSeuratObject(counts = counts, meta.data = meta, assay = assay)
}

get_macrophage_cells <- function(obj) {
  meta <- obj@meta.data
  ct <- as.character(meta$celltype)
  rownames(meta)[grepl("Macrophage", ct, ignore.case = TRUE)]
}

get_macrophage_subset <- function(ds) {
  p <- init_dataset_paths(PROJECT_ROOT, ds)
  obj <- readRDS(file.path(p$中间数据, paste0(ds, "_seurat.rds")))
  obj <- ensure_joined_layers(obj)
  mac <- get_macrophage_cells(obj)
  if (length(mac) < 50) stop(ds, ": 巨噬细胞数不足 (n=", length(mac), ")")
  sub <- subset(obj, cells = mac)
  ensure_joined_layers(sub)
}

run_macrophage_deg <- function(ds, contrast, padj_cut = 0.05, lfc_cut = 1.0,
                               suffix = "", max_cells = 3000) {
  suppressPackageStartupMessages({
    library(Seurat)
    library(edgeR)
    library(limma)
  })
  p <- init_dataset_paths(PROJECT_ROOT, ds)
  obj <- readRDS(file.path(p$中间数据, paste0(ds, "_seurat.rds")))
  DefaultAssay(obj) <- "RNA"
  obj <- ensure_joined_layers(obj)

  mac <- get_macrophage_cells(obj)
  if (length(mac) < 50) stop(ds, ": 巨噬细胞数不足 (n=", length(mac), ")")

  cells <- intersect(mac, rownames(obj@meta.data)[obj$group %in% contrast])
  sub <- subset(obj, cells = cells)
  sub <- ensure_joined_layers(sub)
  DefaultAssay(sub) <- "RNA"
  n_by_grp <- table(sub$group)
  message(ds, suffix, " 巨噬细胞: ", sum(n_by_grp), " | ",
          paste(names(n_by_grp), n_by_grp, sep = "=", collapse = ", "))

  tag <- if (nzchar(suffix)) paste0("_", suffix) else ""
  out_all <- file.path(p$表格, paste0(ds, "_巨噬细胞", tag, "_全部差异基因.csv"))
  out_sig <- file.path(p$表格, paste0(ds, "_巨噬细胞", tag, "_显著差异基因.csv"))
  rds_all <- file.path(p$中间数据, paste0(ds, "_macrophage", tag, "_deg.rds"))
  rds_sig <- file.path(p$中间数据, paste0(ds, "_macrophage", tag, "_deg_sig.rds"))

  method <- "FindMarkers"
  deg <- NULL

  samp_mac <- sub@meta.data %>%
    tibble::as_tibble(rownames = "cell") %>%
    count(sample, group, name = "n_mac")
  n_samp <- samp_mac %>%
    filter(group %in% contrast) %>%
    distinct(group, sample) %>%
    count(group, name = "n_samples")
  ok_pb <- all(contrast %in% samp_mac$group) &&
    all(vapply(contrast, function(g) sum(samp_mac$n_mac[samp_mac$group == g] >= 20) >= 2, logical(1))) &&
    all(n_samp$n_samples >= 2)
  use_cell_level <- ds %in% FORCE_CELL_LEVEL_DS || !ok_pb

  if (ok_pb && !use_cell_level) {
    agg <- AggregateExpression(sub, assays = "RNA", group.by = "sample",
                               slot = "counts", return.seurat = FALSE)
    pb <- as.matrix(agg$RNA)
    meta_s <- sub@meta.data %>% distinct(sample, group) %>% filter(group %in% contrast)
    rownames(meta_s) <- meta_s$sample
    cn <- colnames(pb)
    usam <- unique(as.character(meta_s$sample))
    map_clean <- setNames(usam, make.names(gsub("_", "-", usam)))
    cn2 <- make.names(cn)
    colnames(pb) <- ifelse(cn2 %in% names(map_clean), map_clean[cn2], cn)
    keep_s <- intersect(colnames(pb), meta_s$sample)
    pb <- pb[, keep_s, drop = FALSE]
    grp <- factor(meta_s$group[match(colnames(pb), meta_s$sample)], levels = contrast)
    if (ncol(pb) >= 4 && length(unique(grp)) == 2) {
      dge <- DGEList(counts = pb, group = grp)
      keep_g <- filterByExpr(dge, group = grp)
      dge <- dge[keep_g, , keep.lib.sizes = FALSE]
      dge <- calcNormFactors(dge, method = "TMM")
      design <- model.matrix(~ 0 + grp)
      colnames(design) <- levels(grp)
      cm <- makeContrasts(contrasts = paste0(contrast[1], "-", contrast[2]), levels = design)
      v <- voom(dge, design, plot = FALSE)
      fit <- lmFit(v, design) %>% contrasts.fit(cm) %>% eBayes()
      deg <- topTable(fit, number = Inf, adjust.method = "BH", sort.by = "P") %>%
        rownames_to_column("gene") %>%
        rename(log2FC = logFC, padj = adj.P.Val, pvalue = P.Value) %>%
        select(gene, log2FC, AveExpr, t, pvalue, padj, everything())
      method <- "macrophage_pseudobulk_edgeR-TMM_voom"
    }
  }

  if (is.null(deg) || use_cell_level) {
    sub <- ensure_joined_layers(sub)
    sub <- tryCatch(rebuild_single_layer_seurat(sub), error = function(e) sub)
    sub <- NormalizeData(sub, verbose = FALSE)
    Idents(sub) <- sub$group
    deg <- tryCatch({
      fm <- FindMarkers(sub, ident.1 = contrast[1], ident.2 = contrast[2],
                        logfc.threshold = 0, min.pct = 0.1, max.cells.per.ident = max_cells)
      fm$gene <- rownames(fm)
      fm %>%
        rename(log2FC = avg_log2FC, padj = p_val_adj, pvalue = p_val) %>%
        select(gene, log2FC, pvalue, padj, everything())
    }, error = function(e) {
      message("FindMarkers 失败，尝试 LayerData Wilcoxon: ", conditionMessage(e))
      expr <- get_joined_expr(sub, layer = "data")
      cells <- intersect(colnames(expr), colnames(sub))
      expr <- expr[, cells, drop = FALSE]
      grp <- sub$group[cells]
      i1 <- grp == contrast[1]; i2 <- grp == contrast[2]
      lfc <- rowMeans(expr[, i1, drop = FALSE], na.rm = TRUE) -
        rowMeans(expr[, i2, drop = FALSE], na.rm = TRUE)
      pv <- vapply(seq_len(nrow(expr)), function(i) {
        tryCatch(stats::wilcox.test(expr[i, i1], expr[i, i2])$p.value, error = function(er) 1)
      }, numeric(1))
      padj <- p.adjust(pv, "BH")
      tibble(gene = rownames(expr), log2FC = as.numeric(lfc), pvalue = pv, padj = padj)
    })
    method <- if (use_cell_level) "macrophage_FindMarkers" else "macrophage_FindMarkers_fallback"
  }

  deg$method <- method
  deg$contrast <- paste(contrast[1], "vs", contrast[2])
  deg_sig <- deg %>% filter(padj < padj_cut, abs(log2FC) > lfc_cut)

  write.csv(deg, out_all, row.names = FALSE)
  write.csv(deg_sig, out_sig, row.names = FALSE)
  saveRDS(deg, rds_all)
  saveRDS(deg_sig, rds_sig)

  setup_plot_fonts()
  plot_volcano(deg, title = paste(ds, "巨噬细胞 DEG", tag),
               out_path = file.path(p$图形, paste0(ds, "_巨噬细胞", tag, "_火山图.pdf")),
               padj_cut = padj_cut, lfc_cut = lfc_cut)

  list(
    dataset = ds, suffix = suffix, contrast = contrast, method = method,
    n_macrophages = ncol(sub), n_deg = nrow(deg), n_sig = nrow(deg_sig),
    n_up = sum(deg_sig$log2FC > 0), n_down = sum(deg_sig$log2FC < 0),
    sirt2 = deg_sig %>% filter(gene == "Sirt2"),
    foxo1 = deg_sig %>% filter(gene == "Foxo1"),
    paths = list(all = out_all, sig = out_sig)
  )
}

run_macrophage_mams_intersect <- function(ds, suffix = "") {
  p <- init_dataset_paths(PROJECT_ROOT, ds)
  tag <- if (nzchar(suffix)) paste0("_", suffix) else ""
  sig_f <- file.path(p$表格, paste0(ds, "_巨噬细胞", tag, "_显著差异基因.csv"))
  all_f <- file.path(p$表格, paste0(ds, "_巨噬细胞", tag, "_全部差异基因.csv"))
  if (!file.exists(sig_f)) return(NULL)

  deg_sig <- read.csv(sig_f, stringsAsFactors = FALSE)
  if (!nrow(deg_sig) || !"gene" %in% names(deg_sig)) {
    message("无巨噬显著 DEG，跳过 MAMs 交集: ", ds, tag)
    return(list(n_deg_sig = 0, n_mams = length(unique(MAMS_MOUSE$gene)), n_inter = 0, inter_genes = character(0)))
  }
  deg_sig$gene <- as.character(deg_sig$gene)
  deg_all <- read.csv(all_f, stringsAsFactors = FALSE)
  mams_genes <- unique(MAMS_MOUSE$gene)

  inter <- deg_sig %>% filter(gene %in% mams_genes) %>%
    left_join(MAMS_MOUSE, by = "gene")
  write.csv(inter, file.path(p$表格, paste0(ds, "_巨噬细胞", tag, "_MAMs交集基因.csv")), row.names = FALSE)

  venn_df <- tibble(
    set = c("Macrophage_DEG", "MAMs_geneset", "Intersection"),
    n = c(nrow(deg_sig), length(mams_genes), nrow(inter))
  )
  write.csv(venn_df, file.path(p$表格, paste0(ds, "_巨噬细胞", tag, "_MAMs韦恩统计.csv")), row.names = FALSE)

  setup_plot_fonts()
  plot_df <- tibble(
    category = factor(c("巨噬DEG", "MAMs基因集", "交集"),
                      levels = c("巨噬DEG", "MAMs基因集", "交集")),
    count = c(nrow(deg_sig), length(mams_genes), nrow(inter))
  )
  p_bar <- ggplot(plot_df, aes(category, count, fill = category)) +
    geom_col(width = 0.6, show.legend = FALSE) +
    geom_text(aes(label = count), vjust = -0.3, size = 4) +
    labs(title = paste(ds, "巨噬细胞 DEG ∩ MAMs 韦恩统计", tag),
         subtitle = paste0("交集 ", nrow(inter), " 基因"),
         x = NULL, y = "基因数") +
    theme_no_overlap()
  safe_ggsave(file.path(p$图形, paste0(ds, "_巨噬细胞", tag, "_MAMs韦恩图.pdf")), p_bar, 8, 6)

  deg_all$is_mams <- deg_all$gene %in% mams_genes
  pv <- ggplot(deg_all, aes(log2FC, -log10(pmax(padj, 1e-300)), color = is_mams)) +
    geom_point(alpha = 0.6, size = 1.2) +
    scale_color_manual(values = c(`TRUE` = "#E64B35", `FALSE` = "grey70"),
                       labels = c(`TRUE` = "MAMs相关", `FALSE` = "其他"), name = NULL) +
    labs(title = paste(ds, "巨噬细胞 MAMs 交集火山图", tag),
         x = "log2FC", y = "-log10(padj)") +
    theme_no_overlap()
  safe_ggsave(file.path(p$图形, paste0(ds, "_巨噬细胞", tag, "_MAMs交集火山图.pdf")), pv, 10, 8)

  list(n_deg_sig = nrow(deg_sig), n_mams = length(mams_genes), n_inter = nrow(inter),
       inter_genes = inter$gene)
}

run_macrophage_enrichment <- function(ds, suffix = "") {
  p <- init_dataset_paths(PROJECT_ROOT, ds)
  tag <- if (nzchar(suffix)) paste0("_", suffix) else ""
  sig_f <- file.path(p$表格, paste0(ds, "_巨噬细胞", tag, "_显著差异基因.csv"))
  if (!file.exists(sig_f)) return(NULL)
  deg_sig <- read.csv(sig_f, stringsAsFactors = FALSE)
  if (nrow(deg_sig) < 3) {
    message("巨噬 DEG 不足，跳过富集: ", ds, tag)
    return(list(skipped = TRUE))
  }

  prefix <- paste0(ds, "_巨噬细胞", tag)
  run_enrichment_full(deg_sig, prefix, p$表格, p$图形,
                      org_db = "org.Mm.eg.db", kegg_org = "mmu")

  deg_all <- read.csv(file.path(p$表格, paste0(ds, "_巨噬细胞", tag, "_全部差异基因.csv")),
                      stringsAsFactors = FALSE)
  ranks <- deg_rank_vector(deg_all)
  gs_list <- split(MAMS_MOUSE$gene, MAMS_MOUSE$category)
  gs_list$inflammasome <- c("Nlrp3", "Casp1", "Gsdmd", "Il1b", "Il18", "Pycard")
  gs_list$mtDNA_release <- c("Tlr9", "Tlr4", "Myd88", "Ifnb1", "Sting1", "Tbk1")
  term2gene <- bind_rows(lapply(names(gs_list), function(nm) {
    tibble(gs_name = nm, gene_name = unique(gs_list[[nm]]))
  })) %>% filter(gene_name %in% names(ranks))

  if (nrow(term2gene) >= 5 && requireNamespace("clusterProfiler", quietly = TRUE)) {
    suppressPackageStartupMessages(library(clusterProfiler))
    fg <- tryCatch(
      GSEA(ranks, TERM2GENE = term2gene, minGSSize = 3, maxGSSize = 500,
           pvalueCutoff = 0.25, verbose = FALSE),
      error = function(e) NULL)
    if (!is.null(fg) && nrow(as.data.frame(fg)) > 0) {
      write.csv(as.data.frame(fg), file.path(p$表格, paste0(prefix, "_MAMs通路GSEA.csv")), row.names = FALSE)
      setup_plot_fonts()
      pd <- clusterProfiler::dotplot(fg, showCategory = 15, label_format = enrich_full_labels) +
        ggplot2::scale_y_discrete(labels = enrich_full_labels) +
        ggtitle(paste(ds, "巨噬细胞 MAMs 通路 GSEA", tag))
      sz <- enrich_plot_size(15, as.data.frame(fg)$Description)
      safe_ggsave(file.path(p$图形, paste0(prefix, "_MAMs通路GSEA.pdf")), pd, sz$width, sz$height)
    }
  }

  focus <- deg_sig %>% filter(gene %in% c("Sirt2", "Foxo1"))
  list(n_sig = nrow(deg_sig), focus_genes = focus)
}

plot_macrophage_umap_highlight <- function(ds) {
  suppressPackageStartupMessages(library(Seurat))
  p <- init_dataset_paths(PROJECT_ROOT, ds)
  obj <- readRDS(file.path(p$中间数据, paste0(ds, "_seurat.rds")))
  obj <- ensure_joined_layers(obj)
  meta <- obj@meta.data
  meta$mac_label <- ifelse(grepl("Macrophage", as.character(meta$celltype), ignore.case = TRUE),
                           "Macrophages", "Other cells")
  obj$mac_label <- meta$mac_label

  setup_plot_fonts()
  p1 <- DimPlot(obj, group.by = "mac_label", cols = c(Macrophages = "#E64B35", "Other cells" = "grey85"),
                pt.size = 0.2, order = c("Other cells", "Macrophages")) +
    ggtitle(paste(ds, "巨噬细胞为核心免疫细胞")) + theme_no_overlap()
  safe_ggsave(file.path(p$图形, paste0(ds, "_巨噬细胞_UMAP高亮.pdf")), p1, 10, 8)

  mac <- get_macrophage_cells(obj)
  sub <- subset(obj, cells = mac)
  sub <- ensure_joined_layers(sub)
  p2 <- DimPlot(sub, group.by = "group", pt.size = 0.5) +
    ggtitle(paste(ds, "巨噬细胞亚群（按分组）")) + theme_no_overlap()
  safe_ggsave(file.path(p$图形, paste0(ds, "_巨噬细胞_分组UMAP.pdf")), p2, 10, 8)

  prop <- sub@meta.data %>% tibble::as_tibble() %>%
    count(group, name = "n") %>% mutate(pct = round(100 * n / sum(n), 2))
  write.csv(prop, file.path(p$表格, paste0(ds, "_巨噬细胞_分组比例.csv")), row.names = FALSE)

  p3 <- ggplot(prop, aes(group, pct, fill = group)) +
    geom_col(width = 0.6, show.legend = FALSE) +
    geom_text(aes(label = paste0(pct, "%")), vjust = -0.3, size = 4) +
    labs(title = paste(ds, "巨噬细胞分组占比"), x = NULL, y = "占比 (%)") +
    theme_no_overlap()
  safe_ggsave(file.path(p$图形, paste0(ds, "_巨噬细胞_分组比例.pdf")), p3, 8, 6)
  list(n_mac = length(mac), prop = prop)
}

run_macrophage_theme_heatmap <- function(ds, contrast = NULL, suffix = "") {
  suppressPackageStartupMessages({ library(Seurat); library(pheatmap); library(RColorBrewer) })
  p <- init_dataset_paths(PROJECT_ROOT, ds)
  if (is.null(contrast)) contrast <- MACRO_CONTRASTS[[ds]]$main
  tag <- if (nzchar(suffix)) paste0("_", suffix) else ""

  sub <- get_macrophage_subset(ds)
  sub <- subset(sub, subset = group %in% contrast)
  sub <- ensure_joined_layers(sub)

  avg <- AverageExpression(sub, group.by = "group", assays = "RNA", slot = "data",
                           return.seurat = FALSE)
  mat <- as.matrix(avg$RNA)
  mat <- mat[, contrast[contrast %in% colnames(mat)], drop = FALSE]
  if (ncol(mat) < 2) {
    message("分组不足，跳过热图: ", ds, tag)
    return(list(skipped = TRUE))
  }

  plot_gene_heatmap <- function(genes, title_suffix, file_suffix, type_label) {
    genes <- unique(c(genes, HUB_CANDIDATE_GENES))
    genes <- genes[genes %in% rownames(mat)]
    if (length(genes) < 2) {
      message("基因不足，跳过: ", ds, file_suffix)
      return(invisible(NULL))
    }
    hm <- mat[genes, , drop = FALSE]
    hm_z <- t(scale(t(hm)))
    hm_z[is.na(hm_z)] <- 0
    ann <- data.frame(Group = factor(colnames(hm), levels = contrast))
    rownames(ann) <- colnames(hm)
    gene_type <- ifelse(rownames(hm_z) %in% HUB_CANDIDATE_GENES, "HUB候选", type_label)
    ann_row <- data.frame(Type = factor(gene_type, levels = c("HUB候选", type_label)))
    rownames(ann_row) <- rownames(hm_z)
    nlev <- length(contrast)
    ann_colors <- list(
      Group = setNames(brewer.pal(max(3, nlev), "Set1")[seq_len(nlev)], contrast),
      Type = c("HUB候选" = "#E64B35", "内质网应激" = "#4DBBD5", "线粒体功能障碍" = "#00A087")
    )
    ann_colors$Type <- ann_colors$Type[levels(ann_row$Type)]
    safe_pdf(file.path(p$图形, paste0(ds, "_巨噬细胞", tag, file_suffix)),
             max(8, 6 + max(nchar(rownames(hm_z))) * 0.06),
             max(5, nrow(hm_z) * 0.38), {
      pheatmap(hm_z, annotation_col = ann, annotation_row = ann_row,
               annotation_colors = ann_colors, cluster_cols = FALSE,
               show_rownames = TRUE, fontsize_row = 10, fontsize_col = 11,
               main = paste(ds, "巨噬细胞", title_suffix, tag),
               color = colorRampPalette(c("#4DBBD5", "white", "#E64B35"))(100))
    })
    df_out <- as.data.frame(hm)
    df_out$gene <- rownames(hm)
    df_out$panel <- title_suffix
    write.csv(df_out, file.path(p$表格, paste0(ds, "_巨噬细胞", tag,
                                                gsub(".pdf", "表达.csv", file_suffix))),
              row.names = FALSE)
  }

  plot_gene_heatmap(intersect(ER_STRESS_GENES, rownames(mat)), "内质网应激基因",
                    "_内质网应激热图.pdf", "内质网应激")
  plot_gene_heatmap(intersect(MITO_DYSFUNCTION_GENES, rownames(mat)), "线粒体功能障碍基因",
                    "_线粒体功能障碍热图.pdf", "线粒体功能障碍")
  list(contrast = contrast, n_genes_er = sum(ER_STRESS_GENES %in% rownames(mat)),
       n_genes_mito = sum(MITO_DYSFUNCTION_GENES %in% rownames(mat)))
}

plot_macrophage_hub_genes <- function(ds) {
  suppressPackageStartupMessages(library(Seurat))
  p <- init_dataset_paths(PROJECT_ROOT, ds)
  sub <- get_macrophage_subset(ds)
  sub <- ensure_joined_layers(sub)
  genes <- intersect(HUB_CANDIDATE_GENES, rownames(sub))
  if (!length(genes)) return(invisible(NULL))
  setup_plot_fonts()
  plots <- lapply(genes, function(g) {
    VlnPlot(sub, features = g, group.by = "group", pt.size = 0) +
      theme_bw() + labs(title = paste(ds, "巨噬细胞", g), x = NULL, y = "表达")
  })
  if (length(plots) == 1) {
    safe_ggsave(file.path(p$图形, paste0(ds, "_巨噬细胞_Sirt2_Foxo1.pdf")), plots[[1]], 8, 7)
  } else {
    safe_ggsave(file.path(p$图形, paste0(ds, "_巨噬细胞_Sirt2_Foxo1.pdf")),
                plots[[1]] + plots[[2]], 14, 7)
  }
}

save_step1_scrna_figures <- function(ds) {
  suppressPackageStartupMessages(library(Seurat))
  source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA细胞注释.R"), encoding = "UTF-8")
  p <- init_dataset_paths(PROJECT_ROOT, ds)
  obj <- readRDS(file.path(p$中间数据, paste0(ds, "_seurat.rds")))
  obj <- ensure_joined_layers(obj)
  cfg_stub <- list(deg_padj = 0.05, deg_logfc = 1.0, run_immune_subset = TRUE)
  immune_obj <- if (file.exists(file.path(p$中间数据, paste0(ds, "_immune.rds")))) {
    readRDS(file.path(p$中间数据, paste0(ds, "_immune.rds")))
  } else subset_immune_recluster(obj)
  save_all_scrna_figures(obj, ds, p, cfg_stub, immune_obj)
  plot_macrophage_umap_highlight(ds)
}

SCRNA_FIGURE_KEEP <- function(ds) {
  c(
    paste0(ds, "_UMAP.pdf"),
    paste0(ds, "_UMAP_细胞类型.pdf"),
    paste0(ds, "_UMAP_免疫聚类.pdf"),
    paste0(ds, "_UMAP_免疫谱系.pdf"),
    paste0(ds, "_分组细胞比例堆叠图.pdf"),
    paste0(ds, "_巨噬细胞_UMAP高亮.pdf"),
    paste0(ds, "_巨噬细胞_分组UMAP.pdf"),
    paste0(ds, "_巨噬细胞_分组比例.pdf"),
    paste0(ds, "_巨噬细胞_火山图.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_火山图.pdf"),
    paste0(ds, "_巨噬细胞_内质网应激热图.pdf"),
    paste0(ds, "_巨噬细胞_线粒体功能障碍热图.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_内质网应激热图.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_线粒体功能障碍热图.pdf"),
    paste0(ds, "_巨噬细胞_GO生物过程.pdf"),
    paste0(ds, "_巨噬细胞_GO生物过程图.pdf"),
    paste0(ds, "_巨噬细胞_GO生物过程_上调.pdf"),
    paste0(ds, "_巨噬细胞_GO生物过程_上调图.pdf"),
    paste0(ds, "_巨噬细胞_GO生物过程_下调.pdf"),
    paste0(ds, "_巨噬细胞_GO生物过程_下调图.pdf"),
    paste0(ds, "_巨噬细胞_KEGG通路.pdf"),
    paste0(ds, "_巨噬细胞_KEGG通路图.pdf"),
    paste0(ds, "_巨噬细胞_KEGG通路_上调.pdf"),
    paste0(ds, "_巨噬细胞_KEGG通路_上调图.pdf"),
    paste0(ds, "_巨噬细胞_KEGG通路_下调.pdf"),
    paste0(ds, "_巨噬细胞_KEGG通路_下调图.pdf"),
    paste0(ds, "_巨噬细胞_MAMs韦恩图.pdf"),
    paste0(ds, "_巨噬细胞_MAMs交集火山图.pdf"),
    paste0(ds, "_巨噬细胞_MAMs通路GSEA.pdf"),
    paste0(ds, "_巨噬细胞_Sirt2_Foxo1.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_MAMs韦恩图.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_MAMs交集火山图.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_MAMs通路GSEA.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_GO生物过程.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_GO生物过程图.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_GO生物过程_上调.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_GO生物过程_上调图.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_GO生物过程_下调.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_GO生物过程_下调图.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_KEGG通路.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_KEGG通路图.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_KEGG通路_上调.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_KEGG通路_上调图.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_KEGG通路_下调.pdf"),
    paste0(ds, "_巨噬细胞_SepsisVsControl_KEGG通路_下调图.pdf")
  )
}

cleanup_redundant_scrna_figures <- function(datasets = SCRNA_DS) {
  removed <- list()
  for (ds in datasets) {
    p <- init_dataset_paths(PROJECT_ROOT, ds)
    keep <- SCRNA_FIGURE_KEEP(ds)
    all_pdf <- list.files(p$图形, pattern = "\\.pdf$", full.names = TRUE)
    for (f in all_pdf) {
      if (!basename(f) %in% keep) {
        file.remove(f)
        removed[[length(removed) + 1]] <- f
      }
    }
  }
  message("已删除冗余 PDF: ", length(removed), " 个")
  removed
}

# GSE267388 bulk：仅保留验证相关主图；误标 CLP12h 文件重命名为 LPS_vs_PBS
BULK_FIGURE_KEEP <- function(ds = "GSE267388") {
  c(
    paste0(ds, "_火山图.pdf"),
    paste0(ds, "_质控箱线图.pdf"),
    paste0(ds, "_质控PCA.pdf"),
    paste0(ds, "_PCA.pdf"),
    paste0(ds, "_Top50热图.pdf"),
    paste0(ds, "_GO生物过程.pdf"),
    paste0(ds, "_GO生物过程图.pdf"),
    paste0(ds, "_GO生物过程_上调.pdf"),
    paste0(ds, "_GO生物过程_上调图.pdf"),
    paste0(ds, "_GO生物过程_下调.pdf"),
    paste0(ds, "_GO生物过程_下调图.pdf"),
    paste0(ds, "_KEGG通路.pdf"),
    paste0(ds, "_KEGG通路图.pdf"),
    paste0(ds, "_MAMs交集火山图.pdf"),
    paste0(ds, "_MAMs通路GSEA.pdf"),
    paste0(ds, "_巨噬细胞_Sirt2_Foxo1.pdf"),
    paste0(ds, "_CIBERSORT免疫浸润.pdf"),
    paste0(ds, "_估算细胞比例环图.pdf"),
    paste0(ds, "_分组细胞比例堆叠图.pdf"),
    # 重命名后的次级对比
    paste0(ds, "_LPS_vs_PBS_火山图.pdf"),
    paste0(ds, "_LPS_vs_PBS_GO.pdf"),
    paste0(ds, "_LPS_vs_PBS_GO图.pdf"),
    paste0(ds, "_LPS_vs_PBS_KEGG.pdf"),
    paste0(ds, "_LPS_vs_PBS_KEGG图.pdf")
  )
}

cleanup_and_rename_gse267388_figures <- function() {
  ds <- "GSE267388"
  p <- init_dataset_paths(PROJECT_ROOT, ds)
  fig <- p$图形
  # 误标 CLP12h_vs_24h → LPS_vs_PBS（该数据集实为 LPS vs PBS）
  pairs <- list(
    c(paste0(ds, "_CLP12h_vs_24h_火山图.pdf"), paste0(ds, "_LPS_vs_PBS_火山图.pdf")),
    c(paste0(ds, "_CLP12h_vs_24h_GO.pdf"), paste0(ds, "_LPS_vs_PBS_GO.pdf")),
    c(paste0(ds, "_CLP12h_vs_24h_GO图.pdf"), paste0(ds, "_LPS_vs_PBS_GO图.pdf")),
    c(paste0(ds, "_CLP12h_vs_24h_KEGG.pdf"), paste0(ds, "_LPS_vs_PBS_KEGG.pdf")),
    c(paste0(ds, "_CLP12h_vs_24h_KEGG图.pdf"), paste0(ds, "_LPS_vs_PBS_KEGG图.pdf"))
  )
  renamed <- character(0)
  for (pr in pairs) {
    src <- file.path(fig, pr[1]); dst <- file.path(fig, pr[2])
    if (file.exists(src)) {
      if (file.exists(dst)) file.remove(dst)
      file.rename(src, dst)
      renamed <- c(renamed, paste(pr[1], "→", pr[2]))
    }
  }
  keep <- BULK_FIGURE_KEEP(ds)
  removed <- character(0)
  for (f in list.files(fig, pattern = "\\.pdf$", full.names = TRUE)) {
    if (!basename(f) %in% keep) {
      file.remove(f)
      removed <- c(removed, basename(f))
    }
  }
  message("GSE267388 重命名 ", length(renamed), "；删除冗余 ", length(removed))
  list(renamed = renamed, removed = removed)
}

reprocess_gse207363_no_llts <- function() {
  ds <- "GSE207363"
  p <- init_dataset_paths(PROJECT_ROOT, ds)
  seurat_f <- file.path(p$中间数据, paste0(ds, "_seurat.rds"))
  raw_f <- file.path(p$中间数据, paste0(ds, "_raw_sc.rds"))
  new_keep <- c("Control", "Sham", "Sepsis")

  before_prop <- if (file.exists(file.path(p$表格, paste0(ds, "_细胞类型比例.csv")))) {
    read.csv(file.path(p$表格, paste0(ds, "_细胞类型比例.csv")), stringsAsFactors = FALSE)
  } else NULL

  suppressPackageStartupMessages(library(Seurat))
  source(file.path(PROJECT_ROOT, "共享脚本", "工具_单细胞差异分析.R"), encoding = "UTF-8")
  source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA细胞注释.R"), encoding = "UTF-8")

  if (file.exists(raw_f)) {
    raw <- readRDS(raw_f)
    objs <- list()
    for (i in seq_along(raw$counts)) {
      sid <- names(raw$counts)[i]
      o <- build_seurat_from_10x(raw$counts[[i]], project = sid)
      o$sample <- sid
      o$group <- as.character(raw$meta$group[i])
      objs[[sid]] <- o
    }
    obj <- merge(objs[[1]], y = objs[-1], add.cell.ids = names(objs))
    obj <- run_seurat_qc_cluster(obj)
    if ("JoinLayers" %in% ls("package:Seurat")) obj <- JoinLayers(obj, assay = "RNA")
  } else {
    obj <- readRDS(seurat_f)
    if ("JoinLayers" %in% ls("package:Seurat")) obj <- JoinLayers(obj, assay = "RNA")
  }

  obj <- filter_seurat_by_groups(obj, new_keep)
  if ("JoinLayers" %in% ls("package:Seurat")) obj <- JoinLayers(obj, assay = "RNA")
  saveRDS(obj, seurat_f)

  obj <- annotate_clusters_by_markers(obj, CARDIAC_MARKERS, "celltype")
  saveRDS(obj, seurat_f)
  prop <- obj@meta.data %>% tibble::as_tibble() %>% count(group, celltype, name = "n")
  write.csv(prop, file.path(p$表格, paste0(ds, "_细胞类型比例.csv")), row.names = FALSE)

  cfg_stub <- list(deg_padj = 0.05, deg_logfc = 1.0, run_immune_subset = TRUE)
  immune_obj <- subset_immune_recluster(obj)
  if (!is.null(immune_obj)) saveRDS(immune_obj, file.path(p$中间数据, paste0(ds, "_immune.rds")))
  save_all_scrna_figures(obj, ds, p, cfg_stub, immune_obj)

  list(
    before_cells = if (!is.null(before_prop)) sum(before_prop$n) else NA,
    after_cells = sum(prop$n),
    before_groups = if (!is.null(before_prop)) sort(unique(before_prop$group)) else NA,
    after_groups = sort(unique(prop$group)),
    before_prop = before_prop,
    after_prop = prop
  )
}

collect_baseline_snapshot <- function() {
  rows <- list()
  for (ds in c(SCRNA_DS, "GSE267388")) {
    p <- init_dataset_paths(PROJECT_ROOT, ds)
    deg_f <- file.path(p$表格, paste0(ds, "_显著差异基因.csv"))
    mams_f <- file.path(p$表格, paste0(ds, "_MAMs交集基因.csv"))
    prop_f <- file.path(p$表格, if (ds == "GSE267388") paste0(ds, "_估算细胞比例.csv")
                         else paste0(ds, "_细胞类型比例.csv"))
    rows[[length(rows) + 1]] <- tibble(
      dataset = ds, layer = "tissue_whole",
      n_sig_deg = if (file.exists(deg_f)) nrow(read.csv(deg_f)) else NA,
      n_mams_inter = if (file.exists(mams_f)) nrow(read.csv(mams_f)) else NA,
      n_total = if (file.exists(prop_f)) {
        d <- read.csv(prop_f)
        if ("n" %in% names(d)) sum(d$n) else length(unique(d$sample))
      } else NA
    )
    mac_f <- file.path(p$表格, paste0(ds, "_巨噬细胞_显著差异基因.csv"))
    mf <- file.path(p$表格, paste0(ds, "_巨噬细胞_MAMs交集基因.csv"))
    rows[[length(rows) + 1]] <- tibble(
      dataset = ds, layer = "macrophage",
      n_sig_deg = if (file.exists(mac_f)) nrow(read.csv(mac_f)) else 0,
      n_mams_inter = if (file.exists(mf)) nrow(read.csv(mf)) else 0,
      n_total = NA
    )
  }
  bind_rows(rows)
}

collect_tissue_mams_stats <- function(ds) {
  p <- init_dataset_paths(PROJECT_ROOT, ds)
  list(
    n_sig = {
      f <- file.path(p$表格, paste0(ds, "_显著差异基因.csv"))
      if (file.exists(f)) nrow(read.csv(f)) else NA
    },
    n_mams = {
      f <- file.path(p$表格, paste0(ds, "_MAMs交集基因.csv"))
      if (file.exists(f)) nrow(read.csv(f)) else NA
    }
  )
}
