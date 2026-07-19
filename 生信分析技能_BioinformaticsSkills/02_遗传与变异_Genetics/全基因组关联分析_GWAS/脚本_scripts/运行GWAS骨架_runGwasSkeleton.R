# GWAS 骨架：R 出图包检查；关联主分析为 PLINK CLI
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

run_gwas_pipeline <- function(plink_prefix, pheno_csv, out_dir,
                              maf = 0.01, hwe = 1e-6,
                              project_root = find_project_root()) {
  pkgs <- c("qqman", "ggplot2")
  check_r_packages(pkgs)
  source_pub_viz(project_root)
  stopifnot(file.exists(pheno_csv))
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  message("【骨架】plink=", plink_prefix, " pheno=", pheno_csv)
  message("【骨架】QC MAF>", maf, " HWE>", hwe)
  message("【骨架】CLI 期望: PLINK（或 REGENIE）；R 负责 Manhattan/QQ + save_plot_pub")
  message("【骨架】TODO: PLINK QC -> association -> Manhattan/QQ via save_plot_pub")
  invisible(list(status = "skeleton", pkgs_ok = pkgs, out_dir = out_dir,
               cli_tools = c("PLINK")))
}

if (sys.nframe() == 0L && !interactive()) message("加载 run_gwas_pipeline()")
