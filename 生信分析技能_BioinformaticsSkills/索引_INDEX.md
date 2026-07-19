# 生信分析技能 INDEX / Bioinformatics Skills Index

实体根：`E:/RProject/生信分析技能_BioinformaticsSkills/`  
全景（去重后）：[技能全景清单_SkillLandscape.md](技能全景清单_SkillLandscape.md)  
目录：[技能目录_skill-catalog.json](技能目录_skill-catalog.json)  
工作流：[工作流_workflows.json](工作流_workflows.json)  
验证沙盒：[07_分类验证_Validation/](07_分类验证_Validation/)

## 目录布局（v2）

- `00_基础_Foundation` / `01_组学_Omics` / `02_遗传与变异_Genetics` / `03_药物计算_DrugDiscovery` / `04_临床预测与统计_ClinicalStats` / `05_系统方法_SystemsMethods` / `06_已落地流水线_ProductionPipelines` / `07_分类验证_Validation`
- 映射表：[目录重构说明_LayoutMigration.md](目录重构说明_LayoutMigration.md)
- **样例交付 SSOT**：[统一交付规范_DeliveryStandards](00_基础_Foundation/统一交付规范_DeliveryStandards/技能说明_统一交付规范_DeliveryStandards.md)（命名/审计/报告；出图技术仍用 [VizStandards](00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)）

## 按研究目的

| 研究目的 | 技能组合 |
|----------|----------|
| 任意方案 | 研究方案编排 |
| 机制+细胞 | scRNA-Spatial → 转录组 ± 细胞通讯 ± 单细胞进阶 |
| 预后标志物 | GEO-TCGA → 生存 ± 诊断ROC |
| 药物靶点 | 网络药理 → 蛋白结构与建模 → 分子对接 → 分子动力学 ± 类药性与QSAR |
| 代谢脂质 | 代谢组分析（含脂质/通量） ± 转录组 |
| 甲基化 | DNA甲基化 ± 转录组 ± GSEA |
| ncRNA/ceRNA | 非编码与ceRNA ± 转录组 |
| 免疫 | 免疫浸润 ± 生存 ± 单细胞 |
| 群落病原 | 宏基因组与病原 或 16S |
| 四数据集生产 | DEG-UMAP 流水线 |

## 弃用目录

见 `技能目录_skill-catalog.json` → `deprecated_folders`（勿再新建同名技能）。
