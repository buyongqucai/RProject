# 01 跨物种保守 SCM 核心基因整合
# 数据来源：各数据集 _deg.rds / _deg_sig.rds（GEO 官方数据的差异分析结果）
# 思路：人 GSE79962（SCM vs Control）为参照，小鼠脓毒症模型 DEG 经同源映射后取交集，
#       找出跨物种、跨模型方向一致的保守失调基因。
source("00_公共函数.R", encoding = "UTF-8")
suppressPackageStartupMessages({ library(pheatmap); library(RColorBrewer) })

ds_use <- c("GSE79962", "GSE267388", "GSE207363", "GSE207177", "GSE190856")

# 收集每个数据集：全基因 log2FC（映射到人 symbol）+ 显著基因集合
get_human_lfc <- function(ds) {
  deg <- load_deg(ds); if (is.null(deg)) return(NULL)
  sp <- DATASETS$species[DATASETS$id == ds]
  g <- deg$gene; lfc <- deg$log2FC; padj <- deg$padj
  if (sp == "mouse") {
    map <- mouse_to_human(g)
    hs <- unname(map[g]); keep <- !is.na(hs)
    df <- tibble(gene = hs[keep], log2FC = lfc[keep], padj = padj[keep])
  } else {
    df <- tibble(gene = toupper(g), log2FC = lfc, padj = padj)
  }
  # 多对一取绝对值最大的 log2FC
  df %>% group_by(gene) %>%
    slice_max(order_by = abs(log2FC), n = 1, with_ties = FALSE) %>% ungroup() %>%
    transmute(gene, !!ds := log2FC,
              !!paste0(ds, "_sig") := as.integer(padj < 0.05 & abs(log2FC) > 1))
}

lst <- lapply(ds_use, get_human_lfc)
names(lst) <- ds_use
lst <- lst[!vapply(lst, is.null, logical(1))]

merged <- purrr::reduce(lst, full_join, by = "gene")
lfc_cols <- ds_use[ds_use %in% colnames(merged)]
sig_cols <- paste0(lfc_cols, "_sig")

merged <- merged %>%
  mutate(across(all_of(sig_cols), ~ replace_na(., 0L)))

# 人显著基因
human_sig <- merged %>% filter(GSE79962_sig == 1)
mouse_sig_cols <- setdiff(sig_cols, "GSE79962_sig")

# 每个基因在小鼠数据集中显著的次数
mouse_lfc_cols <- setdiff(lfc_cols, "GSE79962")
mouse_sig_cols2 <- paste0(mouse_lfc_cols, "_sig")
conserved <- human_sig %>%
  mutate(
    n_mouse_sig = rowSums(across(all_of(mouse_sig_cols2)), na.rm = TRUE),
    human_dir = ifelse(GSE79962 > 0, "Up", "Down")
  ) %>%
  filter(n_mouse_sig >= 1)

# 方向一致：小鼠中显著且与人同向的数据集数（向量化，避免 apply 类型强制）
human_sign <- sign(conserved$GSE79962)
concord <- integer(nrow(conserved))
for (i in seq_along(mouse_lfc_cols)) {
  dc <- mouse_lfc_cols[i]; sc <- mouse_sig_cols2[i]
  same_dir <- !is.na(conserved[[dc]]) & (sign(conserved[[dc]]) == human_sign) &
    (conserved[[sc]] %in% 1)
  concord <- concord + as.integer(same_dir)
}
conserved$n_concordant <- concord

core <- conserved %>% filter(n_concordant >= 1) %>%
  arrange(desc(n_concordant), desc(abs(GSE79962)))

save_tab(core %>% select(gene, human_dir, n_mouse_sig, n_concordant, all_of(lfc_cols)),
         "01_跨物种保守核心基因.csv")
message("跨物种保守核心基因（人显著且≥1鼠模型同向显著）: ", nrow(core))

# 热图：核心基因 × 数据集 log2FC
top_core <- core %>% slice_max(n_concordant + abs(GSE79962), n = min(40, nrow(core)))
mat <- as.matrix(top_core[, lfc_cols]); rownames(mat) <- top_core$gene
mat[is.na(mat)] <- 0
if (nrow(mat) >= 2) {
  pdf(file.path(EXT$图形, "01_跨物种保守基因_log2FC热图.pdf"), width = 8, height = 10)
  pheatmap(mat, cluster_cols = FALSE, fontsize_row = 7,
           main = "跨物种保守失调基因 log2FC",
           color = colorRampPalette(c("#4DBBD5", "white", "#E64B35"))(100),
           breaks = seq(-max(abs(mat)), max(abs(mat)), length.out = 101))
  dev.off()
}

# 各数据集显著 DEG 数量条形图（映射到人后）
counts <- tibble(dataset = lfc_cols,
                 n_sig = sapply(sig_cols, function(s) sum(merged[[s]], na.rm = TRUE)))
p_cnt <- ggplot(counts, aes(x = reorder(dataset, -n_sig), y = n_sig, fill = dataset)) +
  geom_col() + geom_text(aes(label = n_sig), vjust = -0.3, size = 3) +
  ext_theme() + theme(legend.position = "none", axis.text.x = element_text(angle = 30, hjust = 1)) +
  labs(title = "各数据集显著 DEG 数（映射到人 symbol 后）", x = NULL, y = "显著基因数")
save_fig(p_cnt, "01_各数据集DEG计数.pdf", width = 7, height = 5)

saveRDS(core, file.path(EXT$中间, "01_conserved_core.rds"))
message("完成: 01_跨物种保守特征.R")
