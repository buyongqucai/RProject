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
