# 书清 / 山水 → 技能样例嵌入登记

日期：2026-07-19

## 原则
- 书清/山水为本地真实分析树（gitignore）；**样例以技能内 `数据文件/real_*` 为 SSOT**。
- 样例脚本 **优先读本技能缓存**；`SHUQING_ROOT`/`SHANSHUI_ROOT` 仅作可选回源。
- 无对应组学资产的技能（对接/GWAS raw/16S 等）不伪造矩阵，保持 TOY/BLOCKED 诚实标注。

## 本轮已接通 REAL 样例脚本（cache-first）
- 细胞通讯 / PPI / 诊断ROC / TF-Network / 荟萃分析 / 虚拟敲除
- 以及既有：GSEA / scRNA / Immune / DoseTime / Survival / DEG-UMAP / RNA-seq / Microarray / GEO-TCGA / WGCNA

## 当前含 real_ 缓存的技能数：18 / 70

### 已嵌入
- 差异分析与UMAP流水线_DEG-UMAP
- 单细胞与空间转录组分析_scRNA-Spatial
- 蛋白质互作网络_PPI-Network
- 公共库挖掘_GEO-TCGA
- 共表达网络WGCNA_WGCNA
- 荟萃分析_MetaAnalysis
- 基因集富集与通路_GSEA-Pathway
- 基因芯片表达分析_Microarray
- 剂量反应与时间序列_DoseTime
- 免疫浸润与免疫治疗_ImmuneInfiltration
- 批次校正与整合_BatchCorrection
- 生存分析与预后模型_Survival
- 数据真实性验证_DataAuthenticity
- 细胞通讯分析_CellCommunication
- 虚拟敲除与扰动_InSilicoKO
- 诊断效能ROC_DiagnosticROC
- 转录因子与调控网络_TF-Network
- 转录组分析_RNA-seq

### 尚未嵌入（无书清山水可映射 slim 表，或属工具/BLOCKED/异组学）
- ATAC专论_ATAC-seq
- CRISPR筛选分析_CRISPRscreen
- DNA甲基化分析_WGBS-RRBS
- NGS质控与比对_NGS-QC-Alignment
- RNA编辑与修饰_RNAEditing
- RNA融合基因检测_FusionGene
- 变异检测与外显子组_Variant-WES
- 表观遗传ChIP-seq_Epigenomics
- 代谢组分析_Metabolomics
- 单细胞多组学_scMultiome
- 单细胞进阶方法_scRNA-Advanced
- 单细胞质谱流式_CyTOF
- 蛋白结构与建模_ProteinStructure
- 蛋白质组分析_Proteomics
- 多组学联合分析_MultiOmics
- 放射组学与病理组学_Radiomics-Pathomics
- 非编码与ceRNA_ncRNA-ceRNA
- 分子动力学模拟_MolecularDynamics
- 分子对接与虚拟筛选_MolecularDocking
- 分子分型与共识聚类_MolecularSubtyping
- 核糖体图谱分析_Ribo-seq
- 宏基因组与病原_Metagenome-Pathogen
- 机器学习生物标志物_ML-Biomarker
- 基因组组装与注释_GenomeAssembly
- 剪接与异构体分析_AlternativeSplicing
- 结构变异分析_StructuralVariant
- 拷贝数变异分析_CNV
- 可复现工作流_ReproducibleWorkflow
- 空间转录组进阶_SpatialAdvanced
- 跨物种基因映射_CrossSpecies
- 类药性与QSAR_ADMET-QSAR
- 孟德尔随机化_MendelianRandomization
- 全基因组关联分析_GWAS
- 群体遗传学_PopulationGenetics
- 三维基因组分析_3DGenome
- 实验设计与统计功效_StudyDesign
- 糖组学分析_Glycomics
- 统一交付规范_DeliveryStandards
- 统一可视化规范_VizStandards
- 外泌体与液体活检_LiquidBiopsy
- 网络药理学_NetworkPharmacology
- 微生物组16S分析_Microbiome16S
- 文献与数据库检索_Literature-DB
- 系统发育分析_Phylogenetics
- 新抗原与免疫组库_Neoantigen-TCR
- 新生转录组_NascentRNA
- 研究方案编排_ResearchOrchestrator
- 药物敏感性与GDSC_DrugResponse
- 药物重定位与连通图_CMap-L1000
- 遗传关联下游_GeneticDownstream
- 长读长测序分析_LongRead
- 肿瘤体细胞景观_TumorSomatic

## 诚实边界
- 「技能完整」= 有书清/山水可映射表的技能已自包含；异组学（16S/对接/蛋白组等）仍 TOY/BLOCKED，不编造。
