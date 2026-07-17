# 13 本轮执行：Mac/DC 注释收紧 + GSE267388 清理

**生成时间：** 2026-07-13 16:53:22
**项目路径：** E:/RProject

## C1 Macrophages vs Dendritic
- Dendritic marker 改为 Flt3/Clec9a/Xcr1（去掉易交叉的 Itgax）
- 全组织 celltype 为 Macrophages/Monocytes/Granulocytes/B/T 时优先锁定，禁止 Mac→DC 误标

| dataset | n_mac_full | n_mac_immune | n_dendritic | n_immune | labels |
|---|---|---|---|---|---|
| GSE190856 | 39756 | 39756 | 0 | 50155 | Macrophages, Monocytes, Granulocytes, B_cells, T_cells |
| GSE207363 |  9433 |  9433 | 0 | 12336 | Macrophages, B_cells, Granulocytes, Monocytes, T_cells |
| GSE207177 |  3246 |  3246 | 0 |  5048 | Macrophages, T_cells, Granulocytes, B_cells |

## C2 GSE267388
- 重命名：5 个
GSE267388_CLP12h_vs_24h_火山图.pdf → GSE267388_LPS_vs_PBS_火山图.pdf
GSE267388_CLP12h_vs_24h_GO.pdf → GSE267388_LPS_vs_PBS_GO.pdf
GSE267388_CLP12h_vs_24h_GO图.pdf → GSE267388_LPS_vs_PBS_GO图.pdf
GSE267388_CLP12h_vs_24h_KEGG.pdf → GSE267388_LPS_vs_PBS_KEGG.pdf
GSE267388_CLP12h_vs_24h_KEGG图.pdf → GSE267388_LPS_vs_PBS_KEGG图.pdf

- 删除冗余：17 个
GSE267388_bulk_LR通讯变化.pdf
GSE267388_GSEA_GO.pdf
GSE267388_GSEA_KEGG.pdf
GSE267388_Hub配体靶标网络.pdf
GSE267388_MAMs时序箱线图.pdf
GSE267388_MAMs通路时序评分.pdf
GSE267388_Sirt2_Foxo1时序.pdf
GSE267388_Top增强通讯对.pdf
GSE267388_UMAP.pdf
GSE267388_UMAP_免疫聚类.pdf
GSE267388_UMAP_免疫谱系.pdf
GSE267388_UMAP_细胞类型.pdf
GSE267388_WGCNA模块表型相关.pdf
GSE267388_巨噬心肌通讯.pdf
GSE267388_配体受体表达.pdf
GSE267388_细胞比例环图.pdf
GSE267388_细胞通讯热图.pdf

## 验收
- GSE207363 免疫谱系中 Macrophages 应接近全组织巨噬数量级，不再 DC >> Mac
- GSE267388 无 CLP12h_vs_24h 文件名

