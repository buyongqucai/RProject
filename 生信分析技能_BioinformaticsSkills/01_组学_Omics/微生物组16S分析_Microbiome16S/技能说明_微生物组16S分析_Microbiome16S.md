---
name: bioinfo-16s
description: >-
  微生物组16S：ASV、多样性、差异分类群。R包：dada2、phyloseq、vegan、
  DESeq2/ANCOM-BC。QIIME2 为 CLI 备选。
---

# 微生物组16S分析 / Microbiome16S

## 1. 数据来源

16S amplicon FASTQ；Qiita/SRA；元数据含部位/处理/批次。

## 2. 数据规范（判断是否可用）

引物区一致才可合并；阴性对照与深度足够；元数据完整可溯源。

## 3. 何时选用本技能

- 菌群组成、Alpha/Beta、差异属种、菌-宿主关联  
- 编排：微生态主线 ± 代谢/宿主转录  

不适用：无菌群测序、仅培养鉴定名单。

## 4. 数据处理方法

DADA2/QIIME2 去噪 → ASV 注释 → 多样性 → 差异（ANCOM-BC/DESeq2）→ PICRUSt2 仅作假说。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 去噪 | `dada2` | ASV | 16S 常用 |
| 对象 | `phyloseq` | 多样性对象 | |
| 生态 | `vegan` | 距离/PERMANOVA | |
| 差异 | `DESeq2` / ANCOM-BC | 差异分类群 | 组成数据注意 |
| 备选 | QIIME2 | 端到端 | CLI |
| 出图 | `ggplot2` + 出版级出图 | 堆叠/PCoA | |

## 6. 数据可视化

稀释曲线、堆叠图、PCoA、差异条图；**DPI≥600；SVG+PNG；图面 English**。

**对齐高分期刊范式：** 遵循 [期刊范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) + [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)；近邻：Alpha 箱线+jitter（Fig1 g–j）、Beta PCoA（Fig1-b）、堆叠比例（Fig3-G）。

## 7. 数据结果解读

相对丰度≠绝对；功能预测写「推测」；勿过度因果。

## 8. 能否结合其它生信

宿主转录/代谢；多组学；可视化规范。

## 样例验证

样例：`01_样例_sample/`
