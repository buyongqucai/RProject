# TEST_REPORT — Journal paradigm sample (Microarray / GSE10072)

**Date:** 2026-07-19  
**Skill:** `基因芯片表达分析_Microarray`  
**Script run:** `01_样例_sample/代码文件/run_sample.R`  
**Also refreshed (QC only):** `公共库挖掘_GEO-TCGA/01_样例_sample/代码文件/run_sample.R`

## What was actually run

1. Parsed local GEO series matrix cache `geo_cache/GSE10072_series_matrix.txt` (**REAL**, not fabricated).
2. limma Tumor vs Normal on a reproducible 20-sample subset (10+10, `set.seed(10072)`).
3. Regenerated journal-style **MA** + **volcano** (`plot_volcano_journal`); PlotQA hooked via `delivery_save_plot`.
4. Wrote authenticity CSV from parsed series metadata.
5. GEO-TCGA sample re-run: PCA (`plot_pca_journal`) + mean-intensity box+jitter.

**Not run:** full-series DEG, enrichment/GSEA, UMAP, KM/TCGA-LUAD survival (Survival sample remains TOY; not used here).

## Accession & authenticity

| Field | Value | Check |
|-------|-------|-------|
| Accession | **GSE10072** | NCBI GEO lung adenocarcinoma vs normal lung (GPL96 HG-U133A) |
| GEO URL | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE10072 | Verified page loads; sample list present |
| Series n (parsed matrix) | **107** | Matches known GSE10072 sample count |
| Tumor / Normal in series | **58 / 49** | From `Sample_source_name_ch1` containing “Normal” vs else |
| Analysis subset n | **20** (10 Tumor + 10 Normal) | Documented subset for speed; not claimed as full series |
| Provenance | `data_provenance: REAL` | `数据文件/PROVENANCE.json` |
| Authenticity table | `结果文件/数据文件/数据表_GSE10072Authenticity.csv` | Written by runner |

Grouping is official GEO phenotype text — **no invented labels**.

## Figures produced

| Figure | Path (relative to skill `01_样例_sample/`) | PlotQA |
|--------|-----------------------------------------------|--------|
| MA | `结果文件/图片文件/示意图_TumorVsNormal_MA.png` (+ `.svg`) | WARN (title length) |
| Volcano | `结果文件/图片文件/火山图_TumorVsNormal_Volcano.png` (+ `.svg`) | WARN (label overlap) |
| PCA (GEO-TCGA skill) | `../公共库挖掘_GEO-TCGA/01_样例_sample/结果文件/图片文件/` PCA GSE10072Lung | PASS |
| Box (GEO-TCGA skill) | same folder, TissueIntensity box | WARN (title length) |

Pipeline STATUS: **PASS** (WARN does not block delivery per PlotQA policy).

## Honesty notes

- Expression values come from NCBI series matrix cache already in-repo; this host historically crashes `GEOquery::getGEO`, so download step was not re-fetched from FTP in this run.
- Tumor/Normal split follows source_name string rules used by the sample runner; website narrative is adenocarcinoma vs non-tumor lung — consistent with that coding.
- NetPharm figures were **not** touched.
