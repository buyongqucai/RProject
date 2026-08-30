# 批量复制 bulk 分析脚本模板

copy_bulk_scripts <- function(dataset_id, project_root = "e:/RProject", template = "GSE171546") {
  src <- file.path(project_root, template, "代码")
  dst <- file.path(project_root, dataset_id, "代码")
  for (f in c("02_预处理与质控.R", "03_差异分析.R", "04_可视化.R", "05_富集分析.R", "运行全部分析.R")) {
    file.copy(file.path(src, f), file.path(dst, f), overwrite = TRUE)
  }
}
