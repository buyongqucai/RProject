options(repos = c(CRAN = "https://cloud.r-project.org"))
cran_pkgs <- c("tidyverse", "ggplot2", "pheatmap", "ggrepel", "RColorBrewer",
  "rentrez", "httr", "Matrix", "Seurat", "R.utils")
bioc_pkgs <- c("GEOquery", "limma", "DESeq2", "edgeR", "clusterProfiler",
  "org.Hs.eg.db", "org.Mm.eg.db", "EnhancedVolcano", "AnnotationDbi",
  "enrichplot", "DOSE", "hugene10sttranscriptcluster.db", "tximport", "Rsubread")
install_if_missing <- function(pkgs, bioc = FALSE) {
  for (pkg in pkgs) {
    if (!requireNamespace(pkg, quietly = TRUE)) {
      message("正在安装 ", pkg, " ...")
      if (bioc) BiocManager::install(pkg, ask = FALSE, update = FALSE)
      else install.packages(pkg)
    }
  }
}
if (!requireNamespace("BiocManager", quietly = TRUE)) install.packages("BiocManager")
install_if_missing(cran_pkgs)
install_if_missing(bioc_pkgs, bioc = TRUE)
message("依赖检查完成。")