# 08 — scRNA 骨架参数真实数据落地（后续迭代）

标签: 待分诊

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
