# pcNet 小矩阵对齐

矩阵：40 个样本 × 15 个基因，列已按 R `scale` 的总体思路中心化（标准差用 N-1）。nComp=3。
线程：OMP/MKL/OpenBLAS=1。没有读取 Formal 的 counts，也没有调用 `scTenifoldKnk()`。

- Python 完整 SVD 与截断 SVD 的最大绝对差：2.284e-14
- 与 pcNetCoreRcpp 的最大绝对差 1.769e-15
- 判定：通过（截断对完整 SVD 要求 < 1e-6；若跑了 R，对 Rcpp 要求 < 1e-5）

截断 SVD 只计算 C++ 里 `svd_econ` 之后保留的那 3 个右奇异向量。符号翻转在系数里会消掉。
本结果不能代替 8000 基因的对齐。未对齐前不得替换 Formal 正在写的结果。
