# DATA_SOURCE 总览 — 昱阳 / 丙泊酚 × 槲皮素

```
data_provenance: REAL
```

## 双口径同级

| 口径 | 根目录 |
|------|--------|
| 未补充（备份） | `02_未补充口径_Baseline_STPonly/` |
| 补充（主执行） | `03_补充口径_Expanded_MultiSource/` |

## 补充口径落点

| 数据 | 路径（相对补充口径 `01_差异分析…/01_初始数据_RawInitial/`） |
|------|------|
| GSE106799 | `01_GEO_GSE106799/` |
| STP 预测 | `02_槲皮素靶点_Quercetin/` + `04_预测靶点_MultiPredict/01_STP_…` |
| ChEMBL/BindingDB | `03_ChEMBL_BindingDB_Experimental/` |
| 多预测站槽 | `04_预测靶点_MultiPredict/`（SEA 等 MANUAL） |
| CTD propofol | `05_CTD_Propofol/` |
| 对接配体 | `../04_分子对接_Docking/…/quercetin.pdbqt` |

口径：P7 单次约 3 h 丙泊酚暴露；无槲皮素给药臂；药靶=实验∪预测（分层）；疾病=DEG∪CTD；计算预测。
