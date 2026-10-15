# Expanded arm Venn — 网药 FROZEN §G 微生信模板（禁止 R/VennDiagram 自绘）
# 调用：昱阳项目/_shared_scripts/build_venn_weishengxin.py
# 库：网络药理学/脚本_scripts/weishengxin_venn_lib.py

py <- Sys.which("python")
if (!nzchar(py)) py <- Sys.which("python3")
if (!nzchar(py)) stop("需要 python 以运行微生信韦恩")

script <- "E:/RProject/昱阳项目/_shared_scripts/build_venn_weishengxin.py"
st <- system2(py, args = c(shQuote(normalizePath(script)), "--arm", "expanded"),
              stdout = TRUE, stderr = TRUE)
message(paste(st, collapse = "\n"))
if (!is.null(attr(st, "status")) && attr(st, "status") != 0) {
  stop("weishengxin venn failed")
}
message("Venn done: weishengxin (NetworkPharm FROZEN §G)")
