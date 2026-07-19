# 统一交付：中英对照出图/表命名（封装 VizStandards::save_plot_pub）
# 路径：00_基础_Foundation/统一交付规范_DeliveryStandards/脚本_scripts/
# 强制模式：{中文语义}_{EnglishCamelOrPascal}[_{主题}].{ext}
# 技能英文缩写仅作目录/内部 id，不得单独作为交付文件名主前缀。
#
# 【文件名双语 ≠ 图面英文】
# - 本文件只生成交付文件名 stem（中英对照）。
# - ggtitle / labs(title=) / main= / 轴 / 图例：English only，禁止中文；禁止
#   「接触矩阵示意 Contact Matrix Stub」「火山图 Treat vs Control Volcano」这类并排。
# - 不要把 delivery_stem() 的中英拼进图题；图面英文与文件名各自独立。

.delivery_find_viz <- function(start = getwd()) {
  p <- normalizePath(start, winslash = "/", mustWork = FALSE)
  for (i in seq_len(12)) {
    cand <- file.path(
      p, "生信分析技能_BioinformaticsSkills", "00_基础_Foundation",
      "统一可视化规范_VizStandards", "脚本_scripts", "出版级出图_PublicationPlot.R"
    )
    if (file.exists(cand)) return(cand)
    cand2 <- file.path(
      p, "00_基础_Foundation", "统一可视化规范_VizStandards",
      "脚本_scripts", "出版级出图_PublicationPlot.R"
    )
    if (file.exists(cand2)) return(cand2)
    parent <- dirname(p)
    if (identical(parent, p)) break
    p <- parent
  }
  stop("未找到 出版级出图_PublicationPlot.R", call. = FALSE)
}

.delivery_find_plotqa <- function(start = getwd()) {
  p <- normalizePath(start, winslash = "/", mustWork = FALSE)
  for (i in seq_len(12)) {
    cand <- file.path(
      p, "生信分析技能_BioinformaticsSkills", "00_基础_Foundation",
      "统一可视化规范_VizStandards", "脚本_scripts", "出图后审核_PlotQA.R"
    )
    if (file.exists(cand)) return(cand)
    cand2 <- file.path(
      p, "00_基础_Foundation", "统一可视化规范_VizStandards",
      "脚本_scripts", "出图后审核_PlotQA.R"
    )
    if (file.exists(cand2)) return(cand2)
    parent <- dirname(p)
    if (identical(parent, p)) break
    p <- parent
  }
  NA_character_
}

ensure_pub_viz <- function(start = getwd()) {
  if (!exists("save_plot_pub", mode = "function")) {
    source(.delivery_find_viz(start), encoding = "UTF-8")
  }
  invisible(TRUE)
}

ensure_plotqa <- function(start = getwd()) {
  if (exists("viz_qa_after_plot", mode = "function")) return(invisible(TRUE))
  qa <- .delivery_find_plotqa(start)
  if (!is.na(qa) && file.exists(qa)) {
    source(qa, encoding = "UTF-8")
    return(invisible(TRUE))
  }
  invisible(FALSE)
}

#' 从技能文件夹名取英文段：转录组分析_RNA-seq -> RNA-seq（仅内部 id）
delivery_skill_en <- function(folder_name) {
  if (grepl("_", folder_name, fixed = TRUE)) {
    sub("^.*_", "", folder_name)
  } else {
    folder_name
  }
}

.delivery_clean <- function(x) {
  x <- gsub("[\\\\/:*?\"<>|]+", "-", x)
  x <- gsub("[[:space:]]+", "-", x)
  x
}

.delivery_to_pascal <- function(x) {
  x <- .delivery_clean(x)
  parts <- unlist(strsplit(x, "[-_]+"))
  parts <- parts[nzchar(parts)]
  if (!length(parts)) return("Item")
  paste0(toupper(substring(parts, 1, 1)), substring(parts, 2), collapse = "")
}

.delivery_has_cjk <- function(x) {
  ints <- utf8ToInt(enc2utf8(as.character(x)[1]))
  any(ints >= 0x4E00L & ints <= 0x9FFFL, na.rm = TRUE)
}

# 图类型 → 中文语义 + 英文 Pascal
.DELIVERY_PLOT_MAP <- list(
  volcano = list(zh = "火山图", en = "Volcano"),
  bar = list(zh = "柱状图", en = "Bar"),
  pca = list(zh = "PCA图", en = "PCA"),
  scatter = list(zh = "散点图", en = "Scatter"),
  heatmap = list(zh = "热图", en = "Heatmap"),
  manhattan = list(zh = "曼哈顿图", en = "Manhattan"),
  forest = list(zh = "森林图", en = "Forest"),
  roc = list(zh = "ROC曲线", en = "ROC"),
  umap = list(zh = "UMAP图", en = "UMAP"),
  line = list(zh = "折线图", en = "Line"),
  box = list(zh = "箱线图", en = "Box"),
  boxplot = list(zh = "箱线图", en = "Box"),
  density = list(zh = "密度图", en = "Density"),
  contact = list(zh = "接触矩阵示意", en = "ContactMatrix"),
  kaplan = list(zh = "生存曲线", en = "KaplanMeier"),
  km = list(zh = "生存曲线", en = "KaplanMeier"),
  network = list(zh = "网络图", en = "Network"),
  bubble = list(zh = "气泡图", en = "Bubble"),
  lollipop = list(zh = "棒棒糖图", en = "Lollipop"),
  venn = list(zh = "韦恩图", en = "Venn"),
  enrichment = list(zh = "富集图", en = "Enrichment"),
  circos = list(zh = "圈图", en = "Circos"),
  chord = list(zh = "圈图", en = "Chord"),
  gsea = list(zh = "GSEA曲线", en = "GSEA"),
  featureumap = list(zh = "特征UMAP", en = "FeatureUMAP"),
  stackedbar = list(zh = "堆叠比例图", en = "StackedProportion"),
  proportion = list(zh = "堆叠比例图", en = "StackedProportion"),
  dendrogram = list(zh = "样本树状图", en = "Dendrogram"),
  cladogram = list(zh = "样本树状图", en = "Cladogram"),
  trend = list(zh = "趋势图", en = "Trend"),
  pairedbox = list(zh = "配对箱线图", en = "PairedBox"),
  densitybox = list(zh = "密度箱线组合", en = "DensityBox")
)

# 表类型 → 中文语义 + 英文 Pascal（object 可拼入英文段）
.DELIVERY_TABLE_MAP <- list(
  deg = list(zh = "差异结果", en = "Deg"),
  contract = list(zh = "契约阻塞桩", en = "ContractBlockedStub"),
  rules = list(zh = "规则清单", en = "RulesChecklist"),
  points = list(zh = "演示点集", en = "PointsDemo"),
  checklist = list(zh = "检查清单", en = "Checklist"),
  qc = list(zh = "质控汇总", en = "QcSummary"),
  gsea = list(zh = "富集结果", en = "Gsea"),
  summary = list(zh = "样例汇总", en = "SampleSummary"),
  activity = list(zh = "活性表", en = "Activity"),
  ortholog = list(zh = "同源计数", en = "OrthologCounts"),
  degree = list(zh = "枢纽度", en = "HubDegree"),
  ko = list(zh = "敲除效应", en = "KoLogFC"),
  lr = list(zh = "配体受体", en = "LrScores"),
  corr = list(zh = "相关表", en = "Corr"),
  trajectory = list(zh = "拟时序", en = "Trajectory"),
  rank = list(zh = "排序表", en = "Rank"),
  forest = list(zh = "森林数据", en = "Forest"),
  af = list(zh = "等位频率", en = "AlleleFreq"),
  timeseries = list(zh = "时序表", en = "TimeSeries"),
  consensus = list(zh = "共识相关", en = "Consensus"),
  check = list(zh = "核对表", en = "Check"),
  umap = list(zh = "UMAP坐标", en = "Umap"),
  contact = list(zh = "接触矩阵", en = "ContactMatrix")
)

.delivery_lookup_plot <- function(plot_type) {
  key <- tolower(plot_type)
  if (!is.null(.DELIVERY_PLOT_MAP[[key]])) return(.DELIVERY_PLOT_MAP[[key]])
  list(zh = "示意图", en = .delivery_to_pascal(plot_type))
}

#' 中英对照 stem（不含扩展名）
#' 兼容旧调用：delivery_stem(skill_en, "volcano", "TreatVsControl")
#'   → 火山图_TreatVsControl_Volcano
#' 新调用：delivery_stem("火山图", "Volcano", "TreatVsControl") 同上
#' 或 delivery_bilingual_stem("审计后检", "AuditPost")
delivery_bilingual_stem <- function(zh_semantic, en_pascal) {
  zh_semantic <- .delivery_clean(zh_semantic)
  en_pascal <- .delivery_clean(en_pascal)
  if (!.delivery_has_cjk(zh_semantic)) {
    stop("交付 stem 必须含中文语义前缀，收到: ", zh_semantic, call. = FALSE)
  }
  if (!nzchar(en_pascal) || .delivery_has_cjk(en_pascal)) {
    stop("交付 stem 英文段须为 Camel/Pascal 且非空: ", en_pascal, call. = FALSE)
  }
  paste(zh_semantic, en_pascal, sep = "_")
}

delivery_stem <- function(skill_en_or_zh, plot_type, theme = NULL, order = NULL) {
  # 若第一参数已是中文且第二参数像英文类型名，走双语直拼
  if (.delivery_has_cjk(skill_en_or_zh) && !.delivery_has_cjk(plot_type)) {
    en <- .delivery_to_pascal(plot_type)
    if (!is.null(theme) && nzchar(theme)) {
      stem <- paste(c(.delivery_clean(skill_en_or_zh), .delivery_clean(theme), en), collapse = "_")
    } else {
      stem <- delivery_bilingual_stem(skill_en_or_zh, en)
    }
    return(delivery_with_order(stem, order))
  }
  info <- .delivery_lookup_plot(plot_type)
  if (!is.null(theme) && nzchar(theme)) {
    stem <- paste(c(info$zh, .delivery_clean(theme), info$en), collapse = "_")
  } else {
    stem <- delivery_bilingual_stem(info$zh, info$en)
  }
  delivery_with_order(stem, order)
}

delivery_table_name <- function(skill_en, table_type, object = NULL) {
  key <- tolower(table_type)
  # 契约阻塞桩固定名
  if (key == "contract" || (!is.null(object) && grepl("blocked", object, ignore.case = TRUE))) {
    return("契约阻塞桩_ContractBlockedStub.csv")
  }
  mapped <- .DELIVERY_TABLE_MAP[[key]]
  if (!is.null(mapped)) {
    # 规则清单/演示点集等：英文段已自含语义，不再拼接 object
    if (key %in% c("rules", "points", "summary") || is.null(object) || !nzchar(object)) {
      return(paste0(delivery_bilingual_stem(mapped$zh, mapped$en), ".csv"))
    }
    stem <- paste(c(mapped$zh, .delivery_clean(object), mapped$en), collapse = "_")
    return(paste0(stem, ".csv"))
  }
  en <- if (!is.null(object) && nzchar(object)) {
    paste0(.delivery_to_pascal(object), .delivery_to_pascal(table_type))
  } else {
    .delivery_to_pascal(table_type)
  }
  paste0(delivery_bilingual_stem("数据表", en), ".csv")
}

delivery_report_name <- function(skill_en = NULL, version = "v1") {
  paste0("样例报告_SampleReport_", version, ".html")
}

delivery_audit_name <- function(skill_en = NULL, stage = "post") {
  if (identical(tolower(stage), "pre")) {
    "审计前检_AuditPre.csv"
  } else {
    "审计后检_AuditPost.csv"
  }
}

#' 样例路径解析：结果嵌套在 代码文件/结果文件/；兼容旧样例根级 结果文件/
#' @return list(sample_root, raw_dir, code_dir, result_dir, fig_dir, tab_dir, rep_dir, layout)
#'   layout = "nested" | "legacy" | "pending"（尚无结果目录时默认 nested）
delivery_sample_paths <- function(sample_root) {
  sample_root <- normalizePath(sample_root, winslash = "/", mustWork = TRUE)
  raw_dir <- file.path(sample_root, "数据文件")
  code_dir <- file.path(sample_root, "代码文件")
  nested <- file.path(code_dir, "结果文件")
  legacy <- file.path(sample_root, "结果文件")
  if (dir.exists(nested)) {
    result_dir <- nested
    layout <- "nested"
  } else if (dir.exists(legacy)) {
    result_dir <- legacy
    layout <- "legacy"
  } else {
    result_dir <- nested
    layout <- "pending"
  }
  list(
    sample_root = sample_root,
    raw_dir = raw_dir,
    code_dir = code_dir,
    result_dir = result_dir,
    fig_dir = file.path(result_dir, "图片文件"),
    tab_dir = file.path(result_dir, "数据文件"),
    rep_dir = file.path(result_dir, "报告文件"),
    layout = layout
  )
}

#' 两位零填充流水线序号：1 -> "01"
delivery_order_prefix <- function(n) {
  sprintf("%02d", as.integer(n))
}

#' 在 delivery_stem 结果前加 NN_ 前缀；order=NULL 时不加
delivery_with_order <- function(stem, order = NULL) {
  if (is.null(order) || is.na(order)) return(stem)
  # 已有 NN_ 前缀则不重复
  if (grepl("^[0-9]{2}_", stem)) return(stem)
  paste0(delivery_order_prefix(order), "_", stem)
}

#' 禁止的无语义 / 纯英文交付名
DELIVERY_BANNED_NAMES <- c(
  "plot.png", "plot.svg", "fig1.png", "fig2.png", "out.csv", "result.html",
  "sample_pca.png", "sample_volcano.png", "sample_summary.csv",
  "toy_deg_results.csv", "样例报告.html"
)

delivery_assert_name_ok <- function(filename) {
  bn <- basename(filename)
  if (tolower(bn) %in% tolower(DELIVERY_BANNED_NAMES)) {
    stop("禁止无语义文件名: ", filename, " — 请用 {中文语义}_{EnglishPascal}", call. = FALSE)
  }
  # 禁止纯英文交付产物（扩展名除外）；允许可选 NN_ 流水线前缀
  stem <- sub("\\.[^.]+$", "", bn)
  stem_chk <- sub("^[0-9]{2}_", "", stem)
  if (grepl("^(sample_|toy_|fig|plot|out)", stem_chk, ignore.case = TRUE)) {
    stop("禁止 sample_/toy_/fig 等纯英文交付名: ", filename, call. = FALSE)
  }
  if (!.delivery_has_cjk(stem_chk)) {
    stop(
      "交付文件名必须中英对照（含中文语义前缀）: ", filename,
      " — 例：01_火山图_TreatVsControl_Volcano.png",
      call. = FALSE
    )
  }
  invisible(TRUE)
}

#' 保存出版级图并校验命名
#' 版式默认单栏约 89 mm（3.5 in）；双栏传 width≈7.1
#' 保存后钩子：VizStandards PlotQA（启发式；WARN 不中断；见出图后审核_PlotQA.md）
delivery_save_plot <- function(plot, skill_en, plot_type, theme = NULL,
                               width = 3.5, height = 3.2, out_dir = ".",
                               start = getwd(), order = NULL) {
  ensure_pub_viz(start)
  stem <- delivery_stem(skill_en, plot_type, theme, order = order)
  delivery_assert_name_ok(paste0(stem, ".png"))
  paths <- save_plot_pub(plot, stem = stem, width = width, height = height, out_dir = out_dir)
  if (isTRUE(getOption("bioinfo.plotqa.after_save", TRUE)) && ensure_plotqa(start)) {
    try(
      viz_qa_after_plot(plot, plot_id = stem, hard_fail = getOption("bioinfo.plotqa.hard_fail", FALSE)),
      silent = TRUE
    )
  }
  invisible(paths)
}
