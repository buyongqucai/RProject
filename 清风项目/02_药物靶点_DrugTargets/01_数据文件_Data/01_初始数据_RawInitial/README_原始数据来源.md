# 原始数据来源 README — 02_药物靶点_DrugTargets

**状态：PENDING（2026-10-14 建骨架，成分瀑布未跑）**

## 本目录放什么

9 味药（水蛭/旋覆花/川芎*/桃仁/浙贝母/蜜麻黄*/紫苏子/黄芪/甘草；* 待确认）成分–靶点瀑布原始导出：

| 子目录 | 来源库 | 规则 |
|--------|--------|------|
| `01_TCMSP_成分靶点_CompoundTargets` | TCMSP | OB≥30%, DL≥0.18 |
| `02_BATMAN_成分靶点_CompoundTargets` | BATMAN-TCM | **仅 known/curated**，禁预测靶 |
| `03_ETCM_成分靶点_CompoundTargets` | ETCM | 补充 |
| `04_HERB_成分表_CompoundList` | HERB 2.0 | 成分 + SMILES → STP |
| `05_STP_预测靶点_PredictedTargets` | SwissTargetPrediction | 剔除 Probability=0 |
| `06_TCMBank_成分表_CompoundList` | TCMBank | 可取成分再预测 |

每子目录落库方原始导出 + `DATA_SOURCE.md`；实验靶/预测靶分层登记，不得混写。

## 获取策略与连通性

见 `../../../01_分析报告_AnalysisReport/01_课题说明_ProjectBrief/02_数据来源总览_DATA_SOURCE.md`。
