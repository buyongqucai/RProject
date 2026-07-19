---
name: bioinfo-genetic-downstream
description: >-
  遗传关联下游 / GeneticDownstream：GWAS 之后的 eQTL、共定位/TWAS、PRS。。触发：eQTL, QTL, coloc, TWAS, PRS, PRSice。
  已合并：`eQTL与QTL作图_eQTL`、`共定位与TWAS_Coloc-TWAS`、`多基因风险评分_PRS`。
---

# 遗传关联下游 / GeneticDownstream

## 1. 数据来源

基因型+表达；GWAS 与 eQTL 汇总；目标队列基因型。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组官方或实验记录可核对；禁止编造结果数字。

## 3. 何时选用本技能

- GWAS 之后的 eQTL、共定位/TWAS、PRS。
- 山水用途层：病因-基因/预测
- **不包含（边界）**：全基因组关联主分析→GWAS；因果 MR→孟德尔随机化

不适用：应改用边界中列出的独立技能。

## 4. 数据处理方法

小节：eQTL → coloc/TWAS → PRS。

### 已合并原技能触发词

`eQTL与QTL作图_eQTL`、`共定位与TWAS_Coloc-TWAS`、`多基因风险评分_PRS` 的触发需求一律走本技能（见 catalog `deprecated_ids`）。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `MatrixEQTL` | 核心 R 包 | |
| 分析 | `coloc` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `PRSice-2` | CLI | 非 R |
| 上游/主分析 | `LDpred2` | CLI | 非 R |
| 出图 | `ggplot2` + 出版级出图 | DPI≥600 | 可视化规范 |

## 6. 数据可视化

位点图/区域图/分位数风险；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

样本量与人群转移性。

## 8. 能否结合其它生信

GWAS、孟德尔随机化（MR 独立）；出图强制统一可视化规范。

## 样例验证

样例：`01_样例_sample/`
