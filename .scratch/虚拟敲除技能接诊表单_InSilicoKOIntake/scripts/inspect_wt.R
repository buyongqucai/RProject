options(stringsAsFactors = FALSE)
p <- "C:/Users/10540/Desktop/琪乐无穷/CPLX2虚拟敲除_Cplx2VirtualKO/结果文件/数据文件/敲除对象_KoObjects/PEP_Cplx2.rds"
obj <- readRDS(p)
wt <- obj$tensorNetworks$WT
cat(class(wt), "\n")
if (is.list(wt)) print(names(wt))
if (is.matrix(wt) || inherits(wt, "Matrix")) {
  cat("dim", paste(dim(wt), collapse = "x"), "\n")
  cat("rownames", paste(head(rownames(wt), 5), collapse = ","), "\n")
}
if (is.list(wt) && !is.null(wt[[1]]) && (is.matrix(wt[[1]]) || inherits(wt[[1]], "Matrix"))) {
  cat("first dim", paste(dim(wt[[1]]), collapse = "x"), "\n")
}
str(wt, max.level = 2)
