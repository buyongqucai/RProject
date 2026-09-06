# 医学 SRMA：从 HR + 95%CI 准备输入并 REML 随机效应合并
# 依赖：metafor

#' 从提取表筛结局并计算 yi=log(HR), vi=se^2
prepare_hr_rows <- function(df, outcome = "OS") {
  stopifnot(all(c("study_id", "hr", "hr_lo", "hr_hi", "outcome") %in% names(df)))
  out <- df[df$outcome %in% outcome, , drop = FALSE]
  if (!nrow(out)) stop("无结局行: ", paste(outcome, collapse = "/"), call. = FALSE)
  out$hr <- as.numeric(out$hr)
  out$hr_lo <- as.numeric(out$hr_lo)
  out$hr_hi <- as.numeric(out$hr_hi)
  out$n_intervention <- as.integer(out$n_intervention)
  out$n_control <- as.integer(out$n_control)
  # SE of logHR from CI: (log(hi)-log(lo))/(2*1.96)
  out$yi <- log(out$hr)
  out$sei <- (log(out$hr_hi) - log(out$hr_lo)) / (2 * 1.96)
  out$vi <- out$sei^2
  out$n_total <- out$n_intervention + out$n_control
  # Short English labels for PlotQA (avoid long subtitles on figure)
  out$label <- gsub("_", " ", out$study_id)
  rownames(out) <- NULL
  out
}

#' REML 随机效应合并
pool_hr_reml <- function(dat) {
  metafor::rma(yi = yi, vi = vi, data = dat, method = "REML", slab = label)
}

#' 汇总一行结果表
summarize_pool <- function(fit, dat, label = "OS") {
  data.frame(
    outcome = label,
    k = fit$k,
    n_total = sum(dat$n_total, na.rm = TRUE),
    hr = exp(as.numeric(fit$b)),
    hr_lo = exp(as.numeric(fit$ci.lb)),
    hr_hi = exp(as.numeric(fit$ci.ub)),
    i2 = as.numeric(fit$I2),
    tau2 = as.numeric(fit$tau2),
    q = as.numeric(fit$QE),
    q_p = as.numeric(fit$QEp),
    model = "REML random-effects",
    stringsAsFactors = FALSE
  )
}

#' 留一法敏感性
leave_one_out_hr <- function(dat) {
  rows <- lapply(seq_len(nrow(dat)), function(i) {
    d <- dat[-i, , drop = FALSE]
    fit <- pool_hr_reml(d)
    data.frame(
      omitted = dat$study_id[[i]],
      k = fit$k,
      hr = exp(as.numeric(fit$b)),
      hr_lo = exp(as.numeric(fit$ci.lb)),
      hr_hi = exp(as.numeric(fit$ci.ub)),
      i2 = as.numeric(fit$I2),
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, rows)
}
