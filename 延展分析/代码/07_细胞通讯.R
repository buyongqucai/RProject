# 07 细胞通讯（配体-受体）：免疫细胞→心肌细胞的炎症信号（疾病 vs 对照）
# 数据来源：GSE207177 Seurat（含 celltype、group）；配体-受体来自文献 curated 列表
# 方法：CellPhoneDB 式打分——通讯强度 = 发送细胞平均配体表达 × 接收细胞平均受体表达
# 意义：DEG/通路是“细胞内”，此处刻画“细胞间”信号，揭示免疫-心肌串扰如何驱动 SCM
source("00_公共函数.R", encoding = "UTF-8")
suppressPackageStartupMessages({ library(Seurat); library(pheatmap); library(RColorBrewer) })

ds <- "GSE207177"
obj <- load_seurat(ds); DefaultAssay(obj) <- "RNA"; obj <- JoinLayers(obj, assay = "RNA")
case <- DATASETS$case[DATASETS$id == ds]; ctrl <- DATASETS$control[DATASETS$id == ds]

# curated 配体-受体对（心脏免疫-实质串扰核心；小鼠 symbol）
LR <- tibble::tribble(
  ~ligand, ~receptor,
  "Tnf","Tnfrsf1a", "Tnf","Tnfrsf1b", "Il1b","Il1r1", "Il1b","Il1rap",
  "Il6","Il6ra", "Il6","Il6st", "Ccl2","Ccr2", "Ccl3","Ccr1", "Ccl4","Ccr5",
  "Ccl5","Ccr5", "Cxcl2","Cxcr2", "Cxcl1","Cxcr2", "Cxcl10","Cxcr3",
  "Csf1","Csf1r", "Csf2","Csf2ra", "Csf3","Csf3r", "Tgfb1","Tgfbr1", "Tgfb1","Tgfbr2",
  "Spp1","Cd44", "Spp1","Itgav", "Icam1","Itgal", "Icam1","Itgb2", "Sele","Selplg",
  "Apoe","Trem2", "Apoe","Ldlr", "Pf4","Cxcr3", "Vegfa","Flt1", "Vegfa","Kdr",
  "Pdgfb","Pdgfrb", "Angpt1","Tek", "Il10","Il10ra", "Ifng","Ifngr1",
  "Cxcl12","Cxcr4", "Ccl7","Ccr2", "Il18","Il18r1", "Nampt","Insr"
)

data_mat <- GetAssayData(obj, layer = "data")
meta <- obj@meta.data
meta$celltype <- as.character(meta$celltype)
keep_ct <- names(which(table(meta$celltype) >= 50))
cts <- sort(keep_ct)

# 各 (group, celltype) 的平均归一化表达（非 log 空间）
mean_expr <- function(cells) {
  if (length(cells) == 0) return(setNames(rep(0, nrow(data_mat)), rownames(data_mat)))
  Matrix::rowMeans(expm1(data_mat[, cells, drop = FALSE]))
}
grp_ct_mean <- list()
for (g in c(ctrl, case)) for (c in cts) {
  cells <- rownames(meta)[meta$group == g & meta$celltype == c]
  grp_ct_mean[[paste(g, c, sep = "|")]] <- mean_expr(cells)
}

genes <- rownames(data_mat)
LR <- LR[LR$ligand %in% genes & LR$receptor %in% genes, ]

# 通讯矩阵：sender × receiver（各 group），值 = 所有 L-R 对得分之和
comm_matrix <- function(g) {
  M <- matrix(0, length(cts), length(cts), dimnames = list(cts, cts))
  for (s in cts) for (r in cts) {
    lv <- grp_ct_mean[[paste(g, s, sep = "|")]][LR$ligand]
    rv <- grp_ct_mean[[paste(g, r, sep = "|")]][LR$receptor]
    M[s, r] <- sum(lv * rv, na.rm = TRUE)
  }
  M
}
M_ctrl <- comm_matrix(ctrl); M_case <- comm_matrix(case)
Mdiff <- M_case - M_ctrl

save_tab(data.frame(sender = rownames(M_case), M_case, check.names = FALSE),
         paste0("07_通讯强度_", case, "_", ds, ".csv"))
save_tab(data.frame(sender = rownames(Mdiff), Mdiff, check.names = FALSE),
         paste0("07_通讯差异_", case, "减", ctrl, "_", ds, ".csv"))

pal <- colorRampPalette(c("#4DBBD5", "white", "#E64B35"))(100)
pdf(file.path(EXT$图形, paste0("07_细胞通讯热图_", ds, ".pdf")), width = 9, height = 8)
pheatmap(M_case, cluster_rows = FALSE, cluster_cols = FALSE, main = paste0(ds, " 细胞通讯强度（", case, "）"),
         color = colorRampPalette(c("white", "#E64B35"))(100),
         display_numbers = TRUE, number_format = "%.1f", fontsize_number = 6)
lim <- max(abs(Mdiff))
pheatmap(Mdiff, cluster_rows = FALSE, cluster_cols = FALSE,
         main = paste0(ds, " 细胞通讯变化（", case, " − ", ctrl, "）"),
         color = pal, breaks = seq(-lim, lim, length.out = 101),
         display_numbers = TRUE, number_format = "%.1f", fontsize_number = 6)
dev.off()

# 疾病中增强最多的 L-R 相互作用（发送→接收）
inter <- list()
for (s in cts) for (r in cts) for (i in seq_len(nrow(LR))) {
  l <- LR$ligand[i]; rec <- LR$receptor[i]
  sc_case <- grp_ct_mean[[paste(case, s, sep = "|")]][l] * grp_ct_mean[[paste(case, r, sep = "|")]][rec]
  sc_ctrl <- grp_ct_mean[[paste(ctrl, s, sep = "|")]][l] * grp_ct_mean[[paste(ctrl, r, sep = "|")]][rec]
  inter[[length(inter) + 1]] <- tibble(pair = paste0(l, "→", rec),
                                       axis = paste0(s, "→", r),
                                       delta = as.numeric(sc_case - sc_ctrl))
}
inter <- bind_rows(inter) %>% arrange(desc(delta)) %>% filter(delta > 0) %>% head(25)
inter$label <- paste0(inter$pair, " | ", inter$axis)
save_tab(inter, paste0("07_Top增强通讯对_", ds, ".csv"))
pi <- ggplot(inter, aes(x = reorder(label, delta), y = delta)) +
  geom_col(fill = "#E64B35") + coord_flip() + ext_theme() +
  theme(axis.text.y = element_text(size = 6)) +
  labs(title = paste0(ds, " 疾病中增强最多的配体-受体通讯"), x = NULL,
       y = paste0("通讯强度变化（", case, " − ", ctrl, "）"))
save_fig(pi, paste0("07_Top增强通讯对_", ds, ".pdf"), width = 9, height = 8)

message("完成: 07_细胞通讯.R; 保留细胞类型: ", paste(cts, collapse = ", "))
