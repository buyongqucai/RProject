# 数据来源 DATA_SOURCE — STRING PPI 网络（补充口径）

- **data_provenance: REAL**
- **来源库**：STRING（https://string-db.org），`string_version` = **12.5**（见 `STRING_版本_Version.json`）
- **物种**：`species=10090`（Mus musculus）
- **获取时间**：2026-10-14（UTC+8）；补登记快照（同参数重放，与原查询同源同参）
- **查询端点与参数**（脚本 `02_代码文件_Code/01_一轮富集与PPI_EnrichAndPPI.R` 同款）：
  - `get_string_ids?identifiers={基因列表}&species=10090&limit=1` → `STRING_标识映射_GetStringIds.json`（57 个基因全部映射成功）
  - `network?identifiers={stringId 列表}&species=10090&required_score=400` → `STRING_互作网络_Network.json`（712 条互作边）
- **输入基因**：`基因列表_Genes.txt`（药∩病 overlap 57 基因；= `../../02_结果数据_ResultTables/05_PPI输入基因_PpiInputGenes.csv` 第一列）
- **对账**：原始快照 712 边 = 派生表 `06_STRING_edges.csv` 712 行（完全一致）；hub 派生 `07_PPI_hub_degree.csv`、`08_PPI_TopHubs.csv`
- **上游指针**：基因表来自 `../../../01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/02_结果数据_ResultTables/`（`19_药靶与疾病交集_DrugDiseaseOverlap.csv`）
- **许可与引用**：STRING 学术免费使用；引用 Szklarczyk et al., *Nucleic Acids Res* 2023（STRING v12）
