root <- "E:/RProject/_np_stage"
source(file.path(root,"tools/PublicationPlot.R"))
source(file.path(root,"tools/PlotQA.R"))
source(file.path(root,"tools/StringNetwork.R"))
source(file.path(root,"tools/DeliveryNetworkLayouts.R"))
.np_ensure_plotqa <- function(...) TRUE
ppi <- read.csv(file.path(root,"out/PPI/Top20_STRING_edges.csv"),stringsAsFactors=FALSE,check.names=FALSE,fileEncoding="UTF-8")
p_fr <- np_plot_string_ppi(ppi,title="Top PPI hub network",label_top_n=NULL,min_score=900L,drop_isolates=TRUE,layout="fr",max_nodes=20L)
p_fr$labels$subtitle <- "Top 20 MCC-like genes"
save_plot_pub(p_fr,stem="candidate_top20_fr",width=9,height=8,dpi=600,out_dir=file.path(root,"out/figures"))
viz_qa_after_plot(p_fr,plot_id="TOP20_FR",hard_fail=FALSE)
p_c3 <- np_plot_string_ppi(ppi,title="Top PPI hub network",label_top_n=NULL,min_score=900L,drop_isolates=TRUE,layout="concentric",n_rings=3,outer_frac=0.52,max_nodes=20L)
p_c3$labels$subtitle <- "Top 20 MCC-like genes"
save_plot_pub(p_c3,stem="candidate_top20_concentric3",width=9,height=8,dpi=600,out_dir=file.path(root,"out/figures"))
viz_qa_after_plot(p_c3,plot_id="TOP20_C3",hard_fail=FALSE)
print(c(edges=nrow(ppi)))
