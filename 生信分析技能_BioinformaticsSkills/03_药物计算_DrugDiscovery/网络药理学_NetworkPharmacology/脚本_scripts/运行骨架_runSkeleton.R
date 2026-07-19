# 网络药理学 骨架：契约检查 + 包检查 + 出版级出图
find_project_root <- function(start = getwd()) {
  p <- normalizePath(start, winslash = "/", mustWork = FALSE)
  for (i in 1:8) {
    if (file.exists(file.path(p, "RProject.Rproj"))) return(p)
    if (dir.exists(file.path(p, "生信分析技能_BioinformaticsSkills"))) return(p)
    parent <- dirname(p); if (identical(parent, p)) break; p <- parent
  }
  stop("未找到项目根")
}
check_r_packages <- function(pkgs) {
  missing <- pkgs[!vapply(pkgs, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
  if (length(missing)) stop("缺少 R 包: ", paste(missing, collapse = ", "), call. = FALSE)
  invisible(TRUE)
}
source_pub_viz <- function(project_root = find_project_root()) {
  f <- file.path(project_root, "生信分析技能_BioinformaticsSkills", "00_基础_Foundation",
                 "统一可视化规范_VizStandards", "脚本_scripts", "出版级出图_PublicationPlot.R")
  if (!file.exists(f)) {
    f <- file.path(project_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                   "脚本_scripts", "出版级出图_PublicationPlot.R")
  }
  stopifnot("缺少出版级出图" = file.exists(f))
  source(f, encoding = "UTF-8")
}

#' @param data_dir 含契约 CSV 的目录；NULL 则跳过读表
run_networkpharmacology_skeleton <- function(data_dir = NULL, out_dir = tempfile("np_"),
                                             project_root = find_project_root()) {
  pkgs <- c("ggplot2", "igraph")
  present <- pkgs[vapply(pkgs, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
  missing <- setdiff(pkgs, present)
  if (length(missing)) message("【骨架】未安装（可稍后）: ", paste(missing, collapse = ", "))
  source_pub_viz(project_root)
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  if (!is.null(data_dir) && dir.exists(data_dir) && exists("np_read_contract")) {
    ct <- np_read_contract(data_dir, "compound_targets")
    ov <- np_read_contract(data_dir, "overlap")
    message("【骨架】compound-target edges=", nrow(ct), " overlap=", nrow(ov))
  } else {
    message("【骨架】未提供 data_dir 或契约函数未加载；仅完成包/出图检查")
  }
  message("【骨架】CLI：无强制；商业库以 CSV 契约替换。out=", out_dir)
  invisible(list(
    status = "skeleton",
    skill = "bioinfo-network-pharmacology",
    pkgs_checked = present,
    out_dir = out_dir
  ))
}
if (sys.nframe() == 0L && !interactive()) message("加载 run_networkpharmacology_skeleton()")
