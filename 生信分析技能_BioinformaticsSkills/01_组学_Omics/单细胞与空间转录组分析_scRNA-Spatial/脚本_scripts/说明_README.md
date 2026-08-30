# 脚本说明 / Scripts README

## 骨架

[`运行单细胞空转骨架_runScrnaSkeleton.R`](运行单细胞空转骨架_runScrnaSkeleton.R)

- 对齐技能说明中的 **GEO 自动单细胞流水线**（参考 [微信文](https://mp.weixin.qq.com/s/Z8x1a1Q8A5uQq3qAzBpDpg)）
- 提供：目录树 `GSE*_auto_scRNA/{00_download…05_reports}`、原始计数校验 stub、DE/Harmony 方法选择、决策 CSV、书清工具 source、VizStandards 出图加载
- `status = "skeleton"`：下载/DoubletFinder/完整 DEG 实现由 Agent 按技能说明补全
- **已实现主链（议题 08）**：`scrna_qc_filter`（QC_MIN_FEATURE_FLOOR）、`scrna_resolution_grid`（RES_GRID）、`scrna_find_markers`（DE_LOGFC/DE_FDR），并接入 `run_scrna_pipeline` 签名；真实数据 E2E 见 `01_样例_sample/代码文件/run_pbmc3k_pipeline.R`（PBMC3k）

```r
source("…/运行单细胞空转骨架_runScrnaSkeleton.R", encoding = "UTF-8")
run_scrna_pipeline(geo_id = "GSE157278")           # GEO 自动目录
run_scrna_pipeline(seurat_rds = "path/to.rds", out_dir = "…/结果文件")
```

## 生产

- `书清项目/共享脚本/工具_scRNA*.R`、`工具_单细胞对象.R`
- `06_已落地流水线_ProductionPipelines/差异分析与UMAP流水线_DEG-UMAP`

## 统计红线（写入报告）

1. 仅分析原始 counts；拒绝芯片/TPM/log 矩阵  
2. DoubletFinder **按样本**，不在合并对象上跑  
3. 每组样本 ≥2 → edgeR pseudobulk；否则细胞级 Wilcoxon +「探索性」标注  
4. 自动决策写入 `05_reports/automatic_decisions.csv`（或样例 `报告文件/`）
