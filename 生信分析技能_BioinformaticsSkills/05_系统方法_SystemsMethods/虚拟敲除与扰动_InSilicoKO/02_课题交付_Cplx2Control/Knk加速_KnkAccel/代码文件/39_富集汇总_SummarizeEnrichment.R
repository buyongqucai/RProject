# Cross-subtype, cross-gene enrichment summary (all engines).
# ONLY official ORA that passed screening (BH p<0.05 and q<0.2 on response genes).
# Exploratory Top-50 DR enrichments are ignored.
options(stringsAsFactors = FALSE)

desk <- "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除"
viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
if (file.exists(viz)) source(viz, encoding = "UTF-8")
suppressPackageStartupMessages(library(ggplot2))
if (!exists("theme_journal")) theme_journal <- function(...) ggplot2::theme_bw()
fill1 <- if (exists("bioinfo_palette")) bioinfo_palette[1] else "#6B8F71"

save_plot <- function(p, dir, stem, w = 7, h = 5) {
  dir.create(dir, recursive = TRUE, showWarnings = FALSE)
  if (exists("save_plot_pub", mode = "function")) {
    save_plot_pub(p, stem = stem, width = w, height = h, dpi = 600, out_dir = dir)
  } else {
    ggplot2::ggsave(file.path(dir, paste0(stem, ".png")), p, width = w, height = h, dpi = 600, bg = "white")
    ggplot2::ggsave(file.path(dir, paste0(stem, ".svg")), p, width = w, height = h, bg = "white")
  }
}

pass_screen <- function(go) {
  if (!ncol(go) || !nrow(go)) return(go[0, , drop = FALSE])
  if (!"term" %in% names(go) && "Description" %in% names(go)) go$term <- go$Description
  ok <- is.finite(go$p.adjust) & go$p.adjust < 0.05
  if ("qvalue" %in% names(go)) {
    q <- go$qvalue
    ok <- ok & (is.na(q) | q < 0.2)
  }
  go[ok, , drop = FALSE]
}

out_root <- file.path(desk, "结果文件", "_跨亚群", "富集汇总_EnrichSummary")
tab_dir <- file.path(out_root, "数据文件")
fig_dir <- file.path(out_root, "图片文件")
rep_dir <- file.path(out_root, "报告文件")
for (d in c(tab_dir, fig_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

subtypes <- c("PEP", "NF1")
targets <- c("Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21")
controls <- list(
  scTenifoldKnk_1.4.3_GPU = c(PEP = "Ret", NF1 = "Rdx"),
  scTenifoldKnk_1.4.3_CPU = c(PEP = "Ret", NF1 = "Rdx"),
  GenKI = c(PEP = "Abcc8", NF1 = "Gm15551")
)

rows <- list()
term_rows <- list()

for (algo in names(controls)) {
  for (st in subtypes) {
    ctrl <- controls[[algo]][[st]]
    for (gene in c(targets, ctrl)) {
      gene_dir <- file.path(desk, "结果文件", st, algo, gene)
      tab <- file.path(gene_dir, "数据文件")
      if (!dir.exists(tab)) next
      is_ctrl <- identical(gene, ctrl)

      n_resp <- NA_integer_
      top_gene <- ""
      if (algo == "GenKI") {
        resp_path <- file.path(tab, "响应基因_Responsive.csv")
        resp <- if (file.exists(resp_path)) read.csv(resp_path, check.names = FALSE) else data.frame()
        eff <- if (nrow(resp)) resp[resp$gene != gene, , drop = FALSE] else resp
        n_resp <- nrow(eff)
        top_gene <- if (nrow(eff)) as.character(eff$gene[1]) else ""
      } else {
        no_edge <- file.exists(file.path(gene_dir, "报告文件", "说明_无出边.txt"))
        resp_path <- file.path(tab, "响应基因_Responsive.csv")
        resp <- if (file.exists(resp_path)) read.csv(resp_path, check.names = FALSE) else data.frame()
        eff <- if (nrow(resp)) resp[resp$gene != gene & is.finite(resp$p.adj) & resp$p.adj < 0.05, , drop = FALSE] else resp
        n_resp <- if (no_edge) 0L else nrow(eff)
        top_gene <- if (nrow(eff)) as.character(eff$gene[1]) else ""
      }

      go <- data.frame()
      go_src <- ""
      parts <- list()
      go_p <- file.path(tab, "富集_GO.csv")
      if (!file.exists(go_p) && algo == "GenKI") go_p <- file.path(tab, "富集_GOBP.csv")
      if (file.exists(go_p)) {
        frame <- tryCatch(read.csv(go_p, check.names = FALSE), error = function(e) data.frame())
        if (ncol(frame) && nrow(frame)) {
          if (!"ontology" %in% names(frame) && "ONTOLOGY" %in% names(frame)) frame$ontology <- frame$ONTOLOGY
          if (!"ontology" %in% names(frame)) frame$ontology <- "BP"
          parts[["GO"]] <- frame
        }
      }
      kegg_p <- file.path(tab, "富集_KEGG.csv")
      if (file.exists(kegg_p)) {
        frame <- tryCatch(read.csv(kegg_p, check.names = FALSE), error = function(e) data.frame())
        if (ncol(frame) && nrow(frame)) {
          frame$ontology <- "KEGG"
          parts[["KEGG"]] <- frame
        }
      }
      if (length(parts)) {
        common <- Reduce(intersect, lapply(parts, names))
        go <- do.call(rbind, lapply(parts, function(x) x[, common, drop = FALSE]))
        go_src <- if (algo == "GenKI") "官方_GenKI响应基因_GO_BPCCMF_KEGG" else "官方_FDR响应基因_GO_BPCCMF_KEGG"
      }
      keep <- pass_screen(go)
      if (ncol(keep) && nrow(keep)) keep <- keep[order(keep$p.adjust), , drop = FALSE]

      rows[[paste(algo, st, gene)]] <- data.frame(
        engine = algo, subtype = st, knockout = gene, control = is_ctrl,
        n_response_excl_ko = n_resp,
        top_response_gene = top_gene,
        n_terms_pass_screen = nrow(keep),
        top_term = if (nrow(keep)) as.character(keep$term[1]) else "",
        top_term_padj = if (nrow(keep)) keep$p.adjust[1] else NA_real_,
        term_source = go_src,
        stringsAsFactors = FALSE
      )
      if (nrow(keep)) {
        k <- head(keep, 10)
        term_rows[[paste(algo, st, gene)]] <- data.frame(
          engine = algo, subtype = st, knockout = gene, control = is_ctrl,
          term = as.character(k$term),
          ontology = if ("ontology" %in% names(k)) as.character(k$ontology) else if ("ONTOLOGY" %in% names(k)) as.character(k$ONTOLOGY) else "BP",
          p.adjust = k$p.adjust,
          count = if ("Count" %in% names(k)) k$Count else NA_real_,
          stringsAsFactors = FALSE
        )
      }
    }
  }
}

summary_df <- do.call(rbind, rows)
write.csv(summary_df, file.path(tab_dir, "汇总_响应与富集_Summary.csv"), row.names = FALSE)
terms_df <- if (length(term_rows)) do.call(rbind, term_rows) else data.frame()
if (nrow(terms_df)) {
  write.csv(terms_df, file.path(tab_dir, "汇总_富集条目_TermsLong.csv"), row.names = FALSE)
} else if (file.exists(file.path(tab_dir, "汇总_富集条目_TermsLong.csv"))) {
  unlink(file.path(tab_dir, "汇总_富集条目_TermsLong.csv"))
}

# remove old explor-based heatmap if present and no official terms
old_heat <- list.files(fig_dir, pattern = "05_热图", full.names = TRUE)
if (length(old_heat) && !nrow(terms_df)) unlink(old_heat)

summary_df$label <- paste(summary_df$engine, summary_df$subtype, summary_df$knockout, sep = " / ")
summary_df$label <- factor(summary_df$label, levels = rev(unique(summary_df$label)))
p_cnt <- ggplot(summary_df, aes(n_response_excl_ko, label, fill = control)) +
  geom_col(width = 0.72) +
  geom_text(aes(label = n_response_excl_ko), hjust = -0.25, size = 2.9) +
  scale_fill_manual(values = c("FALSE" = fill1, "TRUE" = "#B0A44F"), labels = c("target KO", "control KO")) +
  scale_x_continuous(expand = expansion(mult = c(0, 0.12))) +
  labs(
    title = "Response genes per virtual KO, all engines",
    subtitle = "Knk: FDR<0.05 excluding KO gene; GenKI: KL top5% in >95% permutations, KO gene excluded",
    x = "Response genes", y = NULL, fill = NULL
  ) +
  theme_journal() +
  theme(axis.text.y = element_text(size = 7.5))
save_plot(p_cnt, fig_dir, "04_柱状图_响应基因汇总_AllEnginesCounts", 9.5, 8)

p_term <- ggplot(summary_df, aes(n_terms_pass_screen, label, fill = control)) +
  geom_col(width = 0.72) +
  geom_text(aes(label = n_terms_pass_screen), hjust = -0.25, size = 2.9) +
  scale_fill_manual(values = c("FALSE" = fill1, "TRUE" = "#B0A44F"), labels = c("target KO", "control KO")) +
  scale_x_continuous(expand = expansion(mult = c(0, 0.15))) +
  labs(
    title = "Official enrichment terms passing screen",
    subtitle = "Only ORA on response genes with BH p<0.05 and q<0.2; exploratory Top50 excluded",
    x = "Passing terms", y = NULL, fill = NULL
  ) +
  theme_journal() +
  theme(axis.text.y = element_text(size = 7.5))
save_plot(p_term, fig_dir, "05_柱状图_官方富集通过数_PassCount", 9.5, 8)

if (nrow(terms_df)) {
  agg <- aggregate(p.adjust ~ term, data = terms_df, FUN = min)
  top_terms <- as.character(head(agg$term[order(agg$p.adjust)], 25))
  heat <- terms_df[terms_df$term %in% top_terms, , drop = FALSE]
  heat$label <- paste(heat$engine, heat$subtype, heat$knockout, sep = "/")
  heat$neglog <- -log10(heat$p.adjust)
  heat$term <- factor(heat$term, levels = rev(top_terms))
  labels_all <- unique(paste(summary_df$engine, summary_df$subtype, summary_df$knockout, sep = "/"))
  heat$label <- factor(heat$label, levels = labels_all)
  p_heat <- ggplot(heat, aes(label, term, fill = neglog)) +
    geom_tile(color = "white") +
    scale_fill_gradient(low = "#F2E8D5", high = "#B2182B") +
    labs(
      title = "Official enrichment terms passing screen",
      subtitle = "Response-gene ORA only; BH p<0.05 & q<0.2; top 25 by best adjusted P",
      x = NULL, y = NULL, fill = "-log10(adj. P)"
    ) +
    theme_journal() +
    theme(axis.text.x = element_text(angle = 55, hjust = 1, size = 7))
  save_plot(p_heat, fig_dir, "05_热图_富集条目汇总_TermHeatmap", 11, 8)
}

html_rows <- apply(summary_df, 1, function(r) {
  sprintf(
    "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>",
    r[["engine"]], r[["subtype"]], r[["knockout"]], if (as.logical(r[["control"]])) "yes" else "",
    r[["n_response_excl_ko"]], r[["top_response_gene"]], r[["n_terms_pass_screen"]],
    r[["top_term"]], r[["term_source"]]
  )
})
writeLines(
  c(
    "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'/><title>富集与响应汇总</title>",
    "<style>body{font-family:'Segoe UI','Microsoft YaHei',sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;line-height:1.6}table{border-collapse:collapse;width:100%;font-size:0.9rem}th,td{border:1px solid #ccc;padding:0.3rem 0.45rem}th{background:#f2f2f2}.note{background:#f6f6f6;padding:0.6rem 0.8rem}</style></head><body>",
    "<h1>虚拟敲除 · 响应基因与官方富集汇总（全引擎）</h1>",
    "<p class='note'>筛选标准：Knk 响应=FDR&lt;0.05（剔除被敲基因）；GenKI 响应=KL top5% 且 &gt;95% 重复（剔除被敲基因）。富集仅统计官方 ORA（响应基因输入）且 BH p.adjust&lt;0.05 与 qvalue&lt;0.2 的条目。扰动距离前 50 基因的探索性富集不计入、不绘制。对照基因条目不具靶基因特异性。计算预测。</p>",
    "<p>图：<a href='../图片文件/04_柱状图_响应基因汇总_AllEnginesCounts.png'>响应基因数</a> · <a href='../图片文件/05_柱状图_官方富集通过数_PassCount.png'>官方通过条目数</a> · <a href='../图片文件/05_热图_富集条目汇总_TermHeatmap.png'>富集条目热图（若有）</a></p>",
    "<table><tr><th>引擎</th><th>亚群</th><th>基因</th><th>对照</th><th>响应基因数</th><th>Top 响应基因</th><th>通过筛选条目</th><th>Top 条目</th><th>来源</th></tr>",
    html_rows,
    "</table></body></html>"
  ),
  file.path(rep_dir, "富集汇总_EnrichSummary.html"),
  useBytes = TRUE
)
message("ENRICH_SUMMARY_DONE; passing_term_rows=", nrow(terms_df))
