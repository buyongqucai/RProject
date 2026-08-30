# 样例目录说明 / Sample layout

本样例已按 DeliveryStandards 约定：

- `数据文件/` = **原始/raw 输入 only**
- `代码文件/` = 脚本；**结果**在 `代码文件/结果文件/`
- 文件名可用流水线序号前缀 `01_`、`02_`…

规范 SSOT：`00_基础_Foundation/统一交付规范_DeliveryStandards/文档_docs/样例目录与命名_SampleLayoutNaming.md`

技能流水线（GEO 自动 QC→Doublet→注释→pseudobulk）见上级 `技能说明_*.md` 与 `脚本_scripts/`；本样例侧重 UMAP/比例图交付演示（`data_provenance=REAL` 公共坐标/比例表）。

运行（若已编号）：

```bash
Rscript 代码文件/01_run_sample.R
```

若仍为 `run_sample.R`，则：

```bash
Rscript 代码文件/run_sample.R
```
