# 多组学联合骨架：包检查 + 出版级出图
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

#' @param layer_tables 命名列表：如 list(rna=deg_csv, protein=dep_csv, meta=metab_csv)
run_multiomics_pipeline <- function(layer_tables, out_dir, id_map = NULL,
                                    project_root = find_project_root()) {
  pkgs <- c("ggplot2", "mixOmics")
  check_r_packages(pkgs)
  source_pub_viz(project_root)
  stopifnot(is.list(layer_tables), length(layer_tables) >= 1)
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  message("【骨架】层=", paste(names(layer_tables), collapse = ", "))
  message("【骨架】TODO: ID 映射 -> 通路交集/Upset -> 证据分层报告 -> save_plot_pub")
  invisible(list(status = "skeleton", pkgs_ok = pkgs, layers = names(layer_tables), out_dir = out_dir))
}

if (sys.nframe() == 0L && !interactive()) message("加载 run_multiomics_pipeline()")
