# Stage paths are ASCII to avoid Windows R path-encoding failures.
root <- "E:/RProject/_np_stage"
source(file.path(root,"tools/PublicationPlot.R"))
source(file.path(root,"tools/PlotQA.R"))
source(file.path(root,"tools/StringNetwork.R"))
source(file.path(root,"tools/DeliveryNetworkLayouts.R"))
.np_ensure_plotqa <- function(...) TRUE
data_dir <- file.path(root,"data"); out_dir <- file.path(root,"out")
ppi_dir <- file.path(out_dir,"PPI"); enrich_dir <- file.path(out_dir,"enrichment"); fig_dir <- file.path(out_dir,"figures")
dir.create(ppi_dir,recursive=TRUE,showWarnings=FALSE); dir.create(enrich_dir,recursive=TRUE,showWarnings=FALSE); dir.create(fig_dir,recursive=TRUE,showWarnings=FALSE)
read_genes <- function(path){x<-read.csv(path,stringsAsFactors=FALSE,check.names=FALSE,fileEncoding="UTF-8");sort(unique(toupper(trimws(as.character(x$gene)))))}
main_genes<-read_genes(file.path(data_dir,"C_main.csv")); full_genes<-read_genes(file.path(data_dir,"C_full.csv")); disease<-read.csv(file.path(data_dir,"D.csv"),stringsAsFactors=FALSE,check.names=FALSE,fileEncoding="UTF-8"); disease_genes<-sort(unique(toupper(trimws(as.character(disease$gene)))))
fetch_ppi<-function(genes,label,cache){p<-np_fetch_string_ppi(genes,required_score=900L,cache_path=file.path(ppi_dir,cache),force=FALSE);write.csv(p,file.path(ppi_dir,paste0(label,"_STRING_edges.csv")),row.names=FALSE,fileEncoding="UTF-8");p}
ppi_main<-fetch_ppi(main_genes,"Main","STRING_Main_score900.tsv"); ppi_full<-fetch_ppi(full_genes,"Full","STRING_Full_score900.tsv")
plot_ppi<-function(ppi,title,stem){p<-np_plot_string_ppi(ppi,title=title,label_top_n=NULL,min_score=900L,drop_isolates=TRUE,layout="concentric",max_nodes=200L);p$labels$subtitle<-"STRING score >= 0.9; isolates removed";save_plot_pub(p,stem=stem,width=7.2,height=7.2,dpi=600,out_dir=fig_dir);viz_qa_after_plot(p,plot_id=stem,hard_fail=FALSE);invisible(p)}
if(nrow(ppi_main)) plot_ppi(ppi_main,"STRING PPI of shared targets","01_PpiCoreNetwork")
if(nrow(ppi_full)) plot_ppi(ppi_full,"STRING PPI sensitivity network","04_PpiSensitivityNetwork")
suppressPackageStartupMessages({library(clusterProfiler);library(org.Hs.eg.db)})
map_entrez<-function(genes){x<-suppressWarnings(bitr(genes,fromType="SYMBOL",toType="ENTREZID",OrgDb=org.Hs.eg.db));unique(x$ENTREZID)}
run_enrich<-function(genes,prefix){q<-map_entrez(genes);u<-map_entrez(disease_genes);go<-enrichGO(gene=q,universe=u,OrgDb=org.Hs.eg.db,ont="ALL",pAdjustMethod="BH",pvalueCutoff=0.05,qvalueCutoff=0.20,readable=TRUE);godf<-as.data.frame(go);if(nrow(godf)){godf$ONTOLOGY<-factor(godf$ONTOLOGY,levels=c("BP","CC","MF"));godf<-godf[order(godf$ONTOLOGY,godf$p.adjust),]};kg_link<-read.delim(file.path(data_dir,"kegg_hsa_gene_pathway.tsv"),header=FALSE,stringsAsFactors=FALSE)
kg_name<-read.delim(file.path(data_dir,"kegg_hsa_pathway_names.tsv"),header=FALSE,stringsAsFactors=FALSE,sep="\t")
term2gene<-data.frame(term=sub("^path:","",kg_link$V1),gene=sub("^hsa:","",kg_link$V2),stringsAsFactors=FALSE)
term2name<-data.frame(term=kg_name$V1,name=sub(" - Homo sapiens \\(human\\)$","",kg_name$V2),stringsAsFactors=FALSE)
kegg<-tryCatch(enricher(gene=q,universe=u,TERM2GENE=term2gene,TERM2NAME=term2name,pAdjustMethod="BH",pvalueCutoff=0.05,qvalueCutoff=0.20),error=function(e)NULL)
kedf<-if(is.null(kegg))data.frame()else as.data.frame(setReadable(kegg,OrgDb=org.Hs.eg.db,keyType="ENTREZID"))
write.csv(godf,file.path(enrich_dir,paste0(prefix,"_GO_full.csv")),row.names=FALSE,fileEncoding="UTF-8");write.csv(kedf,file.path(enrich_dir,paste0(prefix,"_KEGG_full.csv")),row.names=FALSE,fileEncoding="UTF-8");write.csv(data.frame(set=c("query","universe"),n=c(length(q),length(u))),file.path(enrich_dir,paste0(prefix,"_background_audit.csv")),row.names=FALSE,fileEncoding="UTF-8");list(go=godf,kegg=kedf,n_query=length(q),n_universe=length(u))}
en_main<-run_enrich(main_genes,"Main");en_full<-run_enrich(full_genes,"Full")
if(nrow(en_main$go)){p<-plot_enrich_hbar_facet(en_main$go,top_n=8,title="GO enrichment");save_plot_pub(p,stem="02_GoEnrichment",width=7.2,height=8.2,dpi=600,out_dir=fig_dir);viz_qa_after_plot(p,plot_id="GO",hard_fail=FALSE)}
if(nrow(en_main$kegg)){p<-plot_enrich_dot_journal(en_main$kegg,top_n=20,title="KEGG enrichment");save_plot_pub(p,stem="03_KeggEnrichment",width=7.2,height=7.2,dpi=600,out_dir=fig_dir);viz_qa_after_plot(p,plot_id="KEGG",hard_fail=FALSE)}
summary<-data.frame(analysis=c("Main","Full"),input_genes=c(length(main_genes),length(full_genes)),ppi_edges=c(nrow(ppi_main),nrow(ppi_full)),entrez_query=c(en_main$n_query,en_full$n_query),universe_entrez=c(en_main$n_universe,en_full$n_universe),go_terms=c(nrow(en_main$go),nrow(en_full$go)),kegg_terms=c(nrow(en_main$kegg),nrow(en_full$kegg)))
write.csv(summary,file.path(out_dir,"PPI_enrichment_summary.csv"),row.names=FALSE,fileEncoding="UTF-8");print(summary)





