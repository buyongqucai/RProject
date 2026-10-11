root <- "E:/RProject/_np_stage"
source(file.path(root,"tools/PublicationPlot.R"))
source(file.path(root,"tools/PlotQA.R"))
library(ggplot2); library(tidyr); library(dplyr); library(ggrepel)
td <- file.path(root,"tox_data"); out <- file.path(root,"tox_out"); dir.create(out,recursive=TRUE,showWarnings=FALSE)
exp <- read.csv(file.path(td,"exposures.csv"),stringsAsFactors=FALSE,check.names=FALSE,fileEncoding="UTF-8")
pairs <- read.csv(file.path(td,"pairs.csv"),stringsAsFactors=FALSE,check.names=FALSE,fileEncoding="UTF-8")
exp$label <- factor(exp$label,levels=rev(exp$label))
long <- exp %>% select(label,ctd_human_gene_count,ctd_gene_overlap_I1,ctd_gene_overlap_C) %>%
 pivot_longer(-label,names_to="metric",values_to="count") %>%
 mutate(metric=factor(metric,levels=c("ctd_human_gene_count","ctd_gene_overlap_I1","ctd_gene_overlap_C"),labels=c("CTD genes","Overlap I1","Overlap C")))
p1 <- ggplot(long,aes(x=label,y=log10(1+count),fill=metric))+geom_col(position=position_dodge(0.72),width=0.72)+
 scale_fill_manual(values=c("CTD genes"="#6B8F71","Overlap I1"="#D4A574","Overlap C"="#C17B7B"),name="Metric")+
 geom_text(data=long,aes(label=count),position=position_dodge(0.72),hjust=-0.15,size=2.5,color="grey15")+
 coord_flip(ylim=c(0,4.35))+labs(title="Toxic exposure coverage",x=NULL,y="log10(1 + count)")+theme_journal()+theme(legend.position="bottom")
save_plot_pub(p1,stem="01_ToxicExposureCoverage",width=8.2,height=6.8,dpi=600,out_dir=out);viz_qa_after_plot(p1,plot_id="TOX_COVERAGE",hard_fail=FALSE)

cp <- pairs[pairs$in_C %in% c(TRUE,"True","true"),]
gene_counts <- sort(table(cp$gene),decreasing=TRUE)
top_genes <- names(head(gene_counts,20))
cp20 <- cp[cp$gene %in% top_genes,]
node_exp <- data.frame(id=paste0("E:",unique(cp20$exposure)),label=unique(cp20$exposure),type="Exposure",x=1,stringsAsFactors=FALSE)
node_gene <- data.frame(id=paste0("G:",top_genes),label=top_genes,type="Target",x=2,stringsAsFactors=FALSE)
node_exp <- node_exp[order(node_exp$label),]; node_exp$y <- seq(1,nrow(node_exp),length.out=nrow(node_exp))
node_gene <- node_gene[order(node_gene$label),]; node_gene$y <- seq(1,nrow(node_gene),length.out=nrow(node_gene))
nodes <- rbind(node_exp,node_gene)
edges <- unique(data.frame(from=paste0("E:",cp20$exposure),to=paste0("G:",cp20$gene),exposure=cp20$exposure,stringsAsFactors=FALSE))
edges$x <- nodes$x[match(edges$from,nodes$id)]; edges$y <- nodes$y[match(edges$from,nodes$id)]
edges$xend <- nodes$x[match(edges$to,nodes$id)]; edges$yend <- nodes$y[match(edges$to,nodes$id)]
pal <- setNames(c("#4D9221","#D4A574","#C17B7B","#4F81BD","#8B7BA8","#B07AA1","#7F7F7F"),unique(cp20$exposure))
p2 <- ggplot()+geom_segment(data=edges,aes(x=x,y=y,xend=xend,yend=yend,color=exposure),linewidth=0.32,alpha=0.55)+
 geom_point(data=nodes,aes(x=x,y=y,fill=type,shape=type),size=5,color="grey20",stroke=0.28)+
 geom_text_repel(data=nodes,aes(x=x,y=y,label=label),size=2.6,direction="y",segment.color="grey80",segment.size=0.2,max.overlaps=100,box.padding=0.3)+
 scale_x_continuous(breaks=c(1,2),labels=c("Harmful exposure","Shared target"),limits=c(0.75,2.25))+
 scale_fill_manual(values=c(Exposure="#D4A574",Target="#C17B7B"),guide="none")+scale_shape_manual(values=c(Exposure=21,Target=23),guide="none")+
 scale_color_manual(values=pal,name="Exposure")+labs(title="Toxic exposure-target clues",subtitle="CTD curated targets overlapping C",x=NULL,y=NULL)+theme_journal()+
 theme(axis.text.y=element_blank(),axis.ticks=element_blank(),panel.grid.major=element_blank(),legend.position="bottom")
save_plot_pub(p2,stem="02_ToxicExposureTargetNetwork",width=9.2,height=7.8,dpi=600,out_dir=out);viz_qa_after_plot(p2,plot_id="TOX_NETWORK",hard_fail=FALSE)

cp20$increases <- lengths(regmatches(cp20$interaction_actions,gregexpr("increases",cp20$interaction_actions,ignore.case=TRUE)))
cp20$decreases <- lengths(regmatches(cp20$interaction_actions,gregexpr("decreases",cp20$interaction_actions,ignore.case=TRUE)))
score <- aggregate(increases-decreases ~ exposure+gene,data=cp20,FUN=sum)
names(score)[3] <- "direction_score"
score$gene <- factor(score$gene,levels=top_genes)
score$exposure <- factor(score$exposure,levels=rev(unique(cp20$exposure)))
p3 <- ggplot(score,aes(x=gene,y=exposure,fill=direction_score))+geom_tile(color="white",linewidth=0.35)+
 geom_text(aes(label=direction_score),color="#000000",size=2.6)+
 scale_fill_gradient2(low="#2166AC",mid="white",high="#B2182B",midpoint=0,name="Increase−decrease")+
 labs(title="Curated action direction clues",x=NULL,y=NULL)+theme_journal()+theme(axis.text.x=element_text(angle=45,hjust=1,size=7.5),axis.text.y=element_text(size=7.5),legend.position="bottom")
save_plot_pub(p3,stem="03_ToxicDirectionHeatmap",width=9.2,height=6.8,dpi=600,out_dir=out);viz_qa_after_plot(p3,plot_id="TOX_HEATMAP",hard_fail=FALSE)
print(c(exposures=nrow(exp),pairs=nrow(pairs),overlap_C=sum(pairs$in_C %in% c(TRUE,"True","true")),top_genes=length(top_genes)))
