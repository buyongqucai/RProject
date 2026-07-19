# GEO/TCGA 挖掘骨架：包检查 + 真实性门禁提示 + 出版级出图
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

run_authenticity_gate <- function(project_root = find_project_root()) {
  wrap <- file.path(
    project_root, "生信分析技能_BioinformaticsSkills", "00_基础_Foundation",
    "数据真实性验证_DataAuthenticity", "脚本_scripts", "运行真实性核对_runAuthenticityCheck.R"
  )
  if (file.exists(wrap)) {
    source(wrap, encoding = "UTF-8")
  } else {
    message("请先运行: Rscript 书清项目/校验/数据真实性核对.R")
  }
}

#' @param gse_or_project GEO 登录号或 TCGA 项目 ID
#' @param tasks 字符向量：deg / km / cox / meta
run_geo_tcga_pipeline <- function(gse_or_project, tasks = c("deg", "km"),
                                  out_dir, project_root = find_project_root(),
                                  run_auth_check = FALSE) {
  pkgs <- c("GEOquery", "survival", "survminer", "ggplot2")
  check_r_packages(pkgs)
  message("【门禁】公共数据挖掘前须通过真实性验证")
  if (isTRUE(run_auth_check)) run_authenticity_gate(project_root)
  source_pub_viz(project_root)

  shuqing <- file.path(project_root, "书清项目", "共享脚本")
  for (t in c("工具_GEO元数据.R", "工具_NCBI接口.R")) {
    f <- file.path(shuqing, t)
    if (file.exists(f)) source(f, encoding = "UTF-8")
  }

  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  message("【骨架】对象=", gse_or_project, " tasks=", paste(tasks, collapse = ","))
  message("【骨架】TODO: TCGAbiolinks/GEOquery 下载 + survival/coxph + save_plot_pub")
  invisible(list(status = "skeleton", pkgs_ok = pkgs, id = gse_or_project, tasks = tasks, out_dir = out_dir))
}

if (sys.nframe() == 0L && !interactive()) message("加载 run_geo_tcga_pipeline()")
