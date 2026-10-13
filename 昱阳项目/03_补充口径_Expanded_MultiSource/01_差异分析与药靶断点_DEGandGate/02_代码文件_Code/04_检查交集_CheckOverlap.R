tab <- "E:/RProject/昱阳项目/02_差异分析与药靶断点_DEGandGate/01_数据文件_Data/02_结果数据_ResultTables"
raw <- "E:/RProject/昱阳项目/02_差异分析与药靶断点_DEGandGate/01_数据文件_Data/01_初始数据_RawInitial/02_槲皮素靶点_Quercetin"
ov <- read.csv(file.path(tab, "09_药靶与DEG交集_QuercetinDegOverlap.csv"), stringsAsFactors = FALSE)
cat("Mapped-ortholog overlap rows:\n")
print(ov)
h <- read.csv(file.path(raw, "02_槲皮素靶点基因列表_人源_QuercetinTargetGenes_Human.csv"), stringsAsFactors = FALSE)$gene_human
d <- read.csv(file.path(tab, "05_差异基因_DEG_mainThreshold.csv"), stringsAsFactors = FALSE)
hit <- d[toupper(d$gene) %in% toupper(h), , drop = FALSE]
cat("Direct toupper human-symbol vs DEG overlap:", nrow(hit), "\n")
print(hit[, c("gene", "logFC", "P.Value", "direction")])
write.csv(hit, file.path(tab, "10_交集_直接符号匹配_DirectSymbolOverlap.csv"), row.names = FALSE, fileEncoding = "UTF-8")
