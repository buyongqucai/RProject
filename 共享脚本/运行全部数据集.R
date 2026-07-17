# 批量运行全部骨架数据集分析

PROJECT_ROOT <- if (file.exists("RProject.Rproj")) normalizePath(".") else normalizePath("..")
source(file.path(PROJECT_ROOT, "共享脚本", "工具_项目路径.R"), encoding = "UTF-8")

datasets <- c(
  "GSE171546",
  "PRJNA1171952",
  "PRJCA045393",
  "PRJCA051457",
  "GSE207363",
  "GSE190856",
  "CRA029427"
)

for (ds in datasets) {
  cat("\n########## ", ds, " ##########\n")
  code_dir <- file.path(PROJECT_ROOT, ds, "代码")
  if (!file.exists(file.path(code_dir, "运行全部分析.R"))) {
    message("跳过（无流水线）: ", ds)
    next
  }
  tryCatch({
    setwd(code_dir)
    source("运行全部分析.R", encoding = "UTF-8")
  }, error = function(e) {
    message("失败: ", ds, " — ", conditionMessage(e))
  })
}

cat("\n全部任务结束。\n")
