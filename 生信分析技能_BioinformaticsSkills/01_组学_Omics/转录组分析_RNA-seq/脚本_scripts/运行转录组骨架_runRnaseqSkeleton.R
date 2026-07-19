# 转录组 RNA-seq 骨架入口
# status = "skeleton"；包检查可真实跑通；对接书清共享脚本；出图 source 出版级出图
#
# 示例:
#   source(".../运行转录组骨架_runRnaseqSkeleton.R")
#   run_rnaseq_pipeline(counts_csv, sample_info_csv, out_dir, contrast = c("Treat","Control"))

find_project_root <- function(start = getwd()) {
  p <- normalizePath(start, winslash = "/", mustWork = FALSE)
  for (i in 1:8) {
    if (file.exists(file.path(p, "RProject.Rproj"))) return(p)
    parent <- dirname(p)
    if (identical(parent, p)) break
    p <- parent
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
  invisible(f)
}

source_shuqing_tools <- function(project_root = find_project_root()) {
  shuqing <- file.path(project_root, "书清项目", "共享脚本")
  tools <- c("工具_项目路径.R", "工具_富集与质控图.R", "工具_统一出图.R")
  loaded <- character()
  for (t in tools) {
    f <- file.path(shuqing, t)
    if (file.exists(f)) {
      source(f, encoding = "UTF-8")
      loaded <- c(loaded, t)
    }
  }
  if (!length(loaded)) {
    message("【提示】未找到书清共享脚本，将仅用本库出版级出图；路径期望: ", shuqing)
  } else {
    message("【书清】已 source: ", paste(loaded, collapse = ", "))
  }
  invisible(loaded)
}

#' @param counts_path 基因 x 样本 count CSV（首列 gene）
#' @param sample_info_path 含 sample_id, group 列
#' @param out_dir 结果目录（表格/图形）
#' @param contrast c(实验组, 对照组)
run_rnaseq_pipeline <- function(counts_path, sample_info_path, out_dir,
                                contrast, padj_cut = 0.05, logfc_cut = 1,
                                project_root = find_project_root()) {
  pkgs <- c("ggplot2", "limma", "edgeR")
  check_r_packages(pkgs)
  source_pub_viz(project_root)
  source_shuqing_tools(project_root)

  stopifnot(file.exists(counts_path), file.exists(sample_info_path))
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

  message("【骨架】输入 counts=", counts_path, " sample_info=", sample_info_path)
  message("【骨架】对比=", paste(contrast, collapse = " vs "),
          " padj<", padj_cut, " |logFC|>", logfc_cut)
  message("【骨架】输出目录=", out_dir, "；图须 SVG+PNG DPI>=600（save_plot_pub）")
  message("【骨架】生产实现见 差异分析与UMAP流水线_DEG-UMAP 与书清共享脚本")
  invisible(list(
    status = "skeleton",
    pkgs_ok = pkgs,
    next_step = "填充 limma-voom / DESeq2 DEG + run_enrichment_full + save_plot_pub"
  ))
}

if (sys.nframe() == 0L && !interactive()) {
  message("加载 run_rnaseq_pipeline()；请传入 counts/sample_info 路径后调用。")
}
