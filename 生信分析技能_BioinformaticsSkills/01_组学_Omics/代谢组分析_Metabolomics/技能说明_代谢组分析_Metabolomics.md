---
name: bioinfo-metabolomics
description: >-
  代谢与脂质 / Metabolomics-Lipid：小分子/脂质差异与可选通量估计。。触发：代谢组, OPLS-DA, 脂质组, lipidomics, 通量, FBA。
  已合并：`脂质组分析_Lipidomics`、`代谢通量分析_Fluxomics`。
---

# 代谢与脂质 / Metabolomics-Lipid

## 1. 数据来源

LC-MS/GC-MS 峰表；脂质定量表；约束模型/13C（通量小节）。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组官方或实验记录可核对；禁止编造结果数字。

## 3. 何时选用本技能

- 小分子/脂质差异与可选通量估计。
- 山水用途层：病因-代谢物
- **不包含（边界）**：蛋白酶层→蛋白组；菌群组成→16S/宏基因组

不适用：应改用边界中列出的独立技能。

## 4. 数据处理方法

导入→归一化→PCA/OPLS-DA→VIP；脂质小节；通量小节（COBRA）。

### 已合并原技能触发词

`脂质组分析_Lipidomics`、`代谢通量分析_Fluxomics` 的触发需求一律走本技能（见 catalog `deprecated_ids`）。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `ropls` | 核心 R 包 | |
| 分析 | `mixOmics` | 核心 R 包 | |
| 分析 | `lipidr` | 核心 R 包 | |
| 分析 | `limma` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `COBRApy` | CLI | 非 R |
| 出图 | `ggplot2` + 出版级出图 | DPI≥600 | 可视化规范 |

## 6. 数据可视化

PCA/VIP/热图；**DPI≥600；SVG+PNG；图面 English；防遮挡**。

**对齐高分期刊范式：** 无直接面板一一对应时，遵循 [VizStandards 期刊范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) + [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)；近邻图种用 PCA/热图/水平柱或点图（OPLS-DA 分数图对齐 Fig1-b 分组色）。

## 7. 数据结果解读

鉴定置信度；通量模型假设强。

## 8. 能否结合其它生信

转录组、网络药理、多组学；出图强制统一可视化规范。

## 样例验证

样例：`01_样例_sample/`
