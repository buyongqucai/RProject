# GenKI 代码

训练、建网、Ray Tune 都还没写。不要在正在跑 Formal 的机器上启动。

开跑前先执行 `00_资源上限_CpuCap.py`。它读取当前机器的 CPU、内存和显卡，给系统留出一部分，再把剩余的分给建网、搜索和正式训练。换机器时重新运行，不用改计划里的数字。

脚本接着调用 `prepare("grn" | "search" | "fit")`，再加载 NumPy 或 PyTorch。规则见同级 `文档_docs/课题计划_GenKI_Cplx2.md` 的「资源划分」。
