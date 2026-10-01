# Post-formal figure + analysis pipeline.
# Requires: all 5 subtype checkpoints OR STATUS_Formal.txt from script 13.
# Bridges Formal RDS into KoObjects names expected by 07/09, then re-runs
# enrichR / GSEA / PDF-STRING networks / paper-style panels.
options(stringsAsFactors = FALSE)
set.seed(20261001)

root <- "C:/Users/10540/Desktop/琪乐无穷/CPLX2虚拟敲除_Cplx2VirtualKO"
tab_dir <- file.path(root, "结果文件", "数据文件")
fig_dir <- file.path(root, "结果文件", "图片文件")
rep_dir <- file.path(root, "结果文件", "报告文件")
obj_formal <- file.path(tab_dir, "敲除对象_KoObjects_Formal")
obj_dir <- file.path(tab_dir, "敲除对象_KoObjects")
code_dir <- "E:/RProject/生信分析技能_BioinformaticsSkills/05_系统方法_SystemsMethods/虚拟敲除与扰动_InSilicoKO/02_课题交付_Cplx2Control/代码文件"
rscript <- "E:/R-4.6.0/bin/Rscript.exe"
subtypes <- c("cLTMR", "NF1", "NP", "PEP", "TRPM8")

dir.create(rep_dir, recursive = TRUE, showWarnings = FALSE)
message("=== PostFormal start ", format(Sys.time()), " ===")

is_done <- function(s) {
  rds <- file.path(obj_formal, paste0(s, "_Cplx2_formal.rds"))
  csv <- file.path(tab_dir, paste0("04_扰动基因_", s, "_Cplx2Dr_Formal.csv"))
  file.exists(rds) && file.exists(csv) && file.info(rds)$size > 1000
}
status_ok <- file.exists(file.path(rep_dir, "STATUS_Formal.txt")) &&
  grepl("FORMAL_COMPLETE", paste(readLines(file.path(rep_dir, "STATUS_Formal.txt"), warn = FALSE), collapse = "\n"))
done_n <- sum(vapply(subtypes, is_done, logical(1)))
if (!status_ok && done_n < length(subtypes)) {
  stop(sprintf(
    "Formal KO not ready: STATUS_Formal=%s done=%d/%d. Wait for script 13 to finish.",
    status_ok, done_n, length(subtypes)
  ))
}
message(sprintf("Formal ready: STATUS=%s checkpoints=%d/%d", status_ok, done_n, length(subtypes)))

# Ensure combined DR used by downstream is Formal (script 13 should already write this)
dr_formal_all <- file.path(tab_dir, "04_扰动基因_五亚群_Cplx2DrAll_Formal.csv")
dr_main <- file.path(tab_dir, "04_扰动基因_五亚群_Cplx2DrAll.csv")
if (file.exists(dr_formal_all)) {
  file.copy(dr_formal_all, dr_main, overwrite = TRUE)
  message("Refreshed main DR from Formal combined table")
} else if (!file.exists(dr_main)) {
  stop("Missing Formal DR table")
}

# Bridge Formal RDS -> KoObjects/{subtype}_Cplx2.rds (backup pilot once)
pilot_bak <- file.path(tab_dir, "_pilot_KoObjects_archive")
dir.create(pilot_bak, recursive = TRUE, showWarnings = FALSE)
dir.create(obj_dir, recursive = TRUE, showWarnings = FALSE)
for (s in subtypes) {
  src <- file.path(obj_formal, paste0(s, "_Cplx2_formal.rds"))
  dst <- file.path(obj_dir, paste0(s, "_Cplx2.rds"))
  if (file.exists(dst) && !file.exists(file.path(pilot_bak, basename(dst)))) {
    file.copy(dst, file.path(pilot_bak, basename(dst)), overwrite = FALSE)
  }
  if (!file.exists(src)) stop("Missing Formal RDS: ", src)
  file.copy(src, dst, overwrite = TRUE)
  message("bridged ", basename(src), " -> ", basename(dst))
}

# Archive pilot-era main figures once (do not delete Formal-tagged ones)
fig_bak <- file.path(fig_dir, "_pilot_figures_archive")
dir.create(fig_bak, recursive = TRUE, showWarnings = FALSE)
pilot_stems <- list.files(fig_dir, pattern = "\\.(png|svg)$", full.names = TRUE)
pilot_stems <- pilot_stems[!grepl("_Formal\\.|_pilot_|_deprecated", basename(pilot_stems))]
for (f in pilot_stems) {
  dest <- file.path(fig_bak, basename(f))
  if (!file.exists(dest)) file.copy(f, dest, overwrite = FALSE)
}

run_rscript <- function(script_name) {
  path <- file.path(code_dir, script_name)
  if (!file.exists(path)) stop("Missing script: ", path)
  message(">>> ", script_name, " @ ", format(Sys.time()))
  st <- system2(rscript, args = c("--vanilla", path), stdout = TRUE, stderr = TRUE)
  writeLines(st, file.path(rep_dir, paste0("14_log_", gsub("\\.R$", "", script_name), ".txt")))
  ok <- grepl("DONE|FIG_DONE|PDF_NETWORK_DONE|PDFSTYLE_DONE|HEAT_DONE", paste(st, collapse = "\n"))
  if (!is.null(attr(st, "status")) && attr(st, "status") != 0) {
    stop(script_name, " failed:\n", paste(tail(st, 40), collapse = "\n"))
  }
  message("<<< ", script_name, " ok_marker=", ok)
  invisible(st)
}

# 1) Jaccard + enrichR (+ Phase1 plots if still present) — reuse 02
run_rscript("02_补图_PlotAtlas.R")
# 2) Spaced synaptic GO bars
run_rscript("05_富集拉开_PlotEnrichSpaced.R")
# 3) Enrich panels + WT-adjacency networks
run_rscript("07_修正富集与网络_Redraw.R")
# 4) Paper-style Z vs edge / QQ / egocentric
run_rscript("09_按PDF图种_PlotPaperStyle.R")
# 5) GSEA curves + NES heatmap
run_rscript("10_GSEA曲线_PlotGsea.R")
run_rscript("11_GSEA热图_PlotNes.R")
# 6) PDF FDR+STRING networks (needs proxy for STRING)
run_rscript("12_PDF标准网络_PlotFdrString.R")

# Quick Formal significance summary
dr <- utils::read.csv(dr_main, check.names = FALSE, stringsAsFactors = FALSE)
sig <- dr[dr$gene != "Cplx2" & is.finite(dr$p.adj) & dr$p.adj < 0.05, , drop = FALSE]
sig_tab <- as.data.frame(table(sig$subtype), stringsAsFactors = FALSE)
names(sig_tab) <- c("subtype", "n_fdr05_excl_ko")
utils::write.csv(sig_tab, file.path(tab_dir, "14_正式显著计数_FormalSigCounts.csv"), row.names = FALSE)
utils::write.csv(sig, file.path(tab_dir, "14_正式显著明细_FormalSigDetail.csv"), row.names = FALSE)

writeLines(c(
  "STATUS=POST_FORMAL_COMPLETE",
  paste0("time=", format(Sys.time())),
  "source=formal_package_defaults",
  "scripts=02,05,07,09,10,11,12",
  paste0("n_FDR05_excl_KO=", nrow(sig)),
  paste0("by_subtype=", paste(paste(sig_tab$subtype, sig_tab$n_fdr05_excl_ko, sep = "="), collapse = ";")),
  "claim=computational prediction from formal scTenifoldKnk defaults; not wet-lab KO"
), file.path(rep_dir, "STATUS_PostFormal.txt"))

message("=== POST_FORMAL_DONE ", format(Sys.time()), " ===")
