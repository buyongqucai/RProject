# Lung cancer disease-DB pull test (English)

**Date:** 2026-07-19  
**Query terms (English):** `lung cancer`, `Lung Neoplasms`, `MESH:D008175`

## Skill primary DBs (delivery SOP)

From user delivery / skill 疾病六库：`GeneCards`, `TTD`, `DrugBank`, `OMIM`, `CTD`, `DisGeNET`（https://disgenet.com/）。  
按**英文病名**在各库网页导出；本环境**不**自动登录爬取 GeneCards/TTD/DrugBank/DisGeNET。

样例病名仍为 `Atherosclerosis`（见上级 `PROVENANCE.json`）。本目录仅为 **lung cancer 拉取探测**。

## Test results

| Source | Result | n genes | Notes |
|--------|--------|---------|-------|
| CTD curated bulk（宽过滤：lung + cancer/neoplasm/carcinoma） | **SUCCESS** | **575** | `CTD_bulk_filter_lung_cancer_genes.csv` |
| CTD strict `MESH:D008175` / `Lung Neoplasms` | **SUCCESS** | **295** | `CTD_MESH_D008175_Lung_Neoplasms_genes.csv` |
| OpenTargets GraphQL `"lung cancer"` → `MONDO_0008903` | **SUCCESS** | 200 returned / 16017 total | `OpenTargets_lung_cancer_associatedTargets.csv`（陪跑） |
| CTD Batch Query API | FAIL（HTTP 302 / HTML） | — | 页面改版 |
| GeneCards / OMIM HTTP | 403 | — | 需浏览器按英文名导出 |

推荐报告主数字：**MESH:D008175 / Lung Neoplasms → 295 genes（CTD curated）**。

## Artifacts

- `TEST_REPORT.json` — 完整探测报告  
- `CTD_curated_genes_diseases.tsv.gz` — CTD 官方 curated 批量  
- `CTD_bulk_filter_lung_cancer_genes.csv` — 宽过滤基因表（575）  
- `CTD_MESH_D008175_Lung_Neoplasms_genes.csv` — MeSH 严格过滤  

## How to re-run

```text
# download + filter (Python)
# URL: https://ctdbase.org/reports/CTD_curated_genes_diseases.tsv.gz
# filter DiseaseID == MESH:D008175 or DiseaseName == Lung Neoplasms
```

OMIM API（若要用程序化）：申请 https://www.omim.org/api 后设置 `OMIM_API_KEY`。
