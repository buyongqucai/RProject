# 新抗原与免疫组库_Neoantigen-TCR 骨架 status=skeleton
find_project_root <- function(start = getwd()) {
  p <- normalizePath(start, winslash = "/", mustWork = FALSE)
  for (i in 1:8) {
    if (file.exists(file.path(p, "RProject.Rproj"))) return(p)
    parent <- dirname(p); if (identical(parent, p)) break; p <- parent
  }
  stop("未找到 RProject.Rproj")
}
source_pub_viz <- function(project_root = find_project_root()) {
  f <- file.path(project_root, "生信分析技能_BioinformaticsSkills", "00_基础_Foundation",
                 "统一可视化规范_VizStandards", "脚本_scripts", "出版级出图_PublicationPlot.R")
  stopifnot(file.exists(f)); source(f, encoding = "UTF-8")
}
run_merged_skeleton <- function(input_path = NULL, out_dir = tempfile("bioinfo_"),
                                project_root = find_project_root()) {
  pkgs <- c("ggplot2")
  present <- pkgs[vapply(pkgs, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
  missing <- setdiff(pkgs, present)
  if (length(missing)) message("【骨架】未安装: ", paste(missing, collapse = ", "))
  source_pub_viz(project_root)
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  message("【骨架】新抗原与免疫组库_Neoantigen-TCR input=", input_path, " out=", out_dir)
  invisible(list(status = "skeleton", folder = "新抗原与免疫组库_Neoantigen-TCR", pkgs_checked = present))
}
if (sys.nframe() == 0L && !interactive()) message("加载 run_merged_skeleton()")
