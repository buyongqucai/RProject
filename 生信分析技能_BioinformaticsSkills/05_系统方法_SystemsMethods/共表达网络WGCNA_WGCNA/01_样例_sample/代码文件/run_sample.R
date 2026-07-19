# 样例 — WGCNA REAL GSE10072 (module–trait + dendrogram + ME trend)
# analysis_kind=wgcna  seed=1010
options(stringsAsFactors = FALSE)
set.seed(1010)

sample_root <- normalizePath("..", winslash = "/", mustWork = TRUE)
skill_root <- normalizePath("../..", winslash = "/", mustWork = TRUE)
bio_root <- normalizePath("../../..", winslash = "/", mustWork = TRUE)
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath("../../../..", winslash = "/", mustWork = TRUE)
}
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath(file.path(skill_root, "..", ".."), winslash = "/", mustWork = TRUE)
}

viz_script <- file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards", "脚本_scripts", "出版级出图_PublicationPlot.R")
if (file.exists(viz_script)) source(viz_script, encoding = "UTF-8")
delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
paths <- delivery_sample_paths(sample_root)
data_dir <- paths$raw_dir; fig_dir <- paths$fig_dir; tab_dir <- paths$tab_dir; rep_dir <- paths$rep_dir
for (d in c(data_dir, fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)
source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")

skill_en <- "WGCNA"
skill_folder <- "共表达网络WGCNA_WGCNA"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- if (length(sk_files)) {
  for (sf in sk_files) try(source(sf, encoding = "UTF-8"), silent = TRUE)
  paste0("sourced: ", paste(basename(sk_files), collapse = ", "))
} else "no skill scripts"
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
library(ggplot2)

accession <- "GSE10072"
expr_f <- file.path(data_dir, "real_GSE10072_expr_topVar.csv")
meta_f <- file.path(data_dir, "real_GSE10072_sample_meta.csv")
if (!file.exists(expr_f)) {
  proj <- normalizePath(file.path(bio_root, ".."), winslash = "/", mustWork = TRUE)
  bs <- file.path(proj, "_tmp_build_wave1_caches.R")
  if (file.exists(bs)) source(bs, encoding = "UTF-8")
}
stopifnot(file.exists(expr_f), file.exists(meta_f))
expr <- read.csv(expr_f, check.names = FALSE, stringsAsFactors = FALSE)
meta <- read.csv(meta_f, check.names = FALSE, stringsAsFactors = FALSE)
mat <- as.matrix(expr[, -1, drop = FALSE])
storage.mode(mat) <- "numeric"
rownames(mat) <- make.unique(as.character(expr[[1]]))
# samples as rows for WGCNA
datExpr <- t(mat)
# trait: smoking Never vs Current/Former coded
meta <- meta[match(rownames(datExpr), meta$sample), ]
smoke <- as.character(meta$smoking)
never <- grepl("Never", smoke, ignore.case = TRUE)
trait <- data.frame(
  NeverSmoker = as.numeric(never),
  CurrentSmoker = as.numeric(grepl("Current", smoke, ignore.case = TRUE)),
  row.names = rownames(datExpr)
)

# Prefer WGCNA package; fallback to hierarchical clustering modules
use_wgcna <- requireNamespace("WGCNA", quietly = TRUE)
if (use_wgcna) {
  allowWGCNAThreads <- try(WGCNA::allowWGCNAThreads(), silent = TRUE)
  # fixed soft power for reproducible slim demo
  softPower <- 6
  adjacency <- WGCNA::adjacency(datExpr, power = softPower, type = "unsigned")
  TOM <- WGCNA::TOMsimilarity(adjacency)
  geneTree <- stats::hclust(stats::as.dist(1 - TOM), method = "average")
  dynamicMods <- dynamicTreeCut::cutreeDynamic(
    dendro = geneTree, distM = 1 - TOM, deepSplit = 2, pamRespectsDendro = FALSE,
    minClusterSize = 30
  )
  moduleColors <- WGCNA::labels2colors(dynamicMods)
  MEs <- WGCNA::moduleEigengenes(datExpr, colors = moduleColors)$eigengenes
  moduleTraitCor <- WGCNA::cor(MEs, trait, use = "p")
  sourced_note <- paste(sourced_note, "WGCNA softPower=6", sep = " | ")
} else {
  # correlation clustering fallback (still REAL expression)
  d <- stats::as.dist(1 - stats::cor(t(datExpr), use = "pairwise.complete.obs"))
  geneTree <- stats::hclust(d, method = "average")
  kc <- stats::cutree(geneTree, k = 4)
  moduleColors <- paste0("ME", kc)
  MEs <- sapply(sort(unique(kc)), function(k) {
    idx <- which(kc == k)
    if (length(idx) < 2) return(rep(0, nrow(datExpr)))
    stats::prcomp(scale(datExpr[, idx, drop = FALSE]), center = FALSE)$x[, 1]
  })
  colnames(MEs) <- paste0("ME", sort(unique(kc)))
  rownames(MEs) <- rownames(datExpr)
  moduleTraitCor <- stats::cor(MEs, trait, use = "p")
  sourced_note <- paste(sourced_note, "fallback hclust modules (WGCNA pkg missing)", sep = " | ")
}

# Module size bar
mod_tab <- as.data.frame(table(module = moduleColors))
names(mod_tab)[2] <- "n_genes"
mod_tab <- mod_tab[order(-mod_tab$n_genes), ]
write.csv(mod_tab, file.path(tab_dir, delivery_table_name(skill_en, "moduleSize", "n")), row.names = FALSE)

# Module-trait long
cdf <- data.frame(
  module = rep(rownames(moduleTraitCor), times = ncol(moduleTraitCor)),
  trait = rep(colnames(moduleTraitCor), each = nrow(moduleTraitCor)),
  cor = as.vector(moduleTraitCor),
  stringsAsFactors = FALSE
)
write.csv(cdf, file.path(tab_dir, delivery_table_name(skill_en, "moduleTrait", "cor")), row.names = FALSE)
write_delivery_audit(
  skill_en, "post", nrow(datExpr), ncol(datExpr), nrow(datExpr),
  paste0(accession, " smoking traits"), FALSE, accession, sourced_note,
  "WGCNA module-trait + dendrogram + ME trend; data_provenance=REAL",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "REAL"
)

p <- ggplot(cdf, aes(trait, module, fill = cor)) +
  geom_tile(color = "white", linewidth = 0.4) +
  geom_text(aes(label = sprintf("%.2f", cor)), size = 3) +
  scale_fill_gradient2(low = bioinfo_continuous[1], mid = "white", high = bioinfo_continuous[3], midpoint = 0) +
  labs(title = paste0("Module–trait correlation — ", accession), fill = "r") +
  theme_journal()
delivery_save_plot(p, skill_en, "heatmap", "ModuleTrait", 5.5, 4.8, fig_dir, bio_root, order = 1)

mod_tab$module <- factor(mod_tab$module, levels = mod_tab$module)
p2 <- ggplot(mod_tab, aes(module, n_genes, fill = module)) +
  geom_col(width = 0.7, show.legend = FALSE) +
  scale_fill_manual(values = rep(bioinfo_palette, length.out = nrow(mod_tab))) +
  labs(title = paste0("Module sizes — ", accession), x = NULL, y = "n genes") +
  theme_journal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
delivery_save_plot(p2, skill_en, "bar", "ModuleSize", 6.0, 4.2, fig_dir, bio_root, order = 2)

# ME vs NeverSmoker as severity proxy trend
me_long <- data.frame(MEs, NeverSmoker = trait$NeverSmoker, check.names = FALSE)
me_cols <- grep("^ME", names(me_long), value = TRUE)
if (!length(me_cols)) me_cols <- setdiff(names(me_long), "NeverSmoker")
pick <- me_cols[seq_len(min(2L, length(me_cols)))]
trend_df <- do.call(rbind, lapply(pick, function(m) {
  data.frame(severity = me_long$NeverSmoker, value = me_long[[m]], module = m, stringsAsFactors = FALSE)
}))
p_tr <- plot_severity_trend_journal(
  trend_df, x_col = "severity", y_col = "value", group_col = "module",
  title = paste0("ME vs NeverSmoker — ", accession),
  xlab = "Never smoker (0/1)", ylab = "Module eigengene"
)
delivery_save_plot(p_tr, skill_en, "trend", "ME_Severity", 6.0, 4.2, fig_dir, bio_root, order = 3)

# Sample dendrogram on expression
p_den <- plot_sample_dendrogram_journal(mat, title = paste0("Sample dendrogram — ", accession))
delivery_save_plot(p_den, skill_en, "dendrogram", "Samples", 7.0, 4.5, fig_dir, bio_root, order = 4)

fig_map <- c(
  "模块-性状" = paste0("../图片文件/", delivery_stem(skill_en, "heatmap", "ModuleTrait", order = 1), ".png"),
  "模块大小" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "ModuleSize", order = 2), ".png"),
  "ME趋势" = paste0("../图片文件/", delivery_stem(skill_en, "trend", "ME_Severity", order = 3), ".png"),
  "样本树" = paste0("../图片文件/", delivery_stem(skill_en, "dendrogram", "Samples", order = 4), ".png")
)
interp <- paste0("REAL ", accession, " WGCNA-style modules vs smoking traits. data_provenance=REAL。")
status <- "PASS"
data_html <- paste0("<p><b>data_provenance: REAL</b> — <code>", accession, "</code> top-variance genes.</p>")
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- if (file.exists(audit_path)) paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>") else "<p>none</p>"
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(skill_en, skill_folder, status, data_html, audit_html, sourced_note, fig_map, interp, rep_file, blocked_reason = "")
writeLines(c(status, "data_provenance=REAL", paste0("accession=", accession)), file.path(rep_dir, "STATUS.txt"))
message("DONE ", status, " — ", skill_folder, " REAL ", accession)
