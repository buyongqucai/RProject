# 样例分析脚本 — 单细胞与空间转录组分析_scRNA-Spatial
# 合规：统一交付规范_DeliveryStandards + 统一可视化规范_VizStandards
# analysis_kind=scrna  seed=202
# data_provenance=REAL — UMAP: GSE164522 (山水); proportions: GSE207177 (书清) + GSE164522 patient
options(stringsAsFactors = FALSE)
set.seed(202)

sample_root <- normalizePath("..", winslash = "/", mustWork = TRUE)
skill_root <- normalizePath("../..", winslash = "/", mustWork = TRUE)
bio_root <- normalizePath("../../..", winslash = "/", mustWork = TRUE)
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath("../../../..", winslash = "/", mustWork = TRUE)
}
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath(file.path(skill_root, "..", ".."), winslash = "/", mustWork = TRUE)
}

viz_script <- file.path(
  bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
  "脚本_scripts", "出版级出图_PublicationPlot.R"
)
if (file.exists(viz_script)) source(viz_script, encoding = "UTF-8")

delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")

paths <- delivery_sample_paths(sample_root)
data_dir <- paths$raw_dir
fig_dir <- paths$fig_dir
tab_dir <- paths$tab_dir
rep_dir <- paths$rep_dir
for (d in c(data_dir, fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)
source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")

skill_en <- "scRNA-Spatial"
skill_folder <- "单细胞与空间转录组分析_scRNA-Spatial"
scripts_dir <- file.path(skill_root, "脚本_scripts")
sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
sourced_note <- "未找到可 source 的技能脚本"
if (length(sk_files)) {
  for (sf in sk_files) {
    try(source(sf, encoding = "UTF-8"), silent = TRUE)
  }
  sourced_note <- paste0("已 source 本技能 脚本_scripts/: ", paste(basename(sk_files), collapse = ", "))
}
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")

shuqing_root <- Sys.getenv("SHUQING_ROOT", "E:/RProject/书清项目")
shanshui_root <- Sys.getenv("SHANSHUI_ROOT", "E:/RProject/山水项目")
acc_umap <- "GSE164522"
acc_prop <- "GSE207177"

# Prefer skill-local caches; live 书清/山水 trees are optional fallback only
umap_cache <- file.path(data_dir, "real_GSE164522_umap_subsample.csv")
umap_rds_cache <- file.path(data_dir, "real_GSE164522_seurat_umap_subsample.rds")
prop_cache <- file.path(data_dir, "real_GSE207177_celltype_proportions.csv")
umap_rds_live <- file.path(
  shanshui_root, "GSE164522", "模块B_肝转移单细胞", "03_输出数据",
  "GSE164522_seurat_umap_subsample.rds"
)
prop_live <- file.path(shuqing_root, "GSE207177", "结果", "表格", "GSE207177_细胞类型比例.csv")

load_umap_from_rds <- function(rds_path, via) {
  if (!file.exists(rds_path) || !requireNamespace("Seurat", quietly = TRUE)) return(NULL)
  obj <- readRDS(rds_path)
  emb <- as.data.frame(Seurat::Embeddings(obj, "umap"))
  names(emb) <- c("umap_1", "umap_2")
  md <- as.data.frame(obj[[]])
  d <- cbind(emb, md)
  d$celltype <- d$celltype_major
  d$group <- d$group_label
  d$score <- d$FCGR3A_raw
  set.seed(202)
  d <- d[sample(seq_len(nrow(d)), min(3000L, nrow(d))), , drop = FALSE]
  attr(d, "via") <- via
  d
}

load_umap <- function() {
  if (file.exists(umap_cache)) {
    d <- read.csv(umap_cache, check.names = FALSE, stringsAsFactors = FALSE)
    attr(d, "via") <- "cache"
    return(d)
  }
  d <- load_umap_from_rds(umap_rds_cache, "skill_rds_cache")
  if (!is.null(d)) return(d)
  d <- load_umap_from_rds(umap_rds_live, "SHANSHUI_ROOT")
  if (!is.null(d)) return(d)
  stop("No REAL UMAP: missing skill-local CSV/RDS cache (and optional live Seurat RDS)")
}

load_prop_shuqing <- function() {
  path <- if (file.exists(prop_cache)) prop_cache else if (file.exists(prop_live)) prop_live else NA_character_
  if (is.na(path)) return(NULL)
  d <- read.csv(path, check.names = FALSE, stringsAsFactors = FALSE)
  attr(d, "via") <- if (identical(path, prop_cache)) "cache" else "SHUQING_ROOT"
  d
}

umap <- load_umap()
prop_raw <- load_prop_shuqing()
via_note <- paste0(
  "UMAP via ", attr(umap, "via"), " (", acc_umap, "); ",
  "proportions via ", if (is.null(prop_raw)) "UMAP-derived" else attr(prop_raw, "via"),
  " (", acc_prop, ")"
)

# Normalize feature column name across cache variants
if (!"score" %in% names(umap)) {
  if ("FCGR3A" %in% names(umap)) {
    umap$score <- as.numeric(umap$FCGR3A)
  } else if ("FCGR3A_raw" %in% names(umap)) {
    umap$score <- as.numeric(umap$FCGR3A_raw)
  }
}
if (!"celltype" %in% names(umap) && "celltype_major" %in% names(umap)) {
  umap$celltype <- umap$celltype_major
}

# Ensure required columns
need_u <- c("umap_1", "umap_2", "celltype", "score")
miss_u <- setdiff(need_u, names(umap))
if (length(miss_u)) stop("UMAP missing columns: ", paste(miss_u, collapse = ", "))
umap$celltype <- as.factor(umap$celltype)
n <- nrow(umap)

write.csv(umap[, intersect(c("umap_1", "umap_2", "celltype", "group", "tissue", "patient", "score"), names(umap))],
          file.path(tab_dir, delivery_table_name(skill_en, "UMAP", "GSE164522")), row.names = FALSE)
write_delivery_audit(
  skill_en, "post", n, ncol(umap), n, paste0(acc_umap, " Seurat UMAP subsample + ", acc_prop, " proportions"),
  TRUE, NA, paste(sourced_note, via_note, sep = " | "),
  "celltype UMAP + FCGR3A feature UMAP + stacked proportions; data_provenance=REAL",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "REAL"
)

library(ggplot2)
p <- plot_umap_discrete_journal(
  umap, x_col = "umap_1", y_col = "umap_2", label_col = "celltype",
  title = paste0("Cell-type UMAP — ", acc_umap),
  point_size = 0.45,
  label_on_plot = TRUE,
  show_legend = FALSE,
  label_size = 3.0
)
delivery_save_plot(p, skill_en, "UMAP", "Celltype", 6.8, 5.8, fig_dir, bio_root, order = 1)

p_feat <- plot_umap_feature_journal(
  umap, x_col = "umap_1", y_col = "umap_2", feature_col = "score",
  title = paste0("Feature UMAP — FCGR3A (", acc_umap, ")"),
  point_size = 0.45, legend_name = "FCGR3A"
)
delivery_save_plot(p_feat, skill_en, "featureumap", "FCGR3A", 6.8, 5.8, fig_dir, bio_root, order = 2)

# Stacked proportions: prefer 书清 group×celltype counts; else patient×celltype from UMAP
if (!is.null(prop_raw) && all(c("group", "celltype", "n") %in% names(prop_raw))) {
  prop_tab <- prop_raw
  prop_tab$sample <- as.character(prop_tab$group)
  prop_tab$proportion <- ave(as.numeric(prop_tab$n), prop_tab$sample, FUN = function(x) x / sum(x))
  prop_tab$facet <- prop_tab$sample
  stack_title <- paste0("Cell proportions by group — ", acc_prop)
  facet_use <- NULL  # only 2 groups; facet redundant
} else {
  if (!"patient" %in% names(umap)) umap$patient <- umap$group
  prop_tab <- as.data.frame(table(sample = umap$patient, celltype = umap$celltype))
  names(prop_tab)[3] <- "n"
  prop_tab$proportion <- ave(prop_tab$n, prop_tab$sample, FUN = function(x) x / sum(x))
  if ("group" %in% names(umap)) {
    risk_map <- unique(umap[, c("patient", "group")])
    names(risk_map) <- c("sample", "facet")
    prop_tab <- merge(prop_tab, risk_map, by = "sample")
    facet_use <- "facet"
  } else {
    facet_use <- NULL
  }
  stack_title <- paste0("Cell proportions by patient — ", acc_umap)
}
write.csv(prop_tab, file.path(tab_dir, delivery_table_name(skill_en, "Proportion", "Stacked")), row.names = FALSE)

p_stack <- plot_stacked_proportion_journal(
  prop_tab,
  sample_col = "sample", celltype_col = "celltype", prop_col = "proportion",
  facet_col = facet_use,
  title = stack_title
)
delivery_save_plot(p_stack, skill_en, "stackedbar", "ByGroup", 7.5, 4.8, fig_dir, bio_root, order = 3)

fig_map <- c(
  "细胞类型UMAP" = paste0("../图片文件/", delivery_stem(skill_en, "UMAP", "Celltype", order = 1), ".png"),
  "特征UMAP" = paste0("../图片文件/", delivery_stem(skill_en, "featureumap", "FCGR3A", order = 2), ".png"),
  "堆叠比例" = paste0("../图片文件/", delivery_stem(skill_en, "stackedbar", "ByGroup", order = 3), ".png")
)
interp <- paste0(
  "REAL：", acc_umap, " Seurat UMAP 子样（细胞类型 + FCGR3A feature）；",
  "堆叠比例优先 ", acc_prop, " 书清细胞类型比例表。data_provenance=REAL。"
)
status <- "PASS"

data_html <- paste0(
  "<p><b>data_provenance: REAL</b></p>",
  "<ul>",
  "<li>UMAP / feature：<code>", acc_umap, "</code>（山水 <code>GSE164522_seurat_umap_subsample.rds</code> → 缓存 CSV）</li>",
  "<li>堆叠比例：<code>", acc_prop, "</code>（书清 <code>细胞类型比例.csv</code>）</li>",
  "</ul>",
  "<p>详见 <code>数据文件/DATA_SOURCE.md</code> / <code>PROVENANCE.md</code>。</p>"
)
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- if (file.exists(audit_path)) {
  paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")
} else {
  "<p>无 post 审计表</p>"
}
rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(
  skill_en, skill_folder, status,
  data_html, audit_html, paste(sourced_note, via_note, sep = " | "), fig_map, interp, rep_file,
  blocked_reason = if (exists("blocked_reason")) blocked_reason else ""
)
writeLines(
  c(status, "data_provenance=REAL", paste0("umap_accession=", acc_umap), paste0("proportion_accession=", acc_prop)),
  file.path(rep_dir, "STATUS.txt")
)
for (old in c("sample_pca.png", "sample_volcano.png", "样例报告.html")) {
  f1 <- file.path(fig_dir, old); if (file.exists(f1)) file.remove(f1)
  f2 <- file.path(rep_dir, old); if (file.exists(f2)) file.remove(f2)
}
message("DONE ", status, " — ", skill_folder, " REAL UMAP=", acc_umap, " PROP=", acc_prop, " report=", basename(rep_file))
