---
name: bioinfo-proteomics
description: >-
  蛋白组与PTM / Proteomics-PTM：蛋白定量差异、PTM 位点、AP-MS 物理互作。。触发：蛋白质组, LFQ, TMT, DIA, 磷酸化, PTM, AP-MS, PPI质谱。
  已合并：`磷酸化与PTM蛋白组_PTM-Proteomics`、`相互作用组AP-MS_Interactomics`。
---

# 蛋白组与PTM / Proteomics-PTM

## 1. 数据来源

MaxQuant/Spectronaut 定量；修饰肽表；AP-MS 鉴定表。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组官方或实验记录可核对；禁止编造结果数字。

## 3. 何时选用本技能

- 蛋白定量差异、PTM 位点、AP-MS 物理互作。
- 山水用途层：病因-基因
- **不包含（边界）**：仅知识库 STRING 网络且无质谱→蛋白质互作网络_PPI-Network

不适用：应改用边界中列出的独立技能。

## 4. 数据处理方法

过滤→limma/MSstats→富集；PTM 小节；AP-MS 对照过滤→网络。

### 已合并原技能触发词

`磷酸化与PTM蛋白组_PTM-Proteomics`、`相互作用组AP-MS_Interactomics` 的触发需求一律走本技能（见 catalog `deprecated_ids`）。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `limma` | 核心 R 包 | |
| 分析 | `MSstats` | 核心 R 包 | |
| 分析 | `clusterProfiler` | 核心 R 包 | |
| 分析 | `STRINGdb` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `MaxQuant` | CLI | 非 R |
| 上游/主分析 | `FragPipe` | CLI | 非 R |
| 出图 | `ggplot2` + 出版级出图 | DPI≥600 | 可视化规范 |

## 6. 数据可视化

火山/热图/网络；**DPI≥600；SVG+PNG；图面 English；防遮挡**。

**对齐高分期刊范式：** 遵循 [期刊范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) + [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)；近邻：火山/热图/PCA（Fig2-A/B、Fig1-b）；富集用水平柱或点图。

## 7. 数据结果解读

区分总量与修饰；AP-MS 非特异结合。

## 8. 能否结合其它生信

转录组、代谢组、PPI 网络技能（知识库 PPI≠AP-MS）；出图强制统一可视化规范。

## 样例验证

样例：`01_样例_sample/`
