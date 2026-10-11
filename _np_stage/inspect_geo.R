suppressPackageStartupMessages(library(GEOquery))
for (gse in c("GSE92415","GSE75214")) {
  es <- getGEO(filename=file.path("E:/RProject/_np_stage/geo_data",paste0(gse,"_series_matrix.txt.gz")),getGPL=FALSE)
  pd <- pData(es)
  cat("\n====",gse,"samples",ncol(es),"features",nrow(es),"====\n")
  print(colnames(pd))
  cols <- intersect(c("title","source_name_ch1","characteristics_ch1","characteristics_ch1.1","characteristics_ch1.2","description"),colnames(pd))
  print(pd[,cols,drop=FALSE])
  cat("FEATURE COLS\n"); print(colnames(fData(es)))
  print(head(fData(es),2))
}
