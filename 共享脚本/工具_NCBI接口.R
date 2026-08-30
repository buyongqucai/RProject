# NCBI GEO 下载与解析工具

geo_download_supp <- function(gse_id, destdir) {
  dir.create(destdir, recursive = TRUE, showWarnings = FALSE)
  if (!requireNamespace("GEOquery", quietly = TRUE)) {
    stop("请先运行 共享脚本/安装依赖.R 安装 GEOquery")
  }
  supp <- GEOquery::getGEOSuppFiles(gse_id, baseDir = destdir, makeDirectory = FALSE)
  message("已下载补充文件至: ", destdir)
  invisible(supp)
}

geo_series_ftp_dir <- function(gse_id) {
  n <- sub("GSE", "", gse_id)
  paste0("GSE", substr(n, 1, max(1, nchar(n) - 3)), "nnn")
}

geo_download_file <- function(gse_id, filename, destdir) {
  dir.create(destdir, recursive = TRUE, showWarnings = FALSE)
  dest <- file.path(destdir, filename)
  if (file.exists(dest)) {
    message("使用本地缓存: ", dest)
    return(dest)
  }
  ftp_dir <- geo_series_ftp_dir(gse_id)
  urls <- c(
    sprintf("https://ftp.ncbi.nlm.nih.gov/geo/series/%s/%s/suppl/%s", ftp_dir, gse_id, filename),
    sprintf("https://www.ncbi.nlm.nih.gov/geo/download/?acc=%s&format=file&file=%s", gse_id, filename)
  )
  for (url in urls) {
    message("正在下载: ", filename)
    ok <- tryCatch({
      utils::download.file(url, dest, mode = "wb", quiet = TRUE)
      TRUE
    }, error = function(e) FALSE, warning = function(w) FALSE)
    if (ok && file.exists(dest) && file.info(dest)$size > 0) return(dest)
    if (file.exists(dest)) unlink(dest)
  }
  stop("下载失败: ", filename)
}

geo_get_metadata <- function(gse_id, destdir) {
  if (!requireNamespace("GEOquery", quietly = TRUE)) {
    stop("请先安装 GEOquery")
  }
  gse_list <- GEOquery::getGEO(gse_id, destdir = destdir, GSEMatrix = TRUE, getGPL = FALSE)
  Biobase::pData(gse_list[[1]])
}

extract_raw_tar <- function(tar_path, destdir) {
  dir.create(destdir, recursive = TRUE, showWarnings = FALSE)
  untar(tar_path, exdir = destdir)
  list.files(destdir, recursive = TRUE, full.names = TRUE)
}

find_file_by_pattern <- function(root, pattern) {
  hits <- list.files(root, pattern = pattern, recursive = TRUE, full.names = TRUE)
  if (length(hits) == 0) return(character(0))
  hits
}
