---
name: bioinfo-tumor-somatic
description: >-
  肿瘤体细胞景观 / TumorSomatic：TMB、突变特征与克隆演化解读。。触发：TMB, mutation signature, 克隆演化, PyClone, sigminer。
  已合并：`肿瘤突变负荷与特征_TMB-Signature`、`肿瘤异质性与克隆演化_ClonalEvolution`。
---

# 肿瘤体细胞景观 / TumorSomatic

## 1. 数据来源

体细胞 VCF；多区域/纵向 VAF。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组官方或实验记录可核对；禁止编造结果数字。

## 3. 何时选用本技能

- TMB、突变特征与克隆演化解读。
- 山水用途层：病因-基因
- **不包含（边界）**：CNV 分段主分析→拷贝数变异；融合→RNA融合基因检测

不适用：应改用边界中列出的独立技能。

## 4. 数据处理方法

计 TMB→签名分解→（可选）克隆聚类/鱼图。

### 已合并原技能触发词

`肿瘤突变负荷与特征_TMB-Signature`、`肿瘤异质性与克隆演化_ClonalEvolution` 的触发需求一律走本技能（见 catalog `deprecated_ids`）。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `sigminer` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `PyClone` | CLI | 非 R |
| 出图 | `ggplot2` + 出版级出图 | DPI≥600 | 可视化规范 |

## 6. 数据可视化

签名条图/鱼图；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

WES 与 panel 换算；纯度/拷贝数校正关键。

## 8. 能否结合其它生信

变异检测、CNV、RNA融合、免疫浸润；出图强制统一可视化规范。

## 样例验证

样例：`01_样例_sample/`
