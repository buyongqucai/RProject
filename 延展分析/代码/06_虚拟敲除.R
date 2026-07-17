# 06 虚拟敲除（regulon-based in silico knockout）
# 数据来源：05 得到的 TF 活性 + DoRothEA 调控子 + GSE79962 DEG
# 思路：对疾病中最活跃的 master regulator TF 做“在硅敲除”——移除该 TF 的调控驱动后，
#       其“方向一致的疾病靶基因”被预测回落（rescued）；量化可被逆转的疾病基因及其通路，
#       从而把 TF（第5步）与可干预的下游程序（治疗靶点）连接起来。
# 说明：这是透明的调控子传播式虚拟敲除；更重的机制模型可用 CellOracle/scTenifoldKnk（见 skill）。
source("00_公共函数.R", encoding = "UTF-8")
suppressPackageStartupMessages({ library(clusterProfiler); library(org.Hs.eg.db) })

ds <- "GSE79962"
tf_rds <- file.path(EXT$中间, "05_tf_GSE79962.rds")
if (!file.exists(tf_rds)) stop("请先运行 05_TF与通路活性.R")
tf <- readRDS(tf_rds)
acts <- tf$acts; net <- tf$net
deg <- load_deg(ds)
deg$stat <- if ("t" %in% colnames(deg)) deg$t else sign(deg$log2FC) * -log10(pmax(deg$pvalue, 1e-300))
deg_map <- setNames(deg$log2FC, deg$gene)
stat_map <- setNames(deg$stat, deg$gene)
sig_genes <- deg$gene[deg$padj < 0.05 & abs(deg$log2FC) > 1]

# 候选 master regulators：活性显著且 |score| 大，取激活方向前 6
mr <- acts %>% filter(p_value < 0.05) %>% arrange(desc(score)) %>% head(6)

# 单个 TF 的虚拟敲除：找“方向一致的疾病驱动靶基因”（敲除后被逆转）
knock_out_tf <- function(tfname) {
  reg <- net[net$source == tfname, c("target", "mor")]
  reg <- reg[reg$target %in% names(stat_map), ]
  if (nrow(reg) == 0) return(NULL)
  tf_dir <- sign(acts$score[acts$source == tfname][1])
  reg$target_stat <- stat_map[reg$target]
  reg$expected_dir <- sign(reg$mor) * tf_dir            # TF 激活时靶基因预期方向
  reg$driven <- sign(reg$target_stat) == reg$expected_dir
  reg$is_deg <- reg$target %in% sig_genes
  rescued <- reg$target[reg$driven & reg$is_deg]        # 敲除可逆转的显著疾病基因
  list(tf = tfname, n_target = nrow(reg), n_driven = sum(reg$driven),
       n_rescued = length(rescued), rescued = rescued, reg = reg)
}

ko_list <- lapply(mr$source, knock_out_tf)
ko_list <- ko_list[!vapply(ko_list, is.null, logical(1))]

summ <- tibble(
  TF = vapply(ko_list, function(x) x$tf, character(1)),
  regulon_size = vapply(ko_list, function(x) x$n_target, integer(1)),
  driven_targets = vapply(ko_list, function(x) x$n_driven, integer(1)),
  rescued_DEGs = vapply(ko_list, function(x) x$n_rescued, integer(1))
) %>% arrange(desc(rescued_DEGs))
save_tab(summ, "06_虚拟敲除_TF逆转疾病基因数.csv")

p <- ggplot(summ, aes(x = reorder(TF, rescued_DEGs), y = rescued_DEGs, fill = TF)) +
  geom_col() + geom_text(aes(label = rescued_DEGs), hjust = -0.2, size = 3) + coord_flip() +
  ext_theme() + theme(legend.position = "none") +
  labs(title = paste0(ds, " 虚拟敲除：各 master TF 可逆转的显著疾病基因数"),
       x = "被敲除的转录因子", y = "可逆转的显著疾病 DEG 数")
save_fig(p, "06_虚拟敲除_可逆转基因数.pdf", width = 8, height = 5)

# 对 #1 TF：rescued 基因的疾病 log2FC 条形图 + 富集
top_ko <- ko_list[[which.max(summ$rescued_DEGs)]]
best_tf <- summ$TF[1]; top_ko <- ko_list[[which(vapply(ko_list, function(x) x$tf, character(1)) == best_tf)]]
rescued <- top_ko$rescued
if (length(rescued) >= 3) {
  rdf <- tibble(gene = rescued, log2FC = deg_map[rescued]) %>% arrange(desc(abs(log2FC))) %>% head(25)
  pr <- ggplot(rdf, aes(x = reorder(gene, log2FC), y = log2FC, fill = log2FC > 0)) +
    geom_col() + coord_flip() +
    scale_fill_manual(values = c(`TRUE` = "#E64B35", `FALSE` = "#4DBBD5"),
                      labels = c(`TRUE` = "疾病中上调", `FALSE` = "疾病中下调"), name = NULL) +
    ext_theme() + labs(title = paste0("敲除 ", best_tf, " 可逆转的疾病靶基因"),
                       x = NULL, y = "疾病 log2FC (SCM vs Control)")
  save_fig(pr, paste0("06_虚拟敲除_", best_tf, "_逆转靶基因.pdf"), width = 8, height = 7)

  ent <- suppressMessages(bitr(rescued, "SYMBOL", "ENTREZID", OrgDb = org.Hs.eg.db))
  ego <- tryCatch(enrichGO(ent$ENTREZID, OrgDb = org.Hs.eg.db, ont = "BP",
                           pvalueCutoff = 0.05, qvalueCutoff = 0.2, readable = TRUE),
                  error = function(e) NULL)
  if (!is.null(ego) && nrow(as.data.frame(ego)) > 0) {
    save_tab(as.data.frame(ego), paste0("06_虚拟敲除_", best_tf, "_逆转基因GO.csv"))
    pg <- dotplot(ego, showCategory = 12) + ggtitle(paste0("敲除 ", best_tf, " 逆转基因的 GO-BP"))
    save_fig(pg, paste0("06_虚拟敲除_", best_tf, "_逆转基因GO.pdf"), width = 9, height = 6)
  }
}

saveRDS(list(summ = summ, ko_list = ko_list, best_tf = best_tf),
        file.path(EXT$中间, "06_knockout.rds"))
message("完成: 06_虚拟敲除.R; 首选敲除靶点: ", best_tf,
        " (逆转 ", summ$rescued_DEGs[1], " 个疾病基因)")
