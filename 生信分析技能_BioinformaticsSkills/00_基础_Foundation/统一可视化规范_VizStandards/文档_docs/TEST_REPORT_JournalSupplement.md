# TEST_REPORT — Journal plot-type supplement (2026-07-19)

**Scope:** Fill Fig1–3 journal gaps in VizStandards SSOT + regenerate target skill samples.  
**Frozen:** `网络药理学_NetworkPharmacology` — **no** plot code / color / layout / sample figure changes.

## A. New helpers (`出版级出图_PublicationPlot.R`)

| Helper | Journal role |
|--------|----------------|
| `compute_gsea_running_es` | Running ES from ranked metric + gene set |
| `plot_gsea_classic_journal` | ES curve + barcode + ranked metric |
| `plot_umap_feature_journal` | Continuous feature UMAP (`bioinfo_feature_blue`) |
| `plot_stacked_proportion_journal` | Sample × celltype stacked bars (± risk facet) |
| `plot_km_risk_table_journal` | KM + 95% CI + log-rank p + number-at-risk |
| `save_km_journal` | Save ggsurvplot / patchwork KM objects |
| `plot_box_bracket_journal` | Box + jitter + significance brackets |
| `plot_paired_box_journal` | Paired boxes + grey connectors + paired p |
| `plot_severity_trend_journal` | Severity/time trend smooth + CI |
| `plot_sample_dendrogram_journal` | Sample hclust dendrogram / cladogram-style |
| `plot_pathway_activity_heatmap_journal` | GSVA-style pathway × sample heatmap |
| `plot_pc_density_box_journal` | PC density + box combo |

Delivery plot-type keys added in `规范_出图与命名_PlotNaming.R`: `gsea`, `featureumap`, `stackedbar`/`proportion`, `dendrogram`/`cladogram`, `trend`, `pairedbox`, `densitybox`.

## B. Regenerated sample figures (STATUS)

| Skill | Provenance | New / updated figures | Notes |
|-------|------------|----------------------|-------|
| GSEA-Pathway | **REAL** GSE207177 | `01_柱状图_NES_Pathways_Bar`, `02_气泡图_NES_Bubble_Bubble`, `03_GSEA曲线_ClassicEnrichment_GSEA`, `04_热图_PathwayActivity_Heatmap` | KEGG GSEA NES; classic ES = macrophage DEG log2FC + MAMs geneset; mito/ER heatmap from 书清 |
| scRNA-Spatial | **REAL** GSE164522 + GSE207177 | `01_UMAP图_Celltype_UMAP`, `02_特征UMAP_FCGR3A_FeatureUMAP`, `03_堆叠比例图_ByGroup_StackedProportion` | UMAP from 山水 Seurat subsample; proportions from 书清 celltype table |
| Survival | TOY | `01_生存曲线_HighVsLow_RiskTable_KaplanMeier` | KM + risk table + CI + log-rank (no quick TCGA table this pass) |
| DoseTime | TOY | line + `02_趋势图_ModuleSeverity_Trend` + `03_配对箱线图_PrePost_PairedBox` | |
| ImmuneInfiltration | **REAL** GSE207177 | bar + `02_箱线图_ScoreBrackets_Box` | 书清 CIBERSORT-like fractions; Macrophages Control vs CLP brackets |
| Phylogenetics | TOY counts | bar + `02_样本树状图_SampleTree_Dendrogram` | Dendrogram from existing `toy_counts.csv` |
| WGCNA | TOY | heatmap/bar + `03_趋势图_ME_Severity_Trend` | |
| RNA-seq | **REAL** (airway) | volcano/PCA/heatmap + `04_样本树状图_AirwaySamples_Dendrogram` + `05_密度箱线组合_PC1_ByDex_DensityBox` + `06_箱线图_PathwayScoreBrackets_Box` | Dendrogram/PC/brackets from real voom matrix |

All listed sample scripts exited **0** with STATUS **PASS** (PlotQA label-length WARN on some long English titles — non-blocking).

### B2. REAL data promotion (2026-07-19)

| Skill | Accession(s) | Cached extracts under `数据文件/` | Live roots |
|-------|--------------|-----------------------------------|------------|
| GSEA-Pathway | GSE207177 | `real_GSE207177_macro_DEG.csv`, `real_GSE207177_MAMs_geneset.csv`, `real_GSE207177_KEGG_GSEA_top20.csv`, `real_GSE207177_pathway_gene_heatmap.csv` | `SHUQING_ROOT` |
| scRNA-Spatial | GSE164522 (UMAP), GSE207177 (proportions) | `real_GSE164522_umap_subsample.csv` (3000 cells), `real_GSE207177_celltype_proportions.csv` | `SHANSHUI_ROOT` / `SHUQING_ROOT` |
| ImmuneInfiltration | GSE207177 | `real_GSE207177_CIBERSORT_fractions.csv` | `SHUQING_ROOT` |

书清 UMAP 仅有 PDF、无坐标 CSV → 未编造坐标；山水 `GSE164522_seurat_umap_subsample.rds` 为 REAL embedding（marker-informed subsample，见项目留痕）。

## C. Skipped / honesty notes

- **Survival:** still TOY (no quick ready OS table wired this pass).
- **DoseTime / Phylogenetics / WGCNA:** still TOY.
- **NetworkPharmacology:** untouched (frozen).
- **DEG-UMAP:** already had volcano+UMAP; not re-run this pass (RNA-seq covers dendrogram/brackets/density on REAL data).

## D. Docs touched

- `技能说明_统一可视化规范_VizStandards.md` — helper table
- `高分期刊出图范式_JournalFigureParadigm.md` — recipe pointers + revision
- `出图后审核_PlotQA.md` — legend / figure-type checklist rows
- Desktop: `C:/Users/10540/Desktop/期刊图种补充完成清单.md`
- Desktop: `C:/Users/10540/Desktop/REAL样例数据切换完成清单.md`
