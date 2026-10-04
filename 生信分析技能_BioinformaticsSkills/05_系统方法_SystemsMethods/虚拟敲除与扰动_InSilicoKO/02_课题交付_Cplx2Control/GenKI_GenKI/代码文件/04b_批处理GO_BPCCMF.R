# Batch re-run GO BP/CC/MF for every GenKI gene that already has a response table.
options(stringsAsFactors = FALSE)
root <- "C:/Users/10540/Desktop/琪乐无穷/虚拟敲除/结果文件"
enrich_r <- "E:/RProject/生信分析技能_BioinformaticsSkills/05_系统方法_SystemsMethods/虚拟敲除与扰动_InSilicoKO/02_课题交付_Cplx2Control/GenKI_GenKI/代码文件/04_焦点通路_EnrichResponse.R"
rscript <- "E:/R-4.6.0/bin/Rscript.exe"
n <- 0L
for (subtype in c("PEP", "NF1")) {
  base <- file.path(root, subtype, "GenKI")
  if (!dir.exists(base)) next
  for (gene in list.dirs(base, full.names = FALSE, recursive = FALSE)) {
    if (startsWith(gene, "_") || grepl("烟测|未采用", gene)) next
    resp <- file.path(base, gene, "数据文件", "响应基因_Responsive.csv")
    if (!file.exists(resp)) next
    out <- file.path(base, gene, "数据文件", "富集_GO.csv")
    message("GO ", subtype, " ", gene)
    status <- system2(rscript, c("--encoding=UTF-8", enrich_r, resp, out, gene), stdout = TRUE, stderr = TRUE)
    writeLines(status)
    n <- n + 1L
  }
}
message("GO_BATCH_DONE n=", n)
