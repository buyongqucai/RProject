# 昱阳 · 数据来源总览

## 双口径

| 口径 | 路径 | 药物 | 疾病 |
|------|------|------|------|
| 未补充（备份） | `02_未补充口径_Baseline_STPonly/` | STP only | GSE106799 DEG |
| 补充（主执行） | `03_补充口径_Expanded_MultiSource/` | ChEMBL∪BindingDB ∪ STP(+多站手工槽) | DEG ∪ CTD(propofol) |

## 补充口径关键 ID

- GEO：GSE106799  
- PubChem CID：5280343  
- ChEMBL：CHEMBL50  
- BindingDB monomer：7460  
- CTD MeSH：D015742（Propofol）  

## 严谨包

- 未补充：`SKIPPED_CONFIRMED_DONE`（不加宽；不做严谨包）  
- 补充：`DONE`（已试跑；旁路分析，主交集不变）

## 原始数据登记（2026-10-14 补）

- PPI：两口径 `03_富集与PPI_EnrichPPI/01_数据文件_Data/01_初始数据_RawInitial/` 已补 STRING v12.5 API 原始快照 + `README_原始数据来源.md`（原缺原因与上游指针见该 README）。
- 疾病/药靶 raw：`01_差异分析与药靶断点_DEGandGate`、`02_药物靶点_DrugTargets` 的 `01_初始数据_RawInitial/` 均带来源库前缀（SampleLayoutNaming §2.1）。
