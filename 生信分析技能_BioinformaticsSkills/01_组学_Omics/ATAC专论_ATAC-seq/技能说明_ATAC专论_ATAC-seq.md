---
name: bioinfo-atac
description: >-
  ATAC专论 / ATAC-seq：开放染色质专用（异于 ChIP）。工具：Signac, ggplot2, MACS2, Bowtie2。
  触发：ATAC, 染色质开放。
---

# ATAC专论 / ATAC-seq

## 1. 数据来源

ATAC-seq

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 开放染色质专用（异于 ChIP）
- 山水用途层标签：病因-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

比对→peak→差异→motif

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `Signac` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `MACS2` | CLI 工具 | 非 R |
| 上游/主分析 | `Bowtie2` | CLI 工具 | 非 R |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

峰注释/足迹；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

需线粒体过滤等 QC

## 8. 能否结合其它生信

ChIP、单细胞多组学；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 9. 外部软件操作 SOP（BLOCKED 样例）

本环境不跑 ATAC 上游；样例 `STATUS=BLOCKED`。完整流程请在 Linux/WSL 或 HPC：

1. **质控**：`fastqc` / `fastp` → MultiQC 汇总。
2. **比对**：`bowtie2 -x hg38 -1 R1 -2 R2 | samtools sort -o sorted.bam`（ATAC 常用 `--very-sensitive`）。
3. **Peak**：`macs2 callpeak -t sorted.bam -f BAM -g hs -n sample --nomodel --shift -100 --extsize 200`。
4. **R 下游**：`Signac` → 差异开放区、motif、footprint。
5. **交付**：peak bed + 英文图面；`PROVENANCE.json` 写 GEO/SRA accession。

## 样例验证

样例：`01_样例_sample/`
