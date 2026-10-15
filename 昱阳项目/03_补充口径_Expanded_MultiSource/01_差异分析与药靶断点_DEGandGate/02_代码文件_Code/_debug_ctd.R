ctd_path <- "E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/01_初始数据_RawInitial/05_CTD_Propofol/01_CTD_propofol_D015742_genes_curated.tsv"
raw <- readLines(ctd_path, n = 5, warn = FALSE)
print(raw)
ctd <- read.delim(ctd_path, stringsAsFactors = FALSE, check.names = FALSE, comment.char = "#")
cat("nrow", nrow(ctd), "\n")
print(names(ctd))
print(utils::head(ctd[,1:min(8,ncol(ctd))], 3))