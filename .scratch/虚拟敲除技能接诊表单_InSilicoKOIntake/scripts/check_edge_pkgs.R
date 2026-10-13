options(stringsAsFactors = FALSE)
root <- "C:/Users/10540/Desktop/琪乐无穷/CPLX2虚拟敲除_Cplx2VirtualKO"
obj_dir <- file.path(root, "结果文件", "数据文件", "敲除对象_KoObjects")
obj <- readRDS(file.path(obj_dir, "PEP_Cplx2.rds"))
wt <- as.matrix(obj$tensorNetworks$WT)
cat("Cplx2-Scarb2", wt["Cplx2", "Scarb2"], wt["Scarb2", "Cplx2"], "\n")
cat("packages", paste(intersect(installed.packages()[,1], c("org.Mm.eg.db","clusterProfiler","fgsea")), collapse=","), "\n")
