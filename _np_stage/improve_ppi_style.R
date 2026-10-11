root <- "E:/RProject/_np_stage"
source(file.path(root,"tools/PublicationPlot.R"))
source(file.path(root,"tools/PlotQA.R"))
source(file.path(root,"tools/StringNetwork.R"))
source(file.path(root,"tools/DeliveryNetworkLayouts.R"))
.np_ensure_plotqa <- function(...) TRUE
ppi <- read.csv(file.path(root,"out/PPI/Main_STRING_edges.csv"),stringsAsFactors=FALSE,check.names=FALSE,fileEncoding="UTF-8")
metrics <- read.csv(file.path(root,"mech/ppi_metrics.csv"),stringsAsFactors=FALSE,check.names=FALSE,fileEncoding="UTF-8")
top20 <- head(metrics[order(-metrics$mcc_like_degree_x_triangles,-metrics$degree),],20)$gene
p_full <- np_plot_string_ppi(ppi,title="STRING PPI of shared targets",label_top_n=NULL,min_score=900L,drop_isolates=TRUE,layout="concentric",n_rings=5,outer_frac=0.54,max_nodes=52L)
p_full$labels$subtitle <- "STRING score >= 0.9; isolates removed"
save_plot_pub(p_full,stem="01_PpiCoreNetwork",width=10,height=10,dpi=600,out_dir=file.path(root,"out/figures"))
viz_qa_after_plot(p_full,plot_id="PPI_FULL_UPDATED",hard_fail=FALSE)
p_top <- np_plot_string_ppi(ppi,title="Top PPI hub network",label_top_n=NULL,min_score=900L,drop_isolates=TRUE,layout="concentric",n_rings=5,outer_frac=0.54,max_nodes=52L)
p_top$labels$subtitle <- "Top 20 hubs; full PPI"
save_plot_pub(p_top,stem="08_PpiHubNetwork",width=10,height=10,dpi=600,out_dir=file.path(root,"out/figures"))
viz_qa_after_plot(p_top,plot_id="PPI_TOP_UPDATED",hard_fail=FALSE)
print(c(full_edges=nrow(ppi),top20=length(top20)))

