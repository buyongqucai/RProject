---
name: bioinfo-survival
description: >-
  生存分析与预后模型 / Survival：从 GEO-TCGA 拆出；KM/Cox/列线图。工具：survival, survminer, rms, ggplot2。
  触发：生存, KM, Cox, 预后, 列线图。
---

# 生存分析与预后模型 / Survival

## 1. 数据来源

时间+事件+特征

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 从 GEO-TCGA 拆出；KM/Cox/列线图
- 山水用途层标签：预测

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

KM→单/多因素 Cox→列线图→校准

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `survival` | 核心 R 包 | |
| 分析 | `survminer` | 核心 R 包 | |
| 分析 | `rms` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

对齐 [高分期刊出图范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) **Fig2-G–J / Fig3-H**：

| 图种 | 要求 |
|------|------|
| Kaplan–Meier | High/Low 色 = `bioinfo_survival`；**必须** number-at-risk 表；log-rank p 上图 |
| 实现 | 优先 `plot_km_journal`（survminer）或 `ggsurvplot(..., risk.table=TRUE)` |
| 可选 | Cox 森林图、列线图（主题一致、English） |

**强制：** 时间/事件来自官方临床或可溯源随访（禁止编造）；DPI≥600；SVG+PNG；每图 [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)。

## 7. 数据结果解读

最优截断防数据挖掘

## 8. 能否结合其它生信

GEO-TCGA、ROC、ML；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`（**data_provenance=REAL**）

| 项 | 内容 |
|----|------|
| 数据 | `GSE17536` OS + FCGR3A（山水临床表）；High/Low = 表达中位数分层 |
| 缓存 | `数据文件/real_GSE17536_OS_FCGR3A.csv` |
| 出图 | `plot_km_risk_table_journal` → KM + number-at-risk + log-rank |
| 复跑 | `代码文件/01_run_sample.R`；`SHANSHUI_ROOT` 可回源 |
| 包 | `survival`（必选）；`survminer` 可选（`options(bioinfo.km.use_survminer=TRUE)`） |

**处理步骤：** 临床 OS 时间/事件 → 签名基因分层 → KM → PlotQA。
