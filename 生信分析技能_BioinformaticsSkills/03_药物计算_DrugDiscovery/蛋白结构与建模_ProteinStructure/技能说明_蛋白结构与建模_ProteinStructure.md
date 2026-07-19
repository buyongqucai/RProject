---
name: bioinfo-protein-structure
description: >-
  蛋白结构与建模 / ProteinStructure：对接前置：结构获取、口袋检测、同源建模补全。。触发：AlphaFold, PDB, 口袋, 同源建模, MODELLER。
  已合并：`蛋白结构预测与口袋_ProteinStructure`、`同源建模_HomologyModeling`。
---

# 蛋白结构与建模 / ProteinStructure

## 1. 数据来源

UniProt/PDB/AlphaFold DB；无实验结构时用同源建模模板。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组官方或实验记录可核对；禁止编造结果数字。

## 3. 何时选用本技能

- 对接前置：结构获取、口袋检测、同源建模补全。
- 山水用途层：药物-基因
- **不包含（边界）**：不做对接打分（→分子对接）；不做 MD 轨迹（→分子动力学）

不适用：应改用边界中列出的独立技能。

## 4. 数据处理方法

取结构(AF/PDB)→质控(pLDDT)→口袋(fpocket)→必要时 MODELLER 同源建模→交给对接。

### 已合并原技能触发词

`蛋白结构预测与口袋_ProteinStructure`、`同源建模_HomologyModeling` 的触发需求一律走本技能（见 catalog `deprecated_ids`）。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `bio3d` | 核心 R 包 | |
| 上游/主分析 | `fpocket` | CLI | 非 R |
| 上游/主分析 | `MODELLER` | CLI | 非 R |
| 出图 | `ggplot2` + 出版级出图 | DPI≥600 | 可视化规范 |

## 6. 数据可视化

结构卡通/口袋示意；**DPI≥600；SVG+PNG；图面 English；防遮挡**。

**对齐高分期刊范式：** 遵循 [期刊范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) + [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)；近邻条图/示意图继承 VizStandards。网药视觉 **FROZEN**，勿改。

## 7. 数据结果解读

预测结构标明置信度；低同源建模不可靠。

## 8. 能否结合其它生信

分子对接、分子动力学、网络药理；出图强制统一可视化规范。

## 样例验证

样例：`01_样例_sample/`
