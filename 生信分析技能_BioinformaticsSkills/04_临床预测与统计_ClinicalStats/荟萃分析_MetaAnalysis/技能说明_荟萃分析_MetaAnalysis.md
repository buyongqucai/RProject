---
name: bioinfo-meta-analysis
description: >-
  荟萃分析 / MetaAnalysis：组学多队列 NES 合并 + 医学 SRMA（HR/森林图）。
  工具：meta, metafor, ggplot2。触发：荟萃, meta, 森林图, 异质性, PRISMA, 系统评价。
---

# 荟萃分析 / MetaAnalysis

## 1. 数据来源

- **组学轨：** 多队列效应量或 DEG/GSEA 方向（见 `01_样例_sample/`）
- **医学 SRMA 轨：** 已发表研究的 HR/OR/RR + 95%CI（见 `02_医学SRMA样例_MedicalSrmaPilot/`）

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。  
医学 SRMA：每条研究须有 PMID/DOI；`DATA_SOURCE.md` 标注 `data_provenance`；Pilot 不得冒充完整系统评价。

## 3. 何时选用本技能

- 从 GEO-TCGA 拆出的荟萃方法（组学）
- **干预/预后 RCT 或观察性研究的效应量合并**（医学 SRMA）
- 山水用途层标签：比较

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

**组学：** 效应量→固定/随机→异质性→森林图  

**医学 SRMA：** 提取 HR/CI → logHR + SE → REML 随机效应（`metafor`）→ I²/τ² → 森林图 / 留一法；正式投稿另加 PRISMA、RoB 2、GRADE（见 `文档_docs/`）。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `metafor` | REML 合并、预测区间、留一法 | 医学 SRMA 主用 |
| 分析 | `meta` | 可选便捷封装 | 骨架仍检查 |
| 分析 | `ggplot2` | 核心 R 包 | |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

脚本：`脚本_scripts/医学SRMA合并_poolMedicalSrma.R`、`医学SRMA出图_plotMedicalSrma.R`

## 6. 数据可视化

森林图；**DPI≥600；SVG+PNG；图面 English；防遮挡；PlotQA**。  
医学森林图轴：Hazard ratio（log scale）；合并菱形标注 I²。

## 7. 数据结果解读

异质性须报告（I²、τ²、Q）。  
医学结论须附研究设计局限与（正式 SR）GRADE；Pilot 报告必须标明 **非完整系统评价**。

## 8. 能否结合其它生信

GEO-TCGA、生存（单研究 HR）、文献检索；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。  
方法学文档：[`文档_docs/PROSPERO方案提纲_ProtocolOutline.md`](文档_docs/PROSPERO方案提纲_ProtocolOutline.md)、[`文档_docs/投稿包交付清单_JournalDeliverables.md`](文档_docs/投稿包交付清单_JournalDeliverables.md)。

## 样例验证

| 样例 | 说明 | 入口 |
|------|------|------|
| `01_样例_sample/` | 跨队列 GSEA KEGG NES 森林图 | `代码文件/run_sample.R` |
| `02_医学SRMA样例_MedicalSrmaPilot/` | 胰腺癌新辅助 vs 直接手术（3 RCT，L1 Pilot） | `代码文件/01_run_pilot.R` |