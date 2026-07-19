---
name: bioinfo-chipseq
description: >-
  表观峰检测ChIP与CUT / ChIP-CUTnTag：靶向结合/组蛋白修饰峰检测与差异（含 CUT&Tag）。。触发：ChIP-seq, CUT&Tag, CUT&RUN, peak, DiffBind。
  已合并：`CUT与Tag分析_CUTnTag`、`原名表观遗传ChIP-seq（目录名保留兼容）`。
---

# 表观峰检测ChIP与CUT / ChIP-CUTnTag

## 1. 数据来源

ChIP/CUT&Tag/CUT&RUN FASTQ 或 peak；须有 Input/IgG 记录。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组官方或实验记录可核对；禁止编造结果数字。

## 3. 何时选用本技能

- 靶向结合/组蛋白修饰峰检测与差异（含 CUT&Tag）。
- 山水用途层：病因-基因
- **不包含（边界）**：ATAC 开放染色质；Hi-C/HiChIP 三维接触

不适用：应改用边界中列出的独立技能。

## 4. 数据处理方法

FastQC→比对→MACS2→DiffBind/csaw→ChIPseeker；按实验类型选 ChIP 或 CUT&Tag 参数。

### 已合并原技能触发词

`CUT与Tag分析_CUTnTag`、`原名表观遗传ChIP-seq（目录名保留兼容）` 的触发需求一律走本技能（见 catalog `deprecated_ids`）。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `DiffBind` | 核心 R 包 | |
| 分析 | `csaw` | 核心 R 包 | |
| 分析 | `ChIPseeker` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `FastQC` | CLI | 非 R |
| 上游/主分析 | `Bowtie2` | CLI | 非 R |
| 上游/主分析 | `MACS2` | CLI | 非 R |
| 出图 | `ggplot2` + 出版级出图 | DPI≥600 | 可视化规范 |

## 6. 数据可视化

峰注释饼图、差异火山、profile；**DPI≥600；SVG+PNG；图面 English；防遮挡**。

**对齐高分期刊范式：** 遵循 [期刊范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) + [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)；近邻：火山（Fig2-B）、富集水平柱/点图（Fig1-f / Fig3-C）、热图。

## 7. 数据结果解读

近端基因≠直接靶；无对照须写局限。

## 8. 能否结合其它生信

ATAC（开放染色质独立）、三维基因组、转录组；出图强制统一可视化规范。

## 9. 外部软件操作 SOP（BLOCKED 样例）

样例 `STATUS=BLOCKED`。FastQC → bowtie2/bwa → MACS2 peak → R `DiffBind` 差异 → ChIPseeker 注释。

## 样例验证

样例：`01_样例_sample/`
