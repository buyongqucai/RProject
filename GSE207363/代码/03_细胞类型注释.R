source("配置.R", encoding = "UTF-8")
setup_script_env()
source(file.path(PROJECT_ROOT, "共享脚本", "工具_scRNA细胞注释.R"), encoding = "UTF-8")

suppressPackageStartupMessages(library(Seurat))

obj <- readRDS(file.path(PATHS$中间数据, paste0(DATASET, "_seurat.rds")))
DefaultAssay(obj) <- "RNA"
if ("JoinLayers" %in% ls("package:Seurat")) obj <- JoinLayers(obj, assay = "RNA")
obj <- annotate_clusters_by_markers(obj, CARDIAC_MARKERS, "celltype")
saveRDS(obj, file.path(PATHS$中间数据, paste0(DATASET, "_seurat.rds")))

prop <- obj@meta.data %>%
  tibble::as_tibble() %>%
  dplyr::count(group, celltype, name = "n")
write.csv(prop, file.path(PATHS$表格, paste0(DATASET, "_细胞类型比例.csv")), row.names = FALSE)
message("完成: 03_细胞类型注释.R")
