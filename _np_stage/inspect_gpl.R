suppressPackageStartupMessages(library(GEOquery))
for(gpl in c("GPL13158","GPL6244")){
 cat("\n===",gpl,"===\n")
 g<-getGEO(gpl)
 cat("rows",nrow(Table(g)),"cols",paste(colnames(Table(g)),collapse="|"),"\n")
 print(head(Table(g),3))
}
