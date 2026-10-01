# GenKI 代码

训练、建网、Ray Tune 都还没写。Formal 仍在跑时不要在这里启动 PC 回归或超参数搜索。

以后的脚本先调用 `00_资源上限_CpuCap.py` 的 `apply()`，再加载 NumPy 或 PyTorch。规则见同级 `文档_docs/课题计划_GenKI_Cplx2.md` 的「资源划分」。
