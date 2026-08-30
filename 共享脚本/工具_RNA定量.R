# RNA 定量与 GEO RAW 解析

check_external_tool <- function(name) {
  path <- Sys.which(name)
  if (!nzchar(path)) {
    message("未找到外部工具: ", name)
    return(NULL)
  }
  path
}

get_ref_dir <- function(project_root) {
  ref <- file.path(project_root, "共享脚本", "参考数据")
  dir.create(ref, recursive = TRUE, showWarnings = FALSE)
  ref
}

salmon_check_index <- function(project_root) {
  ref <- get_ref_dir(project_root)
  index <- file.path(ref, "salmon_gencode_m39")
  if (dir.exists(index) && file.exists(file.path(index, "info.json"))) {
    return(index)
  }
  message("Salmon 索引不存在: ", index)
  message("请运行 salmon index 构建 GRCm39/Gencode 索引，或设置 cfg$salmon_index")
  NULL
}

salmon_quant_bulk <- function(fastq_dir, sample_id, r1, r2 = NULL, index, out_dir, threads = 4L) {
  salmon <- check_external_tool("salmon")
  if (is.null(salmon)) stop("需要安装 Salmon")
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  out_sample <- file.path(out_dir, sample_id)
  if (dir.exists(out_sample) && file.exists(file.path(out_sample, "quant.sf"))) {
    message("跳过已定量: ", sample_id)
    return(out_sample)
  }
  args <- c("quant", "-i", index, "-l", "A", "-p", as.character(threads), "-o", out_sample)
  if (!is.null(r2) && file.exists(r2)) {
    args <- c(args, "-1", r1, "-2", r2)
  } else {
    args <- c(args, "-r", r1)
  }
  message("Salmon quant: ", sample_id)
  status <- system2(salmon, args)
  if (status != 0) stop("Salmon 失败: ", sample_id)
  out_sample
}

tximport_salmon_counts <- function(quant_dirs, tx2gene_path = NULL) {
  if (!requireNamespace("tximport", quietly = TRUE)) {
    stop("需要 tximport 包")
  }
  files <- file.path(quant_dirs, "quant.sf")
  names(files) <- basename(quant_dirs)
  txi <- tximport::tximport(files, type = "salmon", txOut = FALSE, ignoreTxVersion = TRUE)
  txi$counts
}

read_gse171546_count_file <- function(f) {
  con_bin <- gzfile(f, "rb")
  bom <- readBin(con_bin, "raw", 4)
  close(con_bin)
  enc <- if (length(bom) >= 2 && bom[1] == as.raw(0xff) && bom[2] == as.raw(0xfe)) "UTF-16LE" else "UTF-8"
  con <- gzfile(f, "rt", encoding = enc)
  on.exit(close(con), add = TRUE)
  read.delim(con, check.names = FALSE, stringsAsFactors = FALSE)
}

parse_gse171546_counts <- function(raw_dir) {
  files <- list.files(raw_dir, pattern = "_Count\\.txt\\.gz$", full.names = TRUE)
  if (length(files) == 0) {
    stop("GSE171546: 未找到 *_Count.txt.gz 文件")
  }
  message("GSE171546: 解析 ", length(files), " 个 count 文件")

  mats <- list()
  for (f in files) {
    df <- read_gse171546_count_file(f)

    count_col <- grep("_Count$", colnames(df), value = TRUE)[1]
    if (is.na(count_col)) count_col <- ncol(df)
    sample_id <- sub("_Count$", "", count_col)

    genes <- if ("gene_name" %in% colnames(df) && any(nzchar(df$gene_name))) {
      ifelse(nzchar(df$gene_name), df$gene_name, df$gene_id)
    } else {
      df$gene_id
    }
    counts <- as.numeric(df[[count_col]])
    ok <- !is.na(genes) & !is.na(counts) & genes != ""
    mats[[sample_id]] <- counts[ok]
    names(mats[[sample_id]]) <- genes[ok]
  }

  all_genes <- unique(unlist(lapply(mats, names)))
  mat <- matrix(0, nrow = length(all_genes), ncol = length(mats),
                dimnames = list(all_genes, names(mats)))
  for (nm in names(mats)) {
    mat[names(mats[[nm]]), nm] <- mats[[nm]]
  }
  mat
}

parse_10x_from_dir <- function(matrix_dir) {
  if (!requireNamespace("Seurat", quietly = TRUE)) stop("需要 Seurat")
  mtx <- list.files(matrix_dir, pattern = "matrix\\.mtx(\\.gz)?$", full.names = TRUE)[1]
  feat <- list.files(matrix_dir, pattern = "features\\.tsv(\\.gz)?$", full.names = TRUE)[1]
  bar <- list.files(matrix_dir, pattern = "barcodes\\.tsv(\\.gz)?$", full.names = TRUE)[1]
  if (!is.na(mtx) && !is.na(feat) && !is.na(bar)) {
    return(Seurat::ReadMtx(mtx = mtx, features = feat, cells = bar))
  }
  Seurat::Read10X(matrix_dir)
}

find_10x_dirs <- function(root) {
  hits <- list.dirs(root, recursive = TRUE, full.names = TRUE)
  hits <- hits[vapply(hits, function(d) {
    file.exists(file.path(d, "matrix.mtx")) ||
      file.exists(file.path(d, "matrix.mtx.gz")) ||
      file.exists(file.path(d, "barcodes.tsv.gz"))
  }, logical(1))]
  unique(hits)
}

read_flat_10x_samples <- function(raw_dir) {
  mats <- list.files(raw_dir, pattern = "(_matrix|\\.matrix)\\.mtx(\\.gz)?$", full.names = FALSE)
  if (length(mats) == 0) return(list())
  samples <- sub("(_matrix|\\.matrix)\\.mtx(\\.gz)?$", "", mats)
  out <- list()
  for (s in samples) {
    mtx <- list.files(raw_dir, pattern = paste0("^", gsub("([.+*?^$(){}|\\[\\]\\\\])", "\\\\\\1", s), "(_matrix|\\.matrix)\\.mtx"), full.names = TRUE)[1]
    feat <- list.files(raw_dir, pattern = paste0("^", gsub("([.+*?^$(){}|\\[\\]\\\\])", "\\\\\\1", s), "_features\\.tsv"), full.names = TRUE)[1]
    if (is.na(feat)) feat <- list.files(raw_dir, pattern = paste0("^", gsub("([.+*?^$(){}|\\[\\]\\\\])", "\\\\\\1", s), "\\.features\\.tsv"), full.names = TRUE)[1]
    bar <- list.files(raw_dir, pattern = paste0("^", gsub("([.+*?^$(){}|\\[\\]\\\\])", "\\\\\\1", s), "_barcodes\\.tsv"), full.names = TRUE)[1]
    if (is.na(bar)) bar <- list.files(raw_dir, pattern = paste0("^", gsub("([.+*?^$(){}|\\[\\]\\\\])", "\\\\\\1", s), "\\.barcodes\\.tsv"), full.names = TRUE)[1]
    if (is.na(mtx) || is.na(feat) || is.na(bar)) next
    out[[s]] <- Seurat::ReadMtx(mtx = mtx, features = feat, cells = bar)
  }
  out
}

parse_geo_raw_tar <- function(tar_path, extract_dir) {
  dir.create(extract_dir, recursive = TRUE, showWarnings = FALSE)
  untar(tar_path, exdir = extract_dir)

  nested_tar <- list.files(extract_dir, pattern = "\\.tar(\\.gz)?$", recursive = TRUE, full.names = TRUE)
  for (nt in nested_tar) {
    subdir <- file.path(dirname(nt), paste0(tools::file_path_sans_ext(basename(nt)), "_ext"))
    dir.create(subdir, recursive = TRUE, showWarnings = FALSE)
    untar(nt, exdir = subdir)
  }

  tenx <- find_10x_dirs(extract_dir)
  if (length(tenx) > 0) {
    return(list(type = "10x", dirs = tenx))
  }

  txt_files <- list.files(extract_dir, pattern = "\\.(txt|tsv)(\\.gz)?$", recursive = TRUE, full.names = TRUE)
  if (length(txt_files) > 0) {
    return(list(type = "counts_txt", dir = extract_dir))
  }

  list(type = "unknown", dir = extract_dir)
}

`%||%` <- function(x, y) if (is.null(x)) y else x

save_bulk_download_objects <- function(data_obj, paths, dataset) {
  prefix <- file.path(paths$中间数据, dataset)
  saveRDS(data_obj$expr, paste0(prefix, "_expr_raw.rds"))
  saveRDS(data_obj$sample_info, paste0(prefix, "_sample_info.rds"))
  saveRDS(data_obj$feature_info, paste0(prefix, "_feature_info.rds"))
  write.csv(data_obj$sample_info, paste0(prefix, "_sample_info.csv"), row.names = FALSE)
  message("已保存: ", nrow(data_obj$expr), " x ", ncol(data_obj$expr))
}

download_gencode_transcripts <- function(project_root) {
  ref <- get_ref_dir(project_root)
  fa <- file.path(ref, "gencode.vM32.transcripts.fa.gz")
  if (!file.exists(fa)) {
    message("下载 Gencode M32 转录组 ...")
    utils::download.file(
      "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M32/gencode.vM32.transcripts.fa.gz",
      fa, mode = "wb", quiet = TRUE
    )
  }
  fa
}

rsubread_quant_bulk <- function(fastq_dir, sample_ids, project_root, out_dir) {
  if (!requireNamespace("Rsubread", quietly = TRUE)) {
    stop("需要 Rsubread 包：BiocManager::install('Rsubread')")
  }
  ref <- get_ref_dir(project_root)
  fa_gz <- download_gencode_transcripts(project_root)
  fa <- file.path(ref, "gencode.vM32.transcripts.fa")
  if (!file.exists(fa)) {
    R.utils::gunzip(fa_gz, destname = fa, overwrite = FALSE, remove = FALSE)
  }
  idx <- file.path(ref, "mm39_rsubread")
  if (!file.exists(paste0(idx, ".files"))) {
    message("构建 Rsubread 索引 ...")
    Rsubread::buildindex(basename = idx, reference = fa)
  }
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  bam_files <- character(length(sample_ids))
  names(bam_files) <- sample_ids
  for (sid in sample_ids) {
    r1 <- list.files(fastq_dir, pattern = paste0(sid, ".*_1\\.fastq"), full.names = TRUE)
    r2 <- list.files(fastq_dir, pattern = paste0(sid, ".*_2\\.fastq"), full.names = TRUE)
    if (length(r1) == 0) next
    message("Rsubread align: ", sid)
    bam <- Rsubread::align(idx, read1 = r1[1], read2 = if (length(r2)) r2[1] else NULL,
                           output_file = file.path(out_dir, sid), type = "rna")
    bam_files[sid] <- paste0(bam, ".BAM")
  }
  gtf <- file.path(ref, "gencode.vM32.annotation.gtf.gz")
  if (!file.exists(gtf)) {
    utils::download.file(
      "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M32/gencode.vM32.annotation.gtf.gz",
      gtf, mode = "wb", quiet = TRUE
    )
  }
  fc <- Rsubread::featureCounts(bam_files, annot.ext = gtf, isGTFAnnotationFile = TRUE,
                               GTF.featureType = "gene", GTF.attrType = "gene_name",
                               isPairedEnd = TRUE, nthreads = 4)
  fc$counts
}

run_bulk_quant <- function(fastq_dir, sample_ids, project_root, out_dir) {
  salmon <- check_external_tool("salmon")
  if (!is.null(salmon)) {
    source(file.path(project_root, "共享脚本", "工具_SRA下载.R"), encoding = "UTF-8")
    return(run_salmon_bulk_project(fastq_dir, sample_ids, project_root, out_dir))
  }
  message("Salmon 不可用，使用 Rsubread 比对定量")
  rsubread_quant_bulk(fastq_dir, sample_ids, project_root, out_dir)
}
