# 包装：从 Skill 目录调用书清真实性核对
# 用法（仓库根）:
#   Rscript 生信分析技能_BioinformaticsSkills/00_基础_Foundation/数据真实性验证_DataAuthenticity/脚本_scripts/运行真实性核对_runAuthenticityCheck.R

find_project_root <- function(start = getwd()) {
  p <- normalizePath(start, winslash = "/", mustWork = FALSE)
  for (i in 1:8) {
    if (file.exists(file.path(p, "RProject.Rproj"))) return(p)
    parent <- dirname(p)
    if (identical(parent, p)) break
    p <- parent
  }
  stop("未找到含 RProject.Rproj 的仓库根")
}

PROJECT_ROOT <- find_project_root()
# 基 R 即可；若脚本内用到 GEOquery 再由书清脚本自行加载
script <- file.path(PROJECT_ROOT, "书清项目", "校验", "数据真实性核对.R")
stopifnot("缺少书清 数据真实性核对.R" = file.exists(script))
message("运行: ", script)
source(script, encoding = "UTF-8")
