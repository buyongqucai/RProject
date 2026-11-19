# DATA_SOURCE 总览 — 昱阳重做（CTD_curated × 槲皮素预测）

```
data_provenance: REAL   # 以各 RawInitial/DATA_SOURCE.md 为准；未落盘前为 PLANNED
```

## 现行主执行

| 侧 | 口径 | 落点（相对 `02_主执行_CTDcurated_QuercetinPredicted/`） |
|----|------|------|
| 疾病 | CTD **curated** · propofol 化学–基因 | `01_…/01_初始数据_RawInitial/01_CTD_Propofol_curated/` |
| 药物 | 槲皮素 **预测**靶（STP±多站） | `01_…/01_初始数据_RawInitial/02_STP_Quercetin_Predicted/` |
| PPI | STRING | `02_富集与PPI_…/01_初始数据_RawInitial/01_STRING_…/` |
| 对接配体 | PubChem CID 5280343 | `03_分子对接_…/`（可自归档复制并重登记） |

**本版不用：** GSE DEG 作疾病主池；ChEMBL/BindingDB 实验层作主门槛；HCTP 药/成分色块图。

旧 raw 可参考：`_archived_旧双口径_2026-10-16/03_补充口径_Expanded_MultiSource/…`（须重过滤 curated / 重写 DATA_SOURCE，勿直接冒充本版）。
