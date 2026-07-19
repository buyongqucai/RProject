# ChIP-seq 骨架：R 包检查（DiffBind/ChIPseeker）；比对/peak 为 CLI
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

run_chipseq_pipeline <- function(fastq_dir = NULL, peak_dir = NULL, out_dir,
                                 genome = "mm10", has_input = TRUE,
                                 project_root = find_project_root()) {
  pkgs <- c("DiffBind", "ChIPseeker", "ggplot2")
  check_r_packages(pkgs)
  source_pub_viz(project_root)
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  message("【骨架】fastq=", fastq_dir, " peaks=", peak_dir, " genome=", genome,
          " input=", has_input)
  message("【骨架】CLI 期望: FastQC / Bowtie2 / MACS2（非 R 包）")
  message("【骨架】TODO: FastQC -> Bowtie2 -> MACS2 -> DiffBind -> annotate -> save_plot_pub")
  invisible(list(status = "skeleton", pkgs_ok = pkgs, out_dir = out_dir, genome = genome,
               cli_tools = c("FastQC", "Bowtie2", "MACS2")))
}

if (sys.nframe() == 0L && !interactive()) message("加载 run_chipseq_pipeline()")
