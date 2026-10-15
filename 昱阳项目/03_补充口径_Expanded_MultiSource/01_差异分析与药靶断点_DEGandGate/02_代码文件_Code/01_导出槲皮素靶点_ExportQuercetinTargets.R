# 昱阳项目专用：从努力学习网药缓存提取槲皮素成分靶点（TCMSP瀑布定稿表）
# provenance: REAL (project cache of CompoundTargets; compound_name Quercetin)

src <- "E:/RProject/努力学习项目/网络药理学/数据文件/药物成分靶点_CompoundTargets.csv"
out_dir <- "E:/RProject/昱阳项目/02_差异分析与药靶断点_DEGandGate/01_数据文件_Data/01_初始数据_RawInitial/02_STP_槲皮素靶点_QuercetinTargets"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

dt <- read.csv(src, stringsAsFactors = FALSE, fileEncoding = "UTF-8")
q <- dt[grepl("quercetin", dt$compound_name, ignore.case = TRUE), , drop = FALSE]
stopifnot(nrow(q) > 0)

uniq <- unique(q[, c("compound_name", "target_gene")])
uniq <- uniq[order(uniq$target_gene), , drop = FALSE]
uniq$source_file <- basename(src)
uniq$data_provenance <- "REAL"
uniq$note <- "Extracted Quercetin rows from 努力学习 CompoundTargets (TCMSP-waterfall cache)"

out1 <- file.path(out_dir, "01_槲皮素靶点_来自网药缓存_QuercetinTargets_fromNetPharmCache.csv")
write.csv(uniq, out1, row.names = FALSE, fileEncoding = "UTF-8")

genes <- sort(unique(uniq$target_gene))
out2 <- file.path(out_dir, "02_槲皮素靶点基因列表_人源_QuercetinTargetGenes_Human.csv")
write.csv(data.frame(gene_human = genes, stringsAsFactors = FALSE), out2,
          row.names = FALSE, fileEncoding = "UTF-8")

message("Quercetin unique human genes: ", length(genes))
message("Wrote: ", out1)
