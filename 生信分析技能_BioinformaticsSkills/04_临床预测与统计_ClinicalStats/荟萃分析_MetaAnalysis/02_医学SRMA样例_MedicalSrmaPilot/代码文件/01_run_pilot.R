# 医学 SRMA Pilot — 胰腺癌新辅助 vs 直接手术
# L1 Pilot：验证 metafor + VizStandards + DeliveryStandards 工具链
# data_provenance=REAL；禁止外推为完整系统评价结论
options(stringsAsFactors = FALSE)

sample_root <- normalizePath("..", winslash = "/", mustWork = TRUE)
skill_root  <- normalizePath("../..", winslash = "/", mustWork = TRUE)
bio_root    <- normalizePath("../../..", winslash = "/", mustWork = TRUE)
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath("../../../..", winslash = "/", mustWork = TRUE)
}

viz_script <- file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                        "脚本_scripts", "出版级出图_PublicationPlot.R")
stopifnot(file.exists(viz_script))
source(viz_script, encoding = "UTF-8")
plotqa <- file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                    "脚本_scripts", "出图后审核_PlotQA.R")
if (file.exists(plotqa)) source(plotqa, encoding = "UTF-8")

delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")

skill_scripts <- file.path(skill_root, "脚本_scripts")
pool_script <- file.path(skill_scripts, "医学SRMA合并_poolMedicalSrma.R")
plot_script <- file.path(skill_scripts, "医学SRMA出图_plotMedicalSrma.R")
source(pool_script, encoding = "UTF-8")
source(plot_script, encoding = "UTF-8")

paths <- delivery_sample_paths(sample_root)
data_dir <- paths$raw_dir
fig_dir  <- paths$fig_dir
tab_dir  <- paths$tab_dir
rep_dir  <- paths$rep_dir
for (d in c(fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

skill_en <- "MetaAnalysis"
skill_folder <- "荟萃分析_MetaAnalysis"

if (!requireNamespace("metafor", quietly = TRUE)) {
  stop("需要 metafor：install.packages('metafor')", call. = FALSE)
}
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2", call. = FALSE)
library(ggplot2)

extract_path <- file.path(data_dir, "03_提取表_Extraction_pilot.csv")
stopifnot(file.exists(extract_path))
raw <- read.csv(extract_path, stringsAsFactors = FALSE, fileEncoding = "UTF-8")

# ---- OS（Pilot 主分析：终点一致）----
os <- prepare_hr_rows(raw, outcome = "OS")
fit_os <- pool_hr_reml(os)
sum_os <- summarize_pool(fit_os, os, label = "OS")
write.csv(os, file.path(tab_dir, delivery_table_name(skill_en, "table", "OsStudyLevel")),
          row.names = FALSE, fileEncoding = "UTF-8")
write.csv(sum_os, file.path(tab_dir, delivery_table_name(skill_en, "table", "OsPooled")),
          row.names = FALSE, fileEncoding = "UTF-8")

p_os <- plot_hr_forest(os, fit_os,
  title = "OS: neoadjuvant vs upfront surgery",
  subtitle = "Pilot REML (not full SR)")
delivery_save_plot(p_os, skill_en, "forest", "OsHrPilot",
                   width = FIG_WIDTH_DOUBLE_IN, height = 4.2,
                   out_dir = fig_dir, start = bio_root, order = 1L)

# leave-one-out sensitivity
loo_os <- leave_one_out_hr(os)
write.csv(loo_os, file.path(tab_dir, delivery_table_name(skill_en, "table", "OsLeaveOneOut")),
          row.names = FALSE, fileEncoding = "UTF-8")
p_loo <- plot_loo_forest(loo_os, title = "OS leave-one-out (Pilot)")
delivery_save_plot(p_loo, skill_en, "forest", "OsLeaveOneOut",
                   width = FIG_WIDTH_DOUBLE_IN, height = 3.8,
                   out_dir = fig_dir, start = bio_root, order = 2L)

# ---- DFS/RFS（示意：终点定义不完全一致）----
dfs <- prepare_hr_rows(raw, outcome = c("DFS", "RFS"))
fit_dfs <- pool_hr_reml(dfs)
sum_dfs <- summarize_pool(fit_dfs, dfs, label = "DFS_RFS")
write.csv(dfs, file.path(tab_dir, delivery_table_name(skill_en, "table", "DfsRfsStudyLevel")),
          row.names = FALSE, fileEncoding = "UTF-8")
write.csv(sum_dfs, file.path(tab_dir, delivery_table_name(skill_en, "table", "DfsRfsPooled")),
          row.names = FALSE, fileEncoding = "UTF-8")
p_dfs <- plot_hr_forest(dfs, fit_dfs,
  title = "DFS/RFS: neoadjuvant vs surgery",
  subtitle = "Illustrative; endpoints differ")
delivery_save_plot(p_dfs, skill_en, "forest", "DfsRfsHrPilot",
                   width = FIG_WIDTH_DOUBLE_IN, height = 4.2,
                   out_dir = fig_dir, start = bio_root, order = 3L)

# ---- 审计 + 报告 ----
write_delivery_audit(
  skill_en, "post",
  n_rows = nrow(os), n_cols = ncol(os), n_samples = nrow(os),
  group_source = "published RCT HRs (Pilot selection)",
  toy = FALSE, accession = paste(os$study_id, collapse = ","),
  sourced_skill_scripts = "医学SRMA合并_poolMedicalSrma.R; 医学SRMA出图_plotMedicalSrma.R",
  notes = paste0(
    "L1 Pilot medical SRMA: OS pooled HR=", round(sum_os$hr[[1]], 3),
    " (95%CI ", round(sum_os$hr_lo[[1]], 3), "-", round(sum_os$hr_hi[[1]], 3),
    "); I2=", round(sum_os$i2[[1]], 1), "%; NOT full SR/GRADE"
  ),
  out_path = file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "REAL"
)

fig_map <- c(
  "OS 森林图（Pilot）" = paste0("../图片文件/", delivery_stem(skill_en, "forest", "OsHrPilot", order = 1), ".png"),
  "OS 留一法敏感性" = paste0("../图片文件/", delivery_stem(skill_en, "forest", "OsLeaveOneOut", order = 2), ".png"),
  "DFS/RFS 森林图（示意）" = paste0("../图片文件/", delivery_stem(skill_en, "forest", "DfsRfsHrPilot", order = 3), ".png")
)

caveats <- paste0(
  "<p><b>L1 Pilot / 非完整系统评价。</b>仅 3 项手动精选 RCT，未做多库系统检索、双人筛选、RoB 2、GRADE。",
  "合并效应仅验证工具链，<b>不可</b>作为治疗决策或投稿结论。</p>"
)

interp <- paste0(
  "<h3>1. Pilot 做了什么</h3>",
  "<p>从已发表 RCT 提取 neoadjuvant vs upfront surgery 的 <b>OS</b> 与 <b>DFS/RFS</b> HR，",
  "用 <code>metafor</code> REML 随机效应合并，并按 VizStandards 出森林图。</p>",
  "<h3>2. OS 合并结果（主分析）</h3>",
  "<p>研究数 ", sum_os$k[[1]], "；合并 HR = <b>", sprintf("%.2f", sum_os$hr[[1]]),
  "</b>（95%CI ", sprintf("%.2f–%.2f", sum_os$hr_lo[[1]], sum_os$hr_hi[[1]]),
  "）；I² = ", sprintf("%.1f", sum_os$i2[[1]]), "%；τ² = ",
  sprintf("%.3f", sum_os$tau2[[1]]), "。方向有利于新辅助路径，但异质性与研究设计差异大（尤其 ESPAC5 为 II 期可行性、随访短）。</p>",
  "<h3>3. DFS/RFS（示意）</h3>",
  "<p>合并 HR = ", sprintf("%.2f", sum_dfs$hr[[1]]),
  "（95%CI ", sprintf("%.2f–%.2f", sum_dfs$hr_lo[[1]], sum_dfs$hr_hi[[1]]),
  "）。Prep-02 报告的是 RFS，ESPAC5 DFS 从手术起算，与 PREOPANC DFS 定义不完全一致，正式 SR 须统一终点或分报。</p>",
  "<h3>4. 下一步（L2 投稿包）</h3>",
  "<ul class='compact'>",
  "<li>锁定 PICO：BRPC 标准、Primary 选 DFS 或 PFS、新辅助方案 Broad/Narrow</li>",
  "<li>PROSPERO 预注册 + 多库检索 + PRISMA 流程图</li>",
  "<li>RoB 2 + GRADE SoF + OS/DFS 双终点正式森林图</li>",
  "</ul>"
)

data_html <- paste0(
  "<p><b>data_provenance = REAL</b>。来源见 <code>数据文件/DATA_SOURCE.md</code>：",
  "PREOPANC（JCO 2022）、Prep-02/JSAP05、ESPAC5（Lancet Gastroenterol Hepatol 2023）。</p>"
)

methods_html <- paste0(
  "<p>R：<code>metafor::rma</code>（REML）；出图：VizStandards + DeliveryStandards；",
  "脚本：<code>医学SRMA合并_poolMedicalSrma.R</code>、<code>医学SRMA出图_plotMedicalSrma.R</code>。</p>"
)

audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")

kpis <- list(
  list(label = "研究数 (OS)", value = as.character(sum_os$k[[1]]), hint = "Pilot"),
  list(label = "合并 OS HR", value = sprintf("%.2f", sum_os$hr[[1]]), hint = "REML"),
  list(label = "95% CI", value = sprintf("%.2f–%.2f", sum_os$hr_lo[[1]], sum_os$hr_hi[[1]]), hint = ""),
  list(label = "I²", value = sprintf("%.1f%%", sum_os$i2[[1]]), hint = "heterogeneity")
)

rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(
  skill_en, skill_folder, "REAL_PILOT",
  data_html, audit_html,
  "医学SRMA合并 + 医学SRMA出图 + VizStandards",
  figures = fig_map, interpretation = interp, out_path = rep_file,
  kpis = kpis, methods_html = methods_html, caveats_html = caveats,
  subtitle = "Pancreatic cancer: neoadjuvant vs upfront surgery — L1 Pilot",
  lead_html = "Tool-chain validation with 3 published RCTs. Not a full systematic review."
)

writeLines(c(
  "REAL_PILOT",
  "data_provenance=REAL",
  "level=L1_Pilot_not_full_SR",
  paste0("os_hr=", round(sum_os$hr[[1]], 4)),
  paste0("os_i2=", round(sum_os$i2[[1]], 2))
), file.path(rep_dir, "STATUS.txt"))

message("DONE REAL_PILOT — OS HR=", round(sum_os$hr[[1]], 3),
        " I2=", round(sum_os$i2[[1]], 1), "% report=", basename(rep_file))
