suppressPackageStartupMessages(library(GEOquery))
read_annot <- function(path){x<-readLines(gzfile(path),warn=FALSE,encoding="UTF-8");s<-match("!platform_table_begin",x)+1L;e<-match("!platform_table_end",x)-1L;read.delim(text=paste(x[s:e],collapse="\n"),sep="\t",quote="",stringsAsFactors=FALSE,check.names=FALSE)}
a<-read_annot('E:/RProject/_np_stage/geo_data/GPL13158.annot.gz'); m<-setNames(toupper(trimws(a[['Gene symbol']])),a[['ID']])
f<-function(ann_map){cat('class in f',class(ann_map),typeof(ann_map),'\n'); es<-getGEO(filename='E:/RProject/_np_stage/geo_data/GSE92415_series_matrix.txt.gz',getGPL=FALSE); ex<-exprs(es); cat('map subset class',class(ann_map[rownames(ex)]),typeof(ann_map[rownames(ex)]),'\n')}
f(m)
