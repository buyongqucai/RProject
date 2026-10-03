# cLTMR 亚群对照

记录时间：2026-10-02 04:03:06。优化后建网用 GPU `gesvd`，1 个 BLAS 线程，10 张网串行。后半段是官方 `tensorDecomposition`、`strictDirection`、`manifoldAlignment`、`dRegulation`，不是加速库里的 CP。优化前是已经跑完的正式参数 cLTMR（Rcpp 完整 SVD，10 张网并行，每网 BLAS 2）。

细胞下标：质控和 CPM 之后，`set.seed(1)`，再按正式脚本里的 furrr `seed=TRUE` 抽样。同一调用连抽两次，下标一致。`q=0.9`，`nComp=3`，`nc_nCells=425`。没有写 Formal 结果目录。PEP 对照期间仍在跑，所以没有再开一套 Rcpp 建网。

## 用时（秒）

| 步骤 | 秒 | 说明 |
|---|---:|---|
| qc | 0.140 | cells_in=426;cells_qc=407;genes=8000 |
| cpm | 0.060 | genes=8000 |
| indices | 0.140 | n_draw=425;n_net=10;q=0.9;stable=yes |
| network_01 | 876.017 | device=gpu;action=resume;genes=8000 |
| network_02 | 810.356 | device=gpu;action=resume;genes=8000 |
| network_03 | 802.064 | device=gpu;action=resume;genes=8000 |
| network_04 | 802.513 | device=gpu;action=resume;genes=8000 |
| network_05 | 811.021 | device=gpu;action=resume;genes=8000 |
| network_06 | 816.444 | device=gpu;action=resume;genes=8000 |
| network_07 | 804.466 | device=gpu;action=resume;genes=8000 |
| network_08 | 809.246 | device=gpu;action=resume;genes=8000 |
| network_09 | 819.745 | device=gpu;action=resume;genes=8000 |
| network_10 | 815.422 | device=gpu;action=resume;genes=8000 |
| load_csr | 3.470 | nets=10 |
| tensor | 91.730 | K=3;maxIter=1000;tol=1e-5 |
| direction | 4.240 | lambda=0 |
| manifold | 17.760 | d=2 |
| dRegulation | 1.290 | empiricalNull=FALSE |

优化后 10 张网合计 8167.3 秒。优化前整次正式调用 28480.6 秒（474.7 分钟），里面是并行建网加后半段，不能把这一格直接除以 10 当成单网。

## 和优化前结果的差异

- 基因数：优化前 8000，两边都有的 8000，只在优化前出现的 0。
- `distance` 最大绝对差：0。中位数 0。`Z` 最大绝对差：0。`p.adj` 最大绝对差：0。
- 绝对差 > 1e-8 的基因：0。> 1e-6：0。> 1e-5：0。
- `distance` 的 Pearson 相关：1.00000000。
- 张量并定向之后的 WT，对官方 RDS 的最大绝对差：0.000000e+00。
- 去掉 Cplx2 后 FDR<0.05：优化前 0 个，优化后 0 个。只在优化前：无。只在优化后：无。
- Cplx2 distance：优化前 2.493806e-05，优化后 2.493806e-05。

逐基因表在 `亚群对照_cLTMR_逐基因.csv`。网络和检查点在 `C:\Users\10540\AppData\Local\knk_accel_cLTMR`。

实测下来，`distance`、`Z`、`p.adj` 和定向之后的 WT 都与正式结果一致，最大绝对差是 0。张量分解会把数值收到 3 位小数，所以前面 SVD 上 1e-16 那一档没有进入这张敲除表。这只是 cLTMR 一个亚群，不能说成 5 个亚群都已对齐，也还没有替换 Formal。
