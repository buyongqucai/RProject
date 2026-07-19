---
name: bioinfo-insilico-ko
description: >-
  虚拟敲除与扰动 / InSilicoKO：从 DEG-UMAP 延展独立。工具：ggplot2。
  触发：虚拟敲除, in silico KO, CellOracle。
---

# 虚拟敲除与扰动 / InSilicoKO

## 1. 数据来源

TF 网络+表达

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 从 DEG-UMAP 延展独立
- 山水用途层标签：预测

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

regulon/GRN→扰动模拟→表型基因逆转评估

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `ggplot2` | 核心 R 包 | |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

扰动前后对比；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

模型假设强

## 8. 能否结合其它生信

TF 网络、细胞通讯；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`
