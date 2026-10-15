# 原始数据来源 README — 03_药病交集与网络_OverlapAndNetwork

**状态：PENDING（2026-10-14 建骨架）**

本模块不直接抓库，消费上游结果，按规范在此写清指针：

| 输入 | 上游位置 |
|------|----------|
| 疾病靶点（六库 + 并集双口径） | `../../01_疾病靶点_DiseaseTargets/01_数据文件_Data/02_结果数据_ResultTables/` |
| 药靶（分层并集） | `../../02_药物靶点_DrugTargets/01_数据文件_Data/02_结果数据_ResultTables/` |

产出：全药∩疾病、每药∩疾病、`network.csv`（A–B/B–C/C–D）+ `type.csv`（A药/B成分/C靶点/D通路）。
