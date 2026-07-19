# 最小数据审计清单：样本数、行列、分组来源、toy 标记、data_provenance

#' @param skill_en 技能英文名
#' @param stage "pre" | "post"
#' @param n_rows,n_cols 矩阵维度
#' @param n_samples 样本数
#' @param group_source 分组来源说明（如 toy_meta.csv / GEO Series Matrix）
#' @param toy 是否玩具数据（兼容旧字段；新规范以 data_provenance 为准）
#' @param accession 公共库编号（可空）
#' @param notes 备注
#' @param out_path 输出 CSV 完整路径
#' @param data_provenance REAL|TOY|BLOCKED（强制显式标注）
write_delivery_audit <- function(skill_en, stage = "post",
                                 n_rows = NA_integer_, n_cols = NA_integer_,
                                 n_samples = NA_integer_,
                                 group_source = NA_character_,
                                 toy = TRUE,
                                 accession = NA_character_,
                                 sourced_skill_scripts = NA_character_,
                                 notes = "",
                                 out_path,
                                 data_provenance = NULL) {
  if (is.null(data_provenance) || !nzchar(as.character(data_provenance)[1])) {
    data_provenance <- if (isTRUE(toy)) "TOY" else "REAL"
  }
  data_provenance <- toupper(as.character(data_provenance)[1])
  if (!data_provenance %in% c("REAL", "TOY", "BLOCKED")) {
    stop("data_provenance 必须是 REAL|TOY|BLOCKED，收到: ", data_provenance, call. = FALSE)
  }
  if (identical(data_provenance, "TOY")) toy <- TRUE
  if (identical(data_provenance, "REAL")) toy <- FALSE
  df <- data.frame(
    skill = skill_en,
    stage = stage,
    n_rows = n_rows,
    n_cols = n_cols,
    n_samples = n_samples,
    group_source = group_source,
    toy = isTRUE(toy),
    data_provenance = data_provenance,
    accession = accession,
    sourced_skill_scripts = sourced_skill_scripts,
    notes = notes,
    checked_at = format(Sys.time(), "%Y-%m-%d %H:%M:%S"),
    stringsAsFactors = FALSE
  )
  dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)
  utils::write.csv(df, out_path, row.names = FALSE, fileEncoding = "UTF-8")
  invisible(df)
}

#' 简单一致性检查：meta$sample 与矩阵列名
audit_meta_vs_matrix <- function(mat_colnames, meta_samples) {
  missing_in_meta <- setdiff(mat_colnames, meta_samples)
  missing_in_mat <- setdiff(meta_samples, mat_colnames)
  list(
    ok = length(missing_in_meta) == 0 && length(missing_in_mat) == 0,
    missing_in_meta = missing_in_meta,
    missing_in_mat = missing_in_mat
  )
}
