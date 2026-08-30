# NCBI SRA 元数据查询与 FASTQ 下载

sra_list_runs <- function(bioproject_id) {
  if (!requireNamespace("rentrez", quietly = TRUE)) {
    stop("请先运行 共享脚本/安装依赖.R 安装 rentrez")
  }
  query <- if (grepl("^PRJNA", bioproject_id, ignore.case = TRUE)) {
    bioproject_id
  } else {
    paste0(bioproject_id, "[BioProject]")
  }
  search <- rentrez::entrez_search(db = "sra", term = query, retmax = 500)
  if (search$count == 0) stop("未找到 SRA runs: ", bioproject_id)

  runinfo <- rentrez::entrez_fetch(
    db = "sra",
    id = search$ids,
    rettype = "runinfo",
    parsed = FALSE
  )
  df <- read.csv(text = runinfo, stringsAsFactors = FALSE)
  message("BioProject ", bioproject_id, ": ", nrow(df), " runs")
  df
}

sra_check_toolkit <- function() {
  prefetch <- Sys.which("prefetch")
  fasterq <- Sys.which("fasterq-dump")
  list(
    prefetch = prefetch,
    fasterq_dump = fasterq,
    ok = nzchar(prefetch) && nzchar(fasterq)
  )
}

sra_download_fastq <- function(run_ids, destdir, threads = 4L) {
  tools <- sra_check_toolkit()
  if (!tools$ok) {
    message("SRA Toolkit 不可用，改用 EBI HTTPS 下载")
    return(sra_download_fastq_ebi(run_ids, destdir))
  }
  dir.create(destdir, recursive = TRUE, showWarnings = FALSE)
  run_ids <- unique(run_ids)
  for (srr in run_ids) {
    fq1 <- file.path(destdir, paste0(srr, "_1.fastq.gz"))
    if (file.exists(fq1)) {
      message("跳过已存在: ", srr)
      next
    }
    message("prefetch ", srr, " ...")
    system2(tools$prefetch, c(srr, "-O", destdir), stdout = TRUE, stderr = TRUE)
    message("fasterq-dump ", srr, " ...")
    system2(
      tools$fasterq_dump,
      c("--split-files", "--threads", as.character(threads), srr),
      stdout = TRUE, stderr = TRUE
    )
  }
  invisible(list.files(destdir, full.names = TRUE))
}

sra_ebi_fastq_urls <- function(srr) {
  srr <- toupper(srr)
  n <- nchar(srr)
  if (n < 6) stop("invalid SRR: ", srr)
  subdir <- substr(srr, n - 2, n)
  mid <- substr(srr, 1, n - 3)
  base <- sprintf("https://ftp.sra.ebi.ac.uk/vol1/fastq/%s/%s/%s", mid, subdir, srr)
  list(
    r1 = paste0(base, "_1.fastq.gz"),
    r2 = paste0(base, "_2.fastq.gz"),
    single = paste0(base, ".fastq.gz")
  )
}

sra_download_fastq_ebi <- function(run_ids, destdir) {
  dir.create(destdir, recursive = TRUE, showWarnings = FALSE)
  for (srr in run_ids) {
    urls <- sra_ebi_fastq_urls(srr)
    for (url in unlist(urls[c("r1", "r2")])) {
      dest <- file.path(destdir, basename(url))
      if (file.exists(dest)) next
      tryCatch({
        message("EBI 下载: ", basename(url))
        utils::download.file(url, dest, mode = "wb", quiet = TRUE)
      }, error = function(e) message("下载失败: ", basename(url)))
    }
  }
  invisible(list.files(destdir, full.names = TRUE))
}

sra_build_sample_info <- function(runinfo, group_parser = NULL) {
  df <- runinfo
  sample_info <- data.frame(
    run = df$Run,
    sample = df$SampleName,
    bio_sample = df$BioSample,
    title = df$SampleName,
    stringsAsFactors = FALSE
  )
  if (!is.null(group_parser)) {
    sample_info$group <- vapply(seq_len(nrow(sample_info)), function(i) {
      group_parser(sample_info$sample[i], sample_info$title[i], sample_info$bio_sample[i])
    }, character(1))
  } else {
    sample_info$group <- NA_character_
  }
  rownames(sample_info) <- sample_info$run
  sample_info
}

salmon_build_index_script <- function(project_root) {
  source(file.path(project_root, "共享脚本", "工具_RNA定量.R"), encoding = "UTF-8")
  ref <- file.path(project_root, "共享脚本", "参考数据")
  dir.create(ref, recursive = TRUE, showWarnings = FALSE)
  fa <- file.path(ref, "gencode.vM32.transcripts.fa.gz")
  index <- file.path(ref, "salmon_gencode_m39")
  if (!file.exists(fa)) {
    message("下载 Gencode M32 转录组 ...")
    utils::download.file(
      "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M32/gencode.vM32.transcripts.fa.gz",
      fa, mode = "wb", quiet = TRUE
    )
  }
  if (!dir.exists(index)) {
    salmon <- check_external_tool("salmon")
    if (is.null(salmon)) stop("需要 salmon 构建索引: ", index)
    system2(salmon, c("index", "-t", fa, "-i", index, "-k", "31"))
  }
  index
}

salmon_quant_sample_dir <- function(fastq_dir, sample_id, index, out_dir, threads = 4L) {
  r1 <- list.files(fastq_dir, pattern = paste0(sample_id, ".*_1\\.fastq"), full.names = TRUE)
  r2 <- list.files(fastq_dir, pattern = paste0(sample_id, ".*_2\\.fastq"), full.names = TRUE)
  if (length(r1) == 0) {
    r1 <- list.files(fastq_dir, pattern = paste0("^", sample_id, "_1"), full.names = TRUE)
    r2 <- list.files(fastq_dir, pattern = paste0("^", sample_id, "_2"), full.names = TRUE)
  }
  if (length(r1) == 0) stop("未找到 FASTQ: ", sample_id)
  salmon_quant_bulk(fastq_dir, sample_id, r1[1], if (length(r2)) r2[1] else NULL, index, out_dir, threads)
}

run_salmon_bulk_project <- function(fastq_dir, sample_ids, project_root, out_dir, threads = 4L) {
  source(file.path(project_root, "共享脚本", "工具_RNA定量.R"), encoding = "UTF-8")
  index <- salmon_check_index(project_root)
  if (is.null(index)) index <- salmon_build_index_script(project_root)
  dirs <- vapply(sample_ids, function(sid) {
    salmon_quant_sample_dir(fastq_dir, sid, index, out_dir, threads)
  }, character(1))
  tximport_salmon_counts(dirs)
}
