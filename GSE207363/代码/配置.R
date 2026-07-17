DATASET <- "GSE207363"
PROJECT_ROOT <- if (file.exists("RProject.Rproj")) normalizePath(".") else normalizePath("../..")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_项目路径.R"), encoding = "UTF-8")
PATHS <- init_dataset_paths(PROJECT_ROOT, DATASET)
PATHS$raw <- PATHS$源数据
PATHS$processed <- PATHS$中间数据
PATHS$tables <- PATHS$表格
PATHS$figures <- PATHS$图形
DEG_PADJ <- 0.05
DEG_LOGFC <- 1.0
cfg <- list(
  type = "scrna",
  organism = "mouse",
  org_db = "org.Mm.eg.db",
  kegg_org = "mmu",
  id_type = "SYMBOL",
  gse_id = "GSE207363",
  # GEO 官方共 4 个样本（各 1 例）：Control/Sham/Sepsis/LLTS，全部纳入以保证数据完整
  # 差异对比仍为 Sepsis vs Sham（疾病 vs 手术对照）；LLTS 为治疗臂，仅用于 QC/UMAP 展示
  keep_groups = c("Control", "Sham", "Sepsis"),  # LLTS 已剔除（见 调整计划/01）
  contrast = c("Sepsis", "Sham"),
  run_immune_subset = TRUE,
  deg_padj = 0.05,
  deg_logfc = 1.0
)
set.seed(42)
