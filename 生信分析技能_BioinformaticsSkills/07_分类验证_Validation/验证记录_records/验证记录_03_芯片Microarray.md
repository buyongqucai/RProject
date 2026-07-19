# 验证记录 03_芯片Microarray: 基因芯片（toy 矩阵）

- **状态**: PASS
- **时间**: 2026-07-18T17:12:46
- **沙盒**: `07_分类验证_Validation/`


## 数据来源

- **Toy 芯片矩阵**（非全量 GEO 下载，避免大 CEL）：`E:\RProject\生信分析技能_BioinformaticsSkills\07_分类验证_Validation\数据_data\toy_microarray_matrix.csv`
- 设计：3 Control vs 3 Treat，100 probes

## 核对

| 项 | 结果 |
|----|------|
| 矩阵写出 | PASS |
| 粗差异探针（\|Δmean\|>1） | 50 |
| 技能对齐 | `基因芯片表达分析_Microarray`（与 RNA-seq 并列，不合并） |

## 说明

完整 Affy CEL 归一化需 `affy`/`limma`；本条验证**输入契约与组间设计**，全量 CEL 下载标为后续扩量。

