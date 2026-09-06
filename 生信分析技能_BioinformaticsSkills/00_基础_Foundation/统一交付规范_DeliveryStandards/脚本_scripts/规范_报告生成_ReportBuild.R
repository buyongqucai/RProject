# HTML 图文报告骨架（相对路径引用本样例图片）
# 范式说明：../文档_docs/样例报告范式_SampleReportParadigm.md
# 金标：分子动力学模拟_MolecularDynamics/01_样例_sample/.../样例报告_SampleReport_v1.html

delivery_or <- function(a, b) {
  if (is.null(a) || length(a) == 0L ||
      (length(a) == 1L && (is.na(a) || (is.character(a) && !nzchar(a))))) {
    b
  } else {
    a
  }
}

delivery_html_escape <- function(x) {
  x <- as.character(x)
  x[is.na(x)] <- ""
  x <- gsub("&", "&amp;", x, fixed = TRUE)
  x <- gsub("<", "&lt;", x, fixed = TRUE)
  x <- gsub(">", "&gt;", x, fixed = TRUE)
  x <- gsub("\"", "&quot;", x, fixed = TRUE)
  x
}

delivery_is_html <- function(x) {
  is.character(x) && length(x) >= 1L &&
    grepl("<(p|div|ul|ol|h[1-6]|section|table|details|article|aside|figure)\\b",
          paste(x, collapse = "\n"), ignore.case = TRUE)
}

delivery_as_html <- function(x, wrap = "p") {
  if (is.null(x)) return("")
  x <- paste(as.character(x), collapse = "\n")
  if (!nzchar(trimws(x))) return("")
  if (delivery_is_html(x)) return(x)
  sprintf("<%s>%s</%s>", wrap, delivery_html_escape(x), wrap)
}

delivery_status_tone <- function(status) {
  s <- toupper(as.character(status)[1])
  if (s %in% c("PASS", "REAL", "OK")) return("ok")
  if (grepl("BLOCK|FAIL", s)) return("bad")
  "warn"
}

#' 期刊 muted 学术报告 CSS（对齐 VizStandards：#5B8FA8 / #6B8F71 / #C17B7B）
delivery_report_css <- function() {
  paste(c(
    ":root{--ink:#1c2430;--muted:#5a6573;--line:#e6e2d9;--paper:#f4f1ea;--card:#fff;",
    "--accent:#5B8FA8;--ok:#6B8F71;--warn:#C17B7B;--accent2:#8B7BA8;--accent3:#D4A574}",
    "*{box-sizing:border-box}",
    "html{font-size:16px}",
    "body{margin:0;background:var(--paper);color:var(--ink);",
    "font-family:'Segoe UI','Source Han Sans SC','Noto Sans SC','Microsoft YaHei',Arial,sans-serif;",
    "line-height:1.65}",
    ".wrap{max-width:1100px;margin:0 auto;padding:2rem 1.4rem 4rem}",
    "header.hero{padding:0 0 1.15rem;border-bottom:1px solid var(--line)}",
    "header.hero .kicker{font-size:.78rem;letter-spacing:.08em;text-transform:uppercase;",
    "color:var(--accent);font-weight:650;margin:0 0 .35rem}",
    "header.hero h1{font-size:1.55rem;font-weight:650;margin:0 0 .45rem;letter-spacing:-.02em;line-height:1.3}",
    ".lead{color:var(--muted);font-size:.98rem;margin:.2rem 0 0}",
    ".pills{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.85rem}",
    ".pill{display:inline-block;padding:.12rem .65rem;border:1px solid var(--line);border-radius:999px;",
    "font-size:.78rem;background:var(--card);color:var(--ink)}",
    ".pill.ok{border-color:#c5d4c8;background:#f3f7f3;color:#3d5c42}",
    ".pill.warn{border-color:#ead3d3;background:#fbf6f6;color:#7a4545}",
    ".pill.bad{border-color:#ead3d3;background:#f8ecec;color:#7a4545}",
    ".kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:.7rem;margin:1.2rem 0 0}",
    ".kpi{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--accent);",
    "border-radius:8px;padding:.7rem .85rem}",
    ".kpi b{display:block;font-size:1.12rem;font-variant-numeric:tabular-nums;font-weight:650}",
    ".kpi span{display:block;color:var(--muted);font-size:.75rem;margin-top:.15rem}",
    "nav.toc{margin:1.2rem 0;padding:.85rem 1rem;background:var(--card);border:1px solid var(--line);",
    "border-radius:8px;font-size:.9rem}",
    "nav.toc strong{display:block;font-size:.78rem;color:var(--muted);margin-bottom:.35rem;font-weight:600}",
    "nav.toc a{color:var(--accent);text-decoration:none;margin-right:1.05rem;white-space:nowrap}",
    "nav.toc a:hover{text-decoration:underline}",
    "h2{font-size:1.18rem;margin:2rem 0 .7rem;padding-bottom:.35rem;",
    "border-bottom:2px solid var(--accent);font-weight:650}",
    "h3{font-size:.98rem;margin:.15rem 0 .45rem;font-weight:650}",
    ".card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:1rem 1.1rem;margin:.75rem 0}",
    ".grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}",
    ".grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.85rem}",
    ".stack{display:flex;flex-direction:column;gap:1rem}",
    "@media(max-width:840px){.grid2,.grid3{grid-template-columns:1fr}.wrap{padding:1.2rem .9rem 3rem}}",
    ".fig-card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:.85rem .9rem}",
    ".fig-card.wide{grid-column:1/-1}",
    "figure{margin:0}",
    "figure img{width:100%;height:auto;background:#fff;border:1px solid var(--line);border-radius:4px;display:block}",
    "figcaption{font-size:.84rem;color:var(--muted);margin-top:.45rem}",
    ".note{font-size:.9rem;margin:.45rem 0 0;color:var(--ink)}",
    ".intro{color:var(--muted);font-size:.95rem;margin:0 0 .85rem}",
    ".callout{border-left:3px solid var(--accent3);background:#faf6f0;padding:.8rem 1rem;margin:1rem 0;border-radius:0 8px 8px 0}",
    ".callout.warn{border-left-color:var(--warn);background:#fbf6f6}",
    ".callout.ok{border-left-color:var(--ok);background:#f4f7f4}",
    "table.kv{width:100%;border-collapse:collapse;font-size:.9rem}",
    "table.kv th,table.kv td{border-bottom:1px solid var(--line);text-align:left;padding:.42rem .5rem;vertical-align:top}",
    "table.kv th{color:var(--muted);font-weight:600;width:26%;white-space:nowrap}",
    "code{font-size:.88em;background:#eeeae3;padding:.05rem .32rem;border-radius:3px}",
    "ul.compact{margin:.25rem 0 .25rem 1.15rem;padding:0}",
    "ul.compact li{margin:.28rem 0}",
    "footer.foot{margin-top:2.4rem;color:var(--muted);font-size:.8rem;border-top:1px solid var(--line);padding-top:.85rem}",
    "@media print{body{background:#fff}.wrap{max-width:none;padding:0}.fig-card,.card{break-inside:avoid}}",
    ""
  ), collapse = "")
}

delivery_kpi_html <- function(kpis) {
  if (is.null(kpis) || length(kpis) == 0L) return("")
  cards <- vapply(seq_along(kpis), function(i) {
    item <- kpis[[i]]
    if (is.character(item) && length(item) == 1L) {
      lab <- names(kpis)[i]
      if (is.null(lab) || !nzchar(lab)) lab <- "指标"
      val <- item
      hint <- ""
    } else {
      lab <- delivery_or(item$label, delivery_or(names(kpis)[i], "指标"))
      val <- delivery_or(item$value, "")
      unit <- delivery_or(item$unit, "")
      if (nzchar(as.character(unit))) val <- paste(val, unit)
      hint <- delivery_or(item$hint, "")
    }
    sprintf(
      "<div class='kpi'><b>%s</b><span>%s%s</span></div>",
      delivery_html_escape(val),
      delivery_html_escape(lab),
      if (nzchar(as.character(hint))) paste0(" · ", delivery_html_escape(hint)) else ""
    )
  }, character(1))
  paste0("<div class='kpis'>", paste(cards, collapse = ""), "</div>")
}

delivery_audit_labels <- function() {
  c(
    skill = "技能",
    stage = "审计阶段",
    n_rows = "行数 / 帧数",
    n_cols = "列数",
    n_samples = "样本数",
    group_source = "分组来源",
    toy = "toy",
    data_provenance = "数据来源标注",
    accession = "Accession / PDB",
    sourced_skill_scripts = "已 source 脚本",
    notes = "备注",
    checked_at = "审计时间"
  )
}

delivery_kv_table <- function(fields) {
  nms <- names(fields)
  rows <- vapply(seq_along(fields), function(i) {
    sprintf("<tr><th>%s</th><td>%s</td></tr>",
            delivery_html_escape(nms[[i]]),
            delivery_html_escape(as.character(fields[[i]])))
  }, character(1))
  paste0("<div class='card'><table class='kv'>", paste(rows, collapse = ""), "</table></div>")
}

delivery_audit_block_html <- function(audit_summary_html, audit_fields = NULL) {
  if (!is.null(audit_fields) && length(audit_fields) > 0L) {
    return(delivery_kv_table(audit_fields))
  }
  raw <- paste(as.character(audit_summary_html), collapse = "\n")
  if (!nzchar(trimws(raw))) return("")
  txt <- raw
  if (grepl("<pre>", txt, ignore.case = TRUE)) {
    txt <- sub("(?s)^.*<pre[^>]*>", "", txt, perl = TRUE)
    txt <- sub("(?s)</pre>.*$", "", txt, perl = TRUE)
    txt <- gsub("&lt;", "<", txt, fixed = TRUE)
    txt <- gsub("&gt;", ">", txt, fixed = TRUE)
    txt <- gsub("&amp;", "&", txt, fixed = TRUE)
    df <- tryCatch(utils::read.csv(text = txt, stringsAsFactors = FALSE, check.names = FALSE),
                   error = function(e) NULL)
    if (!is.null(df) && nrow(df) >= 1L) {
      labs <- delivery_audit_labels()
      row1 <- as.list(df[1, , drop = FALSE])
      nms <- names(row1)
      pretty <- ifelse(nms %in% names(labs), unname(labs[nms]), nms)
      names(row1) <- pretty
      return(delivery_kv_table(row1))
    }
  }
  if (grepl("<table", raw, ignore.case = TRUE)) {
    return(paste0("<div class='card'>", raw, "</div>"))
  }
  paste0("<div class='card'>", delivery_as_html(raw), "</div>")
}

delivery_figure_card_html <- function(item) {
  title <- delivery_or(item$title, delivery_or(item$name, ""))
  src <- delivery_or(item$src, delivery_or(item$path, ""))
  if (!nzchar(src)) return("")
  cap <- delivery_or(item$caption, "")
  note <- delivery_or(item$note, "")
  wide <- isTRUE(item$wide)
  sprintf(
    "<article class='fig-card%s'><h3>%s</h3><figure><img src='%s' alt='%s'/>%s</figure>%s</article>",
    if (wide) " wide" else "",
    delivery_html_escape(title),
    src,
    delivery_html_escape(title),
    if (nzchar(cap)) paste0("<figcaption>", delivery_html_escape(cap), "</figcaption>") else "",
    if (nzchar(note)) paste0("<p class='note'>",
                             if (delivery_is_html(note)) note else delivery_html_escape(note),
                             "</p>") else ""
  )
}

delivery_normalize_figure_items <- function(figures, captions = NULL, notes = NULL) {
  if (is.null(figures) || length(figures) == 0L) return(list())
  if (is.list(figures) && !is.null(figures[[1]]) && is.list(figures[[1]]) &&
      !is.null(delivery_or(figures[[1]]$src, figures[[1]]$path))) {
    return(figures)
  }
  nms <- names(figures)
  if (is.null(nms)) nms <- rep("", length(figures))
  lapply(seq_along(figures), function(i) {
    nm <- if (!nzchar(nms[[i]])) as.character(i) else nms[[i]]
    src <- as.character(figures[[i]])[1]
    list(
      title = nm,
      src = src,
      caption = if (!is.null(captions) && nm %in% names(captions)) captions[[nm]] else "",
      note = if (!is.null(notes) && nm %in% names(notes)) notes[[nm]] else "",
      wide = FALSE
    )
  })
}

delivery_section_html <- function(sec) {
  items <- delivery_or(sec$items, delivery_or(sec$figures, list()))
  items <- delivery_normalize_figure_items(items)
  cards <- Filter(function(x) nzchar(x), vapply(items, delivery_figure_card_html, character(1)))
  layout <- delivery_or(sec$layout, "grid2")
  if (!layout %in% c("grid2", "grid3", "stack")) layout <- "grid2"
  intro <- delivery_or(sec$intro, "")
  sid <- delivery_or(sec$id, gsub("[^A-Za-z0-9_-]", "", delivery_or(sec$title, "section")))
  paste0(
    sprintf("<h2 id='sec-%s'>%s</h2>", sid, delivery_html_escape(delivery_or(sec$title, "图表"))),
    if (nzchar(intro)) paste0("<p class='intro'>",
                              if (delivery_is_html(intro)) intro else delivery_html_escape(intro),
                              "</p>") else "",
    sprintf("<div class='%s'>", layout),
    paste(cards, collapse = "\n"),
    "</div>"
  )
}

#' 写出样例 HTML 报告（向后兼容旧的 9 个位置参数）
#'
#' @param skill_en 技能英文
#' @param skill_folder 完整文件夹名
#' @param status PASS|BLOCKED|FAIL|REAL|…
#' @param data_source_html 数据来源 HTML 片段
#' @param audit_summary_html 审计摘要（CSV `<pre>` 会自动转成两列表）
#' @param sourced_scripts 已 source 的脚本说明
#' @param figures named list/character：显示名 -> 相对路径（相对报告文件）
#' @param interpretation 解读（纯文本或 HTML）
#' @param out_path 输出 HTML 路径
#' @param blocked_reason BLOCKED 时的原因
#' @param version 报告版本后缀
#' @param kpis KPI 条：named character，或 list(list(label,value,unit,hint), …)
#' @param figure_sections 分组图：list(list(id,title,intro,layout,items), …)
#' @param figure_captions / figure_notes 扁平 figures 的图注（按显示名）
#' @param methods_html 覆盖「方法与脚本」正文
#' @param caveats_html 页首警示（演示尺度、TOY 等）
#' @param subtitle / lead_html / report_title 页眉
#' @param audit_fields 命名向量，优先于解析 audit_summary_html
#' @param toc 是否输出目录
write_delivery_report <- function(skill_en, skill_folder, status,
                                  data_source_html, audit_summary_html,
                                  sourced_scripts, figures,
                                  interpretation, out_path,
                                  blocked_reason = "",
                                  version = "v1",
                                  kpis = NULL,
                                  figure_sections = NULL,
                                  figure_captions = NULL,
                                  figure_notes = NULL,
                                  methods_html = NULL,
                                  caveats_html = NULL,
                                  subtitle = NULL,
                                  lead_html = NULL,
                                  report_title = NULL,
                                  audit_fields = NULL,
                                  toc = TRUE) {
  if (is.null(figure_sections) || length(figure_sections) == 0L) {
    if (is.null(figures) || (is.character(figures) && is.null(names(figures)))) {
      stop("figures 须为命名向量/list：显示名 = 相对路径；或提供 figure_sections", call. = FALSE)
    }
  }
  if (is.null(report_title) || !nzchar(report_title)) {
    report_title <- paste0(skill_folder, " — 样例验证报告")
  }
  tone <- delivery_status_tone(status)
  pills <- paste0(
    sprintf("<span class='pill %s'>状态 %s</span>", tone, delivery_html_escape(status)),
    sprintf("<span class='pill'>%s</span>", delivery_html_escape(skill_en)),
    sprintf("<span class='pill'>报告 %s</span>", delivery_html_escape(version))
  )
  if (identical(status, "BLOCKED") && nzchar(blocked_reason)) {
    pills <- paste0(pills, sprintf("<span class='pill bad'>%s</span>",
                                   delivery_html_escape(blocked_reason)))
  }

  methods_body <- if (!is.null(methods_html) && nzchar(methods_html)) {
    methods_html
  } else {
    delivery_as_html(sourced_scripts)
  }

  if (is.null(figure_sections) || length(figure_sections) == 0L) {
    figure_sections <- list(list(
      id = "figures",
      title = "主要图表",
      layout = "grid2",
      items = delivery_normalize_figure_items(figures, figure_captions, figure_notes)
    ))
  }

  toc_links <- c(
    "<a href='#sec-methods'>方法</a>",
    "<a href='#sec-data'>数据来源</a>",
    "<a href='#sec-audit'>审计</a>"
  )
  fig_html <- paste(vapply(figure_sections, function(sec) {
    sid <- delivery_or(sec$id, "figures")
    ttl <- delivery_or(sec$title, "图表")
    toc_links <<- c(toc_links, sprintf("<a href='#sec-%s'>%s</a>", sid, delivery_html_escape(ttl)))
    delivery_section_html(sec)
  }, character(1)), collapse = "\n")
  toc_links <- c(toc_links, "<a href='#sec-interp'>结果解读</a>")

  interp_html <- delivery_as_html(interpretation)
  if (!nzchar(interp_html)) interp_html <- "<p>（无解读）</p>"

  html <- paste0(
    "<!DOCTYPE html>\n<html lang='zh-CN'><head><meta charset='utf-8'/>",
    "<meta name='viewport' content='width=device-width, initial-scale=1'/>",
    "<title>", delivery_html_escape(skill_en), " 样例报告</title>",
    "<style>", delivery_report_css(), "</style></head><body><div class='wrap'>",
    "<header class='hero'>",
    "<p class='kicker'>DeliveryStandards sample report</p>",
    "<h1>", delivery_html_escape(report_title), "</h1>",
    if (!is.null(subtitle) && nzchar(subtitle)) {
      paste0("<p class='lead'>", delivery_html_escape(subtitle), "</p>")
    } else "",
    if (!is.null(lead_html) && nzchar(lead_html)) {
      if (delivery_is_html(lead_html)) lead_html else paste0("<p class='lead'>", delivery_html_escape(lead_html), "</p>")
    } else "",
    "<div class='pills'>", pills, "</div>",
    delivery_kpi_html(kpis),
    "</header>",
    if (!is.null(caveats_html) && nzchar(caveats_html)) {
      cls <- if (grepl("TOY|演示|不可外推|BLOCKED", caveats_html, ignore.case = TRUE)) "callout warn" else "callout"
      paste0("<div class='", cls, "'>",
             if (delivery_is_html(caveats_html)) caveats_html else delivery_as_html(caveats_html),
             "</div>")
    } else "",
    if (isTRUE(toc)) paste0("<nav class='toc'><strong>目录</strong>", paste(toc_links, collapse = ""), "</nav>") else "",
    "<h2 id='sec-methods'>方法与脚本</h2>",
    "<div class='card'>", methods_body, "</div>",
    "<h2 id='sec-data'>数据来源</h2>",
    "<div class='card'>", delivery_as_html(data_source_html), "</div>",
    "<h2 id='sec-audit'>审计摘要</h2>",
    delivery_audit_block_html(audit_summary_html, audit_fields),
    fig_html,
    "<h2 id='sec-interp'>结果解读</h2>",
    "<div class='card'>", interp_html, "</div>",
    "<footer class='foot'>生成时间：",
    format(Sys.time(), "%Y-%m-%d %H:%M:%S"),
    " · 报告规范：统一交付规范_DeliveryStandards · 出图规范：统一可视化规范_VizStandards · 版本 ",
    delivery_html_escape(version),
    "</footer></div></body></html>"
  )
  dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)
  con <- file(out_path, open = "w", encoding = "UTF-8")
  on.exit(close(con), add = TRUE)
  writeLines(html, con, useBytes = FALSE)
  invisible(out_path)
}
