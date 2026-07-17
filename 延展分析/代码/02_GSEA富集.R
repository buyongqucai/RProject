# 02 GSEA：GO 生物过程 + KEGG 通路（基于完整 ranked DEG 列表）
# 数据来源：各数据集 _deg.rds；基因集来自 org.*.eg.db（GO）与 KEGG REST（在线）
# 用 clusterProfiler::gseGO / gseKEGG，避免 msigdbr 数据包依赖
# 意义：GSEA 用全基因排序捕捉“整体协同上/下调”的通路方向(NES)，补充 ORA
source("00_公共函数.R", encoding = "UTF-8")
suppressPackageStartupMessages({ library(clusterProfiler) })

ds_org <- list(GSE79962 = list(db = "org.Hs.eg.db", kegg = "hsa"),
               GSE267388 = list(db = "org.Mm.eg.db", kegg = "mmu"),
               GSE207177 = list(db = "org.Mm.eg.db", kegg = "mmu"))

nes_barplot <- function(df, title, out) {
  if (is.null(df) || nrow(df) == 0) return(invisible(NULL))
  df$Description <- ifelse(nchar(df$Description) > 45, paste0(substr(df$Description, 1, 45), "..."), df$Description)
  top <- rbind(head(df[order(-df$NES), ], 12), head(df[order(df$NES), ], 12))
  top <- top[!duplicated(top$ID), ]
  p <- ggplot(top, aes(x = reorder(Description, NES), y = NES, fill = NES > 0)) +
    geom_col() + coord_flip() +
    scale_fill_manual(values = c(`TRUE` = "#E64B35", `FALSE` = "#4DBBD5"),
                      labels = c(`TRUE` = "激活", `FALSE` = "抑制"), name = NULL) +
    ext_theme() + theme(axis.text.y = element_text(size = 7)) +
    labs(title = title, x = NULL, y = "NES")
  save_fig(p, out, width = 10, height = 8)
}

run_one <- function(ds) {
  deg <- load_deg(ds); if (is.null(deg)) return(invisible(NULL))
  info <- ds_org[[ds]]
  suppressPackageStartupMessages(library(info$db, character.only = TRUE))
  orgdb <- get(info$db, envir = asNamespace(info$db))

  ranks_sym <- deg_rank_vector(deg)
  if (length(ranks_sym) < 100) { message(ds, " 基因过少，跳过"); return(invisible(NULL)) }

  # GO BP（SYMBOL 直接可用）
  set.seed(42)
  ego <- tryCatch(gseGO(geneList = ranks_sym, OrgDb = orgdb, ont = "BP", keyType = "SYMBOL",
                        minGSSize = 10, maxGSSize = 500, pvalueCutoff = 0.25, eps = 0, verbose = FALSE),
                  error = function(e) { message("gseGO 失败(", ds, "): ", conditionMessage(e)); NULL })
  if (!is.null(ego) && nrow(as.data.frame(ego)) > 0) {
    save_tab(as.data.frame(ego), paste0("02_GSEA_GO_", ds, ".csv"))
    nes_barplot(as.data.frame(ego), paste0(ds, " GSEA GO-BP（NES）"), paste0("02_GSEA_GO_", ds, ".pdf"))
  }

  # KEGG（需 ENTREZ）
  map <- suppressMessages(bitr(names(ranks_sym), "SYMBOL", "ENTREZID", OrgDb = orgdb))
  map <- map[!duplicated(map$SYMBOL), ]
  ranks_ent <- ranks_sym[map$SYMBOL]; names(ranks_ent) <- map$ENTREZID
  ranks_ent <- sort(ranks_ent[!is.na(names(ranks_ent))], decreasing = TRUE)
  set.seed(42)
  ekegg <- tryCatch(gseKEGG(geneList = ranks_ent, organism = info$kegg,
                            minGSSize = 10, maxGSSize = 500, pvalueCutoff = 0.25, eps = 0, verbose = FALSE),
                    error = function(e) { message("gseKEGG 失败(", ds, "): ", conditionMessage(e)); NULL })
  if (!is.null(ekegg) && nrow(as.data.frame(ekegg)) > 0) {
    save_tab(as.data.frame(ekegg), paste0("02_GSEA_KEGG_", ds, ".csv"))
    nes_barplot(as.data.frame(ekegg), paste0(ds, " GSEA KEGG（NES）"), paste0("02_GSEA_KEGG_", ds, ".pdf"))
  }
  message("完成 GSEA: ", ds)
}

for (ds in names(ds_org)) run_one(ds)
message("完成: 02_GSEA富集.R")
