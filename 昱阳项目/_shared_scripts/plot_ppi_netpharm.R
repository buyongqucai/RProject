# YuYang PPI 图：调用网药 FROZEN np_plot_string_ppi（同心 Degree）
suppressPackageStartupMessages({
  library(ggplot2)
})

.np_scripts <- file.path(
  "E:/RProject/生信分析技能_BioinformaticsSkills",
  "03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology/脚本_scripts"
)
source(file.path(.np_scripts, "03_STRING与网络图_StringNetwork.R"), encoding = "UTF-8")
source(file.path(.np_scripts, "04_交付网络布局_DeliveryNetworkLayouts.R"), encoding = "UTF-8")

yy_plot_ppi_arm <- function(arm_root) {
  tab <- file.path(arm_root, "03_富集与PPI_EnrichPPI/01_数据文件_Data/02_结果数据_ResultTables")
  fig <- file.path(arm_root, "03_富集与PPI_EnrichPPI/03_图片文件_Figures")
  dir.create(fig, recursive = TRUE, showWarnings = FALSE)
  edges_f <- file.path(tab, "06_STRING_edges.csv")
  if (!file.exists(edges_f)) {
    message("skip PPI viz: missing ", edges_f)
    return(invisible(FALSE))
  }
  ppi <- utils::read.csv(edges_f, stringsAsFactors = FALSE, check.names = FALSE)
  if (!nrow(ppi) || "note" %in% names(ppi)) {
    message("skip PPI viz: empty edges")
    return(invisible(FALSE))
  }
  # STRING API score 0–1；网药默认 min_score=900 → 库内会按量纲换算
  p <- tryCatch(
    np_plot_string_ppi(
      ppi,
      title = "STRING PPI degree gradient",
      min_score = 900L,
      max_nodes = 200L,
      layout = "concentric"
    ),
    error = function(e) {
      message("PPI plot fail @0.9: ", conditionMessage(e), " ; retry min_score=400")
      tryCatch(
        np_plot_string_ppi(
          ppi,
          title = "STRING PPI degree gradient",
          min_score = 400L,
          max_nodes = 200L,
          layout = "concentric"
        ),
        error = function(e2) {
          message("PPI plot fail: ", conditionMessage(e2))
          NULL
        }
      )
    }
  )
  if (is.null(p)) return(invisible(FALSE))
  stem <- "13_网络图_StringPPI_Degree_Network"
  ggplot2::ggsave(file.path(fig, paste0(stem, ".png")), p, width = 11, height = 10, dpi = 600, bg = "white")
  ggplot2::ggsave(file.path(fig, paste0(stem, ".svg")), p, width = 11, height = 10, bg = "white")
  message("OK PPI ", stem, " -> ", fig)
  invisible(TRUE)
}

if (sys.nframe() == 0L || identical(sys.frame(1)$ofile, NULL)) {
  # only auto-run when executed via Rscript, not when sourced as a library
}
.is_main <- !interactive() && length(commandArgs(trailingOnly = FALSE)) > 0 &&
  any(grepl("plot_ppi_netpharm\\.R$", commandArgs(trailingOnly = FALSE)))
if (.is_main) {
  args <- commandArgs(trailingOnly = TRUE)
  arm <- if (length(args)) args[[1]] else "expanded"
  root <- if (identical(arm, "baseline")) {
    "E:/RProject/昱阳项目/02_未补充口径_Baseline_STPonly"
  } else {
    "E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource"
  }
  yy_plot_ppi_arm(root)
}
