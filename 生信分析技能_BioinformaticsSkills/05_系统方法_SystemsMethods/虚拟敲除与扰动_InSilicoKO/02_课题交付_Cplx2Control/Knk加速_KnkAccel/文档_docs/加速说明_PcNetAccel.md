# Knk pcNet 加速（与 Formal 隔离）

这个目录不参与正在跑的 `13_正式参数虚拟敲除_RunFormalDefaults.R`。没有改它的路径，也没有把这里的函数挂进那个进程。

## 慢在哪里

scTenifoldNet 1.4 的 `pcNetCoreRcpp` 对每个基因做一次留一设计矩阵的 `arma::svd_econ`，再只保留 `nComp=3` 个右奇异向量。8000 个基因就是 8000 次约 400×7999 的完整经济 SVD。10 张网已经并行，每张网实际约占 1 个核。

## 这份代码做什么

`01_截断SVD_TruncatedPcNet.py` 用同样的回归公式，但只算那 3 个分量。`02_小矩阵自检_SelfCheck.py` 在 40×15 的矩阵上对照完整 SVD，并尽量对照本机 `pcNetCoreRcpp`。线程固定为 1。

未在 8000 基因上对齐之前，不能把这份结果叫做 scTenifoldKnk 正式结果，也不能替换 Formal 的 RDS。25 基因的自测已经对上 `pcNet`，见 `截断建网自测_CheckpointSelfTest.md`。

可执行入口是 `代码文件/04_截断建网可续跑_BuildCheckpoint.py`。启动时先扫描续跑文件，进度写在输出目录的 `进度_Progress.txt`。

## 为什么不把正在跑的任务改到 GPU

当前进程已经在 Rcpp 循环里。中途换实现就得停掉重跑。完整 `svd_econ` 再丢掉除前 3 个以外的分量，搬到 GPU 上仍然是同一批小 SVD，省不下这 10 个核。先做截断 SVD，是同一公式里真正少算的部分。GPU 版留在对齐通过之后再试。
