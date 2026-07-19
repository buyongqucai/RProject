# 数据来源

- **data_provenance: REAL**
- **accession**: GSE10072（肺腺癌 vs 正常肺 Affymetrix）
- **缓存**: `geo_cache/GSE10072_series_matrix.txt.gz`（NCBI FTP 下载）
- **样例范围**: 24 样本子集 + 2000 probe；元数据表 + PCA + 组织箱线
- **说明**: 本机 `GEOquery::getGEO` 崩溃，使用本地 series matrix 解析；见 `PROVENANCE.json`
