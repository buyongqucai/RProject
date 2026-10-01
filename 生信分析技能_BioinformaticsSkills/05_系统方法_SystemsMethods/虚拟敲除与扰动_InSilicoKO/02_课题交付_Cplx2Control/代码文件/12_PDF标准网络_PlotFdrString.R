# PDF-standard network selection (Osorio Patterns 2022):
#   nodes = FDR < 0.05 DR genes (+ KO gene as egocentric hub)
#   edges = STRING PPI (Mus musculus 10090); try score 400 then 900
# NetPharm concentric layout ONLY when STRING-connected n >= 8.
# Does NOT pad Top40 by distance. Old 06 Top40 nets moved to _deprecated.
options(stringsAsFactors = FALSE)
Sys.setenv(http_proxy = "http://127.0.0.1:7897", https_proxy = "http://127.0.0.1:7897")

root <- "C:/Users/10540/Desktop/琪乐无穷/CPLX2虚拟敲除_Cplx2VirtualKO"
tab_dir <- file.path(root, "结果文件", "数据文件")
fig_dir <- file.path(root, "结果文件", "图片文件")
dep_dir <- file.path(fig_dir, "_deprecated_Top40非PDF标准")
repo <- "E:/RProject/生信分析技能_BioinformaticsSkills/05_系统方法_SystemsMethods/虚拟敲除与扰动_InSilicoKO/02_课题交付_Cplx2Control"
repo_fig <- file.path(repo, "结果文件", "图片文件")
repo_tab <- file.path(repo, "结果文件", "数据文件")
str_r <- "E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology/脚本_scripts/03_STRING与网络图_StringNetwork.R"
lay_r <- "E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology/脚本_scripts/04_交付网络布局_DeliveryNetworkLayouts.R"
viz <- "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一可视化规范_VizStandards/脚本_scripts/出版级出图_PublicationPlot.R"

source(str_r, encoding = "UTF-8")
source(lay_r, encoding = "UTF-8")
if (file.exists(viz)) source(viz, encoding = "UTF-8")
suppressPackageStartupMessages({
  library(ggplot2)
  library(igraph)
})
if (!exists("theme_journal")) theme_journal <- function(...) theme_bw(base_size = 11)

ko_gene <- "Cplx2"
species_mouse <- 10090L
subtypes <- c("cLTMR", "NF1", "NP", "PEP", "TRPM8")
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(dep_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(repo_fig, recursive = TRUE, showWarnings = FALSE)
dir.create(repo_tab, recursive = TRUE, showWarnings = FALSE)

# --- retire non-PDF Top40 networks ---
old06 <- list.files(fig_dir, pattern = "^06_网络图_.*_Cplx2Network\\.(png|svg)$", full.names = TRUE)
if (length(old06)) {
  file.rename(old06, file.path(dep_dir, basename(old06)))
  message("Moved ", length(old06), " Top40 nets -> ", dep_dir)
}

save_plot <- function(p, stem, w, h) {
  for (d in unique(c(fig_dir, repo_fig))) {
    ggsave(file.path(d, paste0(stem, ".png")), p, width = w, height = h, dpi = 600, bg = "white", limitsize = FALSE)
    ggsave(file.path(d, paste0(stem, ".svg")), p, width = w, height = h, bg = "white", limitsize = FALSE)
  }
}

dr <- read.csv(file.path(tab_dir, "04_扰动基因_五亚群_Cplx2DrAll.csv"), check.names = FALSE)
stopifnot(all(c("gene", "p.adj", "subtype", "distance") %in% names(dr)))

# PDF: FDR < 0.05 virtual-KO perturbed genes
fdr_rows <- dr[is.finite(dr$p.adj) & dr$p.adj < 0.05, , drop = FALSE]
inv <- do.call(rbind, lapply(subtypes, function(s) {
  sub <- fdr_rows[fdr_rows$subtype == s, , drop = FALSE]
  others <- setdiff(unique(sub$gene), ko_gene)
  data.frame(
    subtype = s,
    n_fdr_including_ko = nrow(sub),
    n_fdr_excluding_ko = length(others),
    fdr_genes = paste(sort(unique(sub$gene)), collapse = ";"),
    fdr_others = if (length(others)) paste(sort(others), collapse = ";") else "",
    stringsAsFactors = FALSE
  )
}))
write.csv(inv, file.path(tab_dir, "06_PDF入网基因清单_FdrNodes.csv"), row.names = FALSE)
write.csv(inv, file.path(repo_tab, "06_PDF入网基因清单_FdrNodes.csv"), row.names = FALSE)
write.csv(fdr_rows, file.path(tab_dir, "06_PDF入网基因明细_FdrNodesDetail.csv"), row.names = FALSE)
write.csv(fdr_rows, file.path(repo_tab, "06_PDF入网基因明细_FdrNodesDetail.csv"), row.names = FALSE)
message("FDR inventory written")

# STRING only when >=2 FDR genes. A single-gene query returns STRING
# first-neighbor expansion — that would violate PDF node selection.
bad_cache <- list.files(tab_dir, pattern = "^06_STRING_PPI_.*\\.tsv$", full.names = TRUE)
if (length(bad_cache)) file.remove(bad_cache)
bad_repo <- list.files(repo_tab, pattern = "^06_STRING_PPI_.*\\.tsv$", full.names = TRUE)
if (length(bad_repo)) file.remove(bad_repo)

edge_log <- list()
for (s in subtypes) {
  partners <- strsplit(inv$fdr_others[inv$subtype == s], ";", fixed = TRUE)[[1]]
  partners <- partners[nzchar(partners)]
  genes <- unique(c(ko_gene, partners))
  if (length(genes) < 2L) {
    edge_log[[length(edge_log) + 1L]] <- data.frame(
      subtype = s, required_score = NA_integer_, n_genes_query = length(genes),
      n_edges = 0L, genes = paste(genes, collapse = ";"),
      note = "skipped_STRING_single_gene_no_FDR_partner",
      stringsAsFactors = FALSE
    )
    next
  }
  for (sc in c(400L, 900L)) {
    cache <- file.path(tab_dir, sprintf("06_STRING_PPI_%s_score%d.tsv", s, sc))
    ppi <- tryCatch(
      np_fetch_string_ppi(
        genes = genes,
        species = species_mouse,
        required_score = sc,
        cache_path = cache,
        caller_identity = "RProject_InSilicoKO_Cplx2",
        force = TRUE
      ),
      error = function(e) {
        message("STRING fail ", s, " score=", sc, ": ", conditionMessage(e))
        data.frame()
      }
    )
    # Keep ONLY edges whose both ends are in the FDR query set
    edges_n <- 0L
    if (!is.null(ppi) && nrow(ppi)) {
      nm <- names(ppi)
      a <- if ("preferredName_A" %in% nm) ppi$preferredName_A else ppi[[1]]
      b <- if ("preferredName_B" %in% nm) ppi$preferredName_B else ppi[[2]]
      keep <- as.character(a) %in% genes & as.character(b) %in% genes
      ppi <- ppi[keep, , drop = FALSE]
      edges_n <- nrow(ppi)
      utils::write.table(
        ppi, cache, sep = "\t", quote = FALSE,
        row.names = FALSE, fileEncoding = "UTF-8"
      )
    }
    if (file.exists(cache)) {
      file.copy(cache, file.path(repo_tab, basename(cache)), overwrite = TRUE)
    }
    edge_log[[length(edge_log) + 1L]] <- data.frame(
      subtype = s, required_score = sc, n_genes_query = length(genes),
      n_edges = edges_n, genes = paste(genes, collapse = ";"),
      note = "edges_restricted_to_FDR_query_genes",
      stringsAsFactors = FALSE
    )
    Sys.sleep(1.2)
  }
}
edge_df <- do.call(rbind, edge_log)
write.csv(edge_df, file.path(tab_dir, "06_STRING边统计_StringEdgeSummary.csv"), row.names = FALSE)
write.csv(edge_df, file.path(repo_tab, "06_STRING边统计_StringEdgeSummary.csv"), row.names = FALSE)

# --- Figure: inventory bar (honest counts) ---
p_inv <- ggplot(inv, aes(subtype, n_fdr_excluding_ko)) +
  geom_col(fill = "#4C78A8", width = 0.65) +
  geom_text(aes(label = n_fdr_excluding_ko), vjust = -0.35, size = 3.5) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.2)), breaks = function(x) unique(floor(x))) +
  labs(
    title = "PDF node selection: FDR < 0.05 genes excluding KO gene",
    subtitle = "Osorio et al. Patterns 2022 egocentric rule. Zero means no multi-node STRING network.",
    x = NULL, y = "n FDR genes (excl. Cplx2)"
  ) +
  theme_journal()
save_plot(p_inv, "06_柱状图_PDF入网基因数_FdrNodeCounts", w = 7.5, h = 4.2)

# --- Egocentric / STRING draw helpers ---
draw_egocentric <- function(hub, partners, edges_df, title, subtitle, stem) {
  nodes <- unique(c(hub, partners))
  pos <- data.frame(name = nodes, x = 0, y = 0, stringsAsFactors = FALSE)
  oth <- setdiff(nodes, hub)
  if (!length(oth)) {
    pos$x <- 0
    pos$y <- 0
  } else if (length(oth) == 1L) {
    pos$x[match(hub, pos$name)] <- -0.85
    pos$y[match(hub, pos$name)] <- 0
    pos$x[match(oth, pos$name)] <- 0.85
    pos$y[match(oth, pos$name)] <- 0
  } else {
    a <- seq(0, 2 * pi, length.out = length(oth) + 1)[seq_along(oth)]
    pos$x[match(hub, pos$name)] <- 0
    pos$y[match(hub, pos$name)] <- 0
    pos$x[match(oth, pos$name)] <- 1.05 * cos(a)
    pos$y[match(oth, pos$name)] <- 1.05 * sin(a)
  }
  pos$is_hub <- pos$name == hub
  el <- edges_df
  if (is.null(el) || !nrow(el)) {
    el <- data.frame(from = character(), to = character(), score = numeric(), stringsAsFactors = FALSE)
  }
  if (nrow(el)) {
    el$x <- pos$x[match(el$from, pos$name)]
    el$y <- pos$y[match(el$from, pos$name)]
    el$xend <- pos$x[match(el$to, pos$name)]
    el$yend <- pos$y[match(el$to, pos$name)]
  }
  p <- ggplot()
  if (nrow(el)) {
    p <- p + geom_segment(
      data = el, aes(x = x, y = y, xend = xend, yend = yend),
      color = "grey45", linewidth = 0.7
    )
  } else if (length(oth) >= 1L) {
    # show absent STRING as dashed guide between hub and partners (not a real edge)
    guide <- data.frame(
      x = pos$x[match(hub, pos$name)],
      y = pos$y[match(hub, pos$name)],
      xend = pos$x[match(oth, pos$name)],
      yend = pos$y[match(oth, pos$name)]
    )
    p <- p + geom_segment(
      data = guide, aes(x = x, y = y, xend = xend, yend = yend),
      color = "grey75", linewidth = 0.45, linetype = "dashed"
    )
  }
  p <- p +
    geom_point(data = pos, aes(x, y, size = is_hub, color = is_hub)) +
    scale_size_manual(values = c("FALSE" = 12, "TRUE" = 15), guide = "none") +
    scale_color_manual(values = c("FALSE" = "#2B8CBE", "TRUE" = "#E31A1C"), guide = "none") +
    geom_text(data = pos, aes(x, y, label = name), color = "white", fontface = "bold", size = 3.4) +
    coord_equal(xlim = c(-1.7, 1.7), ylim = c(-1.4, 1.4), clip = "off") +
    labs(title = title, subtitle = subtitle) +
    theme_void(base_size = 11) +
    theme(
      plot.title = element_text(face = "bold", hjust = 0.5),
      plot.subtitle = element_text(hjust = 0.5, color = "grey30", size = 8.5),
      plot.background = element_rect(fill = "white", color = NA),
      plot.margin = margin(14, 14, 14, 14)
    )
  save_plot(p, stem, w = 7.2, h = 5.6)
}

normalize_string_edges <- function(ppi) {
  if (is.null(ppi) || !nrow(ppi)) {
    return(data.frame(from = character(), to = character(), score = numeric(), stringsAsFactors = FALSE))
  }
  nm <- names(ppi)
  a <- if ("preferredName_A" %in% nm) "preferredName_A" else if ("from" %in% nm) "from" else nm[1]
  b <- if ("preferredName_B" %in% nm) "preferredName_B" else if ("to" %in% nm) "to" else nm[2]
  sc <- if ("score" %in% nm) ppi$score else NA_real_
  data.frame(
    from = as.character(ppi[[a]]),
    to = as.character(ppi[[b]]),
    score = as.numeric(sc),
    stringsAsFactors = FALSE
  )
}

for (s in subtypes) {
  others <- inv$fdr_others[inv$subtype == s]
  partners <- if (nzchar(others)) strsplit(others, ";", fixed = TRUE)[[1]] else character()
  genes <- unique(c(ko_gene, partners))

  if (!length(partners)) {
    # PDF: no significant partners → no egocentric multi-node network
    p <- ggplot() +
      annotate("text", x = 0, y = 0.15, label = paste0(s, ": no FDR < 0.05 gene besides ", ko_gene),
               fontface = "bold", size = 4.2) +
      annotate("text", x = 0, y = -0.15,
               label = "PDF egocentric rule: do not pad Top-N by distance.\nNo STRING network drawn.",
               size = 3.3, color = "grey35") +
      xlim(-1, 1) + ylim(-1, 1) +
      theme_void() +
      theme(plot.background = element_rect(fill = "white", color = NA))
    save_plot(p, paste0("06_网络图_PDF标准_", s, "_NoFdrPartners"), w = 7, h = 4)
    next
  }

  # Prefer medium 400 for sparse sets; also report 900
  ppi400 <- tryCatch(
    read.delim(file.path(tab_dir, sprintf("06_STRING_PPI_%s_score400.tsv", s)),
               stringsAsFactors = FALSE, check.names = FALSE),
    error = function(e) data.frame()
  )
  edges <- normalize_string_edges(ppi400)
  # keep only edges among query genes
  edges <- edges[edges$from %in% genes & edges$to %in% genes, , drop = FALSE]

  # Concentric NetPharm layout only when STRING-connected nodes are enough.
  # Current trial: usually <8 FDR genes → egocentric only (PDF-faithful).
  if (nrow(edges) >= 1L && length(unique(c(edges$from, edges$to))) >= 8L &&
      exists("np_plot_string_ppi", mode = "function")) {
    p <- tryCatch(
      np_plot_string_ppi(
        edges,
        title = paste0(s, " virtual-KO STRING PPI (FDR nodes)")
      ),
      error = function(e) NULL
    )
    if (inherits(p, "ggplot")) {
      save_plot(p, paste0("06_网络图_PDF标准_", s, "_StringConcentric"), w = 10, h = 8.5)
    }
  }

  sub_txt <- if (nrow(edges)) {
    sprintf("STRING edges=%d (score>=400, mouse). Egocentric: KO hub + FDR partners.", nrow(edges))
  } else {
    "No STRING edge at score>=400 among FDR genes. Nodes shown; edge NOT invented from scGRN."
  }
  draw_egocentric(
    hub = ko_gene,
    partners = partners,
    edges_df = edges,
    title = paste0(s, ": PDF egocentric (FDR < 0.05)"),
    subtitle = sub_txt,
    stem = paste0("06_网络图_PDF标准_", s, "_Egocentric")
  )
}

# concise status note
note <- c(
  "# 06 网络图 — PDF 选点说明",
  "",
  "- 选点：各亚群 `p.adj < 0.05` 的 DR 基因；敲除基因作自我中心图中心。",
  "- 选边：STRING Mus musculus (10090)，先 400 再 900；不按距离凑 Top40。",
  "- 画法：点少 → egocentric；STRING 连通且节点≥8 才用网药同心环。",
  "- 旧 `06_*_Cplx2Network`（Top40+scGRN）已移入 `_deprecated_Top40非PDF标准/`。",
  "",
  "## 本试跑结果",
  paste0("- FDR 排除 Cplx2 后：", paste(sprintf("%s=%s", inv$subtype, inv$n_fdr_excluding_ko), collapse = ", ")),
  paste0("- STRING 边：见 `06_STRING边统计_StringEdgeSummary.csv`")
)
writeLines(note, file.path(tab_dir, "06_PDF网络选点说明_NetworkSelectionNote.md"))
writeLines(note, file.path(repo_tab, "06_PDF网络选点说明_NetworkSelectionNote.md"))
message("PDF_NETWORK_DONE")
