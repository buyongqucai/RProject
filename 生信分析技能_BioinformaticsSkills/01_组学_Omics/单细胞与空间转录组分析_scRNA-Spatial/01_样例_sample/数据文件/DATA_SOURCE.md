# DATA_SOURCE (REAL, skill-local cache)

- **data_provenance:** REAL
- **accession / source:** GSE207177
- **note:** cell type counts by group
- **origin tree:** 书清（已复制进本技能；样例优先读本目录，不依赖完整项目树）
- **embedded:** 2026-07-19

## pbmc3k/（议题 08，2026-08-30）

- **data_provenance:** REAL
- **accession / source:** 10x Genomics 官方 PBMC3k 示例数据集
- **URL:** https://cf.10xgenomics.com/samples/cell/pbmc3k/pbmc3k_filtered_gene_bc_matrices.tar.gz
- **内容:** `filtered_gene_bc_matrices/hg19/{matrix.mtx,barcodes.tsv,genes.tsv}`（32738 基因 × 2700 细胞，原始 UMI 计数）
- **用途:** `代码文件/run_pbmc3k_pipeline.R` E2E：骨架四参数（QC floor=200 / RES_GRID 0.1–1.2 / DE_LOGFC=1 / DE_FDR=0.05）真实数据验证
- **embedded:** 2026-08-30（tar.gz 保留原件，hg19/ 为解包结果）
