`%||%` <- function(x, y) if (is.null(x)) y else x

find_project_root <- function() {
  path <- normalizePath(getwd(), winslash = "/")
  for (i in seq_len(6)) {
    if (file.exists(file.path(path, "RProject.Rproj"))) return(path)
    parent <- dirname(path)
    if (identical(parent, path)) break
    path <- parent
  }
  stop("找不到 RProject.Rproj")
}

get_script_dir <- function() {
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  if (length(file_arg)) {
    return(dirname(normalizePath(sub("^--file=", "", file_arg[1]), winslash = "/")))
  }
  getwd()
}

init_dataset_paths <- function(project_root, dataset_id) {
  ds_root <- file.path(project_root, dataset_id)
  paths <- list(
    根目录   = ds_root,
    源数据   = file.path(ds_root, "源数据"),
    代码     = file.path(ds_root, "代码"),
    结果     = file.path(ds_root, "结果"),
    表格     = file.path(ds_root, "结果", "表格"),
    图形     = file.path(ds_root, "结果", "图形"),
    文档     = file.path(ds_root, "文档"),
    中间数据 = file.path(ds_root, "源数据", "中间文件")
  )
  for (p in paths) dir.create(p, recursive = TRUE, showWarnings = FALSE)
  paths
}

setup_script_env <- function() {
  script_dir <- get_script_dir()
  if (dir.exists(script_dir)) setwd(script_dir)
  invisible(script_dir)
}