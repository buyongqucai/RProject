---
name: bioinfo-insilico-ko
description: >-
  虚拟敲除与扰动 / InSilicoKO：默认 scTenifoldKnk（GRN 虚拟敲除）；接诊确认表单强制。
  触发：虚拟敲除, in silico KO, scTenifoldKnk, GenKI, CellOracle, regulon KO。
---

# 虚拟敲除与扰动 / InSilicoKO

> **接诊 SSOT：** [`文档_docs/接诊与确认表单_IntakeConfirmForm.md`](文档_docs/接诊与确认表单_IntakeConfirmForm.md) — 每次先抽字段出确认表；未确认禁止正式敲除。  
> **方法默认 / 信源：** [`文档_docs/方法默认与信源登记_MethodDefaultsRegistry.md`](文档_docs/方法默认与信源登记_MethodDefaultsRegistry.md)  
> **出图图册：** [`文档_docs/出图图册_VkoFigureAtlas.md`](文档_docs/出图图册_VkoFigureAtlas.md) — PDF 图种重绘；禁论文截图当结果。  
> **可复用方法论（唯一存放处）：** [`文档_docs/虚拟敲除方法论_VkoMethodology.md`](文档_docs/虚拟敲除方法论_VkoMethodology.md) — 换课题只另写实例计划，不改本文件；一实例一引擎；对照不预设。  
> **Cplx2 课题的数据集、亚群、敲除基因：** [`文档_docs/数据集筛选与M4规程_DatasetScreening.md`](文档_docs/数据集筛选与M4规程_DatasetScreening.md) 的「两台机器共用的选择」。GenKI 与 scTenifoldKnk 都读这一处。  
> **Cplx2 桌面存放：** [`02_课题交付_Cplx2Control/文档_docs/桌面存放_DesktopLayout.md`](02_课题交付_Cplx2Control/文档_docs/桌面存放_DesktopLayout.md)。  
> **婷婷痤疮课题：** [`03_课题交付_婷婷痤疮_TingtingAcne/文档_docs/课题计划_婷婷_AHR.md`](03_课题交付_婷婷痤疮_TingtingAcne/文档_docs/课题计划_婷婷_AHR.md)。敲 AHR；Knk 建网用 1.4.3 GPU，另跑 GenKI。不套用 Cplx2 的 PEP/NF1。  
> 具体课题的计划与结果放在该课题目录，不写入本技能方法论。

## 1. 数据来源

单细胞/单核 **counts**（基因×细胞）；优先用户或公共 sc/sn。物种/组织/状态以确认表为准。

## 2. 数据规范

可溯源登录号或路径；保留样本/鼠 ID（能则保留）。禁止编造 DR 基因与富集 p 值。缺数据 → `BLOCKED_EXTERNAL`。

## 3. 何时选用

- 虚拟敲除 / in silico KO：接诊后 **选定一个引擎** 写实例计划（默认 scTenifoldKnk；也可 GenKI 等，见方法登记）  
- regulon 逆转 **仅** master TF + 已有 DEG  

不适用：无表达矩阵的纯网药；非扰动的普通 DEG/富集 → 其它技能。多种算法对照 **不是** 默认步骤。

## 4. 数据处理方法

1. 接诊表确认（`method` = **一个**引擎）→ 2. Phase1 → 3. 按方法论写该引擎实例计划 → 4. 只跑该引擎 → 5. 用该引擎自己的显著性与出图。  
步骤细则见方法论，不在此重复。regulon 备选见旧样例，不默认。

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
