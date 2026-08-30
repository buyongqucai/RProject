# 样例入口 — 分子动力学模拟_MolecularDynamics
# 流程：MD 计算在 WSL2/GROMACS 完成（见 技能说明 §9 SOP 与 脚本_scripts/运行复合物MD_runComplexMd.sh），
#       本脚本负责调用 R 分析出图（xvg → CSV/图/审计/报告）。
# data_provenance=REAL (RCSB PDB 3HTB)；analysis_kind=md_3htb
options(stringsAsFactors = FALSE)

sample_root <- normalizePath("..", winslash = "/", mustWork = TRUE)
md_dir <- file.path(sample_root, "工作文件_mdwork", "3HTB")
need <- file.path(md_dir, c("rmsd_backbone.xvg", "rmsf_calpha.xvg", "hbond_num.xvg", "gyrate.xvg"))

if (!all(file.exists(need))) {
  message("MD 轨迹分析输入未就绪。请先在 WSL2 跑流水线（幂等，断点续跑）：")
  message('  wsl -d Ubuntu-24.04 -- bash -c "cd <工作文件_mdwork/3HTB> && \\')
  message('    LIGAND_RES=JZ4 NET_CHARGE=0 NS=0.2 \\')
  message('    bash <技能根>/脚本_scripts/运行复合物MD_runComplexMd.sh . protein.pdb jz4_h.mol2"')
  quit(save = "no", status = 1)
}

source(file.path("分析出图_plotMdAnalysis.R"), encoding = "UTF-8")
