---
name: bioinfo-3d-genome
description: >-
  三维基因组分析 / 3DGenome：三维接触、TAD/compartment、蛋白锚定 loop。。触发：Hi-C, TAD, HiChIP, ChIA-PET, 染色质环。
  已合并：`HiC三维基因组_HiC`、`染色质环与HiChIP_ChromatinLoop`。
---

# 三维基因组分析 / 3DGenome

## 1. 数据来源

Hi-C 接触图 (.hic/.cool)；HiChIP/ChIA-PET pairs。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组官方或实验记录可核对；禁止编造结果数字。

## 3. 何时选用本技能

- 三维接触、TAD/compartment、蛋白锚定 loop。
- 山水用途层：病因-基因
- **不包含（边界）**：靶向结合 peak 请用表观峰检测；开放染色质用 ATAC

不适用：应改用边界中列出的独立技能。

## 4. 数据处理方法

小节A Hi-C：矩阵→归一化→TAD/loop；小节B HiChIP：loop calling→基因关联。

### 已合并原技能触发词

`HiC三维基因组_HiC`、`染色质环与HiChIP_ChromatinLoop` 的触发需求一律走本技能（见 catalog `deprecated_ids`）。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `GenomicInteractions` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `Juicer` | CLI | 非 R |
| 上游/主分析 | `cooler` | CLI | 非 R |
| 上游/主分析 | `HiCCUPS` | CLI | 非 R |
| 出图 | `ggplot2` + 出版级出图 | DPI≥600 | 可视化规范 |

## 6. 数据可视化

接触热图/loop 图；**DPI≥600；SVG+PNG；中文；防遮挡**。  
客观 BLOCKED 样例产出：`契约阻塞桩_ContractBlockedStub.csv`、`审计后检_AuditPost.csv`、
`热图_ContactMatrixStub_Heatmap.png|.svg`、`样例报告_SampleReport_v1.html`（示意接触矩阵，非 DEG）。

## 7. 数据结果解读

分辨率与深度决定可解析尺度。toy/BLOCKED 不可外推。

## 8. 能否结合其它生信

ChIP/ATAC、转录组；出图强制统一可视化规范；交付命名强制统一交付规范（中英对照）。
样例须按序 source：VizStandards → DeliveryStandards → 本技能脚本。

## 9. 外部软件操作 SOP（BLOCKED 样例）

样例 `STATUS=BLOCKED`。Hi-C 摘要：Juicer/bwa → `.hic`/`.cool` → HiCExplorer TAD/loop → English contact heatmap。

## 样例验证

样例：`01_样例_sample/`（状态 BLOCKED 属契约样例）
