options(stringsAsFactors = FALSE)
p <- "C:/Users/10540/Desktop/琪乐无穷/CPLX2虚拟敲除_Cplx2VirtualKO/结果文件/数据文件/敲除对象_KoObjects/PEP_Cplx2.rds"
obj <- readRDS(p)
cat("names:\n")
print(names(obj))
for (nm in names(obj)) {
  x <- obj[[nm]]
  cat("\n==", nm, class(x), "\n")
  if (is.matrix(x) || inherits(x, "Matrix")) cat("dim", paste(dim(x), collapse = "x"), "\n")
  if (is.data.frame(x)) cat("cols", paste(colnames(x), collapse = ","), "nrow", nrow(x), "\n")
  if (is.list(x) && !is.data.frame(x)) cat("list names", paste(names(x), collapse = ","), "\n")
}
