---
name: bioinfo-dose-time
description: >-
  剂量反应与时间序列 / DoseTime：动态差异与剂量反应表达模式。。触发：时间序列, 纵向, 剂量时间, dose-response。
  已合并：`时间序列组学_TimeSeriesOmics`。
---

# 剂量反应与时间序列 / DoseTime

## 1. 数据来源

多时间点/剂量表达矩阵。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组官方或实验记录可核对；禁止编造结果数字。

## 3. 何时选用本技能

- 动态差异与剂量反应表达模式。
- 山水用途层：比较
- **不包含（边界）**：单时间点两组 DEG→转录组技能

不适用：应改用边界中列出的独立技能。

## 4. 数据处理方法

官方时间/剂量元数据 → 长表（gene × sample × time）→ 均值折线 / severity 映射 → 可选配对前后比较；正式分析可用 limma splines。

样例（GSE207177）：书清 `MAMs时序表达` → Control / CLP12h / CLP24h。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 差异/趋势 | `limma` | spline / 设计矩阵 | 正式分析 |
| 出图 | `ggplot2` + PublicationPlot | 折线 / `plot_severity_trend_journal` / `plot_paired_box_journal` | 样例直接用 |

## 6. 数据可视化

轨迹线图；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

时间点稀疏时谨慎解读。

## 8. 能否结合其它生信

转录组、GSEA；出图强制统一可视化规范。

## 样例验证

样例：`01_样例_sample/`（**data_provenance=REAL**，`GSE207177`）

- 缓存：`real_GSE207177_MAMs_timeseries.csv`（书清）
- 复跑：`代码文件/run_sample.R`；`SHUQING_ROOT` 可回源
- 图：时序折线、基因–时间趋势、Control vs CLP24h 配对箱线

### 已合并原技能触发词

`时间序列组学_TimeSeriesOmics` 的触发需求一律走本技能（见 catalog `deprecated_ids`）。
