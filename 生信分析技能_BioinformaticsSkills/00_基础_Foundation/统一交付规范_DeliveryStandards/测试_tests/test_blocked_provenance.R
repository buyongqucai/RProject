# 议题 01：BLOCKED 样例 provenance 行为契约
# 接缝：write_delivery_audit() 的 data_provenance 行为 + BLOCKED 样例模板调用约定
library(testthat)

this_file <- tryCatch(
  normalizePath(sys.frame(1)$ofile, winslash = "/"),
  error = function(e) normalizePath("test_blocked_provenance.R", winslash = "/", mustWork = TRUE)
)
tests_dir <- dirname(this_file)
skill_dir <- dirname(tests_dir)
source(file.path(skill_dir, "脚本_scripts", "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
source(file.path(skill_dir, "脚本_scripts", "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")

test_that("BLOCKED provenance 强制 toy=FALSE", {
  out <- file.path(tempdir(), "audit_blocked.csv")
  write_delivery_audit(
    "MolecularDocking", "post",
    n_rows = 3, n_cols = 3, n_samples = 0,
    group_source = "n/a BLOCKED",
    notes = "BLOCKED: test",
    out_path = out,
    data_provenance = "BLOCKED"
  )
  df <- read.csv(out, stringsAsFactors = FALSE, fileEncoding = "UTF-8")
  expect_equal(df$data_provenance, "BLOCKED")
  expect_false(df$toy)
})

test_that("所有 BLOCKED 样例模板显式标注 provenance", {
  bio_root <- normalizePath(file.path(skill_dir, "..", ".."), winslash = "/")
  samples <- list.files(bio_root, pattern = "run_sample[.]R$", recursive = TRUE, full.names = TRUE)
  blocked <- samples[vapply(samples, function(f) {
    any(grepl('status\\s*(<-|=)\\s*"BLOCKED"', readLines(f, warn = FALSE, encoding = "UTF-8")))
  }, logical(1))]
  expect_gt(length(blocked), 0)
  for (f in blocked) {
    txt <- paste(readLines(f, warn = FALSE, encoding = "UTF-8"), collapse = "\n")
    expect_true(
      grepl('data_provenance\\s*=\\s*"BLOCKED"', txt),
      info = paste("缺 data_provenance=\"BLOCKED\":", f)
    )
    expect_false(
      grepl("toy=TRUE</b>", txt, fixed = TRUE),
      info = paste("BLOCKED 样例仍宣称 toy=TRUE 模拟数据:", f)
    )
  }
})
