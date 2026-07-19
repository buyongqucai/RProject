# PROVENANCE — GSEA-Pathway sample (REAL)

| Field | Value |
|-------|--------|
| data_provenance | **REAL** |
| Primary accession | **GSE207177** |
| Project tree | 书清项目 (`SHUQING_ROOT`, default `E:/RProject/书清项目`) |
| Extracted | 2026-07-19 |
| Not in git | 书清/山水 full trees are gitignored; only slim caches here |

## Figure → source mapping

1. **NES bar / enrichment bubble** — `GSE207177_GSEA_KEGG.csv` (Top pathways by \|NES\|)
2. **Classic GSEA ES curve** — ranked metric = macrophage DEG `log2FC`; gene set = `GSE207177_MAMs交集基因.csv`
3. **Pathway gene heatmap** — `GSE207177_巨噬细胞_线粒体功能障碍热图表达.csv` + `...内质网应激热图表达.csv` (row z-score for display)

## Notes

- Titles must not say “(toy)”.
- MAMs pathway GSEA table for macrophage may contain few gene sets; classic curve uses MAMs intersection genes on the full DEG rank, which is the intended demo.
