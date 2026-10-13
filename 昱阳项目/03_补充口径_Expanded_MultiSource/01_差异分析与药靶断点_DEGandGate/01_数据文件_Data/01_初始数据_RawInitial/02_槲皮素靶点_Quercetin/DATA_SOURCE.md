# 槲皮素靶点 — 数据来源

```
data_provenance: REAL
source: SwissTargetPrediction
organism: Homo_sapiens
filter: Probability > 0
pubchem_cid: 5280343
```

| 文件 | 说明 |
|------|------|
| `00_成分表_Quercetin_forSTP.csv` | 提交 STP 的 CID/SMILES |
| `Quercetin_Swiss预测靶点_筛选前.csv` | STP 原始返回 |
| `Quercetin_Swiss预测靶点_筛选后.csv` | Probability>0（本课题药物基因唯一来源） |
| `02_…_Human_STP.csv` / `03_…_Mouse_STP.csv` | 基因列表 |

**禁止**使用 `_归档_努力学习缓存勿用/` 内文件作为药物靶点。  
脚本：技能库 `STP批量预测_stpBatchPredict.py`（2026-10-11 实测可达）。
