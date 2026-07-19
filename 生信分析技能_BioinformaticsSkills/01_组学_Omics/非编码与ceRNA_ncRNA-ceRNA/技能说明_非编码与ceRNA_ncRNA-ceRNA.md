---
name: bioinfo-ncrna-cerna
description: >-
  非编码与ceRNA / ncRNA-ceRNA：非编码定量、靶基因与 ceRNA 竞争网络。。触发：miRNA, lncRNA, circRNA, ceRNA, 非编码。
  已合并：`非编码RNA分析_ncRNA`、`ceRNA网络分析_ceRNA`。
---

# 非编码与ceRNA / ncRNA-ceRNA

## 1. 数据来源

小 RNA/RNA-seq；miRNA 与 mRNA/lncRNA 表达。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组官方或实验记录可核对；禁止编造结果数字。

## 3. 何时选用本技能

- 非编码定量、靶基因与 ceRNA 竞争网络。
- 山水用途层：病因-基因
- **不包含（边界）**：编码基因 DEG 主分析→转录组技能

不适用：应改用边界中列出的独立技能。

## 4. 数据处理方法

定量→差异→靶预测→（可选）ceRNA 网络与相关性验证。

### 已合并原技能触发词

`非编码RNA分析_ncRNA`、`ceRNA网络分析_ceRNA` 的触发需求一律走本技能（见 catalog `deprecated_ids`）。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `clusterProfiler` | 核心 R 包 | |
| 分析 | `igraph` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 出图 | `ggplot2` + 出版级出图 | DPI≥600 | 可视化规范 |

## 6. 数据可视化

火山/网络图；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

靶预测与 ceRNA 相关≠机制证实。

## 8. 能否结合其它生信

转录组、生存、网络药理；出图强制统一可视化规范。

## 样例验证

样例：`01_样例_sample/`
