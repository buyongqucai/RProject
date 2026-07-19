# 数据来源

- **data_provenance: REAL**
- **accession: GSE207177**（鼠心 CLP sepsis scRNA / macrophage pseudobulk）
- **技能**：`基因集富集与通路_GSEA-Pathway`
- **analysis_kind**：`gsea`
- **规范**：统一交付规范_DeliveryStandards

## 本目录缓存（可无完整书清树运行）

| 文件 | 内容 |
|------|------|
| `real_GSE207177_macro_DEG.csv` | 巨噬细胞全部差异基因（gene, log2FC, pvalue, padj） |
| `real_GSE207177_MAMs_geneset.csv` | MAMs 交集基因 + category |
| `real_GSE207177_KEGG_GSEA_top20.csv` | KEGG GSEA Top20 by \|NES\| |
| `real_GSE207177_macro_MAMs_GSEA.csv` | 巨噬细胞 MAMs 通路 GSEA |
| `real_GSE207177_pathway_gene_heatmap.csv` | 线粒体功能障碍 + 内质网应激热图表达 |

## 原始路径（书清）

`SHUQING_ROOT` 默认 `E:/RProject/书清项目`：

- `GSE207177/结果/表格/GSE207177_巨噬细胞_全部差异基因.csv`
- `GSE207177/结果/表格/GSE207177_MAMs交集基因.csv`
- `GSE207177/结果/表格/GSE207177_GSEA_KEGG.csv`
- `GSE207177/结果/表格/GSE207177_巨噬细胞_*热图表达.csv`

详见 `PROVENANCE.md`。
