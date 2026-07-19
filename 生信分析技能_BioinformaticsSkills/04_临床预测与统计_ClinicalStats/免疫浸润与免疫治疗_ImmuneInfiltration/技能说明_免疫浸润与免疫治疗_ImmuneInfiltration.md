---
name: bioinfo-immune-infiltration
description: >-
  免疫浸润与免疫治疗 / ImmuneInfiltration：免疫细胞比例与免疫治疗相关评分。工具：GSVA, ggplot2, CIBERSORTx。
  触发：免疫浸润, CIBERSORT, TIDE, ssGSEA。
---

# 免疫浸润与免疫治疗 / ImmuneInfiltration

## 1. 数据来源

bulk 表达

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 免疫细胞比例与免疫治疗相关评分
- 山水用途层标签：病因-细胞

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

反卷积→评分→与临床关联

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `GSVA` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `CIBERSORTx` | CLI 工具 | 非 R |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

堆叠/箱线；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

反卷积依赖签名

## 8. 能否结合其它生信

生存、scRNA；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`
