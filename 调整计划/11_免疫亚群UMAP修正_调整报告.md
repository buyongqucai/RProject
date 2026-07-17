# 11 免疫亚群 UMAP 修正调整报告

**生成时间：** 2026-07-13 16:32:56
**项目路径：** E:\RProject

## 调整内容
1. 免疫亚群 UMAP **数字簇 → 细胞名称**（`immune_lineage`）
2. 剔除非免疫污染（内皮 / 成纤维 / 心肌 / 周细胞等）
3. 修复 `annotate_by_markers` 误用旧 `score_*` 列导致的错误标注
4. `IMMUNE_LINEAGE` 统一：T_cells / NK_cells 分列；Granulocytes 替代 Neutrophils

## 原因
- 原 `_UMAP_免疫聚类.pdf` 按 `seurat_clusters` 着色，故为 0–15 数字
- `immune_score > 0` 过松，基质细胞混入免疫子集
- `annotate_by_markers` 用 `grep('^score_')` 读到全组织 CARDIAC 分数，误标 Endothelial/Fibroblasts

## 各数据集修正前后

### GSE190856
- 免疫细胞数：50155
- 非免疫标签细胞数：0 → **0**
- 修正后谱系：Macrophages, Granulocytes, Monocytes, Cycling, B_cells, T_cells, Dendritic

| celltype | n_after |
|---|---|
| Macrophages | 34389 |
| Granulocytes |  5777 |
| Monocytes |  2817 |
| Cycling |  2362 |
| B_cells |  2171 |
| T_cells |  1607 |
| Dendritic |  1032 |

### GSE207363
- 免疫细胞数：12336
- 非免疫标签细胞数：0 → **0**
- 修正后谱系：Dendritic, Macrophages, B_cells, Granulocytes, Monocytes, T_cells, Cycling

| celltype | n_after |
|---|---|
| Dendritic | 7319 |
| Macrophages | 1607 |
| B_cells |  818 |
| Granulocytes |  801 |
| Monocytes |  702 |
| T_cells |  610 |
| Cycling |  479 |

### GSE207177
- 免疫细胞数：5048
- 非免疫标签细胞数：0 → **0**
- 修正后谱系：Dendritic, Macrophages, T_cells, Granulocytes, B_cells, Monocytes, NK_cells

| celltype | n_after |
|---|---|
| Dendritic | 2377 |
| Macrophages |  760 |
| T_cells |  637 |
| Granulocytes |  445 |
| B_cells |  400 |
| Monocytes |  334 |
| NK_cells |   95 |

## 输出文件
- `{GSE}_UMAP_免疫聚类.pdf`（细胞名）
- `{GSE}_UMAP_免疫谱系.pdf`（淋巴系+髓系）
- `{GSE}_免疫谱系_修正前后对比.csv`
- 更新 `{GSE}_immune.rds`

## 验收
- 免疫图图例为细胞名，无 0–15 主图例
- `immune_lineage` 不含 Endothelial / Fibroblasts / Cardiomyocytes / Pericytes

