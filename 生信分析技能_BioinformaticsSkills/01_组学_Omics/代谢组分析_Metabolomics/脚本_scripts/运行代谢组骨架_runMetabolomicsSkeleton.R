# 代谢组骨架：包检查 + 出版级出图
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

#' @param peak_table_csv 峰表
#' @param sample_info_csv sample_id, group；建议含 QC 标记
run_metabolomics_pipeline <- function(peak_table_csv, sample_info_csv, out_dir,
                                      vip_cut = 1, fc_cut = 1.5, p_cut = 0.05,
                                      project_root = find_project_root()) {
  # ropls 为核心；缺省时至少保证 ggplot2 可检
  pkgs <- c("ggplot2", "ropls")
  check_r_packages(pkgs)
  source_pub_viz(project_root)
  stopifnot(file.exists(peak_table_csv), file.exists(sample_info_csv))
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  message("【骨架】峰表=", peak_table_csv, " meta=", sample_info_csv)
  message("【骨架】阈值 VIP>", vip_cut, " FC>", fc_cut, " p<", p_cut)
  message("【骨架】TODO: 归一化 -> PCA -> OPLS-DA(置换检验) -> 通路富集 -> save_plot_pub")
  invisible(list(status = "skeleton", pkgs_ok = pkgs, out_dir = out_dir))
}

if (sys.nframe() == 0L && !interactive()) message("加载 run_metabolomics_pipeline()")
