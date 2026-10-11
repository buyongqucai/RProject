root <- "E:/RProject/_np_stage"
source(file.path(root,"tools/PublicationPlot.R"))
source(file.path(root,"tools/PlotQA.R"))
library(ggrepel)
mech <- file.path(root,"mech"); fig <- file.path(root,"out/figures"); dir.create(fig,recursive=TRUE,showWarnings=FALSE)
nodes <- read.csv(file.path(mech,"nodes.csv"),stringsAsFactors=FALSE,check.names=FALSE,fileEncoding="UTF-8")
edges <- read.csv(file.path(mech,"edges.csv"),stringsAsFactors=FALSE,check.names=FALSE,fileEncoding="UTF-8")
metrics <- read.csv(file.path(mech,"ppi_metrics.csv"),stringsAsFactors=FALSE,check.names=FALSE,fileEncoding="UTF-8")
layer_x <- c(GutMicrobe=1, Metabolite=2, Compound=3, Target=4, Pathway=5)
layer_label <- c("Gut microbe","Metabolite","Compound","Target","Pathway")
nodes$x <- layer_x[nodes$type]
nodes$y <- NA_real_
nodes <- nodes[order(nodes$layer,-nodes$score,nodes$label),]
for(tp in unique(nodes$type)){idx<-which(nodes$type==tp); nodes$y[idx]<-seq(1,length(idx),length.out=length(idx))}
short_label <- function(x,n=28){x<-as.character(x);ifelse(nchar(x)>n,paste0(substr(x,1,n-3),"..."),x)}
nodes$label_plot <- short_label(nodes$label,28)
edges$x <- nodes$x[match(edges$source,nodes$id)]; edges$y <- nodes$y[match(edges$source,nodes$id)]
edges$xend <- nodes$x[match(edges$target,nodes$id)]; edges$yend <- nodes$y[match(edges$target,nodes$id)]
edge_cols <- c(G_M="#4D9221",M_T="#D4A574",C_T="#4F81BD",T_P="#8B7BA8")
p <- ggplot()+
  geom_segment(data=edges,aes(x=x,y=y,xend=xend,yend=yend,color=edge_type),linewidth=0.32,alpha=0.38)+
  geom_point(data=nodes,aes(x=x,y=y,fill=type,shape=type),size=5.0,color="grey20",stroke=0.28)+
  geom_text_repel(data=nodes,aes(x=x,y=y,label=label_plot),size=2.15,direction="y",segment.color="grey75",segment.size=0.18,max.overlaps=100,box.padding=0.22,point.padding=0.18,min.segment.length=0)+
  scale_x_continuous(breaks=1:5,labels=layer_label,limits=c(0.65,5.35),expand=c(0.02,0.02))+
  scale_fill_manual(values=c(GutMicrobe="#4D9221",Metabolite="#D4A574",Compound="#4F81BD",Target="#C17B7B",Pathway="#8B7BA8"),guide="none")+
  scale_shape_manual(values=c(GutMicrobe=21,Metabolite=21,Compound=22,Target=23,Pathway=24),guide="none")+
  scale_color_manual(values=edge_cols,name="Edge")+
  labs(title="G-M-C-T-P shared network",subtitle="Top-ranked nodes; evidence-derived edges",x=NULL,y=NULL)+
  theme_journal()+
  theme(axis.text.x=element_text(face="bold",size=10),axis.text.y=element_blank(),axis.ticks=element_blank(),panel.grid.major=element_blank(),legend.position="bottom")
save_plot_pub(p,stem="05_GctpmNetwork",width=10.5,height=8.2,dpi=600,out_dir=fig);viz_qa_after_plot(p,plot_id="GCTPM",hard_fail=FALSE)

top <- head(metrics[order(-metrics$mcc_like_degree_x_triangles,-metrics$degree),],20)
top$gene <- factor(top$gene,levels=rev(top$gene))
ph <- ggplot(top,aes(x=mcc_like_degree_x_triangles,y=gene,fill=degree))+geom_col(width=0.72)+scale_fill_gradientn(colours=c("#FFFFCC","#78C679","#006837"),name="Degree")+labs(title="Top PPI hubs",x="MCC-like score",y=NULL)+theme_journal()+theme(legend.position="right")
save_plot_pub(ph,stem="06_PpiHubBar",width=6.8,height=6.2,dpi=600,out_dir=fig);viz_qa_after_plot(ph,plot_id="PPIHUB",hard_fail=FALSE)
print(c(nodes=nrow(nodes),edges=nrow(edges),metrics=nrow(metrics)))

