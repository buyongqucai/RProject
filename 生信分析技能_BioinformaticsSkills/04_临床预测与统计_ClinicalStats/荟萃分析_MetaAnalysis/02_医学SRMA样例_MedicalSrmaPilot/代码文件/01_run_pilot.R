# 医学 SRMA Pilot — 胰腺癌新辅助 vs 直接手术
# L1：对齐高分刊图册（PRISMA/森林/留一/漏斗/Baujat/RoB2/亚组）；非完整 SR
# 依据：文档_docs/高分刊Meta图册与工作量_JournalFigureWorkload.md
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
source(file.path(skill_scripts, "医学SRMA合并_poolMedicalSrma.R"), encoding = "UTF-8")
source(file.path(skill_scripts, "医学SRMA出图_plotMedicalSrma.R"), encoding = "UTF-8")

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
prisma_path  <- file.path(data_dir, "04_PRISMA计数_PrismaCounts_pilot.csv")
rob_path     <- file.path(data_dir, "05_RoB2_pilot.csv")
stopifnot(file.exists(extract_path), file.exists(prisma_path), file.exists(rob_path))
raw <- read.csv(extract_path, stringsAsFactors = FALSE, fileEncoding = "UTF-8")
prisma <- read.csv(prisma_path, stringsAsFactors = FALSE, fileEncoding = "UTF-8")
rob <- read.csv(rob_path, stringsAsFactors = FALSE, fileEncoding = "UTF-8")

# ---- 01 PRISMA flow（诚实 Pilot 计数）----
p_prisma <- plot_prisma_flow(prisma, title = "PRISMA flow (Pilot)")
delivery_save_plot(p_prisma, skill_en, "flow", "PrismaFlow",
                   width = FIG_WIDTH_SINGLE_IN, height = 5.2,
                   out_dir = fig_dir, start = bio_root, order = 1L)

# ---- OS 主分析 ----
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
delivery_save_plot(p_os, skill_en, "forest", "OsHr",
                   width = FIG_WIDTH_DOUBLE_IN, height = 4.4,
                   out_dir = fig_dir, start = bio_root, order = 2L)

# ---- leave-one-out ----
loo_os <- leave_one_out_hr(os)
write.csv(loo_os, file.path(tab_dir, delivery_table_name(skill_en, "table", "OsLeaveOneOut")),
          row.names = FALSE, fileEncoding = "UTF-8")
p_loo <- plot_loo_forest(loo_os, title = "OS leave-one-out sensitivity")
delivery_save_plot(p_loo, skill_en, "forest", "OsLeaveOneOut",
                   width = FIG_WIDTH_DOUBLE_IN, height = 3.8,
                   out_dir = fig_dir, start = bio_root, order = 3L)

# ---- DFS/RFS secondary ----
dfs <- prepare_hr_rows(raw, outcome = c("DFS", "RFS"))
fit_dfs <- pool_hr_reml(dfs)
sum_dfs <- summarize_pool(fit_dfs, dfs, label = "DFS_RFS")
write.csv(dfs, file.path(tab_dir, delivery_table_name(skill_en, "table", "DfsRfsStudyLevel")),
          row.names = FALSE, fileEncoding = "UTF-8")
write.csv(sum_dfs, file.path(tab_dir, delivery_table_name(skill_en, "table", "DfsRfsPooled")),
          row.names = FALSE, fileEncoding = "UTF-8")
p_dfs <- plot_hr_forest(dfs, fit_dfs,
  title = "DFS/RFS: neoadjuvant vs surgery",
  subtitle = "Illustrative; endpoints differ across trials")
delivery_save_plot(p_dfs, skill_en, "forest", "DfsRfsHr",
                   width = FIG_WIDTH_DOUBLE_IN, height = 4.4,
                   out_dir = fig_dir, start = bio_root, order = 4L)

# ---- Funnel（k<10 仅视觉）----
p_funnel <- plot_funnel_hr(os, fit_os, title = "Funnel plot (OS, Pilot)")
delivery_save_plot(p_funnel, skill_en, "funnel", "OsFunnel",
                   width = FIG_WIDTH_SINGLE_IN, height = 4.0,
                   out_dir = fig_dir, start = bio_root, order = 5L)

# ---- Baujat ----
p_baujat <- plot_baujat_hr(fit_os, title = "Baujat plot (OS)")
delivery_save_plot(p_baujat, skill_en, "baujat", "OsBaujat",
                   width = FIG_WIDTH_SINGLE_IN, height = 4.0,
                   out_dir = fig_dir, start = bio_root, order = 6L)

# ---- RoB 2 traffic light ----
write.csv(rob, file.path(tab_dir, delivery_table_name(skill_en, "table", "RoB2Pilot")),
          row.names = FALSE, fileEncoding = "UTF-8")
p_rob <- plot_rob2_traffic(rob, title = "Risk of bias RoB 2 (Pilot, single-rater)")
delivery_save_plot(p_rob, skill_en, "rob", "RoB2TrafficLight",
                   width = FIG_WIDTH_DOUBLE_IN, height = 4.2,
                   out_dir = fig_dir, start = bio_root, order = 7L)

# ---- Subgroup by population ----
p_sub <- plot_subgroup_forest(os, group_col = "population",
                              title = "OS by population (exploratory Pilot)")
delivery_save_plot(p_sub, skill_en, "forest", "OsSubgroupPopulation",
                   width = FIG_WIDTH_DOUBLE_IN, height = 3.6,
                   out_dir = fig_dir, start = bio_root, order = 8L)

# ---- 审计 + 报告 ----
write_delivery_audit(
  skill_en, "post",
  n_rows = nrow(os), n_cols = ncol(os), n_samples = nrow(os),
  group_source = "published RCT HRs (Pilot selection)",
  toy = FALSE, accession = paste(os$study_id, collapse = ","),
  sourced_skill_scripts = "医学SRMA合并_poolMedicalSrma.R; 医学SRMA出图_plotMedicalSrma.R",
  notes = paste0(
    "L1 Pilot atlas: PRISMA+OS+LOO+DFS/RFS+funnel+Baujat+RoB2+subgroup; ",
    "OS HR=", round(sum_os$hr[[1]], 3),
    " (95%CI ", round(sum_os$hr_lo[[1]], 3), "-", round(sum_os$hr_hi[[1]], 3),
    "); I2=", round(sum_os$i2[[1]], 1), "%; NOT full SR/GRADE; funnel k<10 visual only"
  ),
  out_path = file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "REAL"
)

fig_map <- c(
  "PRISMA flow (Pilot)" = paste0("../图片文件/", delivery_stem(skill_en, "flow", "PrismaFlow", order = 1), ".png"),
  "OS forest" = paste0("../图片文件/", delivery_stem(skill_en, "forest", "OsHr", order = 2), ".png"),
  "OS leave-one-out" = paste0("../图片文件/", delivery_stem(skill_en, "forest", "OsLeaveOneOut", order = 3), ".png"),
  "DFS/RFS forest" = paste0("../图片文件/", delivery_stem(skill_en, "forest", "DfsRfsHr", order = 4), ".png"),
  "OS funnel (k<10 visual)" = paste0("../图片文件/", delivery_stem(skill_en, "funnel", "OsFunnel", order = 5), ".png"),
  "OS Baujat" = paste0("../图片文件/", delivery_stem(skill_en, "baujat", "OsBaujat", order = 6), ".png"),
  "RoB 2 traffic light" = paste0("../图片文件/", delivery_stem(skill_en, "rob", "RoB2TrafficLight", order = 7), ".png"),
  "OS subgroup by population" = paste0("../图片文件/", delivery_stem(skill_en, "forest", "OsSubgroupPopulation", order = 8), ".png")
)

caveats <- paste0(
  "<p><b>L1 Pilot / 非完整系统评价。</b>未做多库系统检索、双人筛选与双人 RoB、GRADE。",
  "PRISMA 计数为手选路径；漏斗图 k&lt;10 仅视觉；RoB 为单人试填。",
  "不可作为治疗决策或投稿结论。R0/切除率森林图需 2×2 事件数，本 Pilot 未编造，留待 L2。</p>"
)

interp <- paste0(
  "<h3>1. 相对旧 Pilot 的补强</h3>",
  "<p>对齐 PRISMA 2020 / Cochrane 图种与同题高分文（如 <i>J Clin Med</i> 2020 RCT-only SRMA）：",
  "流程 → 主终点森林 → 次要终点 → 敏感性 → 漏斗/Baujat → RoB → 亚组。</p>",
  "<h3>2. OS 合并（主分析）</h3>",
  "<p>k=", sum_os$k[[1]], "；HR = <b>", sprintf("%.2f", sum_os$hr[[1]]),
  "</b>（95%CI ", sprintf("%.2f–%.2f", sum_os$hr_lo[[1]], sum_os$hr_hi[[1]]),
  "）；I² = ", sprintf("%.1f", sum_os$i2[[1]]), "%。方向利于新辅助，但设计异质（ESPAC5 可行性、随访短）。</p>",
  "<h3>3. 次要与诊断图</h3>",
  "<p>DFS/RFS 示意合并 HR = ", sprintf("%.2f", sum_dfs$hr[[1]]),
  "；终点定义不完全一致。漏斗不做 Egger 结论。亚组按 population 字段探索性展示。</p>",
  "<h3>4. L2 投稿包仍缺</h3>",
  "<ul class='compact'>",
  "<li>多库检索 + 真实 PRISMA 排除数 + PROSPERO</li>",
  "<li>双人 RoB 2 + GRADE SoF</li>",
  "<li>切除率 / R0 / pN0 的 RR 森林图（需事件表）</li>",
  "</ul>"
)

data_html <- paste0(
  "<p><b>data_provenance = REAL</b>。见 <code>数据文件/DATA_SOURCE.md</code>；",
  "PRISMA/RoB 见 <code>04_*</code>、<code>05_*</code>。</p>"
)

methods_html <- paste0(
  "<p>REML（metafor）；图册 SSOT：<code>文档_docs/高分刊Meta图册与工作量_JournalFigureWorkload.md</code>；",
  "VizStandards + DeliveryStandards。</p>"
)

audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")

kpis <- list(
  list(label = "Figures", value = "8", hint = "L1 atlas"),
  list(label = "OS HR", value = sprintf("%.2f", sum_os$hr[[1]]), hint = "REML"),
  list(label = "95% CI", value = sprintf("%.2f–%.2f", sum_os$hr_lo[[1]], sum_os$hr_hi[[1]]), hint = ""),
  list(label = "I²", value = sprintf("%.1f%%", sum_os$i2[[1]]), hint = "heterogeneity")
)

rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v2"))
write_delivery_report(
  skill_en, skill_folder, "REAL_PILOT",
  data_html, audit_html,
  "医学SRMA图册 L1（PRISMA+forest+funnel+RoB+Baujat+subgroup）",
  figures = fig_map, interpretation = interp, out_path = rep_file,
  kpis = kpis, methods_html = methods_html, caveats_html = caveats,
  subtitle = "Pancreatic cancer: neoadjuvant vs upfront surgery — L1 Pilot atlas",
  lead_html = "Expanded figure set aligned to journal SRMA practice. Still not a full systematic review."
)

writeLines(c(
  "REAL_PILOT",
  "data_provenance=REAL",
  "level=L1_Pilot_atlas_not_full_SR",
  "figures=8",
  paste0("os_hr=", round(sum_os$hr[[1]], 4)),
  paste0("os_i2=", round(sum_os$i2[[1]], 2)),
  "funnel=visual_only_k_lt_10",
  "rob=single_rater_provisional"
), file.path(rep_dir, "STATUS.txt"))

message("DONE REAL_PILOT atlas — figures=8 OS HR=", round(sum_os$hr[[1]], 3),
        " I2=", round(sum_os$i2[[1]], 1), "% report=", basename(rep_file))
