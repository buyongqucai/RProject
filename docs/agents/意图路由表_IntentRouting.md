# 意图路由表（Intent Routing）— SSOT

> **地位：** `intent-skill-router` 的路由表唯一来源（git 区，防 `.cursor/` 丢失后断链）。  
> **用法：** 技能说明入口只留指针；**新增/改技能后手工补行**（同 `技能范式清单` D1）。  
> **规则：** 命中即 **Read 对应 `技能说明_*.md`**，勿凭记忆执行。

## 0. 通用铁律（每次任务生效）

| 触发 | 强制动作 |
|------|----------|
| 任何出图任务 | Read 对应技能出图规范 + `00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md`；交付前过 `E:\md_kit\图交付门禁_gateMdFigures.py`（MD）或等价门禁 |
| 任何交付/命名/存放 | Read `00_基础_Foundation/统一交付规范_DeliveryStandards/技能说明_*.md` 与 `文档_docs/样例目录与命名_SampleLayoutNaming.md` |
| 任何 HTML 报告 | Read `00_基础_Foundation/统一交付规范_DeliveryStandards/文档_docs/样例报告范式_SampleReportParadigm.md`；双报告另读项目技能 `dual-report-writing` |
| 任何异常复盘 | 落档技能内 `异常知识库_ExceptionKB/`（写法：`docs/agents/异常知识库规范_ExceptionKb.md`） |

## 1. 意图关键词 → 技能入口

| 关键词（含同义） | Read 入口 |
|------------------|-----------|
| 分子对接 / docking / 对接 / 虚拟筛选 | `生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/分子对接与虚拟筛选_MolecularDocking/技能说明_分子对接与虚拟筛选_MolecularDocking.md`（出图另读 `文档_docs/对接与交付约束_DockingFrozen.md`） |
| 分子动力学 / MD / 轨迹 / 100ns | `…/分子动力学模拟_MolecularDynamics/技能说明_分子动力学模拟_MolecularDynamics.md`（出图另读 `文档_docs/出图与交付约束_MdFigureStandards.md`） |
| 论文版 / 方法版 / 双报告 / 全流程报告 | `.cursor/skills/dual-report-writing/SKILL.md`（先读其 reference.md） |
| 网络药理学 / 网药 | `…/网络药理学_NetworkPharmacology/技能说明_*.md` + `文档_docs/出图约束_NetworkFigureStandards.md` |
| 网络毒理学 / 网毒 | `…/网络毒理学_NetworkToxicology/技能说明_*.md` |
| 虚拟敲除 / GenKI / scTenifoldKnk | `…/05_系统方法_SystemsMethods/虚拟敲除与扰动_InSilicoKO/技能说明_*.md` |
| 研究方案 / 多技能编排 / 课题规划 | `生信分析技能_BioinformaticsSkills/00_基础_Foundation/研究方案编排_ResearchOrchestrator/技能说明_*.md` |
| 转录组 / DEG / UMAP / 差异分析 | `…/06_生产流水线_ProductionPipelines/差异分析UMAP流水线_DEG-UMAP/技能说明_*.md` 或 `01_组学_Omics/转录组学_RNA-seq/` |
| 单细胞 / 空间转录组 | `…/01_组学_Omics/单细胞与空间转录组分析_scRNA-Spatial/技能说明_*.md` |
| 补算 / MM-GBSA / 结合自由能 | 对应计算技能 `文档_docs/`（MD：GromacsSop §9.5/§9.7） |

## 2. 兜底

未命中 → `生信分析技能_BioinformaticsSkills/索引_INDEX.md` → `技能全景清单_SkillLandscape.md`；仍不明确 → 问用户。

## 3. 修订

2026-10-14 重建：原 `intent-skill-router` 丢失（`.cursor/` 不入 git）+ `bioinfo-skill-group` 目录名错误未被发现，导致出图任务绕过 FROZEN 规范与 PlotQA——本表迁入 git 区防再丢。
