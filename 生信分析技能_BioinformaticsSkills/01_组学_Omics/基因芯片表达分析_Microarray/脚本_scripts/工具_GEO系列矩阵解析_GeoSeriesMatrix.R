# 本地 GEO series matrix 解析（避免 GEOquery::getGEO 在本机崩溃）
# 输入：已解压或 .txt.gz 的 series_matrix 文件

parse_geo_series_matrix <- function(path, max_features = 5000L) {
  stopifnot(file.exists(path))
  if (grepl("[.]gz$", path, ignore.case = TRUE)) {
    con <- gzfile(path, open = "rt")
    on.exit(close(con), add = TRUE)
    lines <- readLines(con, warn = FALSE)
  } else {
    lines <- readLines(path, warn = FALSE)
  }
  begin <- grep("^!series_matrix_table_begin", lines)
  end <- grep("^!series_matrix_table_end", lines)
  if (!length(begin) || !length(end)) stop("未找到 series_matrix_table_begin/end: ", path)
  tbl <- utils::read.delim(
    textConnection(lines[(begin[1] + 1L):(end[1] - 1L)]),
    check.names = FALSE, stringsAsFactors = FALSE
  )
  id_col <- intersect(c("ID_REF", "ID"), names(tbl))[1]
  if (is.na(id_col)) stop("表达表缺少 ID_REF/ID 列")
  feat_ids <- tbl[[id_col]]
  mat <- as.matrix(tbl[, setdiff(names(tbl), id_col), drop = FALSE])
  mode(mat) <- "numeric"
  rownames(mat) <- feat_ids
  # 去掉全 NA 行
  keep <- rowSums(is.finite(mat)) >= max(2L, ceiling(ncol(mat) * 0.5))
  mat <- mat[keep, , drop = FALSE]
  if (nrow(mat) > max_features) {
    set.seed(10072L)
    mat <- mat[sample(nrow(mat), max_features), , drop = FALSE]
  }
  sample_rows <- grep("^!Sample_", lines, value = TRUE)
  parse_row <- function(prefix) {
    hit <- grep(paste0("^", prefix, "\t"), sample_rows, value = TRUE)
    if (!length(hit)) return(NULL)
    parts <- strsplit(hit[1], "\t", fixed = TRUE)[[1]][-1]
    gsub('^"|"$', "", parts)
  }
  gsm <- parse_row("!Sample_geo_accession")
  title <- parse_row("!Sample_title")
  source <- parse_row("!Sample_source_name_ch1")
  smoking <- NULL
  for (ln in sample_rows) {
    if (grepl("Cigarette Smoking Status", ln, fixed = TRUE)) {
      parts <- strsplit(ln, "\t", fixed = TRUE)[[1]][-1]
      smoking <- gsub('^"|"$', "", parts)
      break
    }
  }
  if (is.null(gsm)) stop("无法解析 !Sample_geo_accession")
  if (length(title) != length(gsm)) title <- rep(NA_character_, length(gsm))
  if (length(source) != length(gsm)) source <- rep(NA_character_, length(gsm))
  if (is.null(smoking) || length(smoking) != length(gsm)) smoking <- rep(NA_character_, length(gsm))
  meta <- data.frame(
    sample = gsm,
    title = title,
    source = source,
    smoking = smoking,
    stringsAsFactors = FALSE
  )
  # 列名对齐：矩阵列常为 GSM 或 title
  cn <- colnames(mat)
  if (all(cn %in% meta$sample)) {
    meta <- meta[match(cn, meta$sample), , drop = FALSE]
  } else if (all(cn %in% meta$title)) {
    meta <- meta[match(cn, meta$title), , drop = FALSE]
    rownames(meta) <- cn
  }
  list(matrix = mat, meta = meta, accession = sub("_series_matrix.*", "", basename(path)))
}
