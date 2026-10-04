# Uniform figure set for EVERY knockout gene: 04 rank scatter, 04 response bar,
# 05 enrichment ONLY from official ORA that already passed screening:
#   Knk  — FDR<0.05 response genes → 富集_GO.csv / 富集_KEGG.csv (BH p<0.05, q<0.2)
#   GenKI — response genes → 富集_GOBP.csv (same cutoffs)
# No exploratory Top-50 DR-distance enrichment plots.
# English plot text. Computational prediction. Desktop output only.
options(stringsAsFactors = FALSE)

desk <- "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除"
viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
np_plots <- "E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology/脚本_scripts/02_可视化_NetworkPharmPlots.R"
if (file.exists(viz)) source(viz, encoding = "UTF-8")
tryCatch(source(np_plots, encoding = "UTF-8"), error = function(e) message("skip np"))
suppressPackageStartupMessages({
  library(ggplot2)
})
if (!exists("theme_journal")) theme_journal <- function(...) ggplot2::theme_bw()
fill1 <- if (exists("bioinfo_palette")) bioinfo_palette[1] else "#6B8F71"
ctrl_col <- "#B0A44F"
ont_cols <- c(BP = "#1B9E77", CC = "#D95F02", MF = "#7570B3", KEGG = "#386CB0")

save_plot <- function(p, dir, stem, w = 7, h = 5) {
  dir.create(dir, recursive = TRUE, showWarnings = FALSE)
  if (exists("save_plot_pub", mode = "function")) {
    save_plot_pub(p, stem = stem, width = w, height = h, dpi = 600, out_dir = dir)
  } else {
    ggplot2::ggsave(file.path(dir, paste0(stem, ".png")), p, width = w, height = h, dpi = 600, bg = "white")
    ggplot2::ggsave(file.path(dir, paste0(stem, ".svg")), p, width = w, height = h, bg = "white")
  }
}

empty_panel <- function(title, subtitle, lines) {
  df <- data.frame(x = 0, y = seq_along(lines), label = lines, stringsAsFactors = FALSE)
  ggplot(df, aes(x, y)) +
    geom_point(size = 0) +
    geom_text(aes(label = label), size = 4.2, color = "grey25") +
    scale_y_reverse(expand = expansion(add = 0.8)) +
    scale_x_continuous(limits = c(-0.02, 0.02)) +
    labs(title = title, subtitle = subtitle) +
    theme_void() +
    theme(plot.title = element_text(face = "bold", size = 13), plot.subtitle = element_text(color = "grey35"))
}

archive_explor <- function(gene_dir) {
  tab_dir <- file.path(gene_dir, "数据文件")
  fig_dir <- file.path(gene_dir, "图片文件")
  rep_dir <- file.path(gene_dir, "报告文件")
  dest <- file.path(gene_dir, "_未采用_探索Top50")
  hits <- character(0)
  for (d in c(tab_dir, fig_dir, rep_dir)) {
    if (!dir.exists(d)) next
    hits <- c(hits, list.files(d, pattern = "探索|Top50", full.names = TRUE, ignore.case = TRUE))
  }
  if (!length(hits)) return(invisible(0L))
  dir.create(dest, recursive = TRUE, showWarnings = FALSE)
  for (f in unique(hits)) {
    if (!file.exists(f)) next
    file.rename(f, file.path(dest, basename(f)))
  }
  invisible(length(unique(hits)))
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

read_official_enrich <- function(tab_dir, engine) {
  parts <- list()
  go_p <- file.path(tab_dir, "富集_GO.csv")
  if (!file.exists(go_p) && engine == "GenKI") {
    # legacy BP-only file
    go_p <- file.path(tab_dir, "富集_GOBP.csv")
  }
  if (file.exists(go_p)) {
    go <- tryCatch(read.csv(go_p, check.names = FALSE), error = function(e) data.frame())
    if (ncol(go) && nrow(go)) {
      if (!"ontology" %in% names(go) && "ONTOLOGY" %in% names(go)) go$ontology <- go$ONTOLOGY
      if (!"ontology" %in% names(go)) go$ontology <- "BP"
      parts[["GO"]] <- go
    }
  }
  kegg_p <- file.path(tab_dir, "富集_KEGG.csv")
  if (file.exists(kegg_p)) {
    kg <- tryCatch(read.csv(kegg_p, check.names = FALSE), error = function(e) data.frame())
    if (ncol(kg) && nrow(kg)) {
      kg$ontology <- "KEGG"
      parts[["KEGG"]] <- kg
    }
  }
  if (!length(parts)) return(data.frame())
  # column-safe bind
  common <- Reduce(intersect, lapply(parts, names))
  if (!length(common)) return(data.frame())
  bound <- do.call(rbind, lapply(parts, function(x) x[, common, drop = FALSE]))
  pass_screen(bound)
}

draw_05 <- function(go, st, gene, algo, fig_dir, rep_dir, engine, control_flag) {
  # remove any leftover explor / empty stems before rewrite
  old <- list.files(fig_dir, pattern = "^05_", full.names = TRUE)
  if (length(old)) unlink(old)
  old_notes <- list.files(rep_dir, pattern = "^05_", full.names = TRUE)
  if (length(old_notes)) unlink(old_notes)

  keep_all <- pass_screen(go)
  empty_stem <- paste0("05_柱状图_富集无通过条目_", st, "_", gene, "Empty")
  if (!nrow(keep_all)) {
    p <- empty_panel(
      paste0(st, " ", gene, ": no enrichment term passed"),
      "Official ORA on response genes; GO + KEGG; BH p<0.05 and q<0.2",
      c(
        "No pathway passed the project screening cutoffs.",
        "Exploratory Top-50 DR-distance enrichments are archived, not plotted.",
        "Computational prediction."
      )
    )
    save_plot(p, fig_dir, empty_stem, 7.2, 3.8)
    writeLines(
      c(
        "没有任何 GO/KEGG 条目通过课题筛选标准（BH p.adjust < 0.05 且 qvalue < 0.2）。",
        "输入：响应基因 → GO BP/CC/MF + KEGG；仅绘制通过 BH p.adjust < 0.05 且 qvalue < 0.2 的条目。",
        "未通过的本体/KEGG 不强行出图。探索性 Top50 已归档，不绘制。",
        "计算预测。"
      ),
      file.path(rep_dir, "05_富集_无通过条目.txt")
    )
    return(invisible(0L))
  }

  plot_one <- function(keep, stem, title_suffix) {
    keep <- keep[order(keep$p.adjust), , drop = FALSE]
    keep <- head(keep, 8)
    keep$neglog <- -log10(pmax(keep$p.adjust, 1e-300))
    keep$term <- factor(keep$term, levels = rev(unique(as.character(keep$term))))
    p_bar <- ggplot(keep, aes(neglog, term)) +
      geom_col(fill = if (control_flag) ctrl_col else fill1, width = 0.7) +
      labs(
        title = paste0(st, " ", gene, ": ", title_suffix),
        subtitle = if (control_flag) {
          "Official ORA (control KO); BH p<0.05 & q<0.2; max 8; non-specific if shared"
        } else {
          "Official ORA on response genes; BH p<0.05 & q<0.2; max 8"
        },
        x = "-log10(adjusted P)", y = NULL
      ) +
      theme_journal()
    save_plot(p_bar, fig_dir, stem, 8.6, 5.2)
    nrow(keep)
  }

  n_drawn <- 0L
  counts <- c(BP = 0L, CC = 0L, MF = 0L, KEGG = 0L)
  stem_map <- c(
    BP = paste0("05_柱状图_GOBP_", st, "_", gene),
    CC = paste0("05_柱状图_GOCC_", st, "_", gene),
    MF = paste0("05_柱状图_GOMF_", st, "_", gene),
    KEGG = paste0("05_柱状图_KEGG_", st, "_", gene)
  )
  title_map <- c(
    BP = "GO BP terms passing screen",
    CC = "GO CC terms passing screen",
    MF = "GO MF terms passing screen",
    KEGG = "KEGG pathways passing screen"
  )
  for (ont in c("BP", "CC", "MF", "KEGG")) {
    if (!"ontology" %in% names(keep_all)) next
    sub <- keep_all[as.character(keep_all$ontology) == ont, , drop = FALSE]
    counts[[ont]] <- nrow(sub)
    if (!nrow(sub)) next
    n_drawn <- n_drawn + plot_one(sub, stem_map[[ont]], title_map[[ont]])
  }

  multi <- keep_all
  if (nrow(multi) && length(unique(multi$ontology)) > 1) {
    # bubble: top terms across ontologies that passed
    pieces <- lapply(split(multi, multi$ontology), function(d) head(d[order(d$p.adjust), , drop = FALSE], 4))
    both <- do.call(rbind, pieces)
    both$neglog <- -log10(pmax(both$p.adjust, 1e-300))
    both$term <- factor(both$term, levels = rev(unique(as.character(both$term))))
    sz <- if ("Count" %in% names(both)) both$Count else if ("count" %in% names(both)) both$count else 3
    both$Count <- sz
    p_bub <- ggplot(both, aes(neglog, term, size = Count, color = ontology)) +
      geom_point() +
      scale_color_manual(values = ont_cols) +
      labs(
        title = paste0(st, " ", gene, ": GO BP/CC/MF + KEGG passing screen"),
        subtitle = "Only terms that passed BH p<0.05 & q<0.2; no forced empty panels",
        x = "-log10(adjusted P)", y = NULL, color = "Ontology", size = "Genes"
      ) +
      theme_journal()
    save_plot(p_bub, fig_dir, paste0("05_气泡图_GOKEGG_", st, "_", gene), 8.6, 5.2)
  }

  writeLines(
    c(
      sprintf(
        "05 仅绘制通过筛选的条目：BP=%d CC=%d MF=%d KEGG=%d（各图最多 8 条）。BH p.adjust < 0.05 且 qvalue < 0.2。",
        counts[["BP"]], counts[["CC"]], counts[["MF"]], counts[["KEGG"]]
      ),
      "来源：富集_GO.csv（BP/CC/MF）与 富集_KEGG.csv；未通过的本体不强行出图。",
      "计算预测。"
    ),
    file.path(rep_dir, "05_富集_官方筛选通过.txt")
  )
  invisible(n_drawn)
}

draw_knk_gene <- function(st, algo, gene, control_flag) {
  gene_dir <- file.path(desk, "结果文件", st, algo, gene)
  tab_dir <- file.path(gene_dir, "数据文件")
  fig_dir <- file.path(gene_dir, "图片文件")
  rep_dir <- file.path(gene_dir, "报告文件")
  dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)
  dir.create(rep_dir, recursive = TRUE, showWarnings = FALSE)
  archive_explor(gene_dir)

  no_edge <- file.exists(file.path(rep_dir, "说明_无出边.txt"))
  dr_path <- file.path(tab_dir, "扰动_Dr.csv")
  sub_extra <- if (no_edge) {
    "No outgoing edges after rounding; network unchanged (numbers are numerical noise)"
  } else {
    "scTenifoldKnk 1.4.3; computational prediction"
  }
  if (file.exists(dr_path)) {
    d <- read.csv(dr_path, check.names = FALSE)
    d2 <- d[d$gene != gene, , drop = FALSE]
    d2 <- d2[order(d2$distance, decreasing = TRUE), , drop = FALSE]
    d2$rank <- seq_len(nrow(d2))
    d2$sig <- d2$p.adj < 0.05
    p_sc <- ggplot(d2, aes(rank, distance, color = sig)) +
      geom_point(size = 0.55, alpha = 0.7) +
      scale_color_manual(values = c("FALSE" = "grey70", "TRUE" = "#C17B7B")) +
      labs(
        title = paste0(st, " ", gene, " virtual KO (", algo, ")"),
        subtitle = sub_extra,
        x = "Rank (by distance)", y = "Distance", color = "FDR < 0.05"
      ) +
      theme_journal()
    save_plot(p_sc, fig_dir, paste0("04_散点图_扰动排名_", st, "_", gene, "RankScatter"), 6.4, 5)
    top <- head(d2, 15)
    top$gene <- factor(top$gene, levels = rev(top$gene))
    p_bar <- ggplot(top, aes(distance, gene, fill = p.adj < 0.05)) +
      geom_col(width = 0.72) +
      scale_fill_manual(values = c("FALSE" = if (control_flag) ctrl_col else fill1, "TRUE" = "#C17B7B")) +
      labs(
        title = paste0("Top 15 DR genes after ", gene, " KO (", st, ")"),
        subtitle = if (control_flag) "Low-correlation control KO; shared terms are non-specific" else sub_extra,
        x = "Distance", y = NULL, fill = "FDR < 0.05"
      ) +
      theme_journal()
    save_plot(p_bar, fig_dir, paste0("04_柱状图_扰动基因_", st, "_", gene, "DrBar"), 7.2, 5.2)
  } else {
    for (pair in list(
      c(paste0("04_散点图_扰动排名_", st, "_", gene, "RankScatter"), "Rank scatter"),
      c(paste0("04_柱状图_扰动基因_", st, "_", gene, "DrBar"), "Top-15 DR bar")
    )) {
      p <- empty_panel(
        paste0(st, " ", gene, ": ", pair[2], " not available"),
        sub_extra,
        c("扰动表为空：该基因在四舍五入后的野生型网里没有出边。", "敲除不改变网络。计算预测。")
      )
      save_plot(p, fig_dir, pair[1], 7.2, 3.6)
    }
  }

  go <- if (no_edge) data.frame() else read_official_enrich(tab_dir, engine = "Knk")
  draw_05(go, st, gene, algo, fig_dir, rep_dir, engine = "Knk", control_flag = control_flag)
}

draw_genki_gene <- function(st, gene, control_flag) {
  gene_dir <- file.path(desk, "结果文件", st, "GenKI", gene)
  tab_dir <- file.path(gene_dir, "数据文件")
  fig_dir <- file.path(gene_dir, "图片文件")
  rep_dir <- file.path(gene_dir, "报告文件")
  dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)
  dir.create(rep_dir, recursive = TRUE, showWarnings = FALSE)
  archive_explor(gene_dir)

  kl_path <- file.path(tab_dir, "KL排序_RankKL.csv")
  if (!file.exists(kl_path)) return(invisible(NULL))
  kl <- read.csv(kl_path, check.names = FALSE)
  resp_path <- file.path(tab_dir, "响应基因_Responsive.csv")
  resp <- if (file.exists(resp_path)) read.csv(resp_path, check.names = FALSE) else kl[0, ]
  eff <- resp[resp$gene != gene, , drop = FALSE]
  d <- kl
  d$passed <- d$gene %in% resp$gene
  d <- d[order(d$rank), , drop = FALSE]
  d$neglog <- log10(pmax(d$KL, 1e-300))
  p_sc <- ggplot(d, aes(rank, neglog, color = passed)) +
    geom_point(size = 0.55, alpha = 0.7) +
    scale_color_manual(values = c("FALSE" = "grey70", "TRUE" = "#C17B7B")) +
    labs(
      title = paste0(st, " ", gene, " virtual KO (GenKI)"),
      subtitle = "VGAE KL distance; computational prediction",
      x = "Rank (by KL)", y = "log10(KL)", color = "Response"
    ) +
    theme_journal()
  save_plot(p_sc, fig_dir, paste0("04_散点图_KL排名_", st, "_", gene, "RankScatter"), 6.4, 5)

  bar_stem <- paste0("04_柱状图_KL响应_", st, "_", gene, "DrBar")
  unlink(file.path(fig_dir, paste0(bar_stem, ".png")))
  unlink(file.path(fig_dir, paste0(bar_stem, ".svg")))
  if (nrow(eff)) {
    top <- eff[order(eff$KL, decreasing = TRUE), , drop = FALSE]
    top <- head(top, 15)
    top$gene <- factor(top$gene, levels = rev(top$gene))
    p_bar <- ggplot(top, aes(KL, gene)) +
      geom_col(fill = if (control_flag) ctrl_col else fill1, width = 0.72) +
      labs(
        title = paste0("Top ", nrow(top), " response genes after ", gene, " KO (", st, ")"),
        subtitle = if (control_flag) "Low-correlation control KO; terms here are non-specific" else "KO gene itself excluded; GenKI VGAE",
        x = "KL distance", y = NULL
      ) +
      theme_journal()
    save_plot(p_bar, fig_dir, bar_stem, 7.2, 5.2)
  } else {
    p <- empty_panel(
      paste0(st, " ", gene, ": no response genes"),
      "GenKI VGAE; KL top 5% in >95% of 1000 permutations",
      c("除被敲基因自身外，没有基因通过响应规则。", "不做富集图。计算预测。")
    )
    save_plot(p, fig_dir, bar_stem, 7.2, 3.6)
  }

  go <- read_official_enrich(tab_dir, engine = "GenKI")
  draw_05(go, st, gene, "GenKI", fig_dir, rep_dir, engine = "GenKI", control_flag = control_flag)
}

subtypes <- c("PEP", "NF1")
targets <- c("Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21")
controls <- c(
  scTenifoldKnk_1.4.3_GPU = "Ret,Rdx",
  scTenifoldKnk_1.4.3_CPU = "Ret,Rdx",
  GenKI = "Abcc8,Gm15551"
)
knk_algos <- c("scTenifoldKnk_1.4.3_GPU", "scTenifoldKnk_1.4.3_CPU")

n_done <- 0
for (st in subtypes) {
  for (algo in knk_algos) {
    genes <- c(targets, strsplit(controls[[algo]], ",", fixed = TRUE)[[1]][if (st == "PEP") 1 else 2])
    for (gene in genes) {
      if (!dir.exists(file.path(desk, "结果文件", st, algo, gene))) next
      message("knk ", st, " ", algo, " ", gene)
      draw_knk_gene(st, algo, gene, control_flag = !gene %in% targets)
      n_done <- n_done + 1
    }
  }
  ctrl <- strsplit(controls[["GenKI"]], ",", fixed = TRUE)[[1]][if (st == "PEP") 1 else 2]
  for (gene in c(targets, ctrl)) {
    if (!dir.exists(file.path(desk, "结果文件", st, "GenKI", gene))) next
    message("genki ", st, " ", gene)
    draw_genki_gene(st, gene, control_flag = !gene %in% targets)
    n_done <- n_done + 1
  }
}
message("ALL_GENE_FIGURES_DONE n=", n_done)
