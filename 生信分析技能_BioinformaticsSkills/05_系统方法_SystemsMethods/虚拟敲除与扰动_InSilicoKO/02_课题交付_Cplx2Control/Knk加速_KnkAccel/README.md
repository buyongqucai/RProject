# Knk 加速项目

隔离于正在跑的 Formal。不修改 `13_正式参数虚拟敲除_RunFormalDefaults.R`，不读它的中间内存。

建网入口是 Python：`代码文件/04_截断建网可续跑_BuildCheckpoint.py`。

- 每个基因只算 3 个主成分，不再做完整 SVD 再丢掉其余分量。
- 每次启动先扫描续跑文件：完成的网跳过，只有细胞下标的网沿用下标重算，半截 `.partial` 删掉。
- 每张网在 SVD 之前写下细胞下标；算完后另起一个写盘线程写入稀疏网和 `.done`。
- 进度写在输出目录的 `进度_Progress.txt`，默认每 100 个基因刷新一次。
- 默认 1 个线程。基因数超过 500 时拒绝启动，除非设置 `KNK_ALLOW_LARGE=1`。

自测：

```text
python 代码文件/04_截断建网可续跑_BuildCheckpoint.py --self-test
python 代码文件/05_GPU门槛_GpuGate.py
```

未与 8000 基因的 Rcpp 结果对齐之前，不能替换 Formal 的 RDS。
