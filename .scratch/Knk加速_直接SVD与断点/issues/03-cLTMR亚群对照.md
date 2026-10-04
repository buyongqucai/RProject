# 03: 用优化后的算法跑完 cLTMR，对照优化前的正式结果

**类别:** enhancement
**标签:** 已完成
**Blocked by:** None（可立即开始）

**What to build:** cLTMR 用已落地的 GPU `gesvd` 建 10 张网，后半段走官方张量到 `dRegulation`。记录各段用时，以及和正式参数 cLTMR 表的 `distance` / `p.adj` 差异。不写 Formal 结果目录，不停止正在跑的 PEP。

- [x] 建网调用把 `device="gpu"` 传到直接截断 SVD
- [x] 细胞下标按 `set.seed(1)` 之后的 furrr 抽样复现，并检查两次抽样一致
- [x] 各段用时写入记录
- [x] 逐基因差异和 FDR 集合差异写入记录

## Notes

1 个 BLAS 线程。`KNK_ALLOW_LARGE` 只在这次对照进程里打开。

2026-10-02 完成。10 张网合计 8167 秒。`distance`、`Z`、`p.adj` 对正式 cLTMR 的最大绝对差都是 0。记录在 `亚群对照_cLTMR.md`。
