# 公式审计：对照 scTenifoldNet 1.4.3 的 pcNet

记录时间：2026-10-02。工单 `.scratch/Knk仓库公式_Secular/issues/01-按仓库公式做双版本.md`。

## 审查用什么

通用的 diff 审查（对照某次提交看风格和规格）看不出一条数值公式是否和另一个仓库相同。这次的基准是 GitHub master 上的 `pcNet.R`，原样放在 `代码文件/R_仓库公式/pcNet_1.4.3.R`。同一矩阵分别送进这份 R 函数和 PyTorch 实现，比稠密网的最大绝对差。

本机没有安装 R 的 `torch`。R 版本因此直接执行这份仓库源码。Python 版本用 PyTorch 双精度，CPU 和 GPU 走同一套 secular 步骤。

## 旧代码的结论

`knk_accel/pcnet.py` 里的截断 SVD 不是 1.4.3 正在执行的算法。1.4.3 是一次 Gram 特征分解，再对每个基因解 secular equation。截断 SVD 对过的是本机已安装的 1.4 Rcpp。那条路径还留在文件里，供以前的测量对照，不作为和 1.4.3 对齐的建网。

## 两个新版本

| 版本 | 入口 | 公式 | 额外能力 |
|---|---|---|---|
| R | `代码文件/R_仓库公式/建网_SecularStore.R` | `source(..., keep.source = TRUE)` 后调用仓库 `pcNet` | `set.seed` 后按顺序 `sample.int`；已有下标文件不覆盖；RDS 原子写入；完成标记；第二次调用跳过 |
| Python | `knk_accel/secular.py` 的 `pcnet_secular` | 同一套 Gram + secular，float64 | `device="cpu"` 或 `"gpu"`。没有 CUDA 时 `gpu` 报错 |
| Python 落盘 | `knk_accel/secular_store.py` | 建网调用上面的函数 | 下标由 R 的 `sample.int` 产生，存成 0 起的 `.npy`；写盘线程深拷贝；`method` 必须是 `secular143`，旧 SVD 的 npz 不会被跳过 |

进度按网打印。secular 一次处理全部基因，没有逐基因 SVD，所以不再按基因打印百分比。

## 小矩阵结果

16 个基因加 1 个全 0 基因，40 个细胞，`nComp = 3`，`q = 0.9`，`scaleScores = TRUE`。对照仓库 `pcNet` 的稠密网：

| 对照 | 最大绝对差 |
|---|---:|
| PyTorch CPU 对 R | 1.343e-14 |
| PyTorch GPU 对 R | 9.881e-15 |
| CPU 对 GPU | 7.216e-15 |

另一组 12×20、经落盘后再读出的第一张网，对同一份细胞下标上的 R `pcNet`，最大绝对差 5.995e-15。R 落盘连续调用两次，第二次两张网都跳过。Python 同样跳过。

这些是小矩阵。没有拿 8000 基因去和 1.4.3 比，也没有替换 Formal。

## 还没有改成仓库公式的部分

张量收尾（平均、除以最大绝对值、`round`）、流形对齐、`dRegulation` 没有放进这两个版本。本地 `cp_decomp.py` 的迭代表达式接近仓库，初值仍是 NumPy，不是 `rnorm`。本机已安装的 Net 是 1.4、Knk 是 1.1，和 GitHub 上的 1.4.3 / 1.1.5 不是同一份源码。
