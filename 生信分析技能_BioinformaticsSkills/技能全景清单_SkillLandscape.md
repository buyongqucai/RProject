# 技能全景清单 / Skill Landscape（去重后互斥分类）

SSOT：本文件 + `技能目录_skill-catalog.json`。
原则：可合并则合并；一方法一技能；边界写清「不包含」。

布局版本：`layout_version = 2026-07-layout-v2`（见 [目录重构说明_LayoutMigration.md](目录重构说明_LayoutMigration.md)）。

当前技能文档数：**67**（不含组入口）；已弃用目录见 catalog.`deprecated_folders`。

## 基础 / Foundation（`00_基础_Foundation`）

| 技能目录 | id | 触发词摘要 |
|----------|-----|------------|
| `NGS质控与比对_NGS-QC-Alignment` | `bioinfo-ngs-qc` | NGS质控与比对、NGS-QC-Alignment |
| `可复现工作流_ReproducibleWorkflow` | `bioinfo-repro-workflow` | 可复现工作流、ReproducibleWorkflow |
| `实验设计与统计功效_StudyDesign` | `bioinfo-study-design` | 实验设计与统计功效、StudyDesign |
| `批次校正与整合_BatchCorrection` | `bioinfo-batch` | 批次校正与整合、BatchCorrection |
| `数据真实性验证_DataAuthenticity` | `data-authenticity-verification` | 数据真实性验证、DataAuthenticity |
| `文献与数据库检索_Literature-DB` | `bioinfo-literature-db` | 文献与数据库检索、Literature-DB |
| `研究方案编排_ResearchOrchestrator` | `bioinfo-research-orchestrator` | 研究方案编排、ResearchOrchestrator |
| `统一可视化规范_VizStandards` | `bioinfo-viz-standards` | 统一可视化规范、VizStandards |
| `统一交付规范_DeliveryStandards` | `bioinfo-delivery-standards` | 交付规范、文件命名、样例报告 |

## 组学 / Omics（`01_组学_Omics`）

| 技能目录 | id | 触发词摘要 |
|----------|-----|------------|
| `ATAC专论_ATAC-seq` | `bioinfo-atac` | ATAC专论、ATAC-seq |
| `DNA甲基化分析_WGBS-RRBS` | `bioinfo-methylation` | DNA甲基化分析、WGBS-RRBS |
| `RNA编辑与修饰_RNAEditing` | `bioinfo-rna-editing` | RNA编辑与修饰、RNAEditing |
| `三维基因组分析_3DGenome` | `bioinfo-3d-genome` | Hi-C、TAD、HiChIP、ChIA-PET、染色质环 |
| `代谢组分析_Metabolomics` | `bioinfo-metabolomics` | 代谢组、OPLS-DA、脂质组、lipidomics、通量 |
| `公共库挖掘_GEO-TCGA` | `bioinfo-geo-tcga` | 公共库挖掘、GEO-TCGA |
| `剪接与异构体分析_AlternativeSplicing` | `bioinfo-splicing` | 剪接与异构体分析、AlternativeSplicing |
| `单细胞与空间转录组分析_scRNA-Spatial` | `bioinfo-scrna-spatial` | 单细胞与空间转录组分析、scRNA-Spatial |
| `单细胞多组学_scMultiome` | `bioinfo-scmultiome` | 单细胞多组学、scMultiome |
| `单细胞质谱流式_CyTOF` | `bioinfo-cytof` | 单细胞质谱流式、CyTOF |
| `基因芯片表达分析_Microarray` | `bioinfo-microarray` | 基因芯片表达分析、Microarray |
| `宏基因组与病原_Metagenome-Pathogen` | `bioinfo-metagenome-pathogen` | 宏基因组、宏转录组、病毒组、AMR、Kraken |
| `微生物组16S分析_Microbiome16S` | `bioinfo-16s` | 微生物组16S分析、Microbiome16S |
| `新生转录组_NascentRNA` | `bioinfo-nascent-rna` | 新生转录组、NascentRNA |
| `核糖体图谱分析_Ribo-seq` | `bioinfo-riboseq` | 核糖体图谱分析、Ribo-seq |
| `空间转录组进阶_SpatialAdvanced` | `bioinfo-spatial-advanced` | 空间转录组进阶、SpatialAdvanced |
| `糖组学分析_Glycomics` | `bioinfo-glycomics` | 糖组学分析、Glycomics |
| `蛋白质组分析_Proteomics` | `bioinfo-proteomics` | 蛋白质组、LFQ、TMT、DIA、磷酸化 |
| `表观遗传ChIP-seq_Epigenomics` | `bioinfo-chipseq` | ChIP-seq、CUT&Tag、CUT&RUN、peak、DiffBind |
| `转录组分析_RNA-seq` | `bioinfo-rnaseq` | 转录组分析、RNA-seq |
| `非编码与ceRNA_ncRNA-ceRNA` | `bioinfo-ncrna-cerna` | miRNA、lncRNA、circRNA、ceRNA、非编码 |

## 遗传与变异 / Genetics（`02_遗传与变异_Genetics`）

| 技能目录 | id | 触发词摘要 |
|----------|-----|------------|
| `RNA融合基因检测_FusionGene` | `bioinfo-fusion` | RNA融合基因检测、FusionGene |
| `变异检测与外显子组_Variant-WES` | `bioinfo-variant-wes` | 变异检测、VCF、GATK、WES、外显子组 |
| `基因组组装与注释_GenomeAssembly` | `bioinfo-genome-assembly` | 基因组组装与注释、GenomeAssembly |
| `孟德尔随机化_MendelianRandomization` | `bioinfo-mr` | 孟德尔随机化、MendelianRandomization |
| `拷贝数变异分析_CNV` | `bioinfo-cnv` | 拷贝数变异分析、CNV |
| `结构变异分析_StructuralVariant` | `bioinfo-sv` | 结构变异分析、StructuralVariant |
| `肿瘤体细胞景观_TumorSomatic` | `bioinfo-tumor-somatic` | TMB、mutation signature、克隆演化、PyClone、sigminer |
| `遗传关联下游_GeneticDownstream` | `bioinfo-genetic-downstream` | eQTL、QTL、coloc、TWAS、PRS |
| `长读长测序分析_LongRead` | `bioinfo-longread` | 长读长测序分析、LongRead |

## 药物计算 / DrugDiscovery（`03_药物计算_DrugDiscovery`）

| 技能目录 | id | 触发词摘要 |
|----------|-----|------------|
| `分子动力学模拟_MolecularDynamics` | `bioinfo-molecular-dynamics` | 分子动力学模拟、MolecularDynamics |
| `分子对接与虚拟筛选_MolecularDocking` | `bioinfo-molecular-docking` | 分子对接与虚拟筛选、MolecularDocking |
| `类药性与QSAR_ADMET-QSAR` | `bioinfo-admet-qsar` | ADMET、Lipinski、QSAR、药效团、类药性 |
| `网络药理学_NetworkPharmacology` | `bioinfo-network-pharmacology` | 网络药理学、NetworkPharmacology |
| `药物敏感性与GDSC_DrugResponse` | `bioinfo-drug-response` | 药物敏感性与GDSC、DrugResponse |
| `药物重定位与连通图_CMap-L1000` | `bioinfo-cmap` | 药物重定位与连通图、CMap-L1000 |
| `蛋白结构与建模_ProteinStructure` | `bioinfo-protein-structure` | AlphaFold、PDB、口袋、同源建模、MODELLER |

## 临床预测与统计 / ClinicalStats（`04_临床预测与统计_ClinicalStats`）

| 技能目录 | id | 触发词摘要 |
|----------|-----|------------|
| `免疫浸润与免疫治疗_ImmuneInfiltration` | `bioinfo-immune-infiltration` | 免疫浸润与免疫治疗、ImmuneInfiltration |
| `分子分型与共识聚类_MolecularSubtyping` | `bioinfo-subtyping` | 分子分型与共识聚类、MolecularSubtyping |
| `剂量反应与时间序列_DoseTime` | `bioinfo-dose-time` | 时间序列、纵向、剂量时间、dose-response |
| `外泌体与液体活检_LiquidBiopsy` | `bioinfo-liquid-biopsy` | 外泌体与液体活检、LiquidBiopsy |
| `放射组学与病理组学_Radiomics-Pathomics` | `bioinfo-radiomics` | 放射组学与病理组学、Radiomics-Pathomics |
| `新抗原与免疫组库_Neoantigen-TCR` | `bioinfo-neoantigen` | 新抗原、TCR、BCR、HLA、OptiType |
| `机器学习生物标志物_ML-Biomarker` | `bioinfo-ml-biomarker` | 机器学习生物标志物、ML-Biomarker |
| `生存分析与预后模型_Survival` | `bioinfo-survival` | 生存分析与预后模型、Survival |
| `荟萃分析_MetaAnalysis` | `bioinfo-meta-analysis` | 荟萃分析、MetaAnalysis |
| `诊断效能ROC_DiagnosticROC` | `bioinfo-diagnostic-roc` | 诊断效能ROC、DiagnosticROC |

## 系统方法 / SystemsMethods（`05_系统方法_SystemsMethods`）

| 技能目录 | id | 触发词摘要 |
|----------|-----|------------|
| `CRISPR筛选分析_CRISPRscreen` | `bioinfo-crispr-screen` | CRISPR筛选分析、CRISPRscreen |
| `共表达网络WGCNA_WGCNA` | `bioinfo-wgcna` | 共表达网络WGCNA、WGCNA |
| `单细胞进阶方法_scRNA-Advanced` | `bioinfo-scrna-advanced` | 轨迹、monocle、velocity、miloR、scCODA |
| `基因集富集与通路_GSEA-Pathway` | `bioinfo-gsea-pathway` | 基因集富集与通路、GSEA-Pathway |
| `多组学联合分析_MultiOmics` | `bioinfo-multiomics` | 多组学联合分析、MultiOmics |
| `细胞通讯分析_CellCommunication` | `bioinfo-cell-communication` | 细胞通讯分析、CellCommunication |
| `虚拟敲除与扰动_InSilicoKO` | `bioinfo-insilico-ko` | 虚拟敲除与扰动、InSilicoKO |
| `蛋白质互作网络_PPI-Network` | `bioinfo-ppi` | 蛋白质互作网络、PPI-Network |
| `跨物种基因映射_CrossSpecies` | `bioinfo-cross-species` | 跨物种基因映射、CrossSpecies |
| `转录因子与调控网络_TF-Network` | `bioinfo-tf-network` | 转录因子与调控网络、TF-Network |

## 生产流水线 / ProductionPipelines（`06_已落地流水线_ProductionPipelines`）

| 技能目录 | id | 触发词摘要 |
|----------|-----|------------|
| `差异分析与UMAP流水线_DEG-UMAP` | `differential-analysis-and-umap` | 差异分析与UMAP流水线、DEG-UMAP |

## 已合并（deprecated → 现行）

| 旧目录 | 并入 |
|--------|------|
| `ADMET与类药性评价_ADMET` | `类药性与QSAR_ADMET-QSAR` |
| `CUT与Tag分析_CUTnTag` | `表观遗传ChIP-seq_Epigenomics` |
| `HLA分型_HLA-Typing` | `新抗原与免疫组库_Neoantigen-TCR` |
| `HiC三维基因组_HiC` | `三维基因组分析_3DGenome` |
| `QSAR与药效团_QSAR-Pharmacophore` | `类药性与QSAR_ADMET-QSAR` |
| `ceRNA网络分析_ceRNA` | `非编码与ceRNA_ncRNA-ceRNA` |
| `eQTL与QTL作图_eQTL` | `遗传关联下游_GeneticDownstream` |
| `代谢通量分析_Fluxomics` | `代谢组分析_Metabolomics` |
| `全外显子组分析_WES` | `变异检测与外显子组_Variant-WES` |
| `共定位与TWAS_Coloc-TWAS` | `遗传关联下游_GeneticDownstream` |
| `单细胞整合与图谱_AtlasIntegration` | `单细胞进阶方法_scRNA-Advanced` |
| `单细胞组成差异_scComposition` | `单细胞进阶方法_scRNA-Advanced` |
| `单细胞轨迹与命运_Trajectory` | `单细胞进阶方法_scRNA-Advanced` |
| `变异检测与注释_VariantCalling` | `变异检测与外显子组_Variant-WES` |
| `同源建模_HomologyModeling` | `蛋白结构与建模_ProteinStructure` |
| `多基因风险评分_PRS` | `遗传关联下游_GeneticDownstream` |
| `宏基因组分析_Metagenomics` | `宏基因组与病原_Metagenome-Pathogen` |
| `宏转录组分析_Metatranscriptomics` | `宏基因组与病原_Metagenome-Pathogen` |
| `时间序列组学_TimeSeriesOmics` | `剂量反应与时间序列_DoseTime` |
| `染色质环与HiChIP_ChromatinLoop` | `三维基因组分析_3DGenome` |
| `病毒组与病原检测_Virome` | `宏基因组与病原_Metagenome-Pathogen` |
| `相互作用组AP-MS_Interactomics` | `蛋白质组分析_Proteomics` |
| `磷酸化与PTM蛋白组_PTM-Proteomics` | `蛋白质组分析_Proteomics` |
| `耐药与毒力基因_AMR-Virulence` | `宏基因组与病原_Metagenome-Pathogen` |
| `肿瘤异质性与克隆演化_ClonalEvolution` | `肿瘤体细胞景观_TumorSomatic` |
| `肿瘤突变负荷与特征_TMB-Signature` | `肿瘤体细胞景观_TumorSomatic` |
| `脂质组分析_Lipidomics` | `代谢组分析_Metabolomics` |
| `蛋白结构预测与口袋_ProteinStructure` | `蛋白结构与建模_ProteinStructure` |
| `表观峰检测_ChIP-CUTnTag` | `表观遗传ChIP-seq_Epigenomics` |
| `非编码RNA分析_ncRNA` | `非编码与ceRNA_ncRNA-ceRNA` |

## 明确不合并（边界）

- 网络药理 / 分子对接 / 分子动力学
- ATAC vs 表观峰检测(ChIP/CUT&Tag)
- Survival / Meta / ROC / ML-Biomarker
- CMap vs GDSC 药敏
- RNA 融合 vs DNA SV
- GEO-TCGA（下载队列）vs Survival
