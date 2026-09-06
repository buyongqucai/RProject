# 真实数据分析出图 — 分子动力学模拟_MolecularDynamics
# 输入：01_样例_sample/工作文件_MdWork/3HTB/08_轨迹分析_Analysis/*.xvg（GROMACS 2023.3 产出，REAL）
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
result_dir <- paths$result_dir
rep_dir <- paths$rep_dir
dir.create(rep_dir, recursive = TRUE, showWarnings = FALSE)

skill_en <- "MolecularDynamics"
skill_folder <- "分子动力学模拟_MolecularDynamics"
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
library(ggplot2)

# MD 样例覆盖 DeliveryStandards 默认「数据文件/图片文件」总分：
# 一图一文件夹：10_NPT压力图/ 内同时放该图 CSV 与 PNG/SVG
MD_TOPIC_ORDER <- c(
  "骨架RMSD" = 1L, "三线RMSD" = 2L, "残基RMSF" = 3L, "氢键数" = 4L,
  "回旋半径" = 5L, "溶剂可及表面积" = 6L, "质心距离" = 7L, "NVT温度" = 8L,
  "NPT温度" = 9L, "NPT压力" = 10L, "NPT密度" = 11L, "生产势能" = 12L,
  "自由能形貌" = 13L, "自由能形貌RMSDx质心" = 14L, "自由能形貌RMSDxSASA" = 15L,
  "自由能形貌配体蛋白RMSD" = 16L, "自由能形貌3D" = 17L,
  "自由能形貌3D_RMSDx质心" = 18L, "自由能形貌3D_RMSDxSASA" = 19L,
  "自由能形貌3D_配体蛋白RMSD" = 20L, "结合能分解" = 21L, "结合能标注柱" = 22L,
  "结合能表" = 23L, "残基能量贡献" = 24L, "轨迹快照" = 25L, "二维相互作用" = 26L
)
md_topic_n <- function(topic) unname(MD_TOPIC_ORDER[[topic]])
md_fig_dir <- function(topic) {
  n <- md_topic_n(topic)
  dname <- if (is.null(n) || is.na(n)) paste0(topic, "图") else sprintf("%02d_%s图", n, topic)
  d <- file.path(result_dir, dname)
  dir.create(d, recursive = TRUE, showWarnings = FALSE)
  d
}
write_md_csv <- function(df, zh, object) {
  fn <- delivery_table_name(skill_en, "table", object)
  n <- md_topic_n(zh)
  if (!is.null(n) && !is.na(n)) fn <- sprintf("%02d_%s", n, fn)
  write.csv(df, file.path(md_fig_dir(zh), fn), row.names = FALSE, fileEncoding = "UTF-8")
  invisible(fn)
}

md_work <- file.path(sample_root, "工作文件_MdWork", "3HTB")
md_dir  <- file.path(md_work, "08_轨迹分析_Analysis")
md_mmpbsa_dir <- file.path(md_work, "09_结合自由能_MmGbsa")
MD_XVG <- c(
  "rmsd_backbone.xvg" = "骨架RMSD_RmsdBackbone.xvg",
  "rmsd_protein.xvg" = "蛋白RMSD_RmsdProtein.xvg",
  "rmsd_ligand.xvg" = "配体RMSD_RmsdLigand.xvg",
  "rmsd_complex.xvg" = "复合物RMSD_RmsdComplex.xvg",
  "rmsf_calpha.xvg" = "残基RMSF_RmsfCalpha.xvg",
  "hbond_num.xvg" = "氢键数_HbondNum.xvg",
  "gyrate.xvg" = "回旋半径_RadiusGyration.xvg",
  "sasa.xvg" = "溶剂可及表面积_Sasa.xvg",
  "com_distance.xvg" = "质心距离_ComDistance.xvg",
  "energy_nvt_temp.xvg" = "NVT温度_NvtTemperature.xvg",
  "energy_npt_temp.xvg" = "NPT温度_NptTemperature.xvg",
  "energy_npt_press.xvg" = "NPT压力_NptPressure.xvg",
  "energy_npt_dens.xvg" = "NPT密度_NptDensity.xvg",
  "energy_md_temp.xvg" = "生产温度_MdTemperature.xvg",
  "energy_md_potential.xvg" = "生产势能_MdPotential.xvg"
)
md_find <- function(fname) {
  arch <- unname(MD_XVG[fname])
  cands <- c(
    if (!is.na(arch)) file.path(md_dir, arch) else NULL,
    file.path(md_dir, fname),
    file.path(md_work, fname)
  )
  hit <- cands[file.exists(cands)]
  if (length(hit)) hit[[1]] else cands[[1]]
}

# xvg：跳过 @/# 元数据行，读空白分隔数值
read_xvg <- function(fname, col_names) {
  f <- md_find(fname)
  if (!file.exists(f)) stop("缺少分析输入: ", fname, "（先跑 运行复合物MD_runComplexMd.sh 再 layout）")
  ln <- readLines(f, warn = FALSE)
  ln <- ln[!grepl("^[#@]", ln)]
  df <- read.table(text = ln, col.names = col_names)
  df
}

rmsd  <- read_xvg("rmsd_backbone.xvg", c("time_ns", "rmsd_nm"))
rmsf  <- read_xvg("rmsf_calpha.xvg", c("residue", "rmsf_nm"))
hbond <- read_xvg("hbond_num.xvg", c("time_ps", "n_hbond", "n_pairs"))
gyr   <- read_xvg("gyrate.xvg", c("time_ps", "rg_nm", "rg_x", "rg_y", "rg_z"))
sasa  <- read_xvg("sasa.xvg", c("time_ns", "sasa_nm2"))
hbond$time_ns <- hbond$time_ps / 1000
gyr$time_ns   <- gyr$time_ps / 1000

# 样例必备：三线 RMSD / 质心距离 / 平衡曲线（文件由 补算必备分析_extraMdAnalysis.sh 产出）
read_xvg_opt <- function(fname, col_names) {
  f <- md_find(fname)
  if (!file.exists(f) || file.info(f)$size < 50) return(NULL)
  ln <- readLines(f, warn = FALSE)
  ln <- ln[!grepl("^[#@]", ln)]
  if (!length(ln)) return(NULL)
  read.table(text = ln, col.names = col_names)
}
rmsd_p <- read_xvg_opt("rmsd_protein.xvg", c("time_ns", "rmsd_nm"))
rmsd_l <- read_xvg_opt("rmsd_ligand.xvg", c("time_ns", "rmsd_nm"))
rmsd_c <- read_xvg_opt("rmsd_complex.xvg", c("time_ns", "rmsd_nm"))
com_d  <- read_xvg_opt("com_distance.xvg", c("time_ns", "dist_nm"))
nvt_t  <- read_xvg_opt("energy_nvt_temp.xvg", c("time_ps", "temp_K"))
npt_t  <- read_xvg_opt("energy_npt_temp.xvg", c("time_ps", "temp_K"))
npt_p  <- read_xvg_opt("energy_npt_press.xvg", c("time_ps", "press_bar"))
npt_d  <- read_xvg_opt("energy_npt_dens.xvg", c("time_ps", "dens"))
md_t   <- read_xvg_opt("energy_md_temp.xvg", c("time_ps", "temp_K"))
md_pe  <- read_xvg_opt("energy_md_potential.xvg", c("time_ps", "pot_kj"))

ns_label <- sprintf("%.2f ns", max(rmsd$time_ns))
sub_label <- "3HTB/JZ4, GROMACS 2023.3"

# ---- 表格交付（CSV，UTF-8-SIG；写入各图种文件夹） ----
write_md_csv(rmsd, "骨架RMSD", "RmsdBackbone")
write_md_csv(rmsf, "残基RMSF", "RmsfCalpha")
write_md_csv(hbond[, c("time_ns", "n_hbond")], "氢键数", "HbondNum")
write_md_csv(gyr[, c("time_ns", "rg_nm")], "回旋半径", "RadiusGyration")
write_md_csv(sasa, "溶剂可及表面积", "Sasa")

qa_log <- list()
# 语义化中英对照：delivery_stem("三线RMSD","RmsdProteinLigandComplex") → 三线RMSD_RmsdProteinLigandComplex
# ggplot 备图与 Origin 正式图都进 {NN}_{zh}图/；报告引用 Origin PNG
save_md_plot <- function(p, plot_type, theme, w = 6, h = 4, zh = NULL) {
  topic <- if (!is.null(zh) && nzchar(zh)) zh else theme
  d <- md_fig_dir(topic)
  n <- md_topic_n(topic)
  qa <- viz_qa_after_plot(p, plot_id = paste(skill_en, theme, sep = "/"))
  qa_log[[length(qa_log) + 1L]] <<- data.frame(
    plot = theme, status = qa$status,
    detail = paste(vapply(qa$checks, function(x) paste0(x$check, ":", x$status), ""), collapse = "; ")
  )
  if (!is.null(zh) && nzchar(zh)) {
    delivery_save_plot(p, paste0(zh, "备图"), theme, NULL, w, h, d, bio_root, order = n)
  } else {
    delivery_save_plot(p, skill_en, plot_type, theme, w, h, d, bio_root, order = n)
  }
}

# ---- 图 1：Backbone RMSD ----
p_rmsd <- ggplot(rmsd, aes(time_ns, rmsd_nm)) +
  geom_line(color = "#5B8FA8", linewidth = 0.5) +
  labs(title = paste("Backbone RMSD", ns_label),
       subtitle = sub_label,
       x = "Time (ns)", y = "RMSD (nm)")
save_md_plot(p_rmsd, "line", "RmsdBackbone", zh = "骨架RMSD")

# ---- 图 2：C-alpha RMSF ----
p_rmsf <- ggplot(rmsf, aes(residue, rmsf_nm)) +
  geom_line(color = "#C17B7B", linewidth = 0.5) +
  labs(title = paste("C-alpha RMSF per residue", ns_label),
       subtitle = sub_label,
       x = "Residue index", y = "RMSF (nm)")
save_md_plot(p_rmsf, "line", "RmsfCalpha", zh = "残基RMSF")

# ---- 图 3：蛋白-配体氢键数 ----
p_hb <- ggplot(hbond, aes(time_ns, n_hbond)) +
  geom_step(color = "#6B8F71", linewidth = 0.6) +
  geom_point(color = "#6B8F71", size = 1.2) +
  scale_y_continuous(breaks = scales::pretty_breaks()) +
  labs(title = paste("Protein-ligand H-bonds", ns_label),
       subtitle = sub_label,
       x = "Time (ns)", y = "Number of H-bonds")
save_md_plot(p_hb, "line", "HbondNum", zh = "氢键数")

# ---- 图 4：回旋半径 Rg ----
p_rg <- ggplot(gyr, aes(time_ns, rg_nm)) +
  geom_line(color = "#8B7BA8", linewidth = 0.5) +
  labs(title = paste("Radius of gyration", ns_label),
       subtitle = sub_label,
       x = "Time (ns)", y = "Rg (nm)")
save_md_plot(p_rg, "line", "RadiusGyration", zh = "回旋半径")

# ---- 图 5：溶剂可及表面积 SASA ----
p_sasa <- ggplot(sasa, aes(time_ns, sasa_nm2)) +
  geom_line(color = "#D4A574", linewidth = 0.5) +
  labs(title = paste("Solvent accessible surface area", ns_label),
       subtitle = sub_label,
       x = "Time (ns)", y = expression("SASA (nm"^2*")"))
save_md_plot(p_sasa, "line", "Sasa", zh = "溶剂可及表面积")

# ---- 图 6：自由能形貌 FEL（RMSD × Rg，ΔG = -kT ln(P/Pmax)） ----
# 仅用默认 kde2d 带宽估计概率密度（FEL 定义所需）；禁止人为加宽带宽 / 后处理平滑
fel <- data.frame(rmsd = rmsd$rmsd_nm, rg = gyr$rg_nm[match(rmsd$time_ns, gyr$time_ns)])
fel <- fel[complete.cases(fel), ]
if (requireNamespace("MASS", quietly = TRUE) && nrow(fel) >= 5) {
  kd <- MASS::kde2d(fel$rmsd, fel$rg, n = 60)  # 默认 bandwidth.nrd，不额外放大
  p_mat <- kd$z / max(kd$z)
  p_mat[p_mat <= 0] <- min(p_mat[p_mat > 0]) * 1e-3
  kj <- 0.0083144621 * 300
  dg <- -(kj) * log(p_mat)
  dg <- dg - min(dg)
  fel_grid <- expand.grid(rmsd = kd$x, rg = kd$y)
  fel_grid$dg_kj <- as.vector(dg)
  write_md_csv(fel_grid, "自由能形貌", "FreeEnergyLandscape")
  p_fel <- ggplot(fel_grid, aes(rmsd, rg, z = dg_kj)) +
    geom_contour_filled(bins = 12, show.legend = TRUE) +
    scale_fill_viridis_d(option = "D", name = "dG (kJ/mol)") +
    labs(title = paste("Free energy landscape", ns_label),
         subtitle = paste0("3HTB/JZ4 | ", nrow(fel), " frames | default KDE bw"),
         x = "RMSD (nm)", y = "Rg (nm)")
  save_md_plot(p_fel, "contour", "FreeEnergyLandscape", 6.5, 5, zh = "自由能形貌")
} else {
  message("FEL 跳过：帧数不足或缺 MASS 包")
}

# ---- 额外 FEL：换反应坐标（默认 KDE 带宽，禁止后处理平滑；2D/3D 同网格） ----
interp_on <- function(t_ref, t_src, v_src) {
  if (is.null(t_src) || is.null(v_src) || length(t_src) < 2L) return(rep(NA_real_, length(t_ref)))
  stats::approx(t_src, v_src, xout = t_ref, rule = 2)$y
}
plot_fel_pair <- function(x, y, xlab, ylab, title_en, zh, theme, origin_name) {
  d <- data.frame(x = x, y = y)
  d <- d[complete.cases(d), ]
  if (!requireNamespace("MASS", quietly = TRUE) || nrow(d) < 5L) {
    message("FEL 跳过 ", theme, "：帧数不足或缺 MASS")
    return(invisible(NULL))
  }
  kd <- MASS::kde2d(d$x, d$y, n = 60)
  p_mat <- kd$z / max(kd$z)
  p_mat[p_mat <= 0] <- min(p_mat[p_mat > 0]) * 1e-3
  kj <- 0.0083144621 * 300
  dg <- -(kj) * log(p_mat)
  dg <- dg - min(dg)
  grid <- expand.grid(x = kd$x, y = kd$y)
  names(grid) <- c("x", "y")
  grid$dg_kj <- as.vector(dg)
  write_md_csv(grid, zh, theme)
  origin_now <- "E:/Origin_Data/3HTB"
  dir.create(origin_now, recursive = TRUE, showWarnings = FALSE)
  write.csv(grid, file.path(origin_now, origin_name), row.names = FALSE)
  p <- ggplot(grid, aes(x, y, z = dg_kj)) +
    geom_contour_filled(bins = 12, show.legend = TRUE) +
    scale_fill_viridis_d(option = "D", name = "dG (kJ/mol)") +
    labs(title = title_en,
         subtitle = paste0("3HTB/JZ4 | ", nrow(d), " frames | default KDE bw"),
         x = xlab, y = ylab)
  save_md_plot(p, "contour", theme, 6.5, 5, zh = zh)
  invisible(grid)
}
if (!is.null(com_d)) {
  y_com <- interp_on(rmsd$time_ns, com_d$time_ns, com_d$dist_nm)
  plot_fel_pair(rmsd$rmsd_nm, y_com, "RMSD (nm)", "COM distance (nm)",
                paste("Free energy landscape RMSD x COM", ns_label),
                "自由能形貌RMSDx质心", "FreeEnergyRmsdCom", "FEL_RMSD_COM_kJmol.csv")
}
y_sasa <- interp_on(rmsd$time_ns, sasa$time_ns, sasa$sasa_nm2)
plot_fel_pair(rmsd$rmsd_nm, y_sasa, "RMSD (nm)", "SASA (nm^2)",
              paste("Free energy landscape RMSD x SASA", ns_label),
              "自由能形貌RMSDxSASA", "FreeEnergyRmsdSasa", "FEL_RMSD_SASA_kJmol.csv")
if (!is.null(rmsd_p) && !is.null(rmsd_l)) {
  y_lig <- interp_on(rmsd_p$time_ns, rmsd_l$time_ns, rmsd_l$rmsd_nm)
  plot_fel_pair(rmsd_p$rmsd_nm, y_lig, "Protein RMSD (nm)", "Ligand RMSD (nm)",
                paste("Free energy landscape ligand vs protein RMSD", ns_label),
                "自由能形貌配体蛋白RMSD", "FreeEnergyLigandProteinRmsd",
                "FEL_LigandProteinRmsd_kJmol.csv")
}

# ---- 图 7/8：MM-GBSA 结合自由能（gmx_MMPBSA 输出，kcal/mol → kJ/mol） ----
KCAL2KJ <- 4.184
md_find_mmpbsa <- function(english) {
  arch <- c(
    "FINAL_RESULTS_MMPBSA.dat" = "结合能结果_FinalResultsMmpbsa.dat",
    "FINAL_DECOMP_MMPBSA.dat" = "残基分解_FinalDecompMmpbsa.dat"
  )[[english]]
  cands <- c(
    file.path(md_mmpbsa_dir, arch),
    file.path(md_mmpbsa_dir, english),
    file.path(md_work, english)
  )
  hit <- cands[file.exists(cands)]
  if (length(hit)) hit[[1]] else cands[[1]]
}
mmpbsa_dat <- md_find_mmpbsa("FINAL_RESULTS_MMPBSA.dat")
decomp_dat <- md_find_mmpbsa("FINAL_DECOMP_MMPBSA.dat")
dg_total_kj <- NA_real_
if (file.exists(mmpbsa_dat)) {
  ln <- readLines(mmpbsa_dat, warn = FALSE)
  d0 <- grep("Delta \\(Complex - Receptor - Ligand\\)", ln, fixed = FALSE)[1]
  dsec <- ln[seq(d0 + 1L, length.out = min(25L, length(ln) - d0))]
  parse_comp <- function(key) {
    cleaned <- sub("^[^A-Za-z0-9]+", "", trimws(dsec))  # 去掉 Δ 等非 ASCII 前缀
    row <- dsec[startsWith(cleaned, paste0(key, " ")) | startsWith(cleaned, key) & !grepl("1-4", cleaned)][1]
    if (is.na(row)) return(NULL)
    v <- as.numeric(strsplit(trimws(sub("^[^A-Za-z0-9]+", "", trimws(row))), "\\s+")[[1]][2:3])
    c(avg = v[1], sd = v[2])
  }
  comps <- rbind(
    parse_comp("VDWAALS"), parse_comp("EEL"), parse_comp("EGB"), parse_comp("ESURF")
  )
  rownames(comps) <- c("vdW", "Electrostatic", "Polar solv. (GB)", "Nonpolar solv.")
  tot <- parse_comp("TOTAL")
  dg_total_kj <- tot["avg"] * KCAL2KJ
  be_df <- data.frame(component = rownames(comps), avg_kj = comps[, "avg"] * KCAL2KJ,
                      sd_kj = comps[, "sd"] * KCAL2KJ)
  write_md_csv(be_df, "结合能分解", "BindingEnergyDecomp")

  be_df$component <- factor(be_df$component, levels = rev(rownames(comps)))
  # 标签放在柱顶上方空白区，避开 dG 虚线（虚线穿过柱身时勿把文字贴在线上）
  y_top <- max(c(be_df$avg_kj[be_df$avg_kj > 0], 5), na.rm = TRUE)
  y_bot <- min(0, sum(pmin(be_df$avg_kj, 0)) * 1.08)
  p_be <- ggplot(be_df, aes("3HTB/JZ4", avg_kj, fill = component)) +
    geom_col(width = 0.55, color = "white", linewidth = 0.2) +
    geom_hline(yintercept = dg_total_kj, linetype = "dashed", color = "grey40", linewidth = 0.5) +
    annotate("label", x = 1.72, y = y_top + 12,
             hjust = 0.5, vjust = 0, size = 3.4, fill = "white",
             label = sprintf("dG bind = %.1f kJ/mol", dg_total_kj)) +
    scale_fill_manual(values = c("vdW" = "#5B8FA8", "Electrostatic" = "#C17B7B",
                                 "Polar solv. (GB)" = "#D4A574", "Nonpolar solv." = "#6B8F71")) +
    labs(title = "MM-GBSA binding energy decomposition",
         subtitle = sub_label,
         x = NULL, y = "Energy (kJ/mol)", fill = NULL) +
    coord_cartesian(xlim = c(0.35, 2.35), ylim = c(y_bot, y_top + 28), clip = "off") +
    theme(plot.margin = margin(8, 28, 8, 8))
  save_md_plot(p_be, "bar", "BindingEnergyDecomp", 6.5, 4.5, zh = "结合能分解")
} else {
  message("MM-GBSA 结果缺失，跳过图 7/8：", mmpbsa_dat)
}

if (file.exists(decomp_dat)) {
  dl <- readLines(decomp_dat, warn = FALSE)
  dl <- dl[grepl("^[RL]:", dl)]
  dc <- do.call(rbind, strsplit(dl, ",", fixed = TRUE))
  res_lab <- sub("^[RL]:[A-Z]:", "", dc[, 1])
  res_lab <- gsub(":", "", res_lab)
  res_lab[grepl("^L:", dc[, 1])] <- paste0(res_lab[grepl("^L:", dc[, 1])], "(L)")
  res_df <- data.frame(
    residue = res_lab,
    total_kj = as.numeric(dc[, 17]) * KCAL2KJ,
    sd_kj = as.numeric(dc[, 18]) * KCAL2KJ
  )
  res_df <- res_df[order(res_df$total_kj), ]
  top_res <- head(res_df, 15)
  top_res$residue <- factor(top_res$residue, levels = rev(top_res$residue))
  write_md_csv(res_df, "残基能量贡献", "ResidueEnergyContrib")
  p_res <- ggplot(top_res, aes(residue, total_kj)) +
    geom_col(fill = "#5B8FA8", width = 0.7) +
    geom_errorbar(aes(ymin = total_kj - sd_kj, ymax = total_kj + sd_kj), width = 0.3, linewidth = 0.3) +
    coord_flip() +
    labs(title = "Residue dG Top 15",
         subtitle = sub_label,
         x = NULL, y = "dG contribution (kJ/mol)")
  save_md_plot(p_res, "bar", "ResidueEnergyContrib", 6, 5, zh = "残基能量贡献")
}

# ---- 样例必备补图：三线 RMSD / 质心距离 / 平衡曲线 ----
if (!is.null(rmsd_p) && !is.null(rmsd_l) && !is.null(rmsd_c)) {
  tri <- rbind(
    data.frame(time_ns = rmsd_p$time_ns, rmsd_nm = rmsd_p$rmsd_nm, series = "Protein"),
    data.frame(time_ns = rmsd_l$time_ns, rmsd_nm = rmsd_l$rmsd_nm, series = "Ligand"),
    data.frame(time_ns = rmsd_c$time_ns, rmsd_nm = rmsd_c$rmsd_nm, series = "Complex")
  )
  write_md_csv(tri, "三线RMSD", "RmsdTriCurve")
  p_tri <- ggplot(tri, aes(time_ns, rmsd_nm, color = series)) +
    geom_line(linewidth = 0.55) +
    scale_color_manual(values = c(Protein = "#5B8FA8", Ligand = "#C17B7B", Complex = "#8B7BA8")) +
    labs(title = paste("RMSD Protein / Ligand / Complex", ns_label),
         subtitle = sub_label,
         x = "Time (ns)", y = "RMSD (nm)", color = NULL)
  save_md_plot(p_tri, "line", "RmsdProteinLigandComplex", 6.5, 4.2, zh = "三线RMSD")
}

if (!is.null(com_d)) {
  write_md_csv(com_d, "质心距离", "ComDistance")
  p_com <- ggplot(com_d, aes(time_ns, dist_nm)) +
    geom_line(color = "#A67C52", linewidth = 0.55) +
    labs(title = paste("Protein-ligand COM distance", ns_label),
         subtitle = sub_label,
         x = "Time (ns)", y = "Distance (nm)")
  save_md_plot(p_com, "line", "ComDistance", zh = "质心距离")
}

# NVT temperature
if (!is.null(nvt_t)) {
  nvt_t$time_ns <- nvt_t$time_ps / 1000
  write_md_csv(nvt_t[, c("time_ns", "temp_K")], "NVT温度", "NvtTemperature")
  p_nvt <- ggplot(nvt_t, aes(time_ns, temp_K)) +
    geom_line(color = "#5B8FA8", linewidth = 0.45) +
    labs(title = "NVT equilibration temperature",
         subtitle = sub_label,
         x = "Time (ns)", y = "Temperature (K)")
  save_md_plot(p_nvt, "line", "NvtTemperature", zh = "NVT温度")
}
# NPT T / P / density
if (!is.null(npt_t) && !is.null(npt_p) && !is.null(npt_d)) {
  npt_t$time_ns <- npt_t$time_ps / 1000
  npt_p$time_ns <- npt_p$time_ps / 1000
  npt_d$time_ns <- npt_d$time_ps / 1000
  npt_tab <- data.frame(time_ns = npt_t$time_ns, temp_K = npt_t$temp_K,
                        press_bar = npt_p$press_bar, density = npt_d$dens)
  write_md_csv(npt_tab, "NPT温度", "NptEquilibration")
  fn_base <- delivery_table_name(skill_en, "table", "NptEquilibration")
  src_npt <- file.path(md_fig_dir("NPT温度"), sprintf("%02d_%s", md_topic_n("NPT温度"), fn_base))
  for (zh_npt in c("NPT压力", "NPT密度")) {
    dest_npt <- file.path(md_fig_dir(zh_npt), sprintf("%02d_%s", md_topic_n(zh_npt), fn_base))
    invisible(file.copy(src_npt, dest_npt, overwrite = TRUE))
  }
  p_npt_t <- ggplot(npt_t, aes(time_ns, temp_K)) +
    geom_line(color = "#C17B7B", linewidth = 0.45) +
    labs(title = "NPT equilibration temperature", subtitle = sub_label,
         x = "Time (ns)", y = "Temperature (K)")
  save_md_plot(p_npt_t, "line", "NptTemperature", zh = "NPT温度")
  p_npt_p <- ggplot(npt_p, aes(time_ns, press_bar)) +
    geom_line(color = "#6B8F71", linewidth = 0.45) +
    labs(title = "NPT equilibration pressure", subtitle = sub_label,
         x = "Time (ns)", y = "Pressure (bar)")
  save_md_plot(p_npt_p, "line", "NptPressure", zh = "NPT压力")
  p_npt_d <- ggplot(npt_d, aes(time_ns, dens)) +
    geom_line(color = "#8B7BA8", linewidth = 0.45) +
    labs(title = "NPT equilibration density", subtitle = sub_label,
         x = "Time (ns)", y = expression("Density (kg/"*m^3*")"))
  save_md_plot(p_npt_d, "line", "NptDensity", zh = "NPT密度")
}
# Production potential energy
if (!is.null(md_pe)) {
  md_pe$time_ns <- md_pe$time_ps / 1000
  write_md_csv(md_pe[, c("time_ns", "pot_kj")], "生产势能", "MdPotential")
  p_pe <- ggplot(md_pe, aes(time_ns, pot_kj)) +
    geom_line(color = "#D4A574", linewidth = 0.45) +
    labs(title = paste("Production potential energy", ns_label),
         subtitle = sub_label,
         x = "Time (ns)", y = "Potential (kJ/mol)")
  save_md_plot(p_pe, "line", "MdPotential", zh = "生产势能")
}

# ---- Origin 数据导出（E:\Origin_Data\3HTB，一图一 CSV，英文列名） ----
origin_dir <- file.path("E:/Origin_Data", "3HTB")
dir.create(origin_dir, recursive = TRUE, showWarnings = FALSE)
write.csv(rmsd, file.path(origin_dir, "RMSD_backbone.csv"), row.names = FALSE)
write.csv(rmsf, file.path(origin_dir, "RMSF_calpha.csv"), row.names = FALSE)
write.csv(hbond[, c("time_ns", "n_hbond")], file.path(origin_dir, "HBonds_protein_ligand.csv"), row.names = FALSE)
write.csv(gyr[, c("time_ns", "rg_nm")], file.path(origin_dir, "Rg.csv"), row.names = FALSE)
write.csv(sasa, file.path(origin_dir, "SASA.csv"), row.names = FALSE)
if (exists("tri")) write.csv(tri, file.path(origin_dir, "RMSD_protein_ligand_complex.csv"), row.names = FALSE)
if (!is.null(com_d)) write.csv(com_d, file.path(origin_dir, "COM_distance.csv"), row.names = FALSE)
if (!is.null(nvt_t)) write.csv(nvt_t[, c("time_ns", "temp_K")], file.path(origin_dir, "NVT_temperature.csv"), row.names = FALSE)
if (!is.null(npt_t)) write.csv(data.frame(time_ns = npt_t$time_ns, temp_K = npt_t$temp_K,
                                          press_bar = npt_p$press_bar, density = npt_d$dens),
                               file.path(origin_dir, "NPT_equilibration.csv"), row.names = FALSE)
if (!is.null(md_pe)) write.csv(md_pe[, c("time_ns", "pot_kj")], file.path(origin_dir, "MD_potential.csv"), row.names = FALSE)
if (exists("fel_grid")) write.csv(fel_grid, file.path(origin_dir, "FEL_RMSD_Rg_kJmol.csv"), row.names = FALSE)
if (exists("be_df")) write.csv(be_df, file.path(origin_dir, "MMGBSA_binding_decomp.csv"), row.names = FALSE)
if (exists("res_df")) write.csv(res_df, file.path(origin_dir, "MMGBSA_residue_contrib.csv"), row.names = FALSE)

# ---- PlotQA 汇总 + 审计 + 报告（审计/PlotQA 留在 报告文件） ----
qa_df <- do.call(rbind, qa_log)
write.csv(qa_df, file.path(rep_dir, delivery_table_name(skill_en, "table", "PlotQA")),
          row.names = FALSE, fileEncoding = "UTF-8")

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
  out_path = file.path(rep_dir, delivery_audit_name(skill_en, "post")),
  data_provenance = "REAL")

status <- if (all(qa_df$status %in% c("PASS", "WARN"))) "REAL" else "REAL_WITH_QA_FAIL"
writeLines(status, file.path(rep_dir, "STATUS.txt"))
md_report_script <- file.path(sample_root, "代码文件", "03_写样例报告_writeSampleReport.R")
if (!file.exists(md_report_script)) md_report_script <- "03_写样例报告_writeSampleReport.R"
source(md_report_script, encoding = "UTF-8")
message("DONE ", status, " — ", skill_folder, " report=", delivery_report_name(skill_en, "v1"))
