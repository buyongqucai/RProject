# CNCB-NGDC GSA / OMIX 下载工具

ngdc_download_https <- function(url, dest) {
  dir.create(dirname(dest), recursive = TRUE, showWarnings = FALSE)
  if (file.exists(dest)) {
    message("使用本地缓存: ", dest)
    return(dest)
  }
  message("下载: ", basename(dest))
  if (requireNamespace("httr", quietly = TRUE)) {
    resp <- httr::GET(url, httr::write_disk(dest, overwrite = TRUE), httr::progress())
    if (httr::http_error(resp)) stop("下载失败: ", url)
  } else {
    utils::download.file(url, dest, mode = "wb", quiet = TRUE)
  }
  dest
}

ngdc_gsa_https_base <- function(cra_id) {
  sprintf("https://download.cncb.ac.cn/gsa5/%s", cra_id)
}

ngdc_list_gsa_runs <- function(cra_id) {
  base <- ngdc_gsa_https_base(cra_id)
  message("GSA 数据目录: ", base)
  list(cra = cra_id, base_url = base)
}

ngdc_download_gsa_run <- function(cra_id, run_id, destdir) {
  dir.create(destdir, recursive = TRUE, showWarnings = FALSE)
  for (suffix in c("_r1.fastq.gz", "_r2.fastq.gz")) {
    fname <- paste0(run_id, suffix)
    url <- file.path(ngdc_gsa_https_base(cra_id), run_id, fname)
    dest <- file.path(destdir, fname)
    if (file.exists(dest)) next
    tryCatch(ngdc_download_https(url, dest), error = function(e) {
      message("未找到: ", fname)
    })
  }
  invisible(list.files(destdir, full.names = TRUE))
}

ngdc_omix_file_urls <- function(omix_id) {
  base <- sprintf("https://download.cncb.ac.cn/omix/%s", omix_id)
  list(
    count = file.path(base, paste0(omix_id, "-01.txt")),
    metadata = file.path(base, paste0(omix_id, "-02.txt"))
  )
}

ngdc_download_omix <- function(omix_id, destdir) {
  dir.create(destdir, recursive = TRUE, showWarnings = FALSE)
  urls <- ngdc_omix_file_urls(omix_id)
  paths <- list()
  for (nm in names(urls)) {
    dest <- file.path(destdir, paste0(omix_id, "_", nm, ".txt"))
    paths[[nm]] <- ngdc_download_https(urls[[nm]], dest)
  }
  invisible(paths)
}

ngdc_fetch_gsa_page_runs <- function(cra_id) {
  url <- sprintf("https://ngdc.cncb.ac.cn/gsa/browse/%s", cra_id)
  if (!requireNamespace("httr", quietly = TRUE)) {
    stop("需要 httr 包解析 GSA 页面")
  }
  html <- httr::content(httr::GET(url), as = "text", encoding = "UTF-8")
  runs <- unique(regmatches(html, gregexpr("CRR[0-9]+", html))[[1]])
  message(cra_id, " 检测到 ", length(runs), " 个 run")
  runs
}

parse_omix_count_matrix <- function(count_path, meta_path, max_rows = NULL) {
  message("读取 OMIX count: ", basename(count_path))
  if (!file.exists(count_path)) stop("count 文件不存在: ", count_path)

  if (requireNamespace("data.table", quietly = TRUE)) {
    dt <- data.table::fread(count_path, nrows = max_rows, data.table = FALSE)
  } else {
    dt <- read.delim(count_path, check.names = FALSE, nrows = max_rows)
  }

  gene_col <- which(tolower(colnames(dt)) %in% c("gene", "gene_id", "symbol", "gene_name"))[1]
  if (is.na(gene_col)) gene_col <- 1
  genes <- dt[[gene_col]]
  mat <- as.matrix(dt[, -gene_col, drop = FALSE])
  rownames(mat) <- genes

  meta <- if (file.exists(meta_path)) {
    if (requireNamespace("data.table", quietly = TRUE)) {
      data.table::fread(meta_path, data.table = FALSE)
    } else {
      read.delim(meta_path, check.names = FALSE)
    }
  } else {
    data.frame(sample = colnames(mat), group = NA)
  }

  list(counts = mat, meta = meta)
}
