---
name: bioinfo-scrna-advanced
description: >-
  单细胞进阶方法 / scRNA-Advanced：轨迹/RNA 速度、组成差异、图谱整合（主入口仍为 scRNA-Spatial）。。触发：轨迹, monocle, velocity, miloR, scCODA, 图谱整合, scVI。
  已合并：`单细胞轨迹与命运_Trajectory`、`单细胞组成差异_scComposition`、`单细胞整合与图谱_AtlasIntegration`。
---

# 单细胞进阶方法 / scRNA-Advanced

## 1. 数据来源

已注释 Seurat；多样本比例；多批次对象。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组官方或实验记录可核对；禁止编造结果数字。

## 3. 何时选用本技能

- 轨迹/RNA 速度、组成差异、图谱整合（主入口仍为 scRNA-Spatial）。
- 山水用途层：病因-细胞
- **不包含（边界）**：标准 QC/聚类/注释→主技能 scRNA-Spatial；通讯→细胞通讯分析

不适用：应改用边界中列出的独立技能。

## 4. 数据处理方法

小节：Trajectory / Composition / AtlasIntegration。

### 已合并原技能触发词

`单细胞轨迹与命运_Trajectory`、`单细胞组成差异_scComposition`、`单细胞整合与图谱_AtlasIntegration` 的触发需求一律走本技能（见 catalog `deprecated_ids`）。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `monocle3` | 核心 R 包 | |
| 分析 | `slingshot` | 核心 R 包 | |
| 分析 | `miloR` | 核心 R 包 | |
| 分析 | `Seurat` | 核心 R 包 | |
| 分析 | `harmony` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `velocyto` | CLI | 非 R |
| 上游/主分析 | `scVelo` | CLI | 非 R |
| 上游/主分析 | `scvi-tools` | CLI | 非 R |
| 出图 | `ggplot2` + 出版级出图 | DPI≥600 | 可视化规范 |

## 6. 数据可视化

轨迹 UMAP / DA 图 / 整合 UMAP；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

根选择与过度校正风险。

## 8. 能否结合其它生信

单细胞与空间转录组分析_scRNA-Spatial（主入口）、细胞通讯；出图强制统一可视化规范。

## 样例验证

样例：`01_样例_sample/`
