# 昱阳项目 · 文件存放映射（现行）

## 1. 原则

1. **顶层**：`01_分析报告` + **同级双口径** `02_未补充` / `03_补充`。  
2. 口径内步骤：`01` DEG门禁 → `02` 严谨包 → `03` 富集PPI → `04` 对接。  
3. **严谨包**：未补充 = 确认跳过已完成；补充 = 等你确认。  
4. 无「交付文件」；终稿进 `01_分析报告/03_最终报告`。

## 2. 顶层树

```text
E:\RProject\昱阳项目/
  README.md
  01_分析报告_AnalysisReport/
  02_未补充口径_Baseline_STPonly/     ← 备份冻结
    01_差异分析与药靶断点_DEGandGate/
    02_可选严谨包_RigorOptional/
    03_富集与PPI_EnrichPPI/
    04_分子对接_Docking/
  03_补充口径_Expanded_MultiSource/   ← 主执行
    01_差异分析与药靶断点_DEGandGate/
    02_可选严谨包_RigorOptional/
    03_富集与PPI_EnrichPPI/
    04_分子对接_Docking/
```

## 3. 单步内部树

```text
0N_<步骤名>/
  01_数据文件_Data/
    01_初始数据_RawInitial/
    02_结果数据_ResultTables/
  02_代码文件_Code/
  03_图片文件_Figures/
  04_报告文件_Reports/
```

### 3.1 MD 模块变体（`05_分子动力学_MD`，2026-10-13）

```text
05_分子动力学_MD/
  01_数据文件_Data/
    01_初始数据_RawInitial/
      {NN}_{来源}_{体系}_{PDBID}/   # 受体+对接姿态登记，每夹 DATA_SOURCE.md
    02_结果数据_ResultTables/
      {体系}/                       # xvg/csv 表型产物
  02_代码文件_Code/
  03_图片文件_Figures/
    {体系}/{NN}_{中文}图/{NN}_{中文}_{English}.{png,svg}   # 冻结图册（MdFigureStandards）
  04_报告文件_Reports/
  05_工作文件_MdWork/               # GROMACS 运行工作目录（引擎原名不改；轨迹等大文件仅本地）
```

- raw 命名遵 `样例目录与命名_SampleLayoutNaming.md` §2.1（`01_PDB_受体_Receptor_1M17.pdb`、`02_AutoDock_对接姿态_QuercetinPose_EGFR.pdbqt` 等）。
- 图片文件夹内平铺旧导出归 `99_平铺旧导出_LegacyFlat/`，不删图、不乱序。
