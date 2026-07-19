# 目录重构说明 / Layout Migration

版本：`layout_version = 2026-07-layout-v2`

## 目标顶层

```
00_基础_Foundation/
01_组学_Omics/                    # 仅真正组学
02_遗传与变异_Genetics/
03_药物计算_DrugDiscovery/
04_临床预测与统计_ClinicalStats/
05_系统方法_SystemsMethods/
06_已落地流水线_ProductionPipelines/  # 原 02
07_分类验证_Validation/            # 原 03
```

## 旧 → 新映射

| 旧路径 | 新路径 |
|--------|--------|
| `01_组学_Omics/CRISPR筛选分析_CRISPRscreen` | `05_系统方法_SystemsMethods/CRISPR筛选分析_CRISPRscreen` |
| `01_组学_Omics/RNA融合基因检测_FusionGene` | `02_遗传与变异_Genetics/RNA融合基因检测_FusionGene` |
| `01_组学_Omics/免疫浸润与免疫治疗_ImmuneInfiltration` | `04_临床预测与统计_ClinicalStats/免疫浸润与免疫治疗_ImmuneInfiltration` |
| `01_组学_Omics/全基因组关联分析_GWAS` | `02_遗传与变异_Genetics/全基因组关联分析_GWAS` |
| `01_组学_Omics/共表达网络WGCNA_WGCNA` | `05_系统方法_SystemsMethods/共表达网络WGCNA_WGCNA` |
| `01_组学_Omics/分子分型与共识聚类_MolecularSubtyping` | `04_临床预测与统计_ClinicalStats/分子分型与共识聚类_MolecularSubtyping` |
| `01_组学_Omics/分子动力学模拟_MolecularDynamics` | `03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics` |
| `01_组学_Omics/分子对接与虚拟筛选_MolecularDocking` | `03_药物计算_DrugDiscovery/分子对接与虚拟筛选_MolecularDocking` |
| `01_组学_Omics/剂量反应与时间序列_DoseTime` | `04_临床预测与统计_ClinicalStats/剂量反应与时间序列_DoseTime` |
| `01_组学_Omics/单细胞进阶方法_scRNA-Advanced` | `05_系统方法_SystemsMethods/单细胞进阶方法_scRNA-Advanced` |
| `01_组学_Omics/变异检测与外显子组_Variant-WES` | `02_遗传与变异_Genetics/变异检测与外显子组_Variant-WES` |
| `01_组学_Omics/基因组组装与注释_GenomeAssembly` | `02_遗传与变异_Genetics/基因组组装与注释_GenomeAssembly` |
| `01_组学_Omics/基因集富集与通路_GSEA-Pathway` | `05_系统方法_SystemsMethods/基因集富集与通路_GSEA-Pathway` |
| `01_组学_Omics/外泌体与液体活检_LiquidBiopsy` | `04_临床预测与统计_ClinicalStats/外泌体与液体活检_LiquidBiopsy` |
| `01_组学_Omics/多组学联合分析_MultiOmics` | `05_系统方法_SystemsMethods/多组学联合分析_MultiOmics` |
| `01_组学_Omics/孟德尔随机化_MendelianRandomization` | `02_遗传与变异_Genetics/孟德尔随机化_MendelianRandomization` |
| `01_组学_Omics/拷贝数变异分析_CNV` | `02_遗传与变异_Genetics/拷贝数变异分析_CNV` |
| `01_组学_Omics/放射组学与病理组学_Radiomics-Pathomics` | `04_临床预测与统计_ClinicalStats/放射组学与病理组学_Radiomics-Pathomics` |
| `01_组学_Omics/新抗原与免疫组库_Neoantigen-TCR` | `04_临床预测与统计_ClinicalStats/新抗原与免疫组库_Neoantigen-TCR` |
| `01_组学_Omics/机器学习生物标志物_ML-Biomarker` | `04_临床预测与统计_ClinicalStats/机器学习生物标志物_ML-Biomarker` |
| `01_组学_Omics/生存分析与预后模型_Survival` | `04_临床预测与统计_ClinicalStats/生存分析与预后模型_Survival` |
| `01_组学_Omics/类药性与QSAR_ADMET-QSAR` | `03_药物计算_DrugDiscovery/类药性与QSAR_ADMET-QSAR` |
| `01_组学_Omics/系统发育分析_Phylogenetics` | `02_遗传与变异_Genetics/系统发育分析_Phylogenetics` |
| `01_组学_Omics/细胞通讯分析_CellCommunication` | `05_系统方法_SystemsMethods/细胞通讯分析_CellCommunication` |
| `01_组学_Omics/结构变异分析_StructuralVariant` | `02_遗传与变异_Genetics/结构变异分析_StructuralVariant` |
| `01_组学_Omics/网络药理学_NetworkPharmacology` | `03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology` |
| `01_组学_Omics/群体遗传学_PopulationGenetics` | `02_遗传与变异_Genetics/群体遗传学_PopulationGenetics` |
| `01_组学_Omics/肿瘤体细胞景观_TumorSomatic` | `02_遗传与变异_Genetics/肿瘤体细胞景观_TumorSomatic` |
| `01_组学_Omics/荟萃分析_MetaAnalysis` | `04_临床预测与统计_ClinicalStats/荟萃分析_MetaAnalysis` |
| `01_组学_Omics/药物敏感性与GDSC_DrugResponse` | `03_药物计算_DrugDiscovery/药物敏感性与GDSC_DrugResponse` |
| `01_组学_Omics/药物重定位与连通图_CMap-L1000` | `03_药物计算_DrugDiscovery/药物重定位与连通图_CMap-L1000` |
| `01_组学_Omics/虚拟敲除与扰动_InSilicoKO` | `05_系统方法_SystemsMethods/虚拟敲除与扰动_InSilicoKO` |
| `01_组学_Omics/蛋白结构与建模_ProteinStructure` | `03_药物计算_DrugDiscovery/蛋白结构与建模_ProteinStructure` |
| `01_组学_Omics/蛋白质互作网络_PPI-Network` | `05_系统方法_SystemsMethods/蛋白质互作网络_PPI-Network` |
| `01_组学_Omics/诊断效能ROC_DiagnosticROC` | `04_临床预测与统计_ClinicalStats/诊断效能ROC_DiagnosticROC` |
| `01_组学_Omics/跨物种基因映射_CrossSpecies` | `05_系统方法_SystemsMethods/跨物种基因映射_CrossSpecies` |
| `01_组学_Omics/转录因子与调控网络_TF-Network` | `05_系统方法_SystemsMethods/转录因子与调控网络_TF-Network` |
| `01_组学_Omics/遗传关联下游_GeneticDownstream` | `02_遗传与变异_Genetics/遗传关联下游_GeneticDownstream` |
| `01_组学_Omics/长读长测序分析_LongRead` | `02_遗传与变异_Genetics/长读长测序分析_LongRead` |
| `02_已落地流水线_ProductionPipelines` | `06_已落地流水线_ProductionPipelines` |
| `02_已落地流水线_ProductionPipelines/差异分析与UMAP流水线_DEG-UMAP` | `06_已落地流水线_ProductionPipelines/差异分析与UMAP流水线_DEG-UMAP` |
| `03_分类验证_Validation` | `07_分类验证_Validation` |

## 分类原则

- **omics**：测序/组学数据类型本体（转录、单细胞、蛋白、代谢、表观、微生物等）
- **genetics**：变异、组装、GWAS/群体/MR/系统发育等
- **drug**：网络药理、对接、MD、结构、ADMET、CMap、GDSC
- **clinical**：生存/ROC/Meta/ML/分型/液体活检/放射组学/免疫浸润/新抗原/DoseTime
- **systems**：可被多组学调用的方法层（GSEA、WGCNA、PPI、通讯、虚拟敲除等）

脚本：`_layout_migrate_phaseA.py`

## 样例目录规范（2026-07 补充）

- 无编号 `样例_sample/` → 带排序前缀 `01_样例_sample/`（多例则 `02_`、`03_`…）
- `结果文件/` 必须与 `代码文件/`、`数据文件/` **同级**；禁止 `代码文件/结果文件/`
- 迁移脚本：`_fix_sample_layout.py`
