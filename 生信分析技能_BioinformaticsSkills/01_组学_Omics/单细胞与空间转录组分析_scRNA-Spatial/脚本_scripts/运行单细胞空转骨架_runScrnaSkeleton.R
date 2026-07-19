# 单细胞/空转骨架：包检查 + 出版级出图 + 书清 scRNA 工具
# status = "skeleton"

find_project_root <- function(start = getwd()) {
  p <- normalizePath(start, winslash = "/", mustWork = FALSE)
  for (i in 1:8) {
    if (file.exists(file.path(p, "RProject.Rproj"))) return(p)
    parent <- dirname(p); if (identical(parent, p)) break; p <- parent
  }
  stop("未找到 RProject.Rproj")
}

check_r_packages <- function(pkgs) {
  missing <- pkgs[!vapply(pkgs, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
  if (length(missing)) {
    stop("缺少 R 包（请先安装）: ", paste(missing, collapse = ", "), call. = FALSE)
  }
  invisible(TRUE)
}

source_pub_viz <- function(project_root = find_project_root()) {
  f <- file.path(
    project_root, "生信分析技能_BioinformaticsSkills", "00_基础_Foundation",
    "统一可视化规范_VizStandards", "脚本_scripts", "出版级出图_PublicationPlot.R"
  )
  stopifnot("缺少出版级出图_PublicationPlot.R" = file.exists(f))
  source(f, encoding = "UTF-8")
}

run_scrna_pipeline <- function(seurat_rds = NULL, dataset = NULL, out_dir = NULL,
                               project_root = find_project_root()) {
  pkgs <- c("Seurat", "ggplot2")
  check_r_packages(pkgs)
  source_pub_viz(project_root)

  scripts <- file.path(project_root, "书清项目", "共享脚本")
  tools <- c("工具_单细胞对象.R", "工具_scRNA细胞注释.R", "工具_scRNA可视化.R", "工具_统一出图.R")
  loaded <- character()
  for (t in tools) {
    f <- file.path(scripts, t)
    if (file.exists(f)) {
      source(f, encoding = "UTF-8")
      loaded <- c(loaded, t)
    }
  }
  if (length(loaded)) {
    message("【书清】已 source: ", paste(loaded, collapse = ", "))
  } else {
    message("【提示】未找到书清 scRNA 工具，期望目录: ", scripts)
  }

  if (!is.null(out_dir)) dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  message("【骨架】dataset=", dataset, " seurat=", seurat_rds, " out=", out_dir)
  message("【骨架】出图 DPI>=600 SVG+PNG；细胞名非数字簇；免疫子集无基质污染")
  invisible(list(status = "skeleton", pkgs_ok = pkgs, tools_dir = scripts, loaded = loaded))
}

if (sys.nframe() == 0L && !interactive()) message("加载 run_scrna_pipeline()")
