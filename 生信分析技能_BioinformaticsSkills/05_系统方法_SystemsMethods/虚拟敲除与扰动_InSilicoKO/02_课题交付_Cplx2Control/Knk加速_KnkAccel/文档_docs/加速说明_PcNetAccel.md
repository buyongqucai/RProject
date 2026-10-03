# Knk pcNet 加速（与 Formal 隔离）

这个目录不参与正在跑的 `13_正式参数虚拟敲除_RunFormalDefaults.R`。没有改它的路径，也没有把这里的函数挂进那个进程。

## 慢在哪里

scTenifoldNet 1.4 的 `pcNetCoreRcpp` 对每个基因做一次留一设计矩阵的 `arma::svd_econ`，再只保留 `nComp=3` 个右奇异向量。8000 个基因就是 8000 次约 400×7999 的完整经济 SVD。10 张网已经并行，每张网实际约占 1 个核。

## 这份代码做什么

建网在 `代码文件/knk_accel/`。1.4 仍是留一回归，只保留 `nComp=3`。`02_小矩阵自检_SelfCheck.py` 在小矩阵上对照完整 SVD，并尽量对照本机 `pcNetCoreRcpp`。线程固定为 1。这一轮的改动、时间和误差见 `优化记录_这一轮.md`。

未在 8000 基因上对齐之前，不能把这份结果叫做 scTenifoldKnk 正式结果，也不能替换 Formal 的 RDS。25 基因的自测已经对上 `pcNet`，见 `截断建网自测_CheckpointSelfTest.md`。

可执行入口是 `代码文件/knk_accel/checkpoint.py` 的 `build_checkpoint_networks`。启动时先扫描续跑文件。进度文件只在一张网写入时更新；计算过程中每 100 个基因打一行。真实亚群重跑用 `13_亚群对照_RunSubtype.py`（1.4）和 `21_亚群流程_SubtypeFlow.py`（1.4.3）。

## 正在跑的任务不改到 GPU

当前 Formal 进程已经在 Rcpp 的完整 SVD 循环里。中途换实现就得停掉重跑。

1.4 的 `device="auto"` 留在 CPU。1.4.3 的 `auto` 在有 CUDA 时用 GPU。显式 `gpu` 没有 CUDA 就报错，不退回 CPU。1.4 的 GPU 求解器仍是 cuSOLVER `gesvd`。1.4.3 的张量用已确认的稀疏 GPU CP，不铺回稠密数组。检查点路径算完一张网再拷回主机，并释放显存缓存；两张网同时占着显存会在 16 GB 卡上停住。并发探测这台 4080 上没有收益，所以一次一张网。CPU 进程数在已有多个 Rscript 时保持 1。数值和取舍见 `优化记录_这一轮.md`。
