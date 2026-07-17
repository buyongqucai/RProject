# 运行全部延展分析（务必在 延展分析/代码 目录下执行）
# 前置：各数据集已完成差异分析/单细胞预处理（见项目主流程）
scripts <- c("01_跨物种保守特征.R", "02_GSEA富集.R", "03_代谢重编程.R",
             "04_WGCNA模块.R", "05_TF与通路活性.R", "06_虚拟敲除.R", "07_细胞通讯.R")
for (s in scripts) {
  cat("\n========== ", s, " ==========\n")
  ok <- tryCatch({ source(s, encoding = "UTF-8"); TRUE },
                 error = function(e) { message("失败: ", s, " -> ", conditionMessage(e)); FALSE })
  cat(ifelse(ok, "OK", "FAILED"), "\n")
}
cat("\n=== 延展分析全部完成 ===\n")
