suppressPackageStartupMessages(library(GEOquery))
for(gse in c("GSE92415","GSE75214")){
 es<-getGEO(filename=file.path("E:/RProject/_np_stage/geo_data",paste0(gse,"_series_matrix.txt.gz")),getGPL=FALSE)
 pd<-pData(es)
 cat("\n",gse,"n=",ncol(es),"platform=",as.character(unique(pd$platform_id)),"\n")
 for(col in intersect(c("disease:ch1","tissue:ch1","treatment:ch1","visit:ch1","wk6response:ch1","source_name_ch1","title"),colnames(pd))){
  cat("\n--",col,"--\n"); print(head(sort(table(pd[[col]],useNA="ifany"),decreasing=TRUE),30))
 }
 cat("feature rownames",paste(head(rownames(fData(es)),5),collapse=", "),"\n")
}
