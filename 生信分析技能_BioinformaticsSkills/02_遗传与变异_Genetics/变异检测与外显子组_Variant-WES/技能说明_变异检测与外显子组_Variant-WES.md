---
name: bioinfo-variant-wes
description: >-
  变异检测与外显子组 / Variant-WES：SNV/Indel 检测、过滤、注释与 WES 致病性排序。。触发：变异检测, VCF, GATK, WES, 外显子组, SNV。
  已合并：`变异检测与注释_VariantCalling`、`全外显子组分析_WES`。
---

# 变异检测与外显子组 / Variant-WES

## 1. 数据来源

WGS/WES BAM 或 VCF；WES 为捕获场景。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组官方或实验记录可核对；禁止编造结果数字。

## 3. 何时选用本技能

- SNV/Indel 检测、过滤、注释与 WES 致病性排序。
- 山水用途层：病因-基因
- **不包含（边界）**：大结构变异→结构变异分析；RNA 融合→RNA融合基因检测

不适用：应改用边界中列出的独立技能。

## 4. 数据处理方法

QC→比对→GATK call→filter→注释；WES 可加 Exomiser 排序。

### 已合并原技能触发词

`变异检测与注释_VariantCalling`、`全外显子组分析_WES` 的触发需求一律走本技能（见 catalog `deprecated_ids`）。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `VariantAnnotation` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `GATK` | CLI | 非 R |
| 上游/主分析 | `bcftools` | CLI | 非 R |
| 上游/主分析 | `Exomiser` | CLI | 非 R |
| 出图 | `ggplot2` + 出版级出图 | DPI≥600 | 可视化规范 |

## 6. 数据可视化

Ti/Tv、Venn；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

覆盖度与假阳性；捕获偏差（WES）。

## 8. 能否结合其它生信

CNV、SV、TMB/肿瘤体细胞景观、NGS-QC；出图强制统一可视化规范。

## 9. 外部软件操作 SOP（BLOCKED 样例）

样例 `STATUS=BLOCKED`。GATK：BWA → MarkDuplicates → BQSR → HaplotypeCaller/Mutect2 → VEP 注释。

## 样例验证

样例：`01_样例_sample/`
