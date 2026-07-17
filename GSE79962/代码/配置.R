DATASET <- "GSE79962"
PROJECT_ROOT <- if (file.exists("RProject.Rproj")) normalizePath(".") else normalizePath("../..")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_项目路径.R"), encoding = "UTF-8")
PATHS <- init_dataset_paths(PROJECT_ROOT, DATASET)
PATHS$raw <- PATHS$源数据
PATHS$processed <- PATHS$中间数据
PATHS$tables <- PATHS$表格
PATHS$figures <- PATHS$图形
DEG_PADJ <- 0.05
DEG_LOGFC <- 1.0
cfg <- list(type = "microarray", organism = "human", org_db = "org.Hs.eg.db",
  kegg_org = "hsa", contrast = c("SCM", "Control"))
OUT <- list(
  全部差异基因 = paste0(DATASET, "_全部差异基因.csv"),
  显著差异基因 = paste0(DATASET, "_显著差异基因.csv"),
  GO生物过程 = paste0(DATASET, "_GO生物过程.csv"),
  GO生物过程_上调 = paste0(DATASET, "_GO生物过程_上调.csv"),
  GO生物过程_下调 = paste0(DATASET, "_GO生物过程_下调.csv"),
  KEGG通路 = paste0(DATASET, "_KEGG通路.csv"),
  火山图 = paste0(DATASET, "_火山图.pdf"),
  热图 = paste0(DATASET, "_Top50热图.pdf"),
  PCA = paste0(DATASET, "_PCA.pdf"),
  质控箱线图 = paste0(DATASET, "_质控箱线图.pdf"),
  质控PCA = paste0(DATASET, "_质控PCA.pdf")
)
set.seed(42)