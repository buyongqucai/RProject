# RETIRED for enrichment plotting (2026-04): exploratory Top50 DR-distance GO
# must NOT be drawn. Official 05 figures come from 38_全基因图册补齐_AllGeneFigures.R
# (response-gene ORA only). Keep this file only if needed for Phase1 scRNA copy helpers.
# Hard stop so accidental re-runs do not revive explor pathway figures.
message("36_SKIP: exploratory Top50 enrichment plotting is retired; use 38 for official ORA/empty 05.")
quit(save = "no", status = 0)
options(stringsAsFactors = FALSE)
set.seed(1)

desk <- "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除"
algo <- "scTenifoldKnk_1.4.3_GPU"
viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"
np_plots <- "E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology/脚本_scripts/02_可视化_NetworkPharmPlots.R"
if (file.exists(viz)) source(viz, encoding = "UTF-8")
tryCatch(source(np_plots, encoding = "UTF-8"), error = function(e) message("skip np: ", conditionMessage(e)))
suppressPackageStartupMessages({
  library(ggplot2)
  library(clusterProfiler)
  library(org.Mm.eg.db)
})
if (!exists("theme_journal")) theme_journal <- function(...) ggplot2::theme_bw()

gene_ratio <- function(text) {
  parts <- strsplit(as.character(text), "/", fixed = TRUE)
  vapply(parts, function(x) as.numeric(x[[1]]) / as.numeric(x[[2]]), numeric(1))
}

save_plot <- function(p, dir, stem, w, h) {
  dir.create(dir, recursive = TRUE, showWarnings = FALSE)
  if (exists("save_plot_pub", mode = "function")) {
    save_plot_pub(p, stem = stem, width = w, height = h, dpi = 600, out_dir = dir)
  } else {
    ggplot2::ggsave(file.path(dir, paste0(stem, ".png")), p, width = w, height = h, dpi = 600, bg = "white")
    ggplot2::ggsave(file.path(dir, paste0(stem, ".svg")), p, width = w, height = h, bg = "white")
  }
}

cross_fig <- file.path(desk, "结果文件", "_跨亚群", algo, "图片文件")
cross_tab <- file.path(desk, "结果文件", "_跨亚群", algo, "数据文件")
cross_rep <- file.path(desk, "结果文件", "_跨亚群", algo, "报告文件")
dir.create(cross_rep, recursive = TRUE, showWarnings = FALSE)

# Phase1 into each subtype wild-type folder (UMAP is shared PEP+NF1).
for (st in c("PEP", "NF1")) {
  wt_fig <- file.path(desk, "结果文件", st, algo, "_野生型", "图片文件")
  dir.create(wt_fig, recursive = TRUE, showWarnings = FALSE)
  for (f in list.files(cross_fig, pattern = "^(02_|03_)", full.names = TRUE)) {
    file.copy(f, file.path(wt_fig, basename(f)), overwrite = TRUE)
  }
}
unlink(list.files(cross_fig, pattern = "^05_.*GSEA", full.names = TRUE))
unlink(file.path(cross_tab, "05_GSEA_GO_BP_PepNf1.csv"))

subtypes <- c("PEP", "NF1")
targets <- c("Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21")
controls <- c(PEP = "Ret", NF1 = "Rdx")
rows <- list()

for (st in subtypes) {
  for (gene in c(targets, unname(controls[[st]]))) {
    gene_dir <- file.path(desk, "结果文件", st, algo, gene)
    fig_dir <- file.path(gene_dir, "图片文件")
    tab_dir <- file.path(gene_dir, "数据文件")
    rep_dir <- file.path(gene_dir, "报告文件")
    dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)
    dir.create(tab_dir, recursive = TRUE, showWarnings = FALSE)
    dir.create(rep_dir, recursive = TRUE, showWarnings = FALSE)
    unlink(list.files(fig_dir, pattern = "^05_.*GSEA", full.names = TRUE))
    unlink(file.path(tab_dir, "05_GSEA_GO_BP.csv"))
    unlink(file.path(rep_dir, "05_富集_GSEA说明.txt"))

    if (file.exists(file.path(rep_dir, "说明_无出边.txt"))) {
      writeLines("Zero outgoing edges after rounding. No enrichment figure.", file.path(rep_dir, "05_富集_无通过条目.txt"))
      next
    }

    already <- list.files(fig_dir, pattern = "^05_柱状图_探索富集_Top50GO_")
    csv_ok <- file.exists(file.path(tab_dir, "05_探索富集_Top50_GO.csv"))
    if (length(already) && csv_ok) {
      go_df <- read.csv(file.path(tab_dir, "05_探索富集_Top50_GO.csv"), check.names = FALSE)
      go_df$subtype <- st
      go_df$knockout <- gene
      rows[[paste(st, gene)]] <- go_df
      message("skip done ", st, " ", gene)
      next
    }

    dr_path <- file.path(tab_dir, "扰动_Dr.csv")
    if (!file.exists(dr_path)) next
    d <- read.csv(dr_path, check.names = FALSE)
    d <- d[d$gene != gene, , drop = FALSE]
    d <- d[order(d$distance, decreasing = TRUE), , drop = FALSE]
    symbols <- unique(head(d$gene, 50))
    message("enrichGO top50 ", st, " ", gene)
    go_parts <- list()
    for (ont in c("BP", "CC", "MF")) {
      ego <- tryCatch(
        clusterProfiler::enrichGO(
          symbols,
          OrgDb = org.Mm.eg.db::org.Mm.eg.db,
          keyType = "SYMBOL",
          ont = ont,
          pAdjustMethod = "BH",
          pvalueCutoff = 1,
          qvalueCutoff = 1,
          readable = FALSE
        ),
        error = function(e) NULL
      )
      if (is.null(ego) || nrow(as.data.frame(ego)) == 0) next
      frame <- as.data.frame(ego)
      frame$ontology <- ont
      frame$term <- frame$Description
      frame$enrichment <- gene_ratio(frame$GeneRatio)
      frame$count <- frame$Count
      frame$pvalue <- frame$pvalue
      frame$subtype <- st
      frame$knockout <- gene
      go_parts[[ont]] <- frame
    }
    go_df <- if (length(go_parts)) do.call(rbind, go_parts) else data.frame()
    if (!nrow(go_df)) {
      writeLines("Top 50 DR genes: enrichGO returned no terms.", file.path(rep_dir, "05_富集_无通过条目.txt"))
      next
    }
    write.csv(go_df, file.path(tab_dir, "05_探索富集_Top50_GO.csv"), row.names = FALSE)
    rows[[paste(st, gene)]] <- go_df
    if (exists("np_plot_go_bar", mode = "function")) {
      save_plot(np_plot_go_bar(go_df, top_n = 10), fig_dir, paste0("05_柱状图_探索富集_Top50GO_", st, "_", gene), 9, 7)
      if (exists("np_plot_go_bubble", mode = "function")) {
        save_plot(np_plot_go_bubble(go_df, top_n = 10), fig_dir, paste0("05_气泡图_探索富集_Top50GO_", st, "_", gene), 8.5, 9)
      }
    }
    n_pass <- sum(go_df$p.adjust < 0.05, na.rm = TRUE)
    writeLines(
      if (n_pass == 0L) {
        "FDR<0.05 ORA was empty. Figure is enrichGO on top 50 genes by DR distance. No term has adjusted P < 0.05."
      } else {
        sprintf("FDR<0.05 ORA was empty. Top 50 DR-gene enrichGO: %d terms with adjusted P < 0.05. Exploratory.", n_pass)
      },
      file.path(rep_dir, "05_富集_探索Top50说明.txt")
    )
  }
}

if (length(rows)) {
  allr <- do.call(rbind, rows)
  write.csv(allr, file.path(cross_tab, "05_探索富集_Top50_GO_PepNf1.csv"), row.names = FALSE)
}
writeLines(
  c(
    "Desktop gold: 琪乐无穷/虚拟敲除",
    "Phase1 scRNA in _跨亚群 and copied into each subtype _野生型/图片文件.",
    "05 figures: enrichGO on top 50 DR genes. FDR<0.05 ORA had no passing terms.",
    "Computational prediction."
  ),
  file.path(cross_rep, "STATUS_延展出图.txt")
)
message("DESK_EXTENT_DONE")
