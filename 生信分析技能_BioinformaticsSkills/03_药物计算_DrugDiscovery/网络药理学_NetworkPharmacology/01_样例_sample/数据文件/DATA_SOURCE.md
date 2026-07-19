# 数据来源

- **data_provenance: REAL**（query-backed export；草药/多数疾病库仍依赖手工导出；CTD/STRING/KEGG 可程序化）
- **disease_english_name: Atherosclerosis**
- **单药**: 三七 / 丹参 / 人参 / 葛根 / 黄芪 / 黄连（各有独立 `药物_*_靶点基因_HerbTargets.csv` 与疾病交集表）
- **疾病库**: GeneCards / TTD / DrugBank / OMIM / CTD / DisGeNET（按英文病名；AUTO/MANUAL 见下）
- **药物/成分–靶点库**: TCMSP → BATMAN-TCM（仅 known）→ ETCM → HERB/TCMBank + SwissTargetPrediction（瀑布见技能说明 §4.1）；通路=KEGG、PPI=STRING
- **出图**: PPI 与 HCTP **代码绘制（交付默认）**，无需 Cytoscape 手绘
- **AUTO**: CTD bulk、KEGG REST、STRING API（Open Targets 陪跑）
- **MANUAL（需你导出）**: GeneCards、TTD、DrugBank、OMIM、DisGeNET、TCMSP、BATMAN、ETCM2、HERB、TCMBank、SwissTargetPrediction（详见技能说明 §1.5）
- **韦恩图**: 样例结果图可用微生信交付原图；数据分库见 `VennFull` 表
- **下游交集/富集**: GeneCards Relevance≥40（`疾病靶点按库_DiseaseGenesByDB.csv`）
- **交付路径**: `D:\网络药理学文件\网络药理学交付文件20260710(1)\交付文件`
- **规范**: DeliveryStandards + VizStandards + DataAuthenticity
- **说明**: `PROVENANCE.json`；样例 STATUS 可为 PARTIAL（缺手工库时），但 **不得**再把 PPI/HCTP 标成 BLOCKED_EXTERNAL。
