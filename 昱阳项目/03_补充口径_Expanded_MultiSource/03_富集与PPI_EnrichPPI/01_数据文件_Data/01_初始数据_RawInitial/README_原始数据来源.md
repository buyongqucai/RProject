# 原始数据来源 README — 03_富集与PPI_EnrichPPI（补充口径）

本模块 `01_初始数据_RawInitial/` 的构成、补登记缘由与上游指针。

## 为什么原来没有原始数据（2026-10-14 查明）

1. **流水线只落盘派生表**：`02_代码文件_Code/01_一轮富集与PPI_EnrichAndPPI.R` 对 STRING 为**运行时在线 API 查询**（`get_string_ids` → `network`），查询响应直接在内存解析为 `06_STRING_edges.csv` 等派生表，**未把 API 原始响应保存为 raw**。
2. **上游基因表留在别的模块**：ORA/PPI 输入基因（`01_ORA输入基因_OraInputGenes.csv`、`05_PPI输入基因_PpiInputGenes.csv`）由 `01_差异分析与药靶断点_DEGandGate` 的结果表派生，当时未写指针 README。
3. **规范时点差**：raw/02 分层与来源库前缀（SampleLayoutNaming §2.1）为 2026-10-12 新规，早建目录未回补。

## 补登记内容（2026-10-14）

| 目录/文件 | 内容 |
|-----------|------|
| `01_STRING_PPI网络_StringPpiNetwork/` | STRING 12.5 API 原始快照（版本、ID 映射、互作网络 JSON）+ `DATA_SOURCE.md` |
| 本 README | 上游指针与软件库说明 |

对账：快照 57 映射 / 712 边 = 派生表 `06_STRING_edges.csv`（712 行），同源同参可核。

## 上游原始数据指针

| 数据 | 位置 | 来源 |
|------|------|------|
| GEO 差异表达（DEG 120） | `../../01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/01_初始数据_RawInitial/` | GEO GSE106799（小鼠，丙泊酚暴露） |
| CTD 化学–基因（propofol） | 同上模块 | CTD 库导出 |
| 药靶（ChEMBL/BindingDB/STP/PharmMapper/TargetNet/BATMAN） | `../../02_药物靶点_DrugTargets/01_数据文件_Data/`（实验/预测靶 raw 均带来源库前缀） | 各库导出/API |

## 软件库（无文件型 raw）

- GO/KEGG ORA：`clusterProfiler` + `org.Mm.eg.db`（GO）、KEGG `mmu`（在线）；结果落 `02_结果数据_ResultTables/02–04_*.csv`。
- 富集/PPI 出图：网药 FROZEN 图序（`_shared_scripts/enrich_plot_netpharm.R`、`plot_ppi_netpharm.R`）。
