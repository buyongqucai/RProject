# 11: 用仓库原版 pcNet 做基准，而不是正式敲除表

**类别:** enhancement
**标签:** 待Agent处理
**Blocked by:** 10-优化后真实亚群.md

**What to build:** 真实 cLTMR 的 GPU 网要和仓库原版建网比。1.4 的基准是已安装的 scTenifoldNet 1.4 `pcNet`（Rcpp）。1.4.3 的基准是 `R_仓库公式/pcNet_1.4.3.R`。误差看网络系数，不看 dRegulation。1 个 BLAS 线程，不写 Formal。

- [ ] 1.4.3 十张网对原版 R 的最大绝对差、置零差有记录
- [x] 1.4.3 十张网和后半段，GPU Python 与原版 R 的秒数有记录
- [ ] 1.4 至少一张真实网对原版 R 的最大绝对差、置零差和秒数有记录
- [ ] 优化记录写明上一轮对的是正式表，这一轮对的是原版 pcNet

## Notes

正式表是安装版 1.4 走完张量和 dRegulation、再保留三位小数之后的结果。它不是 1.4.3 的仓库公式，也不是建网系数本身。
