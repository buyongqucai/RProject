source("配置.R", encoding = "UTF-8")
setup_script_env()

source(file.path(PROJECT_ROOT, "共享脚本", "工具_NCBI接口.R"), encoding = "UTF-8")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_GEO元数据.R"), encoding = "UTF-8")

gse <- cfg$gse_id
fname <- "GSE267388_gene_expression.xls.gz"
dest <- file.path(PATHS$源数据, fname)
url <- sprintf("https://ftp.ncbi.nlm.nih.gov/geo/series/%s/%s/suppl/%s",
                geo_series_ftp_dir(gse), gse, fname)
if (!file.exists(dest)) geo_download_file(gse, fname, PATHS$源数据)
geo_verify_download(dest, min_bytes = 500000)
geo_save_manifest(gse, url, dest, PATHS)

df <- read.delim(gzfile(dest, "rt"), check.names = FALSE, stringsAsFactors = FALSE)
gene_col <- intersect(c("gene_symbol", "gene", "Gene", "GeneSymbol"), colnames(df))[1]
if (is.na(gene_col)) gene_col <- colnames(df)[1]
genes <- df[[gene_col]]
# 仅取每个生物学重复的 fpkm 列（如 fpkm_WT_LPS_1..5），排除 average_fpkm_* 汇总列
count_cols <- grep("^fpkm_WT_(LPS|PBS)_[0-9]+$", colnames(df), value = TRUE)
if (length(count_cols) < 2) {
  count_cols <- grep("^tpm_WT_(LPS|PBS)_[0-9]+$", colnames(df), value = TRUE)
}
# 兜底：任何情况下都剔除包含 average 的汇总列
count_cols <- count_cols[!grepl("average", count_cols, ignore.case = TRUE)]
if (length(count_cols) < 2) {
  count_cols <- setdiff(colnames(df), c(gene_col, "st_gene_id", "gene_id"))[seq_len(min(10, ncol(df) - 1))]
}

mat <- as.matrix(df[, count_cols, drop = FALSE])
mode(mat) <- "numeric"
rownames(mat) <- genes
mat <- mat[rowSums(mat, na.rm = TRUE) > 0 & !is.na(genes) & genes != "", , drop = FALSE]
mat[is.na(mat)] <- 0

sample_info <- tibble::tibble(
  sample = colnames(mat),
  group = factor(ifelse(grepl("LPS", colnames(mat), ignore.case = TRUE), "LPS", "PBS"),
                 levels = c("PBS", "LPS"))
)
write.csv(sample_info, file.path(PATHS$中间数据, "sample_meta.csv"), row.names = FALSE)
saveRDS(mat, file.path(PATHS$中间数据, paste0(DATASET, "_expr_matrix.rds")))
saveRDS(sample_info, file.path(PATHS$中间数据, paste0(DATASET, "_sample_info.rds")))
message("表达矩阵: ", nrow(mat), " x ", ncol(mat))
message("完成: 01_下载数据.R (GEO 官方 gene_expression.xls.gz)")
