# GEO 样本元数据解析与下载校验

geo_series_ftp_dir <- function(gse_id) {
  n <- sub("GSE", "", gse_id)
  paste0("GSE", substr(n, 1, max(1, nchar(n) - 3)), "nnn")
}

geo_verify_download <- function(path, min_bytes = 1000) {
  if (!file.exists(path)) stop("文件不存在: ", path)
  sz <- file.info(path)$size
  if (sz < min_bytes) stop("文件过小，可能下载不完整: ", path, " (", sz, " bytes)")
  message("校验通过: ", basename(path), " (", format(sz, big.mark = ","), " bytes)")
  invisible(sz)
}

geo_save_manifest <- function(gse_id, url, dest, paths) {
  manifest <- list(
    gse_id = gse_id,
    url = url,
    file = basename(dest),
    bytes = file.info(dest)$size,
    downloaded_at = as.character(Sys.time())
  )
  out <- file.path(paths$源数据, "下载清单.json")
  if (requireNamespace("jsonlite", quietly = TRUE)) {
    jsonlite::write_json(manifest, out, auto_unbox = TRUE, pretty = TRUE)
  } else {
    writeLines(c(
      paste0('{"gse_id":"', gse_id, '","url":"', url, '","file":"', basename(dest),
             '","bytes":', file.info(dest)$size, '}')
    ), out)
  }
  invisible(manifest)
}

extract_characteristic <- function(char_vec, field) {
  if (length(char_vec) == 0 || all(is.na(char_vec))) return(NA_character_)
  parts <- unlist(strsplit(as.character(char_vec), ";\\s*"))
  hit <- grep(paste0("^", field, ":"), parts, ignore.case = TRUE, value = TRUE)
  if (length(hit) == 0) return(NA_character_)
  sub(paste0("(?i)^", field, ":\\s*"), "", hit[1], perl = TRUE)
}

parse_gsm_table <- function(gse_id, destdir = tempdir()) {
  if (!requireNamespace("GEOquery", quietly = TRUE)) stop("需要 GEOquery")
  gse_list <- GEOquery::getGEO(gse_id, destdir = destdir, GSEMatrix = TRUE, getGPL = FALSE)
  pd <- Biobase::pData(gse_list[[1]])
  rows <- lapply(seq_len(nrow(pd)), function(i) {
    ch <- pd$characteristics_ch1[i]
    parts <- if (!is.na(ch)) unlist(strsplit(as.character(ch), ";\\s*")) else character(0)
    list(
      geo_accession = rownames(pd)[i],
      title = pd$title[i],
      genotype = extract_characteristic(ch, "genotype"),
      time_point = extract_characteristic(ch, "time point"),
      source_name = pd$source_name_ch1[i]
    )
  })
  dplyr::bind_rows(rows)
}
