# 1.4 与 1.4.3 的审核版

记录时间：2026-10-02。侧测 1 个 BLAS 线程。没有写 Formal 结果目录，没有停正在跑的 Rscript。CUDA 只从 Python 进入。

审核入口：

```python
from knk_accel.versions import pcnet_14, pcnet_143

network_143 = pcnet_143(counts, n_comp=3, q=0.9, device="gpu")
network_14 = pcnet_14(counts, n_comp=3, q=0.9, device="gpu")
```

`counts` 是基因 × 细胞。`pcnet_143` 返回稠密 `float64`。`pcnet_14` 返回稀疏矩阵。`device` 只能是 `"cpu"` 或 `"gpu"`；没有 CUDA 时 `"gpu"` 报错，不会悄悄改回 CPU。两条函数各算自己的公式，不会互相替换。

## 已有的 Python 包

官方 `scTenifoldKnk` 仓库里的 `PYTHON/README.txt` 只有一句话，指向 [scTenifoldpy](https://github.com/qwerty239qwe/scTenifoldpy)。PyPI 上的包名是 `scTenifoldpy`（检索时页面有 0.5.1），作者 Yu-Te Lin，许可证 MIT。它是完整流程的移植：质控、建网、张量、流形、`dRegulation`，也有虚拟敲除。

读的是该仓库 `master` 的 `scTenifold/core/_networks.py`，没有安装、没有执行这个包。

| 函数 | 它实际在算什么 | 和这次审核版的差别 |
|---|---|---|
| `pc_net` | NumPy 的 Gram 特征分解加 secular equation，和 R 1.4.3 的 `pcNet` 同型 | 只有 CPU。分位数用 `np.nanquantile`。带先验网络。没有断点 |
| `cal_pc_coefs` | 每个基因一次回归。默认 `sklearn` 的 `randomized_svd`（`n_iter=20`）。可选 SciPy 完整 `gesvd` | 默认是随机近似，不是已安装 1.4 的精确截断 SVD，也没有 CUDA |

所以不是“仓库里没有 Python”。1.4.3 的 CPU 公式已经有人移植。缺的是：和已安装 1.4 对齐的截断 SVD、双精度 CUDA、以及按实测选定的设备。审核版继续用本地的 `secular.py` 和 `pcnet.py`，不把 `scTenifoldpy` 当成依赖。

## 测试计划

每条都先问它改不改公式。改公式的只作对照，不进入审核入口。

1. 在 cLTMR 的形状（8000 基因 × 425 细胞，一张网）上比较 1.4.3 的 CPU 与 GPU。通过线：最大绝对差小于 1e-5。
2. 同一矩阵上抽 6 个基因做 1.4 截断 SVD，比较 CPU、GPU，以及这 6 行和 1.4.3 全矩阵对应行。不跑满 8000 次 SVD。
3. 把“只留几个方向”用到 secular 的谱上：80×40 只留 8 个特征值，其余极点不进求和。若误差超过 1e-5，就拒绝。
4. 分位数仍是 R 的 type 7，只改成选取那一到两个顺序统计量，不再为整个 8000×8000 排序。和全排序的阈值必须相同。
5. 不写新的 CUDA kernel。1.4.3 的 GPU 若已经在 1 秒这一档，kernel 留到审核之后再决定。

## 实测

合成泊松计数，`lambda = 2`，种子 143。系数比较发生在 `scaleScores` 和 `q = 0.9` 之前，避免分位数把差异盖住。脚本是 `代码文件/19_大规模审核_LargeReview.py`。

| 项目 | 结果 |
|---|---|
| 1.4.3 CPU，8000×8000 系数 | 3.125 秒 |
| 1.4.3 GPU，同一系数 | 1.070 秒 |
| CPU 对 GPU | 1.825e-16 |
| 分位数，改选择器之前的整表排序 | 1.795 秒 |
| 1.4 CPU，基因 0、10、100、1000、4000、7999 | 3.754 秒 |
| 1.4 GPU，同样 6 个基因 | 0.941 秒 |
| 这 6 行，CPU 对 GPU | 3.194e-15 |
| 这 6 行，1.4 CPU 对 1.4.3 全矩阵 | 4.184e-16 |
| 80×40，谱只留 8 个特征值 | 最大绝对差 3.704e-02 |

6 个基因对上了，不能写成 8000 个基因全部对过。按 6 个基因的耗时线性外推整网 SVD，会得到大约 20 分钟的 GPU 和更长的 CPU；那是外推，不是这次的墙钟。

分位数选择器单独用 6400 万个随机数核对：全排序 0.898 秒，顺序统计量 0.473 秒，`q` 取 0、0.5、0.9、0.95、1 时阈值逐位相同。`1:4` 的 0.9 分位是 3.7，与 type 7 一致。8000×8000 那次 1.795 秒还包含构造绝对值矩阵，选择器替换之后没有把这张网重跑一遍。

## 留下的和去掉的

留下：

- 1.4.3 在这个尺寸上默认走 GPU。`device="cpu"` 仍是同一公式，大约慢 3 倍。800×200 上 GPU 更慢，那个尺寸不要沿用这次的默认判断。
- 1.4 仍是逐基因截断 SVD，`gesvd`，双精度。这个尺寸上 GPU 比 CPU 快。整网没有在本次重跑。
- 分位数改为 `np.partition` 取 type 7 要用的顺序统计量。阈值与全排序相同，比较仍是绝对值小于阈值才置零。

去掉：

- 截断 secular 的谱。80×40 上误差 0.037，已经大于 1e-5。求和必须用上全部特征值；“只留 3 个方向”在 1.4.3 里指的是 3 个根，不是丢掉其余极点。
- 不把 1.4 的逐基因 SVD 换成 1.4.3，也不把 1.4.3 换成随机 SVD。
- 不新增 CUDA kernel，不恢复 R 转发 CUDA。

## 审核时看什么

公式正文仍是 `knk_accel/secular.py` 和 `knk_accel/pcnet.py`。`versions.py` 只是两个名字。对照 R 时，1.4.3 用 `代码文件/R_仓库公式/pcNet_1.4.3.R`，1.4 用本机已安装的 Rcpp `pcNet`。

这次大矩阵是合成数，不是 cLTMR 的真实计数。抽样随机数、张量分解和 `dRegulation` 不在这两个函数里。
