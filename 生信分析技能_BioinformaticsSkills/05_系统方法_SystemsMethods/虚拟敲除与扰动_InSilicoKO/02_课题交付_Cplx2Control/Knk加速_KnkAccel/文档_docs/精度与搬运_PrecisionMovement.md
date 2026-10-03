# 精度与数据搬运

调研记录，2026-10-01。还没有改计算代码。

## 双精度会不会更不准

不会。CUDA 的 `double` 遵循 IEEE 754，基本运算按标准舍入；默认允许把乘加合成一条 FMA，这和 CPU 上打开 FMA 是同一类差异，不是降到单精度（[CUDA Programming Guide, Floating-Point Computation](https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/mathematical-functions.html)）。

本机已经测过：cLTMR 一张网的 GPU 双精度系数，对 CPU 截断 SVD 抽查 10 个基因，最大绝对差 1.132e-16。这是舍入量级。

Ada 游戏卡把双精度做慢，不是做粗。白皮书写 AD102 的 FP64 吞吐是 FP32 的 1/64，少量 FP64 单元是为了让双精度程序能正确运行（[NVIDIA Ada GPU Architecture](https://images.nvidia.com/aem-dam/Solutions/geforce/ada/nvidia-ada-gpu-architecture.pdf)）。4080 SUPER 是同代 GeForce。

## 混合精度

不必全程双精度。数值线性代数里的做法是：贵的分解用低精度，残差和修正用工作精度。Carson 与 Higham 对线性方程组（SIAM J. Sci. Comput. 40, 2018）和最小二乘（同刊 42, 2020, GMRES-LSIR）给出了能回到工作精度的条件；矩阵太病态时，低精度分解直接当答案会失败，需要用低精度因子做预条件再修正。

对本题：

- 工作精度是和官方双精度系数对齐。现行门槛是最大绝对差小于 1e-5。
- 单精度机器精度约 1e-7。425 阶的 Gram 特征值若不太病态，单精度可能已经进得了 1e-5；基因矩阵的条件数没有测过，不能直接换成全程单精度。
- 可用的混合方式：批量乘法用单精度，残差和抽查用双精度；过不了 1e-5 的基因再在双精度里重算。这是修正，不是把半精度当结果。
- 半精度、BF16、FP8 是 Tensor Core 的格式。这里要跟 R 的双精度回归对齐，不先用这些格式。

## 数据搬运

官方建议：要和计算重叠，主机内存必须钉住，拷贝用异步接口，拷贝和核函数放在不同的非默认流里。不钉住的内存在调用异步拷贝时会退回同步（[CUDA Programming Guide, Asynchronous Execution](https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/asynchronous-execution.html)；[Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/)）。

本机测过：0.5 GB 各方向约 0.02 秒，2 GB 上去 0.086 秒、下来 0.102 秒。相对一张网 15 秒的系数计算，整块搬运不是主项。每个基因来回搬一次才会把启动开销变成主体，40×20 那次就是这样。

值得做的是减少字节和减少往返，而不是把七步拆成两条流水：

- 计数矩阵只上传一次。8000 基因、425 个细胞的双精度大约 27 MB。
- 10 张网共用显存里的这块矩阵，只换细胞下标。下标是小数组。
- 系数在显卡上做分位数删边，再把稀疏结果拷回。不要每张网拷回完整的 8000×7999 双精度系数（约 0.5 GB）。
- 显存按一张网的大小分配一次，10 张网复用。
- 拷回上一张网的稀疏结果时，用另一条流算下一张网。钉住内存，两条非默认流。上一张的拷贝远短于下一张的计算，重叠省的是那一次拷贝，不是 15 秒。
- 出边置零若矩阵还在显卡上，就在显卡上改。不要为了一行数下载再上传。
- 张量要等 10 张网齐，流形对齐要等张量结果。这两处不能提前开算，只能避免中间多搬一次。
