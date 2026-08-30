# 真实数据分析出图 — 分子动力学模拟_MolecularDynamics
# 输入：01_样例_sample/工作文件_mdwork/3HTB/*.xvg（GROMACS 2023.3 产出，REAL）
# 合规：统一交付规范_DeliveryStandards + 统一可视化规范_VizStandards（图面英文，PlotQA 强制）
# analysis_kind=md_3htb  data_provenance=REAL (RCSB PDB 3HTB)
options(stringsAsFactors = FALSE)

sample_root <- normalizePath("..", winslash = "/", mustWork = TRUE)
skill_root  <- normalizePath("../..", winslash = "/", mustWork = TRUE)
bio_root    <- normalizePath("../../..", winslash = "/", mustWork = TRUE)
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath("../../../..", winslash = "/", mustWork = TRUE)
}

viz_script <- file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                        "脚本_scripts", "出版级出图_PublicationPlot.R")
if (file.exists(viz_script)) source(viz_script, encoding = "UTF-8")
plotqa_script <- file.path(bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
                           "脚本_scripts", "出图后审核_PlotQA.R")
if (file.exists(plotqa_script)) source(plotqa_script, encoding = "UTF-8")

delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")

paths <- delivery_sample_paths(sample_root)
fig_dir <- paths$fig_dir; tab_dir <- paths$tab_dir; rep_dir <- paths$rep_dir
for (d in c(fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

skill_en <- "MolecularDynamics"
skill_folder <- "分子动力学模拟_MolecularDynamics"
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
library(ggplot2)

md_dir <- file.path(sample_root, "工作文件_mdwork", "3HTB")

# xvg：跳过 @/# 元数据行，读空白分隔数值
read_xvg <- function(fname, col_names) {
  f <- file.path(md_dir, fname)
  if (!file.exists(f)) stop("缺少分析输入: ", f, "（先跑 运行复合物MD_runComplexMd.sh）")
  ln <- readLines(f, warn = FALSE)
  ln <- ln[!grepl("^[#@]", ln)]
  df <- read.table(text = ln, col.names = col_names)
  df
}

rmsd  <- read_xvg("rmsd_backbone.xvg", c("time_ns", "rmsd_nm"))
rmsf  <- read_xvg("rmsf_calpha.xvg", c("residue", "rmsf_nm"))
hbond <- read_xvg("hbond_num.xvg", c("time_ps", "n_hbond", "n_pairs"))
gyr   <- read_xvg("gyrate.xvg", c("time_ps", "rg_nm", "rg_x", "rg_y", "rg_z"))
hbond$time_ns <- hbond$time_ps / 1000
gyr$time_ns   <- gyr$time_ps / 1000
ns_label <- sprintf("%.2f ns", max(rmsd$time_ns))
sub_label <- "3HTB/JZ4, GROMACS 2023.3"

# ---- 表格交付（CSV，UTF-8-SIG） ----
write.csv(rmsd,  file.path(tab_dir, delivery_table_name(skill_en, "table", "RmsdBackbone")), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(rmsf,  file.path(tab_dir, delivery_table_name(skill_en, "table", "RmsfCalpha")), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(hbond[, c("time_ns", "n_hbond")], file.path(tab_dir, delivery_table_name(skill_en, "table", "HbondNum")), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(gyr[, c("time_ns", "rg_nm")], file.path(tab_dir, delivery_table_name(skill_en, "table", "RadiusGyration")), row.names = FALSE, fileEncoding = "UTF-8")

qa_log <- list()
save_md_plot <- function(p, plot_type, theme, w = 6, h = 4) {
  qa <- viz_qa_after_plot(p, plot_id = paste(skill_en, theme, sep = "/"))
  qa_log[[length(qa_log) + 1L]] <<- data.frame(
    plot = theme, status = qa$status,
    detail = paste(vapply(qa$checks, function(x) paste0(x$check, ":", x$status), ""), collapse = "; ")
  )
  delivery_save_plot(p, skill_en, plot_type, theme, w, h, fig_dir, bio_root)
}

# ---- 图 1：Backbone RMSD ----
p_rmsd <- ggplot(rmsd, aes(time_ns, rmsd_nm)) +
  geom_line(color = "#5B8FA8", linewidth = 0.5) +
  labs(title = paste("Backbone RMSD", ns_label),
       subtitle = sub_label,
       x = "Time (ns)", y = "RMSD (nm)")
save_md_plot(p_rmsd, "line", "RmsdBackbone")

# ---- 图 2：C-alpha RMSF ----
p_rmsf <- ggplot(rmsf, aes(residue, rmsf_nm)) +
  geom_line(color = "#C17B7B", linewidth = 0.5) +
  labs(title = paste("C-alpha RMSF per residue", ns_label),
       subtitle = sub_label,
       x = "Residue index", y = "RMSF (nm)")
save_md_plot(p_rmsf, "line", "RmsfCalpha")

# ---- 图 3：蛋白-配体氢键数 ----
p_hb <- ggplot(hbond, aes(time_ns, n_hbond)) +
  geom_step(color = "#6B8F71", linewidth = 0.6) +
  geom_point(color = "#6B8F71", size = 1.2) +
  scale_y_continuous(breaks = scales::pretty_breaks()) +
  labs(title = paste("Protein-ligand H-bonds", ns_label),
       subtitle = sub_label,
       x = "Time (ns)", y = "Number of H-bonds")
save_md_plot(p_hb, "line", "HbondNum")

# ---- 图 4：回旋半径 Rg ----
p_rg <- ggplot(gyr, aes(time_ns, rg_nm)) +
  geom_line(color = "#8B7BA8", linewidth = 0.5) +
  labs(title = paste("Radius of gyration", ns_label),
       subtitle = sub_label,
       x = "Time (ns)", y = "Rg (nm)")
save_md_plot(p_rg, "line", "RadiusGyration")

# ---- PlotQA 汇总 + 审计 + 报告 ----
qa_df <- do.call(rbind, qa_log)
write.csv(qa_df, file.path(tab_dir, delivery_table_name(skill_en, "table", "PlotQA")), row.names = FALSE, fileEncoding = "UTF-8")

n_frames <- nrow(rmsd)
write_delivery_audit(skill_en, "post",
  n_rows = n_frames, n_cols = 4L, n_samples = 1L,
  group_source = "n/a single complex",
  toy = FALSE, accession = "RCSB PDB 3HTB",
  sourced_skill_scripts = "运行复合物MD_runComplexMd.sh; 分析出图_plotMdAnalysis.R; 出版级出图/PlotQA",
  notes = paste0("REAL MD E2E: pdb2gmx(amber99sb-ildn/tip3p) + GAFF2(JZ4) + 0.15M NaCl; ",
                 "EM/NVT/NPT/", ns_label, " production; frames=", n_frames,
                 "; mean RMSD=", round(mean(rmsd$rmsd_nm), 3), " nm",
                 "; mean Rg=", round(mean(gyr$rg_nm), 3), " nm"),
  out_path = file.path(tab_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "REAL")

fig_map <- c(
  "Backbone RMSD" = paste0("../图片文件/", delivery_stem(skill_en, "line", "RmsdBackbone"), ".png"),
  "C-alpha RMSF" = paste0("../图片文件/", delivery_stem(skill_en, "line", "RmsfCalpha"), ".png"),
  "蛋白-配体氢键数" = paste0("../图片文件/", delivery_stem(skill_en, "line", "HbondNum"), ".png"),
  "回旋半径 Rg" = paste0("../图片文件/", delivery_stem(skill_en, "line", "RadiusGyration"), ".png")
)
data_html <- paste0(
  "<p><b>REAL</b>：RCSB PDB 3HTB（T4 lysozyme L99A/M102Q + JZ4）。GROMACS 2023.3 全流程，",
  "amber99sb-ildn/tip3p + GAFF2，0.15 M NaCl，1 ns 生产（演示尺度）。</p>",
  "<p>详见 <code>数据文件/DATA_SOURCE.md</code> 与 <code>工作文件_mdwork/3HTB/</code>。</p>"
)
audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
audit_html <- paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")
interp <- paste0(
  ns_label, " 演示轨迹：backbone RMSD 均值 ", round(mean(rmsd$rmsd_nm), 3),
  " nm（末段 ", round(mean(utils::tail(rmsd$rmsd_nm, 20)), 3), " nm）；",
  "Rg 均值 ", round(mean(gyr$rg_nm), 3), " nm；",
  "蛋白-配体氢键均值 ", round(mean(hbond$n_hbond), 1), " 个。",
  "演示尺度仅验证流程与出图，结合稳定性结论需 ≥100 ns 重复轨迹。")
status <- if (all(qa_df$status %in% c("PASS", "WARN"))) "REAL" else "REAL_WITH_QA_FAIL"

rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(skill_en, skill_folder, status, data_html, audit_html,
                      "运行复合物MD_runComplexMd.sh + 分析出图_plotMdAnalysis.R",
                      fig_map, interp, rep_file)
writeLines(status, file.path(rep_dir, "STATUS.txt"))
message("DONE ", status, " — ", skill_folder, " report=", basename(rep_file))
