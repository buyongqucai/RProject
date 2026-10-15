# 原始数据来源 README — 03_富集与PPI_EnrichPPI（未补充口径/基线）

本模块 `01_初始数据_RawInitial/` 的构成、补登记缘由与上游指针。

## 为什么原来没有原始数据（2026-10-14 查明）

与补充口径同因：`01_一轮富集与PPI_EnrichAndPPI.R` 对 STRING 为运行时在线 API 查询，只落盘派生表（`06_STRING_edges.csv` 等），未保存 API 原始响应；上游基因表留在 `01_差异分析与药靶断点_DEGandGate` 且无指针 README；raw/02 分层为 2026-10-12 新规，早建目录未回补。

## 补登记内容（2026-10-14）

| 目录/文件 | 内容 |
|-----------|------|
| `01_STRING_PPI网络_StringPpiNetwork/` | STRING 12.5 API 原始快照（版本、ID 映射、互作网络 JSON）+ `DATA_SOURCE.md` |
| 本 README | 上游指针与口径说明 |

对账：快照 50 映射 / 8 边 = 派生表 `06_STRING_edges.csv`（8 行），同源同参可核。

## 口径说明（基线为对照口径）

- 药靶仅 SwissTargetPrediction（99 基因 → 小鼠映射 85）；药∩病 overlap = **1（Alox15）**。
- ORA/PPI 输入为回退口径（top-50 DEG）；GO/KEGG 结果为 `no_significant_terms`（诚实阴性）。
- PPI 弱网络（degree max 3）**仅作对照**，科学结论以 `03_补充口径_Expanded_MultiSource` 为准。

## 上游原始数据指针

| 数据 | 位置 | 来源 |
|------|------|------|
| GEO 差异表达（DEG 120） | `../../01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/01_初始数据_RawInitial/` | GEO GSE106799 |
| STP 药靶 | `../../02_药物靶点_DrugTargets/`（`Quercetin_Swiss预测靶点_*.csv`，带来源库） | SwissTargetPrediction |

## 软件库（无文件型 raw）

- GO/KEGG ORA：`clusterProfiler` + `org.Mm.eg.db`、KEGG `mmu`；结果落 `02_结果数据_ResultTables/`。
