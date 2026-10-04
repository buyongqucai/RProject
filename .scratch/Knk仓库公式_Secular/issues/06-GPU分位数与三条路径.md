# 06: GPU 上做 type 7，并对照三条 1.4.3

**类别:** enhancement
**标签:** 已完成
**Blocked by:** None

**What to build:** 分位数留在 GPU 上做，和 CPU type 7 对位置。同一矩阵上跑仓库纯 R、纯 Python、R 调用 Python。1 个 BLAS 线程。

- [x] GPU 分位数和 CPU 分位数的网最大绝对差为 0
- [x] 三条路径对纯 R 的差都小于 1e-5
- [x] 记下用时

## Notes

记录在 `文档_docs/三种路径_ThreeWay.md`。R+Python 与纯 Python GPU 是同一次计算。
