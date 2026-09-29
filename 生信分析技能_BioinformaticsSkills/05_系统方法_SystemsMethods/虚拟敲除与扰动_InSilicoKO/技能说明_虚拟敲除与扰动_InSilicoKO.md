---
name: bioinfo-insilico-ko
description: >-
  虚拟敲除与扰动 / InSilicoKO：默认 scTenifoldKnk（GRN 虚拟敲除）；接诊确认表单强制。
  触发：虚拟敲除, in silico KO, scTenifoldKnk, CellOracle, regulon KO。
---

# 虚拟敲除与扰动 / InSilicoKO

> **接诊 SSOT：** [`文档_docs/接诊与确认表单_IntakeConfirmForm.md`](文档_docs/接诊与确认表单_IntakeConfirmForm.md) — 每次先抽字段出确认表；未确认禁止正式敲除。  
> **方法默认 / 信源：** [`文档_docs/方法默认与信源登记_MethodDefaultsRegistry.md`](文档_docs/方法默认与信源登记_MethodDefaultsRegistry.md)  
> **出图图册：** [`文档_docs/出图图册_VkoFigureAtlas.md`](文档_docs/出图图册_VkoFigureAtlas.md) — PDF 图种重绘；禁论文截图当结果。

## 1. 数据来源

单细胞/单核 **counts**（基因×细胞）；优先用户或公共 sc/sn。物种/组织/状态以确认表为准。

## 2. 数据规范

可溯源登录号或路径；保留样本/鼠 ID（能则保留）。禁止编造 DR 基因与富集 p 值。缺数据 → `BLOCKED_EXTERNAL`。

## 3. 何时选用

- GRN 虚拟敲除、scTenifoldKnk、按细胞亚群扰动预测  
- 备选：CellOracle；regulon 逆转 **仅** master TF + DEG  

不适用：无表达矩阵的纯网药；非扰动的普通 DEG/富集 → 其它技能。

## 4. 数据处理方法

1. 接诊表确认（A+B）→ 2. Phase1 数据可行性（填 C）→ 3. 二次确认亚群/数据集 → 4. scTenifoldKnk（行置零 + 流形对齐）→ 5. DR 表 + 焦点富集 + 图册出图。  
regulon 备选见旧样例，不默认。

## 5. R 包与软件栈

| 步骤 | 工具 | 备注 |
|------|------|------|
| 主分析 | `scTenifoldKnk` | 参数见方法默认登记 |
| QC/亚群 | Seurat / 数据集作者标签 | 小鼠 `mt-` |
| 富集 | clusterProfiler 等 | term 来自确认表 |
| 出图 | ggplot2 + VizStandards | DPI≥600；图面 English |

## 6. 数据可视化

主线序 01–07 见出图图册。强制 VizStandards + DeliveryStandards。旧 KOrescue 柱图 = 附录备选。

## 7. 数据结果解读

强模型假设；只写 **计算预测**。禁止写成真实 KO 差异表达或药效机制已证实。

## 8. 能否结合其它生信

公共库挖掘、单细胞、网药/对接（联合时另定 `delivery_scope`）；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 样例验证

样例：`01_样例_sample/`（当前多为 regulon/TOY 演示；scTenifoldKnk 金标以确认表任务交付为准）。
