---
name: bioinfo-admet-qsar
description: >-
  类药性与QSAR / ADMET-QSAR：类药过滤、ADMET 预测与 QSAR/药效团扩展。。触发：ADMET, Lipinski, QSAR, 药效团, 类药性。
  已合并：`ADMET与类药性评价_ADMET`、`QSAR与药效团_QSAR-Pharmacophore`。
---

# 类药性与QSAR / ADMET-QSAR

## 1. 数据来源

化合物 SMILES；已知活性集（QSAR）。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组官方或实验记录可核对；禁止编造结果数字。

## 3. 何时选用本技能

- 类药过滤、ADMET 预测与 QSAR/药效团扩展。
- 山水用途层：药物-基因
- **不包含（边界）**：对接打分→分子对接；MD→分子动力学

不适用：应改用边界中列出的独立技能。

## 4. 数据处理方法

描述符→Lipinski/ADMET→（可选）QSAR 建模与药效团匹配。

### 已合并原技能触发词

`ADMET与类药性评价_ADMET`、`QSAR与药效团_QSAR-Pharmacophore` 的触发需求一律走本技能（见 catalog `deprecated_ids`）。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| （CLI/网页为主） | — | 见 CLI | |
| 上游/主分析 | `SwissADME` | CLI | 非 R |
| 上游/主分析 | `pkCSM` | CLI | 非 R |
| 上游/主分析 | `RDKit` | CLI | 非 R |
| 出图 | `ggplot2` + 出版级出图 | DPI≥600 | 可视化规范 |

## 6. 数据可视化

雷达图/观测预测散点；**DPI≥600；SVG+PNG；图面 English；防遮挡**。

**对齐高分期刊范式：** 遵循 [期刊范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) + [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)；近邻散点/条图继承 muted 色板。

## 7. 数据结果解读

网页预测非实验值；注意过拟合。

## 8. 能否结合其它生信

网络药理、分子对接；出图强制统一可视化规范。

## 样例验证

样例：`01_样例_sample/`
