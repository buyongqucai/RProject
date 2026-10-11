root <- "E:/RProject/_np_stage"
source(file.path(root,"tools/PublicationPlot.R"))
source(file.path(root,"tools/PlotQA.R"))
source(file.path(root,"tools/StringNetwork.R"))
source(file.path(root,"tools/DeliveryNetworkLayouts.R"))
.np_ensure_plotqa <- function(...) TRUE
library(ggplot2); library(stringr)
dd <- file.path(root,"delivery_data"); out <- file.path(root,"delivery_out"); dir.create(out,recursive=TRUE,showWarnings=FALSE)
kegg <- read.csv(file.path(dd,"kegg.csv"),stringsAsFactors=FALSE,check.names=FALSE,fileEncoding="UTF-8")
kegg <- kegg[order(kegg$p.adjust,kegg$Description),]
top <- head(kegg,30)
top$neglog10 <- -log10(pmax(top$p.adjust,.Machine$double.xmin))
labels <- str_wrap(top$Description,width=32)
top$term <- factor(labels,levels=rev(labels))
p <- ggplot(top,aes(x=neglog10,y=term,size=Count,color=neglog10))+geom_point(alpha=0.92)+
 scale_color_gradientn(colours=bioinfo_sequential_blue,name="AdjP")+
 scale_size_continuous(name="n",range=c(2.2,7.5),breaks=pretty(range(top$Count),3))+
 scale_x_continuous(expand=expansion(mult=c(0.06,0.18)))+
 labs(title="KEGG enrichment",x="-log10(Padj)",y=NULL)+theme_journal()+
 theme(axis.text.y=element_text(size=7.2,lineheight=0.9),legend.position="bottom",legend.box="horizontal",plot.margin=margin(10,20,10,10))+
 guides(color=guide_colorbar(title="AdjP",barwidth=8),size=guide_legend(title="n",override.aes=list(color="grey45")))
save_plot_pub(p,stem="KEGG_Enrichment_Top30",width=9.5,height=13.2,dpi=600,out_dir=out)
viz_qa_after_plot(p,plot_id="DELIVERY_KEGG_TOP30",hard_fail=FALSE)

ppi <- read.csv(file.path(dd,"ppi.tsv"),sep="\t",stringsAsFactors=FALSE,check.names=FALSE,fileEncoding="UTF-8")
p_full <- np_plot_string_ppi(ppi,title="STRING PPI degree gradient",label_top_n=NULL,min_score=900L,drop_isolates=TRUE,layout="concentric",n_rings=5,outer_frac=0.54,max_nodes=200L)
p_full$labels$subtitle <- "Top 200 proteins; STRING score >= 0.9"
save_plot_pub(p_full,stem="PPI_Gradient",width=11.5,height=11.5,dpi=600,out_dir=out)
viz_qa_after_plot(p_full,plot_id="DELIVERY_PPI_FULL",hard_fail=FALSE)
save_plot_pub(p_full,stem="PPI_Gradient_Degree",width=11.5,height=11.5,dpi=600,out_dir=out)

deg <- sort(table(c(ppi$preferredName_A,ppi$preferredName_B)),decreasing=TRUE)
top20 <- names(head(deg,20))
top_ppi <- ppi[ppi$preferredName_A %in% top20 & ppi$preferredName_B %in% top20,]
write.csv(top_ppi,file.path(out,"Top20_PPI_edges.csv"),row.names=FALSE,fileEncoding="UTF-8")
p_top <- np_plot_string_ppi(top_ppi,title="Top PPI hub network",label_top_n=NULL,min_score=900L,drop_isolates=TRUE,layout="concentric",n_rings=3,outer_frac=0.52,max_nodes=20L)
p_top$labels$subtitle <- "Top 20 hubs; full PPI"
save_plot_pub(p_top,stem="Top20_PPI_HubNetwork",width=9,height=8,dpi=600,out_dir=out)
viz_qa_after_plot(p_top,plot_id="DELIVERY_TOP20_PPI",hard_fail=FALSE)
print(c(kegg_total=nrow(kegg),kegg_top=nrow(top),ppi_edges=nrow(ppi),ppi_proteins=length(unique(c(ppi$preferredName_A,ppi$preferredName_B))),top20_edges=nrow(top_ppi)))
