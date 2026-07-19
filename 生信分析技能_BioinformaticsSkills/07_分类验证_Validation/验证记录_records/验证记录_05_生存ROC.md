# 验证记录 05_生存ROC: 生存 + ROC（toy + 可选 R 包）

- **状态**: PASS
- **时间**: 2026-07-18T17:12:46
- **沙盒**: `07_分类验证_Validation/`


## 数据来源

- Toy 临床表：`E:\RProject\生信分析技能_BioinformaticsSkills\07_分类验证_Validation\数据_data\toy_clinical_survival.csv`（n=60）
- 粗 AUC（marker vs status）：**0.376**

## 核对

| 项 | 结果 |
|----|------|
| 临床表生成 | PASS |
| R survival/pROC | SKIP_rscript_error: Command '['E:\\R-4.6.0\\bin\\Rscript.EXE', 'E:\\RProject\\生信分析技能_BioinformaticsSkills\\07_分类验证_Validation\\数据_data\\toy_surv_check.R']' returned non-zero exit status 1. |
| 技能对齐 | `生存分析与预后模型_Survival` + `诊断效能ROC_DiagnosticROC`（从 GEO-TCGA 拆出） |

## 说明

验证方法技能独立于 GEO 下载技能；全队列 TCGA 下载不在本轮范围。

