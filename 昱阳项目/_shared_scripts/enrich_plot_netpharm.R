# YuYang: convert clusterProfiler enrichResult → 网药 FROZEN enrich tables + figures.
# Recipes: 网络药理学 脚本_scripts/02_可视化_NetworkPharmPlots.R（不解冻改样式）

.np_plots <- file.path(
  "E:/RProject/生信分析技能_BioinformaticsSkills",
  "03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology",
  "脚本_scripts/02_可视化_NetworkPharmPlots.R"
)
# always re-source so YuYang picks up skill script updates (sort_by=count etc.)
if (!file.exists(.np_plots)) stop("missing NetworkPharmPlots: ", .np_plots)
source(.np_plots, encoding = "UTF-8")

#' enrichResult / data.frame → go_df (term, enrichment, pvalue, count, ontology)
yy_go_from_enrich <- function(obj, ontology) {
  if (is.null(obj)) return(NULL)
  df <- as.data.frame(obj)
  if (!nrow(df) || "note" %in% names(df)) return(NULL)
  term <- if ("Description" %in% names(df)) df$Description else df[[1]]
  enrichment <- if ("FoldEnrichment" %in% names(df)) {
    as.numeric(df$FoldEnrichment)
  } else if ("RichFactor" %in% names(df)) {
    as.numeric(df$RichFactor)
  } else {
    np_parse_gene_ratio(df$GeneRatio) / pmax(np_parse_gene_ratio(df$BgRatio), 1e-12)
  }
  count <- if ("Count" %in% names(df)) as.numeric(df$Count) else NA_real_
  data.frame(
    term = as.character(term),
    enrichment = enrichment,
    pvalue = as.numeric(df$pvalue),
    count = count,
    ontology = ontology,
    stringsAsFactors = FALSE
  )
}

yy_bind_go_df <- function(ego_bp, ego_cc, ego_mf) {
  parts <- list(
    yy_go_from_enrich(ego_bp, "BP"),
    yy_go_from_enrich(ego_cc, "CC"),
    yy_go_from_enrich(ego_mf, "MF")
  )
  parts <- Filter(Negate(is.null), parts)
  if (!length(parts)) return(NULL)
  out <- do.call(rbind, parts)
  rownames(out) <- NULL
  out
}

#' enrichKEGG → table for np_plot_kegg_* / chord (term, pvalue, count, Group, GeneRatio, geneID)
yy_kegg_from_enrich <- function(obj) {
  if (is.null(obj)) return(NULL)
  df <- as.data.frame(obj)
  if (!nrow(df) || "note" %in% names(df)) return(NULL)
  term <- if ("Description" %in% names(df)) df$Description else as.character(df$ID)
  grp <- if ("category" %in% names(df)) {
    as.character(df$category)
  } else if ("Group" %in% names(df)) {
    as.character(df$Group)
  } else {
    NA_character_
  }
  out <- data.frame(
    term = as.character(term),
    pvalue = as.numeric(df$pvalue),
    count = if ("Count" %in% names(df)) as.numeric(df$Count) else 10,
    Group = grp,
    GeneRatio = if ("GeneRatio" %in% names(df)) as.character(df$GeneRatio) else NA_character_,
    geneID = if ("geneID" %in% names(df)) as.character(df$geneID) else NA_character_,
    ID = if ("ID" %in% names(df)) as.character(df$ID) else NA_character_,
    stringsAsFactors = FALSE
  )
  out
}

yy_ggsave_pair <- function(p, stem, out_fig, width, height, dpi = 600L) {
  if (is.null(p)) return(invisible(NULL))
  png <- file.path(out_fig, paste0(stem, ".png"))
  svg <- file.path(out_fig, paste0(stem, ".svg"))
  ggplot2::ggsave(png, p, width = width, height = height, dpi = dpi, bg = "white")
  ggplot2::ggsave(svg, p, width = width, height = height, bg = "white")
  invisible(list(png = png, svg = svg))
}

#' Write 网药 enrich figures into out_fig; remove legacy enrichplot dots if present.
yy_plot_enrich_netpharm <- function(go_df, kegg_df, out_fig, out_tab = NULL) {
  dir.create(out_fig, recursive = TRUE, showWarnings = FALSE)
  # drop journal-style dots from prior runs
  old <- list.files(out_fig, pattern = "_(GO|KEGG)_.*_dot\\.(png|svg)$", full.names = TRUE)
  old <- c(old, list.files(out_fig, pattern = "^0[123]_GO_|^03_KEGG_dot", full.names = TRUE))
  unlink(old)

  written <- character()
  if (!is.null(go_df) && nrow(go_df) > 0) {
    if (!is.null(out_tab)) {
      utils::write.csv(go_df, file.path(out_tab, "02b_GO_BPCCMF_forPlot.csv"),
                       row.names = FALSE, fileEncoding = "UTF-8")
    }
    # 昱阳：大泡泡（count）在上；top_n=8 + 加高画布减轻 Y 标签重叠
    p_b <- tryCatch(
      np_plot_go_bubble(go_df, top_n = 8, sort_by = "count"),
      error = function(e) {
        message("GO bubble fail: ", conditionMessage(e)); NULL
      }
    )
    yy_ggsave_pair(p_b, "01_气泡图_GO_BPCCMF_Bubble", out_fig, 12.0, 15.0)
    p_bar <- tryCatch(np_plot_go_bar(go_df, top_n = 10), error = function(e) {
      message("GO bar fail: ", conditionMessage(e)); NULL
    })
    yy_ggsave_pair(p_bar, "02_柱状图_GO_BPCCMF_Bar", out_fig, 11.0, 7.5)
    written <- c(written, "GO_bubble", "GO_bar")
  } else {
    message("GO netpharm plots skipped: empty go_df")
  }

  if (!is.null(kegg_df) && nrow(kegg_df) > 0) {
    if (!is.null(out_tab)) {
      utils::write.csv(kegg_df, file.path(out_tab, "04b_KEGG_forPlot.csv"),
                       row.names = FALSE, fileEncoding = "UTF-8")
    }
    p_l <- tryCatch(np_plot_kegg_lollipop(kegg_df, top_n = 20), error = function(e) {
      message("KEGG lollipop fail: ", conditionMessage(e)); NULL
    })
    yy_ggsave_pair(p_l, "03_棒棒糖图_KEGG_Pathways_Lollipop", out_fig, 10.5, 8.5)
    p_kb <- tryCatch(np_plot_kegg_bar(kegg_df, top_n = 20), error = function(e) {
      message("KEGG bar fail: ", conditionMessage(e)); NULL
    })
    yy_ggsave_pair(p_kb, "07_柱状图_KEGG_Pathways_Bar", out_fig, 10.5, 8.5)
    written <- c(written, "KEGG_lollipop", "KEGG_bar")
    if (requireNamespace("circlize", quietly = TRUE) &&
        "geneID" %in% names(kegg_df) && any(nzchar(kegg_df$geneID))) {
      circ <- tryCatch(
        np_save_kegg_chord(
          kegg_df,
          out_dir = out_fig,
          stem = "08_圈图_KEGG_Circos",
          top_n = 20,
          label_genes = TRUE,
          width = 11,
          height = 10,
          dpi = 600L
        ),
        error = function(e) {
          message("KEGG circos fail: ", conditionMessage(e))
          NULL
        }
      )
      if (!is.null(circ)) written <- c(written, "KEGG_circos")
    } else {
      message("KEGG circos skipped (need circlize + geneID)")
    }
  } else {
    message("KEGG netpharm plots skipped: empty kegg_df")
  }
  invisible(written)
}
