
d <- read.csv(r"E:/RProject/生信分析技能_BioinformaticsSkills/07_分类验证_Validation/数据_data/toy_clinical_survival.csv")
if (requireNamespace("survival", quietly=TRUE)) {
  fit <- survival::survfit(survival::Surv(time, status) ~ group, data=d)
  cat("SURV_OK\n")
} else {
  cat("SURV_PKG_MISSING\n")
}
if (requireNamespace("pROC", quietly=TRUE)) {
  cat("PROC_OK\n")
} else {
  cat("PROC_PKG_MISSING\n")
}
