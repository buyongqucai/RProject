options(repos=c(CRAN="https://cloud.r-project.org"))
pkgs <- c("remotes","devtools","data.table","dplyr","ggplot2","ieugwasr","TwoSampleMR")
for (p in c("remotes","devtools","data.table","dplyr","ggplot2")) {
  if (!requireNamespace(p, quietly=TRUE)) install.packages(p, Ncpus=4)
}
if (!requireNamespace("ieugwasr", quietly=TRUE)) remotes::install_github("MRCIEU/ieugwasr")
if (!requireNamespace("TwoSampleMR", quietly=TRUE)) remotes::install_github("MRCIEU/TwoSampleMR")
cat("TwoSampleMR=", requireNamespace("TwoSampleMR", quietly=TRUE), "\n")
cat("ieugwasr=", requireNamespace("ieugwasr", quietly=TRUE), "\n")
