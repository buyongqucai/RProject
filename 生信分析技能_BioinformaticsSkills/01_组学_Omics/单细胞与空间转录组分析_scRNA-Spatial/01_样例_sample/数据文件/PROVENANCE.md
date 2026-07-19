# PROVENANCE — scRNA-Spatial sample (REAL)

| Field | Value |
|-------|--------|
| data_provenance | **REAL** |
| UMAP / feature | **GSE164522** (山水) |
| Stacked proportions | **GSE207177** (书清) preferred |
| Extracted | 2026-07-19 |

## Honesty

- 书清 GSE190856/207177/207363 仅有 UMAP **PDF**，无坐标 CSV；故 UMAP 不从书清编造。
- UMAP 来自山水已质控的 Seurat 子样 RDS（7228 → 缓存 3000 cells；marker-informed UMAP，非全转录组 HVG — 与项目留痕一致）。
- Feature UMAP 使用元数据列 `FCGR3A_raw`（真实表达分数，非随机）。
- 堆叠比例优先书清 `GSE207177_细胞类型比例.csv`（CLP vs Control × celltype）。

## Figure → source

1. Discrete celltype UMAP — `real_GSE164522_umap_subsample.csv`
2. Feature UMAP (FCGR3A) — same
3. Stacked proportions — `real_GSE207177_celltype_proportions.csv`
