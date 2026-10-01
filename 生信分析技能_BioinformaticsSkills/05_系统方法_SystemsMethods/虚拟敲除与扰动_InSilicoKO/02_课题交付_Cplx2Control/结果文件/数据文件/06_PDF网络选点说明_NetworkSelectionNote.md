# 06 网络图 — PDF 选点说明

- 选点：各亚群 `p.adj < 0.05` 的 DR 基因；敲除基因作自我中心图中心。
- 选边：STRING Mus musculus (10090)，先 400 再 900；不按距离凑 Top40。
- 画法：点少 → egocentric；STRING 连通且节点≥8 才用网药同心环。
- 旧 `06_*_Cplx2Network`（Top40+scGRN）已移入 `_deprecated_Top40非PDF标准/`。

## 本试跑结果
- FDR 排除 Cplx2 后：cLTMR=0, NF1=0, NP=0, PEP=1, TRPM8=0
- STRING 边：见 `06_STRING边统计_StringEdgeSummary.csv`
