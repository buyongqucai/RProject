# 数据来源

- **data_provenance: REAL**
- **UMAP accession: GSE164522**（山水项目肝转移单细胞 UMAP 子样）
- **Proportion accession: GSE207177**（书清项目细胞类型比例）
- **技能**：`单细胞与空间转录组分析_scRNA-Spatial`
- **analysis_kind**：`scrna`
- **规范**：统一交付规范_DeliveryStandards

## 本目录缓存

| 文件 | 内容 |
|------|------|
| `real_GSE164522_umap_subsample.csv` | 3000 cells: umap_1/2, celltype, group, tissue, patient, FCGR3A score |
| `real_GSE164522_patient_celltype_proportions.csv` | patient × celltype from same subsample |
| `real_GSE207177_celltype_proportions.csv` | group × celltype counts（书清） |

## 原始路径

- UMAP RDS: `SHANSHUI_ROOT`/`GSE164522/模块B_肝转移单细胞/03_输出数据/GSE164522_seurat_umap_subsample.rds`
- 比例: `SHUQING_ROOT`/`GSE207177/结果/表格/GSE207177_细胞类型比例.csv`

默认：`SHUQING_ROOT=E:/RProject/书清项目`，`SHANSHUI_ROOT=E:/RProject/山水项目`。

详见 `PROVENANCE.md`。
