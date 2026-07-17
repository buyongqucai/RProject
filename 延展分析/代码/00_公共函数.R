# 延展分析公共函数：路径、数据加载、ID/同源映射、绘图主题
suppressPackageStartupMessages({
  library(tidyverse)
})

`%||%` <- function(x, y) if (is.null(x)) y else x

# ---- 中文字体（PDF 正确显示中文）----
suppressPackageStartupMessages(try(library(showtext), silent = TRUE))
if ("showtext" %in% loadedNamespaces()) {
  fp <- "C:/Windows/Fonts/simhei.ttf"
  if (file.exists(fp)) {
    sysfonts::font_add("SimHei", fp)
    showtext::showtext_auto()
    showtext::showtext_opts(dpi = 300)
    ggplot2::theme_set(ggplot2::theme_bw(base_size = 11) +
                         ggplot2::theme(text = ggplot2::element_text(family = "SimHei")))
    CJK_FONT <- "SimHei"
  }
}
if (!exists("CJK_FONT")) CJK_FONT <- ""

# ---- 路径 ----
find_root <- function() {
  p <- normalizePath(getwd(), winslash = "/")
  for (i in seq_len(6)) {
    if (file.exists(file.path(p, "RProject.Rproj"))) return(p)
    parent <- dirname(p); if (identical(parent, p)) break; p <- parent
  }
  normalizePath("../..", winslash = "/")
}
PROJECT_ROOT <- find_root()
EXT_ROOT <- file.path(PROJECT_ROOT, "延展分析")
EXT <- list(
  代码 = file.path(EXT_ROOT, "代码"),
  图形 = file.path(EXT_ROOT, "结果", "图形"),
  表格 = file.path(EXT_ROOT, "结果", "表格"),
  报告 = file.path(EXT_ROOT, "报告"),
  中间 = file.path(EXT_ROOT, "结果", "中间")
)
for (p in EXT) dir.create(p, recursive = TRUE, showWarnings = FALSE)

# ---- 数据集元信息（物种、对比、类型）----
DATASETS <- tibble::tribble(
  ~id,          ~species, ~type,   ~case,     ~control,
  "GSE79962",   "human",  "bulk",  "SCM",     "Control",
  "GSE267388",  "mouse",  "bulk",  "LPS",     "PBS",
  "GSE207363",  "mouse",  "scrna", "Sepsis",  "Sham",
  "GSE207177",  "mouse",  "scrna", "CLP",     "Control",
  "GSE190856",  "mouse",  "scrna", "CLP",     "Steady"
)

mid_path <- function(ds, suffix) file.path(PROJECT_ROOT, ds, "源数据", "中间文件",
                                           paste0(ds, "_", suffix))

load_deg <- function(ds) {
  f <- mid_path(ds, "deg.rds")
  if (!file.exists(f)) return(NULL)
  d <- readRDS(f)
  d %>% dplyr::filter(!is.na(gene), !is.na(log2FC), !is.na(padj))
}

load_bulk_expr <- function(ds) {
  f <- mid_path(ds, "expr_matrix.rds")
  if (!file.exists(f)) return(NULL)
  readRDS(f)
}
load_bulk_meta <- function(ds) {
  f <- mid_path(ds, "sample_info_final.rds")
  if (!file.exists(f)) f <- mid_path(ds, "sample_info.rds")
  if (!file.exists(f)) return(NULL)
  readRDS(f)
}
load_seurat <- function(ds) {
  f <- mid_path(ds, "seurat.rds")
  if (!file.exists(f)) return(NULL)
  readRDS(f)
}

# ---- 同源基因映射（小鼠 symbol -> 人 symbol）----
mouse_to_human <- function(mouse_symbols) {
  suppressPackageStartupMessages(library(babelgene))
  ortho <- babelgene::orthologs(genes = unique(mouse_symbols), species = "mouse", human = FALSE)
  # 返回列：human_symbol, symbol(mouse)
  setNames(ortho$human_symbol, ortho$symbol)
}
human_to_mouse <- function(human_symbols) {
  suppressPackageStartupMessages(library(babelgene))
  ortho <- babelgene::orthologs(genes = unique(human_symbols), species = "mouse", human = TRUE)
  setNames(ortho$symbol, ortho$human_symbol)
}

# ---- ranked 向量（用于 GSEA/decoupleR）----
deg_rank_vector <- function(deg) {
  # 用符号 * -log10(p) 排序统计量；缺失 t 时用 log2FC 方向
  stat <- if ("t" %in% colnames(deg)) deg$t else sign(deg$log2FC) * -log10(pmax(deg$pvalue, 1e-300))
  v <- stat
  names(v) <- deg$gene
  v <- v[!is.na(v) & !is.na(names(v)) & names(v) != ""]
  v <- v[!duplicated(names(v))]
  sort(v, decreasing = TRUE)
}

ext_theme <- function() ggplot2::theme_bw(base_size = 11)

save_fig <- function(p, name, width = 8, height = 6) {
  ggplot2::ggsave(file.path(EXT$图形, name), p, width = width, height = height)
}
save_tab <- function(df, name) {
  write.csv(df, file.path(EXT$表格, name), row.names = FALSE)
}

message("公共函数就绪；PROJECT_ROOT=", PROJECT_ROOT)
