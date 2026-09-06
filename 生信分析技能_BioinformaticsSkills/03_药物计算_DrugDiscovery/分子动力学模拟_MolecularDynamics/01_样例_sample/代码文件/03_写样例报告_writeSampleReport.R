# 从已有结果 CSV / PNG 写出样例 HTML（不重跑 GROMACS / Origin / ggplot）
# 用法：在 代码文件/ 下  Rscript 03_写样例报告_writeSampleReport.R
# 亦可被 02_分析出图_plotMdAnalysis.R 在出图结束后 source
options(stringsAsFactors = FALSE)

if (!exists("sample_root")) {
  cmd_args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", cmd_args, value = TRUE)
  code_dir <- if (length(file_arg)) {
    dirname(normalizePath(sub("^--file=", "", file_arg[[1]]), winslash = "/", mustWork = TRUE))
  } else {
    normalizePath(getwd(), winslash = "/", mustWork = TRUE)
  }
  sample_root <- normalizePath(file.path(code_dir, ".."), winslash = "/", mustWork = TRUE)
}
if (!exists("skill_root")) {
  skill_root <- normalizePath(file.path(sample_root, ".."), winslash = "/", mustWork = TRUE)
}
if (!exists("bio_root")) {
  bio_root <- normalizePath(file.path(skill_root, "../.."), winslash = "/", mustWork = TRUE)
  if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
    bio_root <- normalizePath(file.path(skill_root, "../../.."), winslash = "/", mustWork = TRUE)
  }
}

delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
if (!exists("write_delivery_report", mode = "function")) {
  source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
  source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")
}
if (!exists("paths")) paths <- delivery_sample_paths(sample_root)
if (!exists("result_dir")) result_dir <- paths$result_dir
if (!exists("rep_dir")) rep_dir <- paths$rep_dir
if (!exists("skill_en")) skill_en <- "MolecularDynamics"
if (!exists("skill_folder")) skill_folder <- "分子动力学模拟_MolecularDynamics"

md_read_csv <- function(dir, candidates) {
  for (fn in candidates) {
    p <- file.path(dir, fn)
    if (file.exists(p)) {
      return(utils::read.csv(p, stringsAsFactors = FALSE, fileEncoding = "UTF-8"))
    }
  }
  NULL
}

md_num <- function(x) suppressWarnings(as.numeric(x))
md_fmt <- function(x, d = 3) {
  if (length(x) == 0L || is.na(x[[1]])) return("NA")
  format(round(x[[1]], d), nsmall = d, trim = TRUE)
}

rmsd <- md_read_csv(file.path(result_dir, "01_骨架RMSD图"),
                    c("01_数据表_RmsdBackboneTable.csv", "RMSD_backbone.csv"))
tri <- md_read_csv(file.path(result_dir, "02_三线RMSD图"),
                   c("02_数据表_RmsdTriCurveTable.csv", "RMSD_protein_ligand_complex.csv"))
rmsf <- md_read_csv(file.path(result_dir, "03_残基RMSF图"),
                    c("03_数据表_RmsfCalphaTable.csv", "RMSF_calpha.csv"))
hbond <- md_read_csv(file.path(result_dir, "04_氢键数图"),
                     c("04_数据表_HbondNumTable.csv", "HBonds_protein_ligand.csv"))
gyr <- md_read_csv(file.path(result_dir, "05_回旋半径图"),
                   c("05_数据表_RadiusGyrationTable.csv", "Rg.csv"))
sasa <- md_read_csv(file.path(result_dir, "06_溶剂可及表面积图"),
                    c("06_数据表_SasaTable.csv", "SASA.csv"))
com_d <- md_read_csv(file.path(result_dir, "07_质心距离图"),
                     c("07_数据表_ComDistanceTable.csv", "COM_distance.csv"))
be_tab <- md_read_csv(file.path(result_dir, "23_结合能表图"),
                      c("23_数据表_BindingEnergyTable.csv", "MMGBSA_binding_table.csv"))
be_de <- md_read_csv(file.path(result_dir, "21_结合能分解图"),
                     c("21_数据表_BindingEnergyDecompTable.csv", "MMGBSA_binding_decomp.csv"))
res_df <- md_read_csv(file.path(result_dir, "24_残基能量贡献图"),
                      c("24_数据表_ResidueEnergyContribTable.csv", "MMGBSA_residue_contrib.csv"))

if (is.null(rmsd) || is.null(gyr) || is.null(hbond)) {
  stop("缺少 RMSD/Rg/氢键 CSV，无法写报告。请先跑 02_分析出图_plotMdAnalysis.R", call. = FALSE)
}

n_frames <- nrow(rmsd)
prod_ns <- max(md_num(rmsd$time_ns), na.rm = TRUE)
rmsd_x <- md_num(rmsd$rmsd_nm)
rg_x <- md_num(gyr$rg_nm)
hb_x <- md_num(hbond[[grep("hbond|n_hbond", names(hbond), ignore.case = TRUE)[1]]])
sasa_x <- if (!is.null(sasa)) md_num(sasa[[grep("sasa", names(sasa), ignore.case = TRUE)[1]]]) else NA_real_
com_x <- if (!is.null(com_d)) md_num(com_d[[grep("dist", names(com_d), ignore.case = TRUE)[1]]]) else NA_real_
rmsf_x <- if (!is.null(rmsf)) md_num(rmsf$rmsf_nm) else NA_real_

mean_rmsd <- mean(rmsd_x, na.rm = TRUE)
tail_rmsd <- mean(utils::tail(rmsd_x, min(20L, length(rmsd_x))), na.rm = TRUE)
mean_rg <- mean(rg_x, na.rm = TRUE)
sd_rg <- stats::sd(rg_x, na.rm = TRUE)
mean_hb <- mean(hb_x, na.rm = TRUE)
mean_sasa <- mean(sasa_x, na.rm = TRUE)
mean_com <- mean(com_x, na.rm = TRUE)
com_range <- max(com_x, na.rm = TRUE) - min(com_x, na.rm = TRUE)
rmsf_max <- max(rmsf_x, na.rm = TRUE)
rmsf_max_res <- if (!is.null(rmsf) && length(rmsf_x)) as.character(rmsf$residue[which.max(rmsf_x)]) else "NA"
rmsf_mean <- mean(rmsf_x, na.rm = TRUE)

tri_mean <- function(label) {
  if (is.null(tri) || !"series" %in% names(tri)) return(NA_real_)
  mean(md_num(tri$rmsd_nm[tri$series == label]), na.rm = TRUE)
}
tri_max <- function(label) {
  if (is.null(tri) || !"series" %in% names(tri)) return(NA_real_)
  max(md_num(tri$rmsd_nm[tri$series == label]), na.rm = TRUE)
}

pick_be <- function(df, key) {
  if (is.null(df) || !nrow(df)) return(NULL)
  comp <- as.character(df[[1]])
  hit <- which(toupper(comp) == toupper(key) | grepl(paste0("^", key, "$"), comp, ignore.case = TRUE))
  if (!length(hit)) hit <- grep(key, comp, ignore.case = TRUE)
  if (!length(hit)) return(NULL)
  df[hit[[1]], , drop = FALSE]
}
be_val <- function(row, col) {
  if (is.null(row) || !col %in% names(row)) return(NA_real_)
  md_num(row[[col]])
}
tot <- pick_be(be_tab, "TOTAL")
if (is.null(tot)) tot <- pick_be(be_de, "TOTAL")
vdw <- pick_be(be_tab, "VDWAALS")
if (is.null(vdw)) vdw <- pick_be(be_de, "vdW")
eel <- pick_be(be_tab, "EEL")
if (is.null(eel)) eel <- pick_be(be_de, "Electrostatic")
egb <- pick_be(be_tab, "EGB")
if (is.null(egb)) egb <- pick_be(be_de, "Polar solv")
esurf <- pick_be(be_tab, "ESURF")
if (is.null(esurf)) esurf <- pick_be(be_de, "Nonpolar")
ggas <- pick_be(be_tab, "GGAS")
gsolv <- pick_be(be_tab, "GSOLV")

dg_kj <- be_val(tot, "avg_kj")
dg_kcal <- be_val(tot, "avg_kcal")
dg_sd_kcal <- be_val(tot, "sd_kcal")
if (is.na(dg_kcal) && !is.na(dg_kj)) dg_kcal <- dg_kj / 4.184
if (is.na(dg_kj) && !is.na(dg_kcal)) dg_kj <- dg_kcal * 4.184

top_res <- if (!is.null(res_df) && nrow(res_df)) {
  ord <- res_df[order(md_num(res_df$total_kj)), , drop = FALSE]
  utils::head(ord, 6L)
} else {
  NULL
}
res_txt <- function(i) {
  if (is.null(top_res) || nrow(top_res) < i) return("NA")
  sprintf("%s（%.1f kJ/mol）", top_res$residue[[i]], md_num(top_res$total_kj[[i]]))
}

status_path <- file.path(rep_dir, "STATUS.txt")
if (!(exists("status") && is.character(status) && length(status) == 1L && nzchar(status))) {
  status <- if (file.exists(status_path)) {
    trimws(readLines(status_path, warn = FALSE, encoding = "UTF-8")[[1]])
  } else {
    "REAL"
  }
}

audit_path <- file.path(rep_dir, delivery_audit_name(skill_en, "post"))
audit_html <- if (file.exists(audit_path)) {
  paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n"), "</pre>")
} else {
  "<p>未找到审计后检 CSV。</p>"
}

fig <- function(title, folder, file, caption = "", note = "", wide = FALSE) {
  abs_p <- file.path(result_dir, folder, file)
  if (!file.exists(abs_p)) return(NULL)
  list(
    title = title,
    src = paste0("../", folder, "/", file),
    caption = caption,
    note = note,
    wide = wide
  )
}
keep <- function(...) Filter(Negate(is.null), list(...))

ns_lab <- sprintf("%.2f ns", prod_ns)
kpis <- list(
  list(label = "生产时长", value = ns_lab, hint = "演示尺度"),
  list(label = "分析帧数", value = as.character(n_frames), hint = "10 ps 间隔"),
  list(label = "骨架 RMSD", value = md_fmt(mean_rmsd, 3), unit = "nm", hint = "轨迹均值"),
  list(label = "回旋半径 Rg", value = md_fmt(mean_rg, 3), unit = "nm", hint = "整体紧实度"),
  list(label = "蛋白–配体氢键", value = md_fmt(mean_hb, 2), unit = "", hint = "均值 / 帧"),
  list(label = "MM-GBSA ΔG", value = sprintf("%.1f kJ/mol", dg_kj), hint = "未含熵")
)

data_html <- paste0(
  "<p><b>data_provenance = REAL</b>。复合物来自 RCSB PDB <code>3HTB</code>",
  "（T4 lysozyme L99A/M102Q + 配体 JZ4 / 2-propylphenol；GROMACS 教程常用体系）。",
  "生产模拟用 GROMACS 2023.3，蛋白/水/离子为 amber99sb-ildn + TIP3P，",
  "配体 GAFF2（acpype/AmberTools），溶剂化后 0.15 M NaCl。</p>",
  "<p>原始 PDB：<code>数据文件/01_复合物结构_3HTB.pdb</code>。",
  "引擎产物与 xvg 归档在 <code>工作文件_MdWork/3HTB/</code>（按 EM / NVT / NPT / 生产 / 分析 / MM-GBSA 分阶段）。",
  "出处备忘见 <code>数据文件/DATA_SOURCE.md</code>。</p>"
)

methods_html <- paste0(
  "<p>本报告由 DeliveryStandards <code>write_delivery_report()</code> 生成，",
  "图面规范走 VizStandards（DPI≥600、图面英文、journal muted；FEL 用 Viridis）。</p>",
  "<ul class='compact'>",
  "<li>GROMACS 全流程：<code>脚本_scripts/运行复合物MD_runComplexMd.sh</code>（EM → NVT → NPT → 生产）</li>",
  "<li>分析表：<code>代码文件/02_分析出图_plotMdAnalysis.R</code>（xvg → CSV；ggplot 仅备份）</li>",
  "<li>正式分析图：Origin，<code>脚本_scripts/origin出图_plotMdOrigin.py</code></li>",
  "<li>快照：PyMOL；末帧二维接触：LigPlot+（<code>ligplot二维相互作用_runLigPlot2d.py</code>）</li>",
  "<li>MM-GBSA：gmx_MMPBSA，GB <code>igb=5</code>，21 帧；<b>未算熵</b>（nmode/QT 未开）</li>",
  "</ul>",
  "<p>HTML 可单独重写（不重跑模拟）：<code>Rscript 代码文件/03_写样例报告_writeSampleReport.R</code>。</p>"
)

caveats_html <- paste0(
  "<p><b>这是 ", ns_lab, " / ", n_frames, " 帧的流程金标，不是发表级自由能结论。</b> ",
  "骨架 RMSD 平台、口袋内滞留和 MM-GBSA 负值只说明：在本演示窗口里体系没有崩、配体没有飞出。",
  "构象采样、结合稳定性、ΔG 排序或 FEL 能垒，需要 <b>≥100 ns 生产 + 重复轨迹 + 熵项</b> 才能讨论。</p>"
)

interp <- paste0(
  "<h3>1. 先把尺度说清楚</h3>",
  "<p>生产段只有 <b>", ns_lab, "</b>，分析用 ", n_frames, " 帧（约 10 ps/帧）。",
  "对 T4 溶菌酶这种球状蛋白，这个长度只够看局部热涨落，不够看环区重排、口袋开合或配体进出。",
  "下面数字全部直接来自样例 CSV，不外推到体内或到「稳定结合」。</p>",

  "<h3>2. 平衡段在做什么</h3>",
  "<p>NVT / NPT 图是质控，不是生物学结果：看温度是否被恒温器拉住、密度是否落到平台、生产势能有没有发散。",
  "本样例把这些曲线收进报告，是为了证明 GROMACS 分段跑通，而不是证明 300 K 下已经「充分平衡到实验系综」。</p>",

  "<h3>3. 蛋白有没有散开</h3>",
  "<p>骨架 RMSD 均值为 <b>", md_fmt(mean_rmsd, 3), " nm</b>（末段 ", md_fmt(tail_rmsd, 3),
  " nm；峰值 ", md_fmt(max(rmsd_x), 3), " nm）。",
  "0.06–0.10 nm 的平台对溶菌酶短窗口是正常热涨落，没有出现纳米级展开。</p>",
  "<p>Rg 均值 <b>", md_fmt(mean_rg, 3), " nm</b>（SD ", md_fmt(sd_rg, 3),
  " nm，全距仅 ", md_fmt(max(rg_x) - min(rg_x), 3), " nm），整体紧实度几乎不变。",
  "SASA 均值 <b>", md_fmt(mean_sasa, 1), " nm²</b>（约 ", md_fmt(min(sasa_x), 1), "–", md_fmt(max(sasa_x), 1),
  " nm²），溶剂暴露只有小幅波动。</p>",
  "<p>Cα RMSF 均值 ", md_fmt(rmsf_mean, 3), " nm，最高点在残基 ", rmsf_max_res,
  "（", md_fmt(rmsf_max, 3), " nm），符合末端比核更软的常识；核区多数残基约 0.03–0.06 nm。</p>",

  "<h3>4. 配体还在不在口袋里</h3>",
  "<p>蛋白–配体质心距离均值 <b>", md_fmt(mean_com, 3), " nm</b>，全距 ", md_fmt(com_range, 3),
  " nm，没有出现突然拉到 &gt;2 nm 的逃逸。</p>",
  "<p>三线 RMSD：蛋白 ", md_fmt(tri_mean("Protein"), 3), " nm，配体 ", md_fmt(tri_mean("Ligand"), 3),
  " nm（峰值 ", md_fmt(tri_max("Ligand"), 3), " nm），复合物 ", md_fmt(tri_mean("Complex"), 3),
  " nm。配体有一帧冲到 ~0.22 nm，仍属口袋内姿态调整，不能读成解离。</p>",
  "<p>蛋白–配体氢键为 0 或 1 个/帧，均值 <b>", md_fmt(mean_hb, 2), "</b>（21 帧里大约一半帧有 1 个氢键）。",
  "L99A 空腔本来就是疏水口袋，结合不以持续氢键网络为主——这一点和后面的能量分解、LigPlot 一致。</p>",
  "<p>PyMOL 始/中/末快照上 JZ4 仍停在空腔。短窗口里「姿态还在」只是必要质控，不是亲和力证据。</p>",

  "<h3>5. MM-GBSA：范德华在付钱，溶剂化在找零</h3>",
  "<p>GB <code>igb=5</code>，", n_frames, " 帧平均，<b>未含 −TΔS</b>。",
  "TOTAL = <b>", sprintf("%.1f", dg_kj), " kJ/mol</b>（", sprintf("%.2f", dg_kcal),
  if (!is.na(dg_sd_kcal)) sprintf(" ± %.2f", dg_sd_kcal) else "",
  " kcal/mol）。符号为负，表示本方法下焓型结合分为负，但不能把它当成实验 ΔG 或对接打分的替代。</p>",
  "<p>分解（kJ/mol）：vdW ", sprintf("%.1f", be_val(vdw, "avg_kj")),
  "；静电 ", sprintf("%.1f", be_val(eel, "avg_kj")),
  "；极性溶剂化 EGB ", sprintf("%+.1f", be_val(egb, "avg_kj")),
  "；非极性溶剂化 ESurf ", sprintf("%.1f", be_val(esurf, "avg_kj")),
  "；GGAS ", sprintf("%.1f", be_val(ggas, "avg_kj")),
  "，GSOLV ", sprintf("%+.1f", be_val(gsolv, "avg_kj")),
  "。主导项是范德华；极性溶剂化把静电贡献抵消掉一大部分。这是疏水空腔包埋苯环配体的典型账本。</p>",
  "<p>逐残基最负的几项：", res_txt(1), "、", res_txt(2), "、", res_txt(3), "、",
  res_txt(4), "、", res_txt(5), "。",
  "配体自身一项最大，是分解惯例；蛋白侧 ALA99 正是 L99A 突变造出来的空腔壁，",
  "LEU118 / LEU84 / VAL111 是口袋疏水衬里。GLN102（M102Q）也在名单里，但贡献小于空腔疏水残基。",
  "残基 SD 很大（短采样），排序只适合当假设，不适合当热点突变清单。</p>",

  "<h3>6. LigPlot 与能量账互相印证</h3>",
  "<p>末帧 LigPlot 以疏水接触为主、未画出蛋白–配体氢键，与氢键时间序列（经常是 0）和 vdW 主导的 MM-GBSA 同一故事：",
  "<b>短窗口里 JZ4 靠形状互补和疏水接触待在 L99A 空腔，而不是靠一两条稳定氢键锁死。</b>",
  "LigPlot 是单帧 2D 示意，不能代替接触占用率或水桥统计。</p>",

  "<h3>7. 自由能形貌只能当流程图</h3>",
  "<p>2D/3D FEL 来自 ", n_frames, " 个点的 KDE（RMSD×Rg 及 RMSD×COM / SASA / 配体–蛋白 RMSD）。",
  "21 个点撑不满 60×60 网格，颜色深浅反映的是稀疏采样的密度，不是可逆功或真实能垒。",
  "<b>不要读「势阱深度」或「过渡态」。正式 FEL 需要微秒级或至少百纳秒级、充分投影、最好再加复现。</b></p>",

  "<h3>8. 这个样例证明了什么、没证明什么</h3>",
  "<ul class='compact'>",
  "<li><b>已证明：</b>3HTB 真实结构可以按本技能 SOP 跑通 GROMACS + GAFF2 + 分析出图 + Origin/LigPlot/PyMOL + MM-GBSA，并给出可核对的数字。</li>",
  "<li><b>未证明：</b>JZ4 的实验亲和力、相对其它配体的排序、口袋长期稳定、或任何可写入论文 Results 的 ΔG。</li>",
  "<li><b>若要把结论升级：</b>NS≥100（更好 ≥500）+ ≥3 条独立轨迹 + 熵项 + 接触占用率/水桥；必要时再上 ABF/umbrella 或 FEP。</li>",
  "</ul>"
)

figure_sections <- list(
  list(
    id = "eq",
    title = "平衡与生产质控",
    intro = "恒温/恒压/密度/势能只回答「模拟有没有跑飞」，不回答结合是否稳定。",
    layout = "grid2",
    items = keep(
      fig("NVT 温度", "08_NVT温度图", "08_NVT温度_NvtTemperature.png",
          "NVT 段温度随时间。用于确认 V-rescale 恒温器把体系拉到设定温度附近。",
          "读图时看是否在目标温度上下涨落，而不是看有没有生物学趋势。"),
      fig("NPT 温度", "09_NPT温度图", "09_NPT温度_NptTemperature.png",
          "NPT 段温度。与 NVT 衔接后的温度质控。"),
      fig("NPT 压力", "10_NPT压力图", "10_NPT压力_NptPressure.png",
          "NPT 段瞬时压力。Parrinello–Rahman 下单帧压力本来就会大幅振荡。",
          "不要把压力曲线的尖峰读成体系不稳定；应看密度是否收敛。"),
      fig("NPT 密度", "11_NPT密度图", "11_NPT密度_NptDensity.png",
          "NPT 段质量密度。溶剂盒体积稳定的直接指标。"),
      fig("生产势能", "12_生产势能图", "12_生产势能_MdPotential.png",
          paste0("生产段势能（", ns_lab, "）。"),
          "本窗口未见发散式上漂；更长轨迹仍要再查漂移和约束能量。",
          wide = TRUE)
    )
  ),
  list(
    id = "stab",
    title = "蛋白构象稳定性",
    intro = paste0("骨架 RMSD 均值 ", md_fmt(mean_rmsd, 3), " nm，Rg ", md_fmt(mean_rg, 3),
                   " nm，SASA ", md_fmt(mean_sasa, 1), " nm²。短窗口内蛋白保持紧实，没有展开。"),
    layout = "grid2",
    items = keep(
      fig("骨架 RMSD", "01_骨架RMSD图", "01_骨架RMSD_RmsdBackbone.png",
          "Backbone RMSD 相对 0 ns 参考结构。",
          paste0("均值 ", md_fmt(mean_rmsd, 3), " nm，末段 ", md_fmt(tail_rmsd, 3),
                 " nm。平台在 0.06–0.10 nm，是局部涨落而不是结构崩溃。")),
      fig("蛋白 / 配体 / 复合物 RMSD", "02_三线RMSD图", "02_三线RMSD_RmsdProteinLigandComplex.png",
          "三条 RMSD：蛋白、配体、复合物。",
          paste0("配体均值 ", md_fmt(tri_mean("Ligand"), 3), " nm，峰值 ",
                 md_fmt(tri_max("Ligand"), 3), " nm，仍在口袋内姿态变化范围。")),
      fig("Cα RMSF", "03_残基RMSF图", "03_残基RMSF_RmsfCalpha.png",
          "按残基的 Cα 波动。",
          paste0("最高点残基 ", rmsf_max_res, "（", md_fmt(rmsf_max, 3),
                 " nm），末端更软；核区多数低于 0.06 nm。")),
      fig("回旋半径", "05_回旋半径图", "05_回旋半径_RadiusGyration.png",
          "蛋白 Rg。",
          paste0("均值 ", md_fmt(mean_rg, 3), " nm，SD ", md_fmt(sd_rg, 3), " nm，整体体积几乎不变。")),
      fig("溶剂可及表面积", "06_溶剂可及表面积图", "06_溶剂可及表面积_Sasa.png",
          "蛋白 SASA。",
          paste0("均值 ", md_fmt(mean_sasa, 1), " nm²，波动约 6 nm² 量级，没有持续暴露增加。"),
          wide = TRUE)
    )
  ),
  list(
    id = "bind",
    title = "结合几何：还在口袋里吗",
    intro = paste0("质心距离均值 ", md_fmt(mean_com, 3), " nm；氢键均值 ", md_fmt(mean_hb, 2),
                   " 个/帧。配体未解离，但结合不以持续氢键为主。"),
    layout = "grid2",
    items = keep(
      fig("质心距离", "07_质心距离图", "07_质心距离_ComDistance.png",
          "蛋白–配体 COM 距离。",
          paste0("均值 ", md_fmt(mean_com, 3), " nm，全距 ", md_fmt(com_range, 3),
                 " nm。没有飞出口袋的判据。")),
      fig("氢键数", "04_氢键数图", "04_氢键数_HbondNum.png",
          "蛋白–配体氢键条数（阶梯图）。",
          paste0("0 或 1 个，均值 ", md_fmt(mean_hb, 2), "。疏水空腔的典型占用，不是「氢键锁死」。"))
    )
  ),
  list(
    id = "fel",
    title = "自由能形貌（21 点示意）",
    intro = "与 2D 同网格的 KDE。点太少，只能证明出图流程，不能读能垒或亚稳盆。",
    layout = "grid2",
    items = keep(
      fig("FEL · RMSD × Rg", "13_自由能形貌图", "13_自由能形貌_FreeEnergyLandscape.png",
          "投影：骨架 RMSD × Rg。Viridis，等值线关闭。"),
      fig("FEL · RMSD × COM", "14_自由能形貌RMSDx质心图", "14_自由能形貌RMSDx质心_FreeEnergyRmsdCom.png",
          "投影：RMSD × 质心距离。看结合松紧，不是景观热力学。"),
      fig("FEL · RMSD × SASA", "15_自由能形貌RMSDxSASA图", "15_自由能形貌RMSDxSASA_FreeEnergyRmsdSasa.png",
          "投影：RMSD × SASA。"),
      fig("FEL · 配体 RMSD × 蛋白 RMSD", "16_自由能形貌配体蛋白RMSD图",
          "16_自由能形貌配体蛋白RMSD_FreeEnergyLigandProteinRmsd.png",
          "谁在动：配体相对蛋白。"),
      fig("FEL 3D · RMSD × Rg", "17_自由能形貌3D图", "17_自由能形貌3D_FreeEnergyLandscape3D.png",
          "与 2D 同网格的 OpenGL 曲面。"),
      fig("FEL 3D · RMSD × COM", "18_自由能形貌3D_RMSDx质心图",
          "18_自由能形貌3D_RMSDx质心_FreeEnergyRmsdCom3D.png",
          "3D：RMSD × 质心距离。"),
      fig("FEL 3D · RMSD × SASA", "19_自由能形貌3D_RMSDxSASA图",
          "19_自由能形貌3D_RMSDxSASA_FreeEnergyRmsdSasa3D.png",
          "3D：RMSD × SASA。"),
      fig("FEL 3D · 配体 × 蛋白 RMSD", "20_自由能形貌3D_配体蛋白RMSD图",
          "20_自由能形貌3D_配体蛋白RMSD_FreeEnergyLigandProteinRmsd3D.png",
          "3D：配体 RMSD × 蛋白 RMSD。")
    )
  ),
  list(
    id = "mmgbsa",
    title = "MM-GBSA 结合自由能",
    intro = paste0("TOTAL = ", sprintf("%.1f kJ/mol", dg_kj), "（", sprintf("%.2f kcal/mol", dg_kcal),
                   "），vdW 主导，未含熵。数字可核对，结论不可当实验 ΔG。"),
    layout = "grid2",
    items = keep(
      fig("能量分解柱", "21_结合能分解图", "21_结合能分解_BindingEnergyDecomp.png",
          "vdW / 静电 / EGB / ESurf。",
          paste0("vdW ", sprintf("%.1f", be_val(vdw, "avg_kj")),
                 " kJ/mol 是主项；EGB ", sprintf("%+.1f", be_val(egb, "avg_kj")),
                 " kJ/mol 部分抵消静电。")),
      fig("标注柱", "22_结合能标注柱图", "22_结合能标注柱_BindingEnergyLabeled.png",
          "同分解，便于读数。"),
      fig("能量表", "23_结合能表图", "23_结合能表_BindingEnergyTable.png",
          "GGAS / GSOLV / TOTAL（kcal·mol⁻¹ 与 kJ·mol⁻¹）。",
          paste0("TOTAL ", sprintf("%.1f", dg_kj), " kJ/mol；无 −TΔS。")),
      fig("逐残基贡献", "24_残基能量贡献图", "24_残基能量贡献_ResidueEnergyContrib.png",
          "最负的残基（含配体 JZ4）。",
          paste0("蛋白侧最负：", res_txt(2), "、", res_txt(3), "、", res_txt(4),
                 "。ALA99 对应 L99A 空腔；其后为疏水衬里。残基 SD 大，排序仅供假设。"))
    )
  ),
  list(
    id = "snap",
    title = "轨迹快照与二维接触",
    intro = "PyMOL 三帧确认姿态仍在空腔；LigPlot 末帧以疏水接触为主、无氢键，与氢键时间序列和 vdW 主导一致。",
    layout = "grid3",
    items = keep(
      fig("快照 · 起点", "25_轨迹快照图", "25_轨迹快照始_SnapshotStart.png",
          "0 ns 附近：JZ4 在 L99A 空腔。"),
      fig("快照 · 中点", "25_轨迹快照图", "25_轨迹快照中_SnapshotMid.png",
          "轨迹中点。口袋内姿态可有小幅摆动。"),
      fig("快照 · 终点", "25_轨迹快照图", "25_轨迹快照末_SnapshotEnd.png",
          "0.20 ns：配体仍在腔内。"),
      fig("三帧拼图", "25_轨迹快照图", "25_轨迹快照拼图_TrajectorySnapshots.png",
          "始 / 中 / 末并排。演示窗口内未见解离。", wide = TRUE),
      fig("LigPlot 二维接触", "26_二维相互作用图", "26_二维相互作用_LigPlot2D.png",
          "末帧 LigPlot+：疏水接触为主。",
          "未画出蛋白–配体氢键，与氢键时间序列和 vdW 主导的 MM-GBSA 同一机制图像。单帧不能当占用率。",
          wide = TRUE)
    )
  )
)

rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
write_delivery_report(
  skill_en, skill_folder, status,
  data_html, audit_html,
  "运行复合物MD_runComplexMd.sh + 分析出图_plotMdAnalysis.R + Origin/LigPlot/PyMOL",
  figures = NULL,
  interpretation = interp,
  out_path = rep_file,
  version = "v1",
  kpis = kpis,
  figure_sections = figure_sections,
  methods_html = methods_html,
  caveats_html = caveats_html,
  subtitle = "T4 lysozyme L99A/M102Q + JZ4（PDB 3HTB）· GROMACS 2023.3 真实轨迹",
  lead_html = paste0(
    "生产 ", ns_lab, "，", n_frames, " 帧。图为 Origin / PyMOL / LigPlot 交付件；",
    "正文解读只陈述本窗口内的统计，并标明不能外推的部分。"
  )
)
message("WROTE report ", rep_file)
