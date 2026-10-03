# 1.4.3 的三条路径

记录时间：2026-10-02。1 个 BLAS 线程。纯 R 是仓库 `pcNet_1.4.3.R`。纯 Python 是 `pcnet_secular`。R+Python 是 R 用 reticulate 调用同一个 Python 函数，`device="gpu"`。三份结果都做了缩放和 `q=0.9`。

| 矩阵 | 纯 R | 纯 Python CPU | 纯 Python GPU | R+Python | 对纯 R 的最大绝对差 |
|---|---:|---:|---:|---:|---|
| 40×30 | 0.800 秒 | 0.031 秒 | 0.005 秒 | 3.360 秒 | Python CPU 5.329e-15，GPU 与 R+Python 都是 6.106e-15 |
| 800×200 | 1.090 秒 | 0.131 秒 | 0.039 秒 | 3.440 秒 | Python CPU 2.065e-14，GPU 与 R+Python 都是 2.043e-14 |
| 8000×425 | 54.500 秒 | 6.513 秒 | 1.496 秒 | 5.720 秒 | Python CPU 7.966e-14，GPU 与 R+Python 都是 1.444e-13 |

R+Python 和纯 Python GPU 的差是 0，因为 R 只是把同一份矩阵送进 Python。40×30 上 R+Python 的 3.360 秒大部分是启动 reticulate。

## 分位数还要不要先拷回 CPU

不必。type 7 用的是第 k 小的那个数，GPU 的 `kthvalue` 和 CPU 的 `partition` 取的是同一个名次。8000×425 上，先拷贝再在 CPU 做分位数 2.062 秒（拷贝 0.156 秒，分位数 1.906 秒）；留在 GPU 上做完再拷回 1.356 秒。两张网的最大绝对差是 0，置零位置没有一处不同。`1:4` 的 0.9 分位两边都是 3.7。

函数仍然返回 NumPy 数组，所以算完的那张网还是要拷一次。这一次不是为了做分位数。
