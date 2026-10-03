# Python 库函数参数

给要调用 `knk_accel` 的人。优化过程不写在这里，见 `优化记录_这一轮.md`。公布用的数是双精度。1.4 和 1.4.3 不是同一个建网公式，不要混用。

计数矩阵一律是基因 × 细胞，`float64`。`device` 只接受 `cpu`、`gpu`、`auto`。显式 `gpu` 在没有 CUDA 时直接报错，不会改去 CPU。

## `pcnet_14`

1.4：每个基因一次留一回归，只留 `n_comp` 个右奇异向量。

| 参数 | 默认 | 含义 |
|---|---|---|
| `counts_genes_by_cells` | 必填 | 基因 × 细胞 |
| `n_comp` | 3 | 保留的成分数，官网 `nc_nComp` |
| `q` | 0.9 | 绝对值低于该分位数的边置 0。0 或 1 表示不删边 |
| `device` | `auto` | `auto` 固定用 CPU。写出 `gpu` 才走 CUDA，大矩阵是每个基因一次 `gesvd` |

返回稀疏矩阵。40×40 以内、且样本和基因都大于 `n_comp`、`n_comp` 不超过 8 时，GPU 合成一次 Jacobi 核。更大的矩阵仍是逐基因 `gesvd`。

## `pcnet_143`

1.4.3：一次 Gram 特征分解，再对每个基因解 secular 方程。

| 参数 | 默认 | 含义 |
|---|---|---|
| `counts_genes_by_cells` | 必填 | 基因 × 细胞 |
| `n_comp` | 3 | 每个基因保留的根的个数 |
| `q` | 0.9 | 与 `pcnet_14` 相同。底层 `pcnet_secular` 自己的默认是 0，走本函数才会带上 0.9 |
| `device` | `auto` | 有 CUDA 时用 GPU，否则 CPU |

返回稠密 `float64` 数组。调用 `pcnet_secular` 时还可以设 `scale_scores=True`、`symmetric=False`、`merge="auto"`、`async_copy=False`。`merge="auto"` 只决定 GPU 上 secular 是否合成一个核，不会把 `gpu` 改成 `cpu`。8000 基因的检查点不要开 `async_copy`。

## `tensor_from_networks_gpu`

稀疏三阶 CP。公式与官方 `tensorDecomposition` 的三模分支相同，不铺稠密张量。

| 参数 | 默认 | 含义 |
|---|---|---|
| `networks` | 必填 | 至少两张同阶方阵，零保持为零 |
| `init` | 必填 | 三个列主序 `rnorm` 因子，形状 `(基因, K)`、`(基因, K)`、`(网络数, K)`。用 R 的 `set.seed(1)` |
| `n_comp` | 3 | 秩，官网 `td_K` |
| `max_iter` | 1000 | 最多轮数 |
| `tol` | 1e-5 | 相邻残差之差除以张量范数，低于它就停 |
| `n_decimal` | 3 | 按最大绝对值缩放后收到几位小数，向偶数舍入 |

返回字典：`matrix` 是舍入后的平均，还没有清对角线，也还没有转成官方 WT 的转置；另有 `iterations` 和 `converged`。没有 CUDA 时报错。

官方停机点之后不要多跑。稀疏相加和 R 的稠密 BLAS 顺序不同，只在残差比值贴着 1e-5，或缩放后贴着 `x.xxx5` 时，才可能让公布的 3 位小数差 0.001。
