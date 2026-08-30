# CellPhoneDB 式细胞通讯：基于 AverageExpression，兼容 Seurat v5 多层 assay

suppressPackageStartupMessages({
  library(Seurat)
  library(tidyverse)
})

if (!exists("FIG_DPI")) {
  pr <- if (file.exists("RProject.Rproj")) normalizePath(".") else {
    p <- normalizePath(getwd(), winslash = "/")
    for (i in 1:6) { if (file.exists(file.path(p, "RProject.Rproj"))) break; p <- dirname(p) }
    p
  }
  source(file.path(pr, "共享脚本", "工具_统一出图.R"), encoding = "UTF-8")
}

#' 返回 list(ctrl, case, cts, grp_ct_mean, LR)
prepare_cell_comm <- function(obj, case, ctrl, lr_pairs) {
  DefaultAssay(obj) <- "RNA"
  if ("JoinLayers" %in% ls("package:Seurat")) {
    obj <- tryCatch(JoinLayers(obj, assay = "RNA"), error = function(e) obj)
  }
  meta <- obj@meta.data
  meta$celltype <- as.character(meta$celltype)
  cts <- names(which(table(meta$celltype) >= 50))
  if (length(cts) < 2) return(NULL)
  obj$group_celltype <- paste(obj$group, obj$celltype, sep = "|")
  avg <- AverageExpression(obj, group.by = "group_celltype", assays = "RNA",
                           slot = "data", verbose = FALSE)
  avg_mat <- as.matrix(avg$RNA)
  grp_ct_mean <- setNames(
    lapply(colnames(avg_mat), function(col) {
      setNames(expm1(avg_mat[, col]), rownames(avg_mat))
    }),
    colnames(avg_mat)
  )
  genes <- rownames(avg_mat)
  LR <- lr_pairs[lr_pairs$ligand %in% genes & lr_pairs$receptor %in% genes, ]
  list(ctrl = ctrl, case = case, cts = cts, grp_ct_mean = grp_ct_mean, LR = LR)
}

comm_matrix_from_prep <- function(prep, group) {
  cts <- prep$cts; LR <- prep$LR; gcm <- prep$grp_ct_mean
  M <- matrix(0, length(cts), length(cts), dimnames = list(cts, cts))
  for (s in cts) for (r in cts) {
    key_s <- paste(group, s, sep = "|")
    key_r <- paste(group, r, sep = "|")
    if (!key_s %in% names(gcm) || !key_r %in% names(gcm)) next
    lv <- gcm[[key_s]][LR$ligand]
    rv <- gcm[[key_r]][LR$receptor]
    M[s, r] <- sum(lv * rv, na.rm = TRUE)
  }
  M
}

run_cell_comm_plots <- function(ds, prep, tab_dir, fig_dir) {
  if (is.null(prep)) return(invisible(NULL))
  case <- prep$case; ctrl <- prep$ctrl; cts <- prep$cts; LR <- prep$LR
  M_case <- comm_matrix_from_prep(prep, case)
  M_ctrl <- comm_matrix_from_prep(prep, ctrl)
  Mdiff <- M_case - M_ctrl
  write.csv(data.frame(sender = rownames(M_case), M_case, check.names = FALSE),
            file.path(tab_dir, paste0(ds, "_细胞通讯强度_", case, ".csv")), row.names = FALSE)
  write.csv(data.frame(sender = rownames(Mdiff), Mdiff, check.names = FALSE),
            file.path(tab_dir, paste0(ds, "_细胞通讯差异_", case, "减", ctrl, ".csv")), row.names = FALSE)
  suppressPackageStartupMessages(library(pheatmap))
  pal <- colorRampPalette(c("#4DBBD5", "white", "#E64B35"))(100)
  safe_pdf(file.path(fig_dir, paste0(ds, "_细胞通讯热图.pdf")), width = 12, height = 11, {
    pheatmap(M_case, cluster_rows = FALSE, cluster_cols = FALSE,
           main = paste0(ds, " 细胞通讯强度（", case, "）"),
           color = colorRampPalette(c("white", "#E64B35"))(100),
           display_numbers = TRUE, number_format = "%.1f", fontsize_number = 7)
    lim <- max(abs(Mdiff), na.rm = TRUE); if (lim == 0) lim <- 1
    pheatmap(Mdiff, cluster_rows = FALSE, cluster_cols = FALSE,
           main = paste0(ds, " 细胞通讯变化（", case, " − ", ctrl, "）"),
           color = pal, breaks = seq(-lim, lim, length.out = 101),
           display_numbers = TRUE, number_format = "%.1f", fontsize_number = 7)
  })
  gcm <- prep$grp_ct_mean
  inter <- list()
  for (s in cts) for (r in cts) for (i in seq_len(nrow(LR))) {
    l <- LR$ligand[i]; rec <- LR$receptor[i]
    sc_case <- gcm[[paste(case, s, sep = "|")]][l] * gcm[[paste(case, r, sep = "|")]][rec]
    sc_ctrl <- gcm[[paste(ctrl, s, sep = "|")]][l] * gcm[[paste(ctrl, r, sep = "|")]][rec]
    inter[[length(inter) + 1]] <- tibble(pair = paste0(l, "→", rec), axis = paste0(s, "→", r),
                                         delta = as.numeric(sc_case - sc_ctrl))
  }
  inter <- bind_rows(inter) %>% arrange(desc(delta)) %>% filter(delta > 0) %>% head(25)
  if (nrow(inter)) {
    inter$label <- paste0(inter$pair, " | ", inter$axis)
    write.csv(inter, file.path(tab_dir, paste0(ds, "_Top增强通讯对.csv")), row.names = FALSE)
    pi <- ggplot(inter, aes(reorder(label, delta), delta)) +
      geom_col(fill = "#E64B35") + coord_flip() + theme_bw() +
      theme(axis.text.y = element_text(size = 6)) +
      labs(title = paste0(ds, " 疾病中增强最多的配体-受体通讯"), x = NULL,
           y = paste0("通讯强度变化（", case, " − ", ctrl, "）"))
    safe_ggsave(file.path(fig_dir, paste0(ds, "_Top增强通讯对.pdf")), pi, width = 11, height = max(8, nrow(inter) * 0.35))
  }
  mac_like <- grep("Macrophage|Monocyte", cts, ignore.case = TRUE, value = TRUE)
  cm_like <- grep("Cardiomyocyte", cts, ignore.case = TRUE, value = TRUE)
  if (length(mac_like) && length(cm_like)) {
    mac_cm <- list()
    for (m in mac_like) for (c in cm_like) for (i in seq_len(nrow(LR))) {
      l <- LR$ligand[i]; rec <- LR$receptor[i]
      d <- gcm[[paste(case, m, sep = "|")]][l] * gcm[[paste(case, c, sep = "|")]][rec] -
        gcm[[paste(ctrl, m, sep = "|")]][l] * gcm[[paste(ctrl, c, sep = "|")]][rec]
      mac_cm[[length(mac_cm) + 1]] <- tibble(pair = paste0(l, "→", rec), axis = paste0(m, "→", c), delta = d)
    }
    mac_cm <- bind_rows(mac_cm) %>% arrange(desc(delta)) %>% filter(delta > 0) %>% head(15)
    if (nrow(mac_cm)) {
      mac_cm$label <- paste0(mac_cm$pair, " | ", mac_cm$axis)
      write.csv(mac_cm, file.path(tab_dir, paste0(ds, "_巨噬心肌通讯增强.csv")), row.names = FALSE)
      pm <- ggplot(mac_cm, aes(reorder(label, delta), delta)) +
        geom_col(fill = "#3C5488") + coord_flip() + theme_bw() +
        theme(axis.text.y = element_text(size = 7)) +
        labs(title = paste0(ds, " 巨噬细胞→心肌细胞 增强通讯"), x = NULL, y = "Δ通讯强度")
      safe_ggsave(file.path(fig_dir, paste0(ds, "_巨噬心肌通讯.pdf")), pm, width = 11, height = max(7, nrow(mac_cm) * 0.4))
    }
  }
  invisible(TRUE)
}
