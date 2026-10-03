# GPU 门槛

矩阵：40 样本 × 20 基因，nComp=3，CPU 线程 1。GPU 这边用的是完整 SVD 再留 3 个分量，用来看小矩阵值不值得搬上显卡。

- CPU 截断 SVD：0.008 秒
- GPU：6.380 秒
- 最大绝对差：3.129e-15
- 决定：GPU 不启用。这次小矩阵上 GPU 不比 CPU 快。

这种尺寸盖不住内核启动开销，不能代表 400×8000。正式 cLTMR 一张网的双精度批量分解见 `GPU正式规模_FormalGpuProbe.md`。Formal 仍不迁到 GPU。
