# GenKI per-gene result figures (KL response) and cross-subtype summary.
# Engine columns: KL / rank / hit_fraction, not Knk distance/p.adj.
# KO gene itself is excluded from bars and enrichment input per plan.
# English labels, SVG+PNG. Computational prediction.
options(stringsAsFactors = FALSE)

desk <- "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除"
viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
if (file.exists(viz)) source(viz, encoding = "UTF-8")
suppressPackageStartupMessages(library(ggplot2))
if (!exists("theme_journal")) theme_journal <- function(...) ggplot2::theme_bw()
fill1 <- if (exists("bioinfo_palette")) bioinfo_palette[1] else "#6B8F71"
ctrl_col <- "#B0A44F"

save_plot <- function(p, dir, stem, w = 7, h = 5) {
  dir.create(dir, recursive = TRUE, showWarnings = FALSE)
  if (exists("save_plot_pub", mode = "function")) {
    save_plot_pub(p, stem = stem, width = w, height = h, dpi = 600, out_dir = dir)
  } else {
    ggplot2::ggsave(file.path(dir, paste0(stem, ".png")), p, width = w, height = h, dpi = 600, bg = "white")
    ggplot2::ggsave(file.path(dir, paste0(stem, ".svg")), p, width = w, height = h, bg = "white")
  }
}

subtypes <- c("PEP", "NF1")
targets <- c("Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21")
controls <- c(PEP = "Abcc8", NF1 = "Gm15551")
cross_fig <- file.path(desk, "结果文件", "_跨亚群", "GenKI", "图片文件")
cross_tab <- file.path(desk, "结果文件", "_跨亚群", "GenKI", "数据文件")
cross_rep <- file.path(desk, "结果文件", "_跨亚群", "GenKI", "报告文件")
for (d in c(cross_fig, cross_tab, cross_rep)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

counts_summary <- data.frame()
sets <- list()

for (st in subtypes) {
  ctrl <- unname(controls[[st]])
  for (gene in c(targets, ctrl)) {
    gene_dir <- file.path(desk, "结果文件", st, "GenKI", gene)
    kl_path <- file.path(gene_dir, "数据文件", "KL排序_RankKL.csv")
    resp_path <- file.path(gene_dir, "数据文件", "响应基因_Responsive.csv")
    if (!file.exists(kl_path)) next
    kl <- read.csv(kl_path, check.names = FALSE)
    resp <- if (file.exists(resp_path)) read.csv(resp_path, check.names = FALSE) else kl[0, ]
    eff <- resp[resp$gene != gene, , drop = FALSE]
    sets[[paste(st, gene)]] <- eff$gene
    is_ctrl <- identical(gene, ctrl)
    counts_summary <- rbind(counts_summary, data.frame(
      subtype = st, knockout = gene, control = is_ctrl,
      n_response_incl_ko = nrow(resp),
      n_response_excl_ko = nrow(eff),
      stringsAsFactors = FALSE
    ))

    fig_dir <- file.path(gene_dir, "图片文件")
    rep_dir <- file.path(gene_dir, "报告文件")
    dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)
    dir.create(rep_dir, recursive = TRUE, showWarnings = FALSE)

    # 04 scatter: rank vs KL, colored by response rule
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

    if (nrow(eff)) {
      top <- eff[order(eff$KL, decreasing = TRUE), , drop = FALSE]
      top <- head(top, 15)
      top$gene <- factor(top$gene, levels = rev(top$gene))
      p_bar <- ggplot(top, aes(KL, gene)) +
        geom_col(fill = if (is_ctrl) ctrl_col else fill1, width = 0.72) +
        labs(
          title = paste0("Top ", nrow(top), " response genes after ", gene, " KO (", st, ")"),
          subtitle = if (is_ctrl) "Low-correlation control KO; terms here are non-specific" else "KO gene itself excluded",
          x = "KL distance", y = NULL
        ) +
        theme_journal()
      save_plot(p_bar, fig_dir, paste0("04_柱状图_KL响应_", st, "_", gene, "DrBar"), 7.2, 5.2)
    }

    go_path <- file.path(gene_dir, "数据文件", "富集_GOBP.csv")
    go <- if (file.exists(go_path)) tryCatch(read.csv(go_path, check.names = FALSE), error = function(e) data.frame()) else data.frame()
    n_pass <- if (ncol(go) == 0 || nrow(go) == 0) 0L else sum(go$p.adjust < 0.05, na.rm = TRUE)
    if (n_pass == 0L) {
      writeLines(
        c(
          "GenKI 响应基因（剔除被敲基因本身）的 GO BP 富集没有 BH p.adjust < 0.05 条目，不绘图。",
          sprintf("响应基因数（含自身/不含自身）：%d/%d。计算预测。", nrow(resp), nrow(eff))
        ),
        file.path(rep_dir, "05_富集_无通过条目.txt")
      )
    } else {
      keep <- go[go$p.adjust < 0.05, , drop = FALSE]
      keep <- keep[order(keep$p.adjust), , drop = FALSE]
      keep <- head(keep, 8)
      keep$neglog <- -log10(keep$p.adjust)
      keep$term <- factor(keep$Description, levels = rev(keep$Description))
      p_go <- ggplot(keep, aes(neglog, term)) +
        geom_col(fill = if (is_ctrl) ctrl_col else fill1, width = 0.7) +
        labs(
          title = paste0(st, " ", gene, ": GO BP with BH adj. P < 0.05"),
          subtitle = "GenKI response genes (KO gene excluded); computational prediction",
          x = "-log10(adjusted P)", y = NULL
        ) +
        theme_journal()
      save_plot(p_go, fig_dir, paste0("05_柱状图_GOBP_", st, "_", gene), 8.6, 5.2)
    }
    if (!nrow(eff)) {
      writeLines(
        if (nrow(resp) == 0) {
          "没有任何基因通过响应规则（KL top5% 且 >95% 重复）。不做富集图。计算预测。"
        } else {
          "只有被敲基因自身通过响应规则，没有其他响应基因。不做富集图。计算预测。"
        },
        file.path(rep_dir, "说明_仅自身响应.txt")
      )
    }
  }
}

write.csv(counts_summary, file.path(cross_tab, "04_响应基因数_PepNf1GenKiResponseCounts.csv"), row.names = FALSE)

counts_summary$label <- paste(counts_summary$subtype, counts_summary$knockout, sep = " ")
counts_summary$label <- factor(counts_summary$label, levels = rev(unique(counts_summary$label)))
p_cnt <- ggplot(counts_summary, aes(n_response_excl_ko, label, fill = control)) +
  geom_col(width = 0.72) +
  geom_text(aes(label = n_response_excl_ko), hjust = -0.25, size = 3) +
  scale_fill_manual(values = c("FALSE" = fill1, "TRUE" = ctrl_col), labels = c("target KO", "control KO")) +
  scale_x_continuous(expand = expansion(mult = c(0, 0.12))) +
  labs(
    title = "GenKI response genes per virtual KO (PEP, NF1)",
    subtitle = "KL top 5% in >95% of 1000 permutations; KO gene excluded",
    x = "Response genes", y = NULL, fill = NULL
  ) +
  theme_journal()
save_plot(p_cnt, cross_fig, "04_柱状图_响应基因数_PepNf1GenKiCounts", 8.6, 6)

labs <- names(sets)
jac <- matrix(0, length(labs), length(labs), dimnames = list(labs, labs))
for (i in labs) for (j in labs) {
  a <- sets[[i]]; b <- sets[[j]]
  u <- length(union(a, b))
  jac[i, j] <- if (u == 0) 0 else length(intersect(a, b)) / u
}
write.csv(jac, file.path(cross_tab, "07_重叠_响应基因Jaccard_PepNf1GenKi.csv"))
jac_df <- as.data.frame(as.table(jac))
names(jac_df) <- c("a", "b", "jaccard")
p_j <- ggplot(jac_df, aes(a, b, fill = jaccard)) +
  geom_tile(color = "white") +
  geom_text(aes(label = sprintf("%.2f", jaccard)), size = 2.1) +
  scale_fill_gradient(low = "white", high = fill1, limits = c(0, 1)) +
  labs(title = "Overlap of GenKI response genes (KO gene excluded)", x = NULL, y = NULL, fill = "Jaccard") +
  theme_journal() +
  theme(axis.text.x = element_text(angle = 50, hjust = 1, size = 7), axis.text.y = element_text(size = 7))
save_plot(p_j, cross_fig, "07_热图_响应重叠Jaccard_PepNf1GenKi", 9, 7.8)

for (st in subtypes) {
  ctrl <- unname(controls[[st]])
  ctrl_set <- sets[[paste(st, ctrl)]]
  if (is.null(ctrl_set) || !length(ctrl_set)) next
  rows <- do.call(rbind, lapply(targets, function(g) {
    s <- sets[[paste(st, g)]]
    if (is.null(s) || !length(s)) return(NULL)
    data.frame(
      subtype = st, knockout = g,
      n_response = length(s),
      n_shared_with_control = length(intersect(s, ctrl_set)),
      fraction_shared = round(length(intersect(s, ctrl_set)) / length(s), 3),
      stringsAsFactors = FALSE
    )
  }))
  if (!is.null(rows)) {
    write.csv(rows, file.path(cross_tab, paste0("06_对照重叠_", st, "_", ctrl, "Overlap.csv")), row.names = FALSE)
    writeLines(
      c(
        sprintf("%s 对照 %s 有 %d 个响应基因（不含自身）。", st, ctrl, length(ctrl_set)),
        "与对照共享的响应基因不能算靶基因特异。计算预测。"
      ),
      file.path(cross_rep, paste0("06_对照说明_", st, "_", ctrl, ".txt"))
    )
  }
}

writeLines(
  c(
    "GenKI (Yang et al., NAR 2023) virtual KO results for PEP/NF1, GSE197289 Control.",
    "Response rule: KL top 5% and >95% of 1000 no-replacement cell-order permutations; KO gene excluded.",
    "No GO BP term passed BH p.adjust < 0.05 in any response list; 05 figures are absent by design.",
    "Controls: PEP Abcc8 (r=0.000010), NF1 Gm15551 (r=0.000064). Control overlap tables flag non-specific genes.",
    "Computational prediction. Not wet-lab KO DEG."
  ),
  file.path(cross_rep, "STATUS_GenKI出图.txt")
)
message("GENKI_PLOT_DONE")
