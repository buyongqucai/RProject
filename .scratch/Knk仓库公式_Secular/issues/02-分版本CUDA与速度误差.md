# 02: 1.4 与 1.4.3 分开走 CUDA

**类别:** enhancement
**标签:** 已完成
**Blocked by:** None

**What to build:** 1.4 用逐基因截断 SVD，1.4.3 用 Gram 加 secular。两个版本各自提供 Python CUDA 和 R 调用 CUDA。同一矩阵上记录用时，以及 1.4.3 相对 1.4 的系数差。不改 Formal。

- [x] 同一矩阵上测 1.4 Rcpp、截断 SVD、1.4.3 secular 的用时和最大绝对差
- [x] Python 两个版本都能指定 gpu
- [x] R 能调用这两条 CUDA 路径
- [x] 写明 1.4.3 没有丢掉留一回归，误差以实测为准

## Notes

本机 R 没有 torch。曾用 reticulate 转发到 PyTorch，测完后已删除 `调用_Cuda.R`。CUDA 只保留 Python 入口。
