# 昱阳项目专用：槲皮素人源靶点 → 小鼠同源 → 与 DEG 交集 → GateCounts 断点
# 同源：优先 org.Hs.eg.db + org.Mm.eg.db via AnnotationDbi::mapIds homolog?
# 使用 biomaRt 若可用；否则用 NCBI gene_orthologs 简化：mouse gene symbol case-insensitive match
# 对网药缓存靶点多为人类基因符号，小鼠 DEG 为小鼠符号——用 homologene 风格映射表

suppressPackageStartupMessages({
  library(AnnotationDbi)
  library(org.Mm.eg.db)
})

root <- "E:/RProject/昱阳项目/02_差异分析与药靶断点_DEGandGate"
raw_q <- file.path(root, "01_数据文件_Data/01_初始数据_RawInitial/02_STP_槲皮素靶点_QuercetinTargets")
tab_dir <- file.path(root, "01_数据文件_Data/02_结果数据_ResultTables")
gate_dir <- tab_dir
rep_dir <- file.path(root, "04_报告文件_Reports")
report_sum <- "E:/RProject/昱阳项目/01_分析报告_AnalysisReport/02_阶段汇总_StageSummaries"

human_f <- file.path(raw_q, "02_槲皮素靶点基因列表_人源_QuercetinTargetGenes_Human.csv")
deg_f <- file.path(tab_dir, "05_差异基因_DEG_mainThreshold.csv")
stopifnot(file.exists(human_f), file.exists(deg_f))

human <- read.csv(human_f, stringsAsFactors = FALSE)$gene_human
human <- unique(toupper(trimws(human)))
deg <- read.csv(deg_f, stringsAsFactors = FALSE)
deg$gene_mm <- as.character(deg$gene)

# ---- human -> mouse via org.Hs.eg if available, else same-symbol heuristic + babel ----
map_df <- NULL
if (requireNamespace("org.Hs.eg.db", quietly = TRUE) && requireNamespace("Orthology.eg.db", quietly = TRUE)) {
  # optional path
  message("Orthology.eg.db available — using AnnotationDbi orthology")
}
if (requireNamespace("biomaRt", quietly = TRUE)) {
  message("Trying biomaRt human->mouse...")
  try({
    mart_h <- biomaRt::useEnsembl("ensembl", dataset = "hsapiens_gene_ensembl")
    mart_m <- biomaRt::useEnsembl("ensembl", dataset = "mmusculus_gene_ensembl")
    hm <- biomaRt::getLDS(
      attributes = c("hgnc_symbol"),
      filters = "hgnc_symbol",
      values = human,
      mart = mart_h,
      attributesL = c("mgi_symbol"),
      martL = mart_m
    )
    names(hm) <- c("gene_human", "gene_mouse")
    map_df <- unique(hm)
    map_df$method <- "biomaRt_getLDS"
  }, silent = TRUE)
}

if (is.null(map_df) || nrow(map_df) == 0) {
  message("Fallback: case-insensitive symbol match + common human/mouse identical symbols")
  # Many drug-target symbols identical across species (e.g. TNF, AKT1 vs Akt1)
  deg_u <- unique(deg$gene_mm)
  # map: for each human gene, find mouse with toupper match
  mm_upper <- setNames(deg_u, toupper(deg_u))
  # also map against all possible mouse symbols from org.Mm.eg.db
  all_mm <- keys(org.Mm.eg.db, keytype = "SYMBOL")
  all_mm_map <- setNames(all_mm, toupper(all_mm))
  gene_mouse <- all_mm_map[human]
  # fill NAs with title-case guess
  miss <- is.na(gene_mouse)
  if (any(miss)) {
    gene_mouse[miss] <- vapply(human[miss], function(h) {
      # Akt1-style: first letter upper rest lower for short? Better keep as-is lower
      cand <- paste0(substring(h, 1, 1), tolower(substring(h, 2)))
      if (cand %in% all_mm) return(cand)
      if (tolower(h) %in% tolower(all_mm)) {
        return(all_mm[match(tolower(h), tolower(all_mm))])
      }
      NA_character_
    }, character(1))
  }
  map_df <- data.frame(
    gene_human = human,
    gene_mouse = unname(gene_mouse),
    method = "symbol_casefold_orgMm",
    stringsAsFactors = FALSE
  )
}

map_df <- map_df[!is.na(map_df$gene_mouse) & nzchar(map_df$gene_mouse), , drop = FALSE]
write.csv(map_df, file.path(tab_dir, "08_人鼠同源映射_HumanMouseOrtholog.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

mouse_targets <- unique(map_df$gene_mouse)
write.csv(data.frame(gene_mouse = sort(mouse_targets)),
          file.path(raw_q, "03_槲皮素靶点基因列表_小鼠_QuercetinTargetGenes_Mouse.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

# intersect with DEG
inter <- deg[toupper(deg$gene_mm) %in% toupper(mouse_targets), , drop = FALSE]
# attach human symbol if available
inter$gene_human <- map_df$gene_human[match(toupper(inter$gene_mm), toupper(map_df$gene_mouse))]
write.csv(inter, file.path(tab_dir, "09_药靶与DEG交集_QuercetinDegOverlap.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

n_human <- length(unique(human))
n_mapped <- length(mouse_targets)
n_deg <- nrow(deg)
n_up <- sum(deg$direction == "up")
n_down <- sum(deg$direction == "down")
n_overlap <- nrow(inter)

suggest <- if (n_overlap < 15) {
  "ORA_on_full_DEG (overlap<15; intersection enrichment may be unstable)"
} else {
  "ORA_on_intersection (default per plan)"
}

gate <- data.frame(
  item = c(
    "DEG_total", "DEG_up", "DEG_down",
    "Quercetin_targets_human", "Quercetin_targets_mouse_mapped",
    "Overlap_Quercetin_x_DEG",
    "Suggest_enrichment_gene_set",
    "RigorPack_03_status",
    "Next_user_decision"
  ),
  value = c(
    n_deg, n_up, n_down,
    n_human, n_mapped,
    n_overlap,
    suggest,
    "PLACEHOLDER_skip_by_default",
    "Decide: enable rigor pack? tighten threshold? then continue stage C"
  ),
  stringsAsFactors = FALSE
)
write.csv(gate, file.path(tab_dir, "01_数量断点_GateCounts.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")
# also copy to report stage summary name
dir.create(report_sum, recursive = TRUE, showWarnings = FALSE)
write.csv(gate, file.path(report_sum, "01_数量断点_GateCounts.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

md <- c(
  "# 阶段 A 数量断点（等人决定）",
  "",
  sprintf("- DEG：%s（上调 %s / 下调 %s），阈值 `|logFC|>=1 & P<0.05`", n_deg, n_up, n_down),
  sprintf("- 槲皮素靶点：人源 %s → 小鼠映射 %s", n_human, n_mapped),
  sprintf("- 交集：**%s**", n_overlap),
  sprintf("- 富集建议：`%s`", suggest),
  "- 步骤 `03_可选严谨包_占位_…`：**默认跳过**",
  "",
  "**请回复**：是否启用严谨包；是否收紧阈值；确认后继续阶段 C（富集/PPI/对接）。",
  "",
  sprintf("生成时间：%s", format(Sys.time(), "%Y-%m-%d %H:%M"))
)
writeLines(md, file.path(report_sum, "01_数量断点结论_GateDecision.md"), useBytes = TRUE)

status <- paste(
  "STATUS: GATE_PAUSE",
  sprintf("overlap=%s deg=%s targets_mm=%s", n_overlap, n_deg, n_mapped),
  "Awaiting user decision on rigor pack / threshold before stage C.",
  sep = "\n"
)
writeLines(status, file.path(rep_dir, "01_STATUS.txt"))
message(status)
print(gate)
