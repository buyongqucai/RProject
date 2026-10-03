# Knk 加速项目

隔离于正在跑的 Formal。不修改 `13_正式参数虚拟敲除_RunFormalDefaults.R`，不读它的中间内存。

建网入口是 Python：`代码文件/04_截断建网可续跑_BuildCheckpoint.py`。

- 每个基因只算 3 个主成分，不再做完整 SVD 再丢掉其余分量。
- 每次启动先扫描续跑文件：完成的网跳过，只有细胞下标的网沿用下标重算，半截 `.partial` 删掉。
- 每张网在 SVD 之前写下细胞下标；算完后另起一个写盘线程写入稀疏网和 `.done`。
- 进度文件 `进度_Progress.txt` 只在一张网写入时更新，和该网的 npz、done 同一次落盘。计算过程中终端每 100 个基因打一行，不写盘。
- 默认 1 个线程。基因数超过 500 时拒绝启动，除非设置 `KNK_ALLOW_LARGE=1`。

测试标准在 [`文档_docs/测试规程_TestProtocol.md`](文档_docs/测试规程_TestProtocol.md)。自测：

```text
python 代码文件/04_截断建网可续跑_BuildCheckpoint.py --self-test
python 代码文件/05_GPU门槛_GpuGate.py
python 代码文件/07_四核对照_FourCoreCompare.py
python 代码文件/08_功能缺口_FunctionalGaps.py
```

`07` 只用 4 个进程，每个进程 1 个 BLAS 线程，先跑官方 `pcNet` 再跑截断 SVD。日常建网入口仍然是 1 个线程。

未与 8000 基因的 Rcpp 结果对齐之前，不能替换 Formal 的 RDS。
