# 延展分析依赖安装（在 R 4.6 / Windows 上尽量用二进制包）
options(timeout = 3600)
repos <- "https://cloud.r-project.org"
options(repos = c(CRAN = repos))

ensure_cran <- function(pkgs) {
  miss <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
  if (length(miss)) install.packages(miss, quiet = TRUE)
}
ensure_bioc <- function(pkgs) {
  if (!requireNamespace("BiocManager", quietly = TRUE)) install.packages("BiocManager")
  miss <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
  if (length(miss)) BiocManager::install(miss, update = FALSE, ask = FALSE)
}

cran_pkgs <- c("msigdbr", "babelgene", "WGCNA", "circlize", "reshape2", "ggpubr")
bioc_pkgs <- c("GO.db", "impute", "preprocessCore",
               "fgsea", "GSVA", "AUCell", "decoupleR", "progeny", "dorothea",
               "GSEABase", "ComplexHeatmap")

ensure_cran(cran_pkgs)
ensure_bioc(bioc_pkgs)

all_pkgs <- c(cran_pkgs, bioc_pkgs)
status <- vapply(all_pkgs, requireNamespace, logical(1), quietly = TRUE)
cat("\n===== 安装结果 =====\n")
for (i in seq_along(all_pkgs)) cat(sprintf("%-16s %s\n", all_pkgs[i], status[i]))
cat("INSTALL_DONE\n")
