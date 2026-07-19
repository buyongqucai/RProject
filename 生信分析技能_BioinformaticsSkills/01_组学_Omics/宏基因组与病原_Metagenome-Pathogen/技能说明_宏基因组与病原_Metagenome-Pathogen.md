---
name: bioinfo-metagenome-pathogen
description: >-
  宏基因组与病原 / Metagenome-Pathogen：物种/功能/MAG、宏转录、病毒鉴定、耐药毒力筛查。。触发：宏基因组, 宏转录组, 病毒组, AMR, Kraken, HUMAnN, CARD。
  已合并：`宏基因组分析_Metagenomics`、`宏转录组分析_Metatranscriptomics`、`病毒组与病原检测_Virome`、`耐药与毒力基因_AMR-Virulence`。
---

# 宏基因组与病原 / Metagenome-Pathogen

## 1. 数据来源

群落 WGS/RNA reads；细菌基因组（AMR）。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组官方或实验记录可核对；禁止编造结果数字。

## 3. 何时选用本技能

- 物种/功能/MAG、宏转录、病毒鉴定、耐药毒力筛查。
- 山水用途层：病因-细胞
- **不包含（边界）**：16S amplicon 用微生物组16S技能

不适用：应改用边界中列出的独立技能。

## 4. 数据处理方法

模式：metagenome / metatranscriptome / virome / AMR；质控→分类或组装→功能或 CARD/VFDB。

### 已合并原技能触发词

`宏基因组分析_Metagenomics`、`宏转录组分析_Metatranscriptomics`、`病毒组与病原检测_Virome`、`耐药与毒力基因_AMR-Virulence` 的触发需求一律走本技能（见 catalog `deprecated_ids`）。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `Kraken2` | CLI | 非 R |
| 上游/主分析 | `HUMAnN` | CLI | 非 R |
| 上游/主分析 | `MetaBAT` | CLI | 非 R |
| 上游/主分析 | `VirSorter` | CLI | 非 R |
| 上游/主分析 | `ABRicate` | CLI | 非 R |
| 出图 | `ggplot2` + 出版级出图 | DPI≥600 | 可视化规范 |

## 6. 数据可视化

丰度堆叠/热图；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

宿主污染；存在≠表达（AMR）。

## 8. 能否结合其它生信

16S（扩增子独立）、代谢组；出图强制统一可视化规范。

## 样例验证

样例：`01_样例_sample/`
