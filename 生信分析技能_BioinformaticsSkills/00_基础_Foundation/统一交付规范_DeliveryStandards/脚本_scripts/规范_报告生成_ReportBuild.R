# HTML 图文报告骨架（相对路径引用本样例图片）

#' @param skill_en 技能英文
#' @param skill_folder 完整文件夹名
#' @param status PASS|BLOCKED|FAIL
#' @param data_source_html 数据来源 HTML 片段
#' @param audit_summary_html 审计摘要
#' @param sourced_scripts 已 source 的脚本说明
#' @param figures named list 或 character：显示名 -> 相对路径（相对报告文件）
#' @param interpretation 解读段落
#' @param out_path 输出 HTML 路径
#' @param version 报告版本后缀
write_delivery_report <- function(skill_en, skill_folder, status,
                                  data_source_html, audit_summary_html,
                                  sourced_scripts, figures,
                                  interpretation, out_path,
                                  blocked_reason = "",
                                  version = "v1") {
  if (is.character(figures) && is.null(names(figures))) {
    stop("figures 须为命名向量/list：显示名 = 相对路径", call. = FALSE)
  }
  fig_html <- paste0(vapply(names(figures), function(nm) {
    sprintf("<h3>%s</h3><p><img src='%s' alt='%s'/></p>", nm, figures[[nm]], nm)
  }, character(1)), collapse = "\n")

  status_block <- if (identical(status, "BLOCKED")) {
    sprintf("<p><b>状态：BLOCKED</b> — %s</p>", blocked_reason)
  } else {
    sprintf("<p><b>状态：%s</b></p>", status)
  }

  html <- paste0(
    "<!DOCTYPE html><html><head><meta charset='utf-8'><title>",
    skill_en, " 样例报告</title>",
    "<style>",
    "body{font-family:'Segoe UI',Arial,sans-serif;max-width:920px;margin:2rem auto;line-height:1.55;color:#222}",
    "img{max-width:100%;border:1px solid #ddd;background:#fff}",
    "code{background:#f5f5f5;padding:1px 4px}",
    "table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:4px 8px}",
    "</style></head><body>",
    "<h1>", skill_folder, " — 样例验证报告</h1>",
    status_block,
    "<h2>1. 是否 source 本技能脚本</h2>",
    "<p>", sourced_scripts, "</p>",
    "<h2>2. 数据来源</h2>",
    data_source_html,
    "<h2>3. 审计摘要</h2>",
    audit_summary_html,
    "<h2>4. 主要图表</h2>",
    fig_html,
    "<h2>5. 结果解读</h2>",
    "<p>", interpretation, "</p>",
    "<p><i>生成时间：", format(Sys.time(), "%Y-%m-%d %H:%M:%S"),
    " · 报告规范：统一交付规范_DeliveryStandards · 版本 ", version, "</i></p>",
    "</body></html>"
  )
  dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)
  # writeLines useBytes 对 UTF-8 中文更稳
  con <- file(out_path, open = "w", encoding = "UTF-8")
  on.exit(close(con), add = TRUE)
  writeLines(html, con, useBytes = FALSE)
  invisible(out_path)
}
