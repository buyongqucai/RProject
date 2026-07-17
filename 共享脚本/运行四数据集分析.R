# 运行文档指定的四个数据集：差异分析 + 单细胞可视化
# R 路径: E:\R-4.6.0\bin (已加入用户 PATH)

PROJECT_ROOT <- normalizePath(".")
datasets <- list(
  list(id = "GSE267388", type = "bulk"),
  list(id = "GSE207363", type = "scrna"),
  list(id = "GSE207177", type = "scrna"),
  list(id = "GSE190856", type = "scrna")
)

for (ds in datasets) {
  cat("\n", strrep("=", 60), "\n")
  cat("开始: ", ds$id, " (", ds$type, ")\n", sep = "")
  code_dir <- file.path(PROJECT_ROOT, ds$id, "代码")
  if (!dir.exists(code_dir)) {
    warning("跳过，目录不存在: ", code_dir)
    next
  }
  tryCatch({
    setwd(code_dir)
    source("运行全部分析.R", encoding = "UTF-8")
    cat("完成: ", ds$id, "\n", sep = "")
  }, error = function(e) {
    cat("失败: ", ds$id, " -> ", conditionMessage(e), "\n", sep = "")
  })
}
setwd(PROJECT_ROOT)
cat("\n全部任务结束\n")
