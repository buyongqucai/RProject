---
name: bioinfo-repro-workflow
description: >-
  可复现工作流 / ReproducibleWorkflow：可复现编排与环境固定。工具：sessioninfo, Snakemake, Nextflow, Docker。
  触发：Snakemake, Nextflow, 可复现, 容器。
---

# 可复现工作流 / ReproducibleWorkflow

## 1. 数据来源

分析脚本集

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 可复现编排与环境固定
- 山水用途层标签：基础

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

容器化→工作流→会话信息

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `sessioninfo` | 核心 R 包 | |
| 上游/主分析 | `Snakemake` | CLI 工具 | 非 R |
| 上游/主分析 | `Nextflow` | CLI 工具 | 非 R |
| 上游/主分析 | `Docker` | CLI 工具 | 非 R |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

DAG 图可选；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

环境漂移

## 8. 能否结合其它生信

全部技能；出图强制 [统一可视化规范](../统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`
