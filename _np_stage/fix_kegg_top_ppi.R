root <- "E:/RProject/_np_stage"
source(file.path(root,"tools/PublicationPlot.R"))
source(file.path(root,"tools/PlotQA.R"))
source(file.path(root,"tools/StringNetwork.R"))
source(file.path(root,"tools/DeliveryNetworkLayouts.R"))
.np_ensure_plotqa <- function(...) TRUE
library(ggplot2); library(stringr)
fig <- file.path(root,"out/figures"); en <- file.path(root,"out/enrichment"); ppi_dir <- file.path(root,"out/PPI")
kegg <- read.csv(file.path(en,"Main_KEGG_full.csv"),stringsAsFactors=FALSE,check.names=FALSE,fileEncoding="UTF-8")
kegg <- kegg[order(kegg$p.adjust,kegg$Description),]
kegg$neglog10 <- -log10(pmax(kegg$p.adjust,.Machine$double.xmin))
kegg$term <- factor(str_wrap(kegg$Description,width=32),levels=rev(str_wrap(kegg$Description,width=32)))
p <- ggplot(kegg,aes(x=neglog10,y=term,size=Count,color=neglog10))+
  geom_point(alpha=0.92)+
  scale_color_gradientn(colours=bioinfo_sequential_blue,name="AdjP")+
  scale_size_continuous(name="n",range=c(2.2,7.5),breaks=pretty(range(kegg$Count),3))+
  scale_x_continuous(expand=expansion(mult=c(0.06,0.16)))+
  labs(title="KEGG enrichment",x="-log10(Padj)",y=NULL)+theme_journal()+
  theme(axis.text.y=element_text(size=7.4,lineheight=0.9),legend.position="bottom",legend.box="horizontal",plot.margin=margin(10,18,10,10))+
  guides(color=guide_colorbar(title="AdjP",barwidth=8),size=guide_legend(title="n",override.aes=list(color="grey45")))
save_plot_pub(p,stem="03_KeggEnrichment",width=9.2,height=10.8,dpi=600,out_dir=fig)
viz_qa_after_plot(p,plot_id="KEGG_FULL",hard_fail=FALSE)

metrics <- read.csv(file.path(root,"mech/ppi_metrics.csv"),stringsAsFactors=FALSE,check.names=FALSE,fileEncoding="UTF-8")
top <- head(metrics[order(-metrics$mcc_like_degree_x_triangles,-metrics$degree),],20)
top_genes <- unique(top$gene)
ppi <- read.csv(file.path(ppi_dir,"Main_STRING_edges.csv"),stringsAsFactors=FALSE,check.names=FALSE,fileEncoding="UTF-8")
ppi$preferredName_A <- toupper(ppi$preferredName_A); ppi$preferredName_B <- toupper(ppi$preferredName_B)
top_ppi <- ppi[ppi$preferredName_A %in% top_genes & ppi$preferredName_B %in% top_genes,]
write.csv(top_ppi,file.path(ppi_dir,"Top20_STRING_edges.csv"),row.names=FALSE,fileEncoding="UTF-8")
ptop <- np_plot_string_ppi(top_ppi,title="Top PPI hub network",label_top_n=NULL,min_score=900L,drop_isolates=TRUE,layout="concentric",max_nodes=20L)
ptop$labels$subtitle <- "Top 20 MCC-like genes"
save_plot_pub(ptop,stem="08_PpiHubNetwork",width=8.2,height=8.2,dpi=600,out_dir=fig)
viz_qa_after_plot(ptop,plot_id="TOP_PPI_NETWORK",hard_fail=FALSE)
print(c(kegg_terms=nrow(kegg),top_ppi_edges=nrow(top_ppi),top_ppi_nodes=length(unique(c(top_ppi$preferredName_A,top_ppi$preferredName_B)))))

