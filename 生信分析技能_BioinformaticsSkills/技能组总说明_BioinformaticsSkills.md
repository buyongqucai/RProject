---
name: bioinfo-skill-group
description: >-
  生信分析技能组 Bioinformatics Skills。用户给出研究目的时：先读
  研究方案编排_ResearchOrchestrator，产出方法/数据/技能组合/R包计划；
  再执行对应技能说明。含转录组、单细胞、代谢、蛋白、ChIP、16S、GWAS、GEO-TCGA、多组学。
  触发：研究目的、分析方案、生信、组学、RNA-seq、Seurat、OPLS-DA、生存、多组学。
---

# 生信分析技能 / Bioinformatics Skills

**实体根目录：** `E:/RProject/生信分析技能_BioinformaticsSkills/`  
**Cursor 发现入口：** `.cursor/skills/生信分析技能_BioinformaticsSkills/`

## 工作方式（强制）

```text
用户研究目的
  -> 先读 00_基础_Foundation/研究方案编排_ResearchOrchestrator/技能说明_….md
  -> 输出 7 章结构化计划（方法、数据、技能组合、R包、交付物、风险）
  -> 按组合依次打开对应 技能说明_*.md（含 R 包表）并执行
  -> 公共数据：数据真实性验证；出图：统一可视化规范；命名/审计/报告：统一交付规范
```

- 编排：[研究方案编排_ResearchOrchestrator](00_基础_Foundation/研究方案编排_ResearchOrchestrator/技能说明_研究方案编排_ResearchOrchestrator.md)
- 全景：[技能全景清单_SkillLandscape.md](技能全景清单_SkillLandscape.md)（去重后互斥分类）
- 验证：[07_分类验证_Validation/验证总报告.md](07_分类验证_Validation/验证总报告.md)
- 路由：[索引_INDEX.md](索引_INDEX.md)
- 规范：[项目结构规范_ProjectLayout.md](项目结构规范_ProjectLayout.md)
- 目录：[技能目录_skill-catalog.json](技能目录_skill-catalog.json)
- 工作流模板：[工作流_workflows.json](工作流_workflows.json)

## 固定交付要求

- 图：DPI ≥ 600；SVG + PNG；图面 English；防遮挡；统一配色（`统一可视化规范_VizStandards`）
- **期刊多面板范式：** [`高分期刊出图范式_JournalFigureParadigm.md`](00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md)
- **冻结登记：** [`已跑通范式登记_FrozenParadigms.md`](00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/已跑通范式登记_FrozenParadigms.md) — `网络药理学_NetworkPharmacology`、`分子动力学模拟_MolecularDynamics` **frozen**，未解冻不得改布局/配色/样例图/报告范式
- **出图后审核：** 每张图保存后强制 PlotQA（色块/标签互挡、长标签版式）— [`出图后审核_PlotQA.md`](00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)
- 命名 / 审计 / HTML 报告：`统一交付规范_DeliveryStandards`（禁止 `plot.png`、`sample_volcano.png`、无前缀 `样例报告.html`）
- 样例须 `source` 本技能 `脚本_scripts/`，不可用全局同构假流程冒充
- 禁止编造 GEO/TCGA 分组与分析结果数字

## 子目录

| 区 | 说明 |
|----|------|
| `00_基础_Foundation/` | 编排、可视化、**交付规范**、真实性、实验设计、批次、NGS质控、文献、可复现 |
| `01_组学_Omics/` | 真正组学（转录/单细胞/蛋白/代谢/表观/微生物等） |
| `02_遗传与变异_Genetics/` | 变异、组装、GWAS、群体、MR、系统发育等 |
| `03_药物计算_DrugDiscovery/` | 网络药理、对接、MD、结构、ADMET、CMap、GDSC |
| `04_临床预测与统计_ClinicalStats/` | 生存/ROC/Meta/ML/分型/液体活检等 |
| `05_系统方法_SystemsMethods/` | GSEA、WGCNA、PPI、通讯、虚拟敲除等跨组学方法 |
| `06_已落地流水线_ProductionPipelines/` | DEG-UMAP 生产流水线（原 02） |
| `07_分类验证_Validation/` | 分类验证与每技能样例总表（原 03） |
