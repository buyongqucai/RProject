# 03 巨噬细胞 DEG 调整报告

**生成时间：** 2026-07-09 21:21:59
**项目路径：** E:/RProject

## 对应用户流程 Step 2
对照/疾病组巨噬细胞差异基因（上调、下调）。

## 方法
- GSE207177：样本级巨噬 pseudobulk + edgeR-TMM + voom
- GSE190856 / GSE207363：Seurat FindMarkers（低重复/功效不足）
- 阈值：padj < 0.05，|log2FC| > 1

## 主对比结果

| dataset | contrast | method | n_macrophages | n_sig | n_up | n_down | Sirt2_sig | Foxo1_sig |
|---|---|---|---|---|---|---|---|---|
| GSE190856 | CLP vs Steady | macrophage_FindMarkers | NA |  179 | NA | NA | FALSE | FALSE |
| GSE207363 | Sepsis | macrophage_FindMarkers | 5097 |  873 | 293 |  580 | FALSE | FALSE |
| GSE207363 | Sham | macrophage_FindMarkers | 5097 |  873 | 293 |  580 | FALSE | FALSE |
| GSE207177 | CLP | macrophage_pseudobulk_edgeR-TMM_voom | 3246 | 2891 | 973 | 1918 | FALSE | FALSE |
| GSE207177 | Control | macrophage_pseudobulk_edgeR-TMM_voom | 3246 | 2891 | 973 | 1918 | FALSE | FALSE |

## GSE207363 补充对比 Sepsis vs Control
- 显著 DEG：591（上调 357 / 下调 234）

## 输出
- `{GSE}_巨噬细胞_全部/显著差异基因.csv`
- `{GSE}_巨噬细胞_火山图.pdf`
