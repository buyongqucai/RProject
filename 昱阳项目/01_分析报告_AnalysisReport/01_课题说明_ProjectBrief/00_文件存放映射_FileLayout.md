# 昱阳项目 · 文件存放映射（重做版 · 2026-10-16）

## 1. 原则

1. **顶层**：`01_分析报告` + **单一主执行** `02_主执行_CTDcurated_QuercetinPredicted`。  
2. 旧双口径整夹迁入 `_archived_旧双口径_2026-10-16/`；仓外备份见 `_备份_Backup/昱阳项目_重做前_2026-10-16/`。  
3. 主执行内步骤：`01` 靶点交集 → `02` 富集 PPI → `03` 对接。  
4. 无轨 B「交付文件」强制树；终稿进 `01_分析报告/03_最终报告`（课题双报告）。  
5. **网络图**：禁止药/成分色块层（见 ResearchPlan §4.3）。

## 2. 顶层树

```text
E:\RProject\昱阳项目/
  README.md
  01_分析报告_AnalysisReport/
  02_主执行_CTDcurated_QuercetinPredicted/
    01_靶点获取与交集_TargetsAndOverlap/
    02_富集与PPI_EnrichPPI/
    03_分子对接_Docking/
  _archived_旧双口径_2026-10-16/     ← 只读
```

## 3. 单步内部树

```text
0N_<步骤名>/
  01_数据文件_Data/
    01_初始数据_RawInitial/     # 子夹名须带库名 CTD_ / STP_ / STRING_ / PDB_ …
    02_结果数据_ResultTables/
  02_代码文件_Code/
  03_图片文件_Figures/
  04_报告文件_Reports/
```
