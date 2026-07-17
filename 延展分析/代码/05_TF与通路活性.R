# 05 转录因子活性 + 通路活性（decoupleR + DoRothEA + PROGENy）
# 数据来源：各数据集 DEG 的 t 统计量（差异方向强度）
# 意义：从靶基因整体变化反推“上游调控子(TF)与信号通路”的激活/抑制，找 master regulators
source("00_公共函数.R", encoding = "UTF-8")
suppressPackageStartupMessages({ library(decoupleR); library(dorothea); library(progeny) })

get_dorothea_net <- function(species) {
  if (species == "human") data("dorothea_hs", package = "dorothea", envir = environment())
  net <- if (species == "human") get("dorothea_hs") else { data("dorothea_mm", package = "dorothea", envir = environment()); get("dorothea_mm") }
  net <- net[net$confidence %in% c("A", "B", "C"), ]
  data.frame(source = net$tf, target = net$target, mor = net$mor)
}

get_progeny_net <- function(species) {
  org <- if (species == "human") "Human" else "Mouse"
  m <- progeny::getModel(organism = org, top = 500)
  df <- as.data.frame(as.table(as.matrix(m)))
  colnames(df) <- c("target", "source", "weight")
  df <- df[df$weight != 0, ]
  df
}

run_one <- function(ds) {
  deg <- load_deg(ds); if (is.null(deg)) return(invisible(NULL))
  sp <- DATASETS$species[DATASETS$id == ds]
  stat <- if ("t" %in% colnames(deg)) deg$t else sign(deg$log2FC) * -log10(pmax(deg$pvalue, 1e-300))
  mat <- matrix(stat, ncol = 1, dimnames = list(deg$gene, "SCM_vs_Ctrl"))
  mat <- mat[!is.na(rownames(mat)) & rownames(mat) != "", , drop = FALSE]

  # ---- TF 活性 ----
  net <- get_dorothea_net(sp)
  acts <- decoupleR::run_ulm(mat, net, .source = "source", .target = "target", .mor = "mor", minsize = 5)
  acts <- acts[acts$statistic == "ulm", ]
  acts <- acts[order(-abs(acts$score)), ]
  save_tab(as.data.frame(acts), paste0("05_TF活性_", ds, ".csv"))

  top <- rbind(head(acts[order(-acts$score), ], 15), head(acts[order(acts$score), ], 15))
  top <- top[!duplicated(top$source), ]
  p <- ggplot(top, aes(x = reorder(source, score), y = score, fill = score > 0)) +
    geom_col() + coord_flip() +
    scale_fill_manual(values = c(`TRUE` = "#E64B35", `FALSE` = "#4DBBD5"),
                      labels = c(`TRUE` = "激活", `FALSE` = "抑制"), name = NULL) +
    ext_theme() + labs(title = paste0(ds, " 转录因子活性(DoRothEA)"), x = NULL, y = "活性得分")
  save_fig(p, paste0("05_TF活性_", ds, ".pdf"), width = 8, height = 8)

  # ---- 通路活性 (PROGENy) ----
  pnet <- get_progeny_net(sp)
  pacts <- decoupleR::run_mlm(mat, pnet, .source = "source", .target = "target", .mor = "weight", minsize = 5)
  pacts <- pacts[pacts$statistic == "mlm", ]
  pacts <- pacts[order(-pacts$score), ]
  save_tab(as.data.frame(pacts), paste0("05_通路活性PROGENy_", ds, ".csv"))
  pp <- ggplot(pacts, aes(x = reorder(source, score), y = score, fill = score > 0)) +
    geom_col() + coord_flip() +
    scale_fill_manual(values = c(`TRUE` = "#E64B35", `FALSE` = "#4DBBD5"),
                      labels = c(`TRUE` = "激活", `FALSE` = "抑制"), name = NULL) +
    ext_theme() + labs(title = paste0(ds, " 信号通路活性(PROGENy)"), x = NULL, y = "活性得分")
  save_fig(pp, paste0("05_通路活性PROGENy_", ds, ".pdf"), width = 7, height = 6)

  message("完成 TF/通路活性: ", ds, "; top 激活 TF: ",
          paste(head(acts$source[acts$score > 0], 5), collapse = ", "))
  list(acts = acts, net = net)
}

res_hs <- run_one("GSE79962")
run_one("GSE207177")

# 保存人 master regulators + regulon（供 06 虚拟敲除）
if (!is.null(res_hs)) saveRDS(res_hs, file.path(EXT$中间, "05_tf_GSE79962.rds"))
message("完成: 05_TF与通路活性.R")
