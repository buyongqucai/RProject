# 08 — scRNA 骨架参数真实数据落地（后续迭代）

标签: 已完成（2026-08-30）

## 修复记录

- 骨架新增三函数并接入 `run_scrna_pipeline` 签名（默认值与技能说明 §4 一致）：`scrna_qc_filter`（QC_MIN_FEATURE_FLOOR=200）、`scrna_resolution_grid`（RES_GRID=0.1–1.2 step 0.1）、`scrna_find_markers`（DE_LOGFC=1 / DE_FDR=0.05）；`pb_min_samples` 接入 `choose_de_method`。
- 红→绿：`测试_tests/test_scrna_params.R`（testthat 12 PASS）锁定签名默认值、QC 过滤、网格列、DE 阈值过滤。
- 真实数据 E2E：10x PBMC3k（32738×2700 原始 UMI，provenance 登记 DATA_SOURCE.md）跑通 QC→网格聚类→UMAP→marker；res=0.6 得 8 簇，5261 marker 行通过阈值；审计 `审计后检_AuditPost_PBMC3k.csv` = REAL；UMAP PNG+SVG PlotQA PASS。
- 技能说明 §4 恢复「默认值」表述；`run_sample.R` REAL 审计的位置参数 toy=TRUE→FALSE 顺手修正。
- 范围说明：DoubletFinder/harmony/edgeR 未装，单样本 PBMC3k 走 cell_level_exploratory（符合 choose_de_method 契约）；GEO 自动下载阶段仍为 TODO（不属本议题）。

## 来源

议题 05 选「文档降级」后的后续动作；ADR 0002 真实数据循环。

## 目标

在 `运行单细胞空转骨架_runScrnaSkeleton.R` 落地技能说明 §4 的规划参数（`QC_MIN_FEATURE_FLOOR=200`、`PB_MIN_SAMPLES=2`、`DE_LOGFC/DE_FDR=1/0.05`、`RES_GRID=0.1–1.2`），并接入真实公开数据（如 GSE164522 全量或 PBMC3k）跑通 QC → 聚类 → DE 主链。

## 验收标准

- 骨架函数接受上述参数并有实际作用（非 TODO 注释）；
- 真实数据 E2E 跑通，审计表 `data_provenance=REAL`；
- 技能说明 §4 参数表恢复「默认值」表述；
- testthat 或 pytest 接缝测试锁定参数透传。

## 备注

工作量预估较大（Seurat 依赖 + 数据下载 + 运行时长），建议独占一个迭代循环，不与其他议题并行。
