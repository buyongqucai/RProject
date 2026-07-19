# 脚本说明 / Scripts README — 转录组 RNA-seq

## 路径

- 本目录目标文件：`运行转录组骨架_runRnaseqSkeleton.R`（需 Agent 模式写入）
- 生产实现：`书清项目/共享脚本/` + `06_已落地流水线_ProductionPipelines/差异分析与UMAP流水线_DEG-UMAP`

## 输入 / 输出契约

| 输入 | 输出 |
|------|------|
| counts 矩阵 + sample_info | DEG csv；火山/热图/富集 SVG+PNG（DPI≥600） |

## 依赖

`limma` / `edgeR` / `DESeq2` / `clusterProfiler` / `ggplot2` / 出版级出图
