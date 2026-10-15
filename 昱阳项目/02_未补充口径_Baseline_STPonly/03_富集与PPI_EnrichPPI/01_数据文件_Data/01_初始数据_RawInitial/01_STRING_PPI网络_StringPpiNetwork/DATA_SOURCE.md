# 数据来源 DATA_SOURCE — STRING PPI 网络（未补充口径/基线）

- **data_provenance: REAL**
- **来源库**：STRING（https://string-db.org），`string_version` = **12.5**（见 `STRING_版本_Version.json`）
- **物种**：`species=10090`（Mus musculus）
- **获取时间**：2026-10-14（UTC+8）；补登记快照（同参数重放，与原查询同源同参）
- **查询端点与参数**（与 `01_一轮富集与PPI_EnrichAndPPI.R` 同款）：
  - `get_string_ids?identifiers={基因列表}&species=10090&limit=1` → `STRING_标识映射_GetStringIds.json`（50/50 映射成功）
  - `network?identifiers={stringId 列表}&species=10090&required_score=400` → `STRING_互作网络_Network.json`（8 条互作边）
- **输入基因**：`基因列表_Genes.txt`（= `../../02_结果数据_ResultTables/05_PPI输入基因_PpiInputGenes.csv` 第一列）。基线口径药∩病 overlap=1（Alox15），<3 触发回退：取 top-50 DEG（|logFC|）作为 STRING 输入（`ppi_source=overlap<3_use_topDEG_for_STRING`）
- **对账**：快照 8 边 = 派生表 `06_STRING_edges.csv` 8 行；hub 派生 `07_PPI_hub_degree.csv`、`08_PPI_TopHubs.csv`
- **注意**：基线 PPI 为**回退口径**的弱网络（最高 degree=3），仅作对照，不作为结论依据（结论以补充口径为准）
- **许可与引用**：STRING 学术免费使用；引用 Szklarczyk et al., *Nucleic Acids Res* 2023（STRING v12）
