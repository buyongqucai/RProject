# 跨物种基因映射 骨架 status=skeleton；包检查；出图 source 出版级出图
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
  if (length(missing)) stop("缺少 R 包: ", paste(missing, collapse = ", "), call. = FALSE)
  invisible(TRUE)
}
source_pub_viz <- function(project_root = find_project_root()) {
  f <- file.path(project_root, "生信分析技能_BioinformaticsSkills", "00_基础_Foundation",
                 "统一可视化规范_VizStandards", "脚本_scripts", "出版级出图_PublicationPlot.R")
  stopifnot("缺少出版级出图" = file.exists(f))
  source(f, encoding = "UTF-8")
}
run_crossspecies_skeleton <- function(input_path = NULL, out_dir = tempfile("bioinfo_"),
                  project_root = find_project_root()) {
  pkgs <- c("babelgene", "ggplot2")
  present <- pkgs[vapply(pkgs, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
  missing <- setdiff(pkgs, present)
  if (length(missing)) message("【骨架】未安装（可稍后安装）: ", paste(missing, collapse = ", "))
  if (length(present)) check_r_packages(present)
  source_pub_viz(project_root)
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  message("【骨架】跨物种基因映射 input=", input_path, " out=", out_dir)
  message("【骨架】CLI 期望: 无（见技能说明）")
  invisible(list(status = "skeleton", skill = "bioinfo-cross-species", pkgs_checked = present, out_dir = out_dir))
}
if (sys.nframe() == 0L && !interactive()) message("加载 run_crossspecies_skeleton()")
