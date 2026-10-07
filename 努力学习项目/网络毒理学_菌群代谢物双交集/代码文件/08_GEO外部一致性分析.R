root <- "E:/RProject/_np_stage"
source(file.path(root,"tools/PublicationPlot.R"))
source(file.path(root,"tools/PlotQA.R"))
suppressPackageStartupMessages({library(GEOquery);library(limma);library(pROC);library(dplyr);library(tidyr);library(ggrepel);library(patchwork)})
geo <- file.path(root,"geo_data"); out <- file.path(root,"geo_out"); dir.create(out,recursive=TRUE,showWarnings=FALSE)
core <- read.csv(file.path(root,"geo_data","C_main.csv"),fileEncoding="UTF-8",stringsAsFactors=FALSE)$gene
core <- unique(toupper(trimws(core)))

read_annot <- function(path){
 x <- readLines(gzfile(path),warn=FALSE,encoding="UTF-8")
 s <- match("!platform_table_begin",x)+1L; e <- match("!platform_table_end",x)-1L
 read.delim(text=paste(x[s:e],collapse="\n"),sep="\t",quote="",stringsAsFactors=FALSE,check.names=FALSE)
}
a13158 <- read_annot(file.path(geo,"GPL13158.annot.gz"))
a6244 <- read_annot(file.path(geo,"GPL6244.annot.gz"))
map13158 <- setNames(toupper(trimws(a13158[["Gene symbol"]])),a13158[["ID"]])
map6244 <- setNames(toupper(trimws(a6244[["Gene symbol"]])),a6244[["ID"]])

prep <- function(gse, ann_table, group_fun){
 es <- getGEO(filename=file.path(geo,paste0(gse,"_series_matrix.txt.gz")),getGPL=FALSE)
 pd <- pData(es); ex <- exprs(es)
  sel <- group_fun(pd)
  keep <- as.logical(unlist(sel$keep))
  pd <- pd[keep,,drop=FALSE]; ex <- ex[,keep,drop=FALSE]; group_values <- as.character(unlist(sel$group))[keep]
  ann_idx <- match(rownames(ex), ann_table[["ID"]])
  sym <- toupper(trimws(as.character(ann_table[["Gene symbol"]][ann_idx])))
 valid <- !is.na(sym) & nzchar(sym) & sym %in% core
 ex <- ex[valid,,drop=FALSE]; sym <- sym[valid]
 # median summarize multiple probes per gene
 genes <- sort(unique(sym))
 mat <- sapply(genes,function(g) apply(ex[sym==g,,drop=FALSE],2,median,na.rm=TRUE))
 mat <- t(mat)
 group <- factor(group_values,levels=c("Control","UC"))
 design <- model.matrix(~group)
 fit <- eBayes(lmFit(mat,design))
 tt <- topTable(fit,coef=2,number=Inf,sort.by="none")
 res <- data.frame(gene=rownames(mat),logFC=tt$logFC,AveExpr=tt$AveExpr,t=tt$t,P.Value=tt$P.Value,adj.P.Val=tt$adj.P.Val,dataset=gse,stringsAsFactors=FALSE)
 sample_audit <- data.frame(dataset=gse,geo_accession=rownames(pd),title=pd$title,group=as.character(group),stringsAsFactors=FALSE)
 list(es=es,pd=pd,mat=mat,group=group,res=res,audit=sample_audit)
}

g92 <- prep("GSE92415",a13158,function(pd){
 g <- ifelse(pd[["disease:ch1"]]=="Healthy","Control",ifelse(pd[["disease:ch1"]]=="Ulcerative Colitis (UC)" & pd[["visit:ch1"]]=="Week 0","UC",NA))
 list(keep=!is.na(g),group=g)
})
g75 <- prep("GSE75214",a6244,function(pd){
 src <- pd[["source_name_ch1"]]
 g <- ifelse(grepl("inflamed colonic mucosa of active UC",src,fixed=TRUE) & pd[["tissue:ch1"]]=="colon","UC",ifelse(grepl("normal colonic mucosa of control",src,fixed=TRUE) & pd[["tissue:ch1"]]=="colon","Control",NA))
 list(keep=!is.na(g),group=g)
})

audit <- rbind(g92$audit,g75$audit)
write.csv(audit,file.path(out,"GEO_sample_audit.csv"),row.names=FALSE,fileEncoding="UTF-8")
comb <- merge(g92$res,g75$res,by="gene",suffixes=c("_GSE92415","_GSE75214"))
comb$direction_consistent <- sign(comb$logFC_GSE92415)==sign(comb$logFC_GSE75214)
comb$both_fdr05 <- comb$adj.P.Val_GSE92415<0.05 & comb$adj.P.Val_GSE75214<0.05 & comb$direction_consistent
comb$min_abs_logFC <- pmin(abs(comb$logFC_GSE92415),abs(comb$logFC_GSE75214))
write.csv(comb,file.path(out,"GEO_core_gene_consistency.csv"),row.names=FALSE,fileEncoding="UTF-8")

calc_auc <- function(mat,group,genes,orient=NULL){
 y <- as.integer(group=="UC")
 out <- lapply(genes,function(g){
  x <- as.numeric(mat[g,])
  roc_obj <- suppressMessages(roc(y,x,quiet=TRUE,ci=TRUE))
  ci <- as.numeric(ci.auc(roc_obj))
  data.frame(gene=g,auc=as.numeric(auc(roc_obj)),ci_low=ci[1],ci_high=ci[3],p_direction=ifelse(median(x[y==1])>median(x[y==0]),"UC_high","UC_low"))
 })
 do.call(rbind,out)
}
auc92 <- calc_auc(g92$mat,g92$group,comb$gene)
auc75 <- calc_auc(g75$mat,g75$group,comb$gene)
auc92$dataset <- "GSE92415"; auc75$dataset <- "GSE75214"
auc <- rbind(auc92,auc75)
write.csv(auc,file.path(out,"GEO_gene_AUC.csv"),row.names=FALSE,fileEncoding="UTF-8")

# Panel score oriented by GSE92415 discovery logFC and evaluated in both sets.
orient <- setNames(sign(g92$res$logFC),g92$res$gene)
score_panel <- function(x){
 z <- t(scale(t(x)))
 vapply(seq_len(ncol(z)),function(j) mean(z[,j]*orient[rownames(z)],na.rm=TRUE),numeric(1))
}
s92 <- score_panel(g92$mat); s75 <- score_panel(g75$mat)
r92 <- suppressMessages(roc(as.integer(g92$group=="UC"),s92,quiet=TRUE,ci=TRUE)); c92 <- as.numeric(ci.auc(r92))
r75 <- suppressMessages(roc(as.integer(g75$group=="UC"),s75,quiet=TRUE,ci=TRUE)); c75 <- as.numeric(ci.auc(r75))
panel_auc <- data.frame(dataset=c("GSE92415","GSE75214"),panel="all 78 C genes oriented by GSE92415",auc=c(as.numeric(auc(r92)),as.numeric(auc(r75))),ci_low=c(c92[1],c75[1]),ci_high=c(c92[3],c75[3]),n=c(length(s92),length(s75)))
write.csv(panel_auc,file.path(out,"GEO_panel_AUC.csv"),row.names=FALSE,fileEncoding="UTF-8")

volcano_plot <- function(res,title){
 d <- res; d$.neg <- -log10(pmax(d$adj.P.Val,.Machine$double.xmin)); d$.class <- ifelse(d$adj.P.Val<0.05 & d$logFC>=0.5,"Up",ifelse(d$adj.P.Val<0.05 & d$logFC<=-0.5,"Down","NS"))
 d$label <- ifelse(d$gene %in% head(d$gene[order(d$adj.P.Val)],12),d$gene,NA)
 ggplot(d,aes(x=logFC,y=.neg,color=.class))+geom_point(size=1.8,alpha=0.85)+geom_vline(xintercept=c(-0.5,0.5),linetype=2,color="grey55")+geom_hline(yintercept=-log10(0.05),linetype=2,color="grey55")+geom_text_repel(aes(label=label),size=2.7,max.overlaps=20,show.legend=FALSE)+scale_color_manual(values=c(Up="#C0392B",Down="#1A7A6D",NS="#BDBDBD"),name=NULL)+labs(title=title,x="log2 fold change",y="-log10(adjusted P)")+theme_journal()
}
p1 <- volcano_plot(g92$res,"GSE92415: UC vs healthy")
save_plot_pub(p1,stem="01_GSE92415_Volcano",width=7.2,height=6.5,dpi=600,out_dir=out);viz_qa_after_plot(p1,plot_id="GSE92415_VOL",hard_fail=FALSE)
p2 <- volcano_plot(g75$res,"GSE75214: active UC vs control")
save_plot_pub(p2,stem="02_GSE75214_Volcano",width=7.2,height=6.5,dpi=600,out_dir=out);viz_qa_after_plot(p2,plot_id="GSE75214_VOL",hard_fail=FALSE)

top <- comb[order(-comb$min_abs_logFC),]$gene
top <- head(top,20)
heat_plot <- function(obj,genes,title){
 z <- t(scale(t(obj$mat[genes,,drop=FALSE])))
 dd <- as.data.frame(as.table(z)); colnames(dd)<-c("gene","sample","z")
 dd$gene <- factor(dd$gene,levels=rev(genes))
 ggplot(dd,aes(x=sample,y=gene,fill=z))+geom_tile(color="white",linewidth=0.15)+scale_fill_gradient2(low="#2166AC",mid="white",high="#B2182B",midpoint=0,name="Z-score")+labs(title=title,x=NULL,y=NULL)+theme_journal()+theme(axis.text.x=element_blank(),axis.text.y=element_text(size=6.5),legend.position="bottom")
}
p3 <- heat_plot(g92,top,"GSE92415 core-gene heatmap")+heat_plot(g75,top,"GSE75214 core-gene heatmap")+plot_layout(ncol=1)
save_plot_pub(p3,stem="03_GEO_CoreGeneHeatmaps",width=9.5,height=10.5,dpi=600,out_dir=out);viz_qa_after_plot(p3,plot_id="GEO_HEATMAP",hard_fail=FALSE)

forest <- auc %>% mutate(gene=factor(gene,levels=rev(unique(gene))),label=sprintf("%.2f (%.2f-%.2f)",auc,ci_low,ci_high))
p4 <- ggplot(forest,aes(x=auc,y=gene,color=dataset))+geom_point(size=2.2,position=position_dodge(width=0.55))+geom_errorbarh(aes(xmin=ci_low,xmax=ci_high),height=0.18,position=position_dodge(width=0.55))+geom_vline(xintercept=0.5,linetype=2,color="grey55")+scale_color_manual(values=c(GSE92415="#4F81BD",GSE75214="#C17B7B"),name=NULL)+coord_cartesian(xlim=c(0,1))+labs(title="Exploratory gene AUCs",x="AUC (95% CI)",y=NULL)+theme_journal()+theme(legend.position="bottom")
save_plot_pub(p4,stem="04_GEO_GeneAUCForest",width=8.2,height=9,dpi=600,out_dir=out);viz_qa_after_plot(p4,plot_id="GEO_AUC",hard_fail=FALSE)

summary <- data.frame(
 dataset=c("GSE92415","GSE75214"),n_control=c(sum(g92$group=="Control"),sum(g75$group=="Control")),n_uc=c(sum(g92$group=="UC"),sum(g75$group=="UC")),
 genes=c(nrow(g92$res),nrow(g75$res)),
 consistent_direction=sum(comb$direction_consistent,na.rm=TRUE),
 both_fdr05_same_direction=sum(comb$both_fdr05,na.rm=TRUE),
 panel_auc=panel_auc$auc,panel_ci_low=panel_auc$ci_low,panel_ci_high=panel_auc$ci_high
)
write.csv(summary,file.path(out,"GEO_analysis_summary.csv"),row.names=FALSE,fileEncoding="UTF-8")
print(summary)
print(panel_auc)
