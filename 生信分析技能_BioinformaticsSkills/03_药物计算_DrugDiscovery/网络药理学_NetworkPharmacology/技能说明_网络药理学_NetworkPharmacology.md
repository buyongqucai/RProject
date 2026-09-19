---
name: bioinfo-network-pharmacology
description: >-
  网络药理学 / NetworkPharmacology：单药成分靶点瀑布 TCMSP→BATMAN(仅已知)→ETCM→HERB+STP；
  疾病六库；KEGG/STRING；韦恩与 HCTP/PPI 代码出图。
  触发：网络药理, 单药靶点, 疾病韦恩, TCMSP, BATMAN, HERB, STRING PPI。
---

# 网络药理学 / NetworkPharmacology

> **出图约束 SSOT（FROZEN）：** [`出图约束_NetworkFigureStandards.md`](文档_docs/出图约束_NetworkFigureStandards.md) — 改视觉 recipe / 疾病双口径前须「解冻」。  
> **库与流水线 SSOT：** [`数据库分类与流水线_DataSourcesPipeline.md`](文档_docs/数据库分类与流水线_DataSourcesPipeline.md)  
> **成分靶点 SOP：** [`成分靶点获取与交付规范_CompoundTargetSOP.md`](文档_docs/成分靶点获取与交付规范_CompoundTargetSOP.md)  
> **手工/Cytoscape 可选：** [`手工导出与Cytoscape可选_ManualOps.md`](文档_docs/手工导出与Cytoscape可选_ManualOps.md)

基因列表与 STRING 边须可溯源。交付默认 **代码/AI（R）出图**；Cytoscape 仅可选精修。

## 1. 数据来源

三类库不得混写。疾病六库 / 成分瀑布 / AUTO·MANUAL → [`数据库分类与流水线`](文档_docs/数据库分类与流水线_DataSourcesPipeline.md)。  
样例：`data_provenance: REAL`（用户交付中间表 + 可程序化 CTD/STRING/KEGG）。

## 2. 数据规范

- 可溯源：单药名 + 英文病名 + 库导出；整合 schema = **药物–有效成分–靶点**
- HERB→STP 交付精简与异常清单 → CompoundTargetSOP
- 禁止 UniProt 全表左拼主交付；缺导出 → `BLOCKED_EXTERNAL`，不编造基因
- 列契约：`脚本_scripts/01_契约接口_DataContracts.R`

## 3. 何时选用

中药/复方成分–靶点–疾病网络与通路。下游：结构 → 对接 → MD。  
不适用：仅 bulk DEG；仅 PPI 无成分层 → `蛋白质互作网络_PPI-Network`。

## 4. 数据处理方法

完整步骤与瀑布 → [`数据库分类与流水线`](文档_docs/数据库分类与流水线_DataSourcesPipeline.md)。  
快速网络预览：`01_样例_sample/代码文件/02_run_network_preview.R`。  
布局代码 SSOT：`脚本_scripts/04_交付网络布局_DeliveryNetworkLayouts.R`。

## 5. R 包与软件栈

| 步骤 | 工具 | 备注 |
|------|------|------|
| 韦恩/柱/GO/KEGG 重绘 | ggplot2 + VizStandards | 表驱动 |
| HCTP / STRING PPI | 本技能布局脚本 + STRING API | 交付默认代码出图 |
| GO 原始 | Metascape（外部） | 样例可用预计算表 |
| KEGG REST / 位图 | REST AUTO；官网位图可选 | |

## 6. 数据可视化

图种、Degree、环布局、PlotQA → **出图约束 FROZEN**（不在此复述 recipe）。  
强制叠加 VizStandards + DeliveryStandards。图册对账表见出图约束与样例 `STATUS`（`PARTIAL` 允许；禁假全流程 PASS）。

## 7. 数据结果解读

多库并集抬高假阳性；中心性 ≠ 因果；样例为演示非诊疗建议。

## 8. 能否结合其它生信

强制：Viz / Delivery / DataAuthenticity。下游：蛋白结构 → 对接 → MD。

## 样例验证

`01_样例_sample/`。PPI/HCTP **不得**再标 `BLOCKED_EXTERNAL`（代码可绘）；缺手工库导出时该步诚实断点。
