# 02: GenKI 引擎补齐与图册

**类别:** enhancement
**标签:** 已完成
**Blocked by:** None

**What to build:** PEP/NF1 有 GenKI 结果与延展图（01 原理图按 NAR 2023、02 单细胞、03 检出率），每基因 `KL排序/响应基因/富集` 进 `结果文件/<亚群>/GenKI/<基因>/`。

- [x] 修 genki_formal.py 路径（R-4.6.0、DesktopLayout 输出树）并解除 285K 占用限制
- [x] 烟测 PEP 通过（02_烟测_PEPNF1.py，对照 Abcc8）
- [x] 正式运行 PEP→NF1 完成（100 搜索 × 100 轮、1000 不放回排列）
- [x] 各基因 KL 图、响应数、Jaccard、对照重叠入目录；富集无 BH<0.05 条目，留说明

## Notes
工单：`.scratch/现行PEPNF1图册_CurrentAtlas/issues/02-GenKI补齐.md`；富集修剪与 06 网络对比见 `37_探索富集修剪与网络对比_TrimAndNetwork.R`。
