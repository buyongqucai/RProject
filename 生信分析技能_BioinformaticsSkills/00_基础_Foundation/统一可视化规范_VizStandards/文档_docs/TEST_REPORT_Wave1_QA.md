# Wave 1 REAL 样例自审报告（2026-07-19）

## 范围
Survival / WGCNA / DoseTime / DEG-UMAP；NetPharm **未改**（FROZEN）。

## 检查结果

| 技能 | STATUS | accession | PlotQA | 数据真实性 | 技能说明 |
|------|--------|-----------|--------|------------|----------|
| Survival | PASS + REAL | GSE17536 | PASS | FCGR3A median High/Low，OS 官方临床 | 已更新样例/包 |
| WGCNA | PASS + REAL | GSE10072 | PASS | GEO-TCGA 子集表达 + smoking | 已更新流程/包 |
| DoseTime | PASS + REAL | GSE207177 | PASS（标题缩短后） | 书清 MAMs 时序 | 已更新 |
| DEG-UMAP | PASS + REAL | airway + GSE164522 | volcano WARN→label_n=6；其余 PASS | airway limma-voom；UMAP 山水 | 已更新样例节 |

## 返修记录
1. DoseTime 图题过长 → PlotQA WARN → 缩短标题后 **PASS**。
2. DEG-UMAP 火山标签重叠 WARN → `label_n=6` + 短标题。
3. 删除各技能 leftover `toy_*.csv`。

## 结论
Wave 1 **自审通过**，可推送 GitHub（仅 BioinformaticsSkills 变更；不含书清/山水全量）。
