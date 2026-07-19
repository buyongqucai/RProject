# -*- coding: utf-8 -*-
"""Batch-create missing bioinfo skills (one method = one skill). Do not run twice carelessly."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OMICS = ROOT / "01_组学_Omics"
FOUND = ROOT / "00_基础_Foundation"

FOUNDATION_FOLDERS = {
    "实验设计与统计功效_StudyDesign",
    "批次校正与整合_BatchCorrection",
    "文献与数据库检索_Literature-DB",
    "可复现工作流_ReproducibleWorkflow",
    "NGS质控与比对_NGS-QC-Alignment",
}

# tuple fields documented in write_skill()
SKILLS: list[tuple] = []


def S(*args):
    SKILLS.append(args)


# --- H Drug ---
S(
    "网络药理学_NetworkPharmacology",
    "bioinfo-network-pharmacology",
    "网络药理学",
    "NetworkPharmacology",
    "H",
    "P0-Drug",
    ["网络药理", "中药靶点", "成分靶点疾病"],
    ["化合物", "靶点列表", "DEG"],
    ["igraph", "clusterProfiler", "ggplot2"],
    [],
    "TCMSP/HERB/SwissTargetPrediction；疾病基因或 DEG",
    "中药/化合物多靶点网络、成分-靶点-疾病；药物-基因层",
    "成分收集→靶点预测→与疾病基因交集→网络/通路→出图",
    "网络图、韦恩、通路气泡",
    "网络中心性≠因果；数据库覆盖有偏；须正交验证",
    "分子对接、MD、转录组 DEG；PPI 边界：不含成分",
    "药物-基因",
)
S(
    "分子对接与虚拟筛选_MolecularDocking",
    "bioinfo-molecular-docking",
    "分子对接与虚拟筛选",
    "MolecularDocking",
    "H",
    "P0-Drug",
    ["分子对接", "Vina", "虚拟筛选"],
    ["受体PDB", "配体SDF"],
    ["bio3d", "ggplot2"],
    ["AutoDock Vina", "Open Babel"],
    "PDB/AlphaFold 结构；配体 3D",
    "验证靶点结合、虚筛排序；山水 M16",
    "受体/配体准备→对接→打分排序→姿态分析→出图",
    "结合能条图、2D 相互作用图",
    "打分近似；勿单凭对接定药效",
    "网络药理、蛋白结构、MD、ADMET",
    "药物-基因",
)
S(
    "分子动力学模拟_MolecularDynamics",
    "bioinfo-molecular-dynamics",
    "分子动力学模拟",
    "MolecularDynamics",
    "H",
    "P0-Drug",
    ["分子动力学", "GROMACS", "MD", "RMSD"],
    ["拓扑", "轨迹"],
    ["bio3d", "ggplot2"],
    ["GROMACS", "Amber"],
    "对接复合物或已知复合物",
    "对接后稳定性/结合自由能；山水 M17；勿假装纯 R 跑 MD",
    "溶剂化→最小化→平衡→生产→RMSD/RMSF/氢键/MM-PBSA",
    "RMSD/RMSF 曲线",
    "力场与时长影响结论；MM-PBSA 有近似",
    "分子对接、蛋白结构",
    "药物-基因",
)
S(
    "蛋白结构预测与口袋_ProteinStructure",
    "bioinfo-protein-structure",
    "蛋白结构预测与口袋",
    "ProteinStructure",
    "H",
    "P0-Drug",
    ["AlphaFold", "蛋白结构", "口袋", "PDB"],
    ["序列", "PDB ID"],
    ["bio3d"],
    ["fpocket"],
    "UniProt/PDB/AlphaFold DB",
    "对接前置：结构获取与口袋",
    "取结构→质控→口袋检测→交给对接",
    "结构卡通/口袋示意",
    "预测结构需标明置信度 pLDDT",
    "分子对接、同源建模",
    "药物-基因",
)
S(
    "ADMET与类药性评价_ADMET",
    "bioinfo-admet",
    "ADMET与类药性评价",
    "ADMET",
    "H",
    "P0-Drug",
    ["ADMET", "类药性", "Lipinski"],
    ["SMILES"],
    [],
    ["SwissADME", "pkCSM", "RDKit"],
    "候选化合物 SMILES",
    "筛选漏斗、毒性/吸收过滤",
    "描述符→Lipinski→ADMET 预测→过滤表",
    "雷达/条图",
    "网页预测非实验值",
    "网络药理、对接、QSAR",
    "药物-基因",
)
S(
    "QSAR与药效团_QSAR-Pharmacophore",
    "bioinfo-qsar",
    "QSAR与药效团",
    "QSAR-Pharmacophore",
    "H",
    "P2",
    ["QSAR", "药效团"],
    ["活性数据", "SMILES"],
    [],
    ["RDKit"],
    "已知活性化合物集",
    "定量构效、药效团扩展",
    "描述符→模型→验证→药效团匹配",
    "观测 vs 预测散点",
    "过拟合与适用范围",
    "ADMET、对接",
    "药物-基因",
)
S(
    "药物重定位与连通图_CMap-L1000",
    "bioinfo-cmap",
    "药物重定位与连通图",
    "CMap-L1000",
    "H",
    "P1",
    ["CMap", "L1000", "药物重定位"],
    ["基因签名", "DEG"],
    ["PharmacoGx", "ggplot2"],
    [],
    "上调/下调基因签名",
    "表达逆转药签、重定位假说",
    "签名→查询 CMap/L1000→药物列表→解读",
    "连通性条图",
    "细胞系≠组织；假说级",
    "转录组、药物敏感性 GDSC",
    "药物-基因",
)

# A
S("基因组组装与注释_GenomeAssembly", "bioinfo-genome-assembly", "基因组组装与注释", "GenomeAssembly", "A", "P2",
  ["基因组组装", "de novo", "Prokka"], ["FASTQ"], ["rtracklayer"], ["SPAdes", "Flye", "Prokka"],
  "测序 reads", "组装与基因注释", "质控→组装→评估→注释", "N50 等质控图", "污染与杂合影响组装", "变异检测、长读长", "—")
S("变异检测与注释_VariantCalling", "bioinfo-variant-calling", "变异检测与注释", "VariantCalling", "A", "P0",
  ["变异检测", "VCF", "GATK", "SNV"], ["BAM", "VCF"], ["VariantAnnotation", "ggplot2"], ["GATK", "bcftools"],
  "比对 BAM 或已有 VCF", "体细胞/胚系 SNV Indel", "BQSR→call→filter→注释", "Ti/Tv、Venn", "覆盖度与假阳性", "WES、CNV、TMB", "病因-基因")
S("拷贝数变异分析_CNV", "bioinfo-cnv", "拷贝数变异分析", "CNV", "A", "P1",
  ["CNV", "拷贝数"], ["BAM"], ["DNAcopy", "ggplot2"], ["CNVkit"],
  "WGS/WES/芯片", "拷贝数增益缺失", "深度→分段→基因注释", "染色体 CNV 图", "肿瘤纯度影响", "变异检测、克隆演化", "病因-基因")
S("结构变异分析_StructuralVariant", "bioinfo-sv", "结构变异分析", "StructuralVariant", "A", "P2",
  ["结构变异", "SV"], ["BAM"], ["StructuralVariantAnnotation"], ["Manta", "lumpy"],
  "WGS BAM", "大结构变异", "call SV→过滤→注释", "circos", "短读长对 SV 敏感度有限", "融合基因 RNA、长读长", "病因-基因")
S("全外显子组分析_WES", "bioinfo-wes", "全外显子组分析", "WES", "A", "P2",
  ["WES", "外显子组"], ["WES FASTQ"], ["VariantAnnotation"], ["GATK", "Exomiser"],
  "WES 数据", "外显子组致病性解读", "QC→比对→变异→致病性排序", "同变异检测图", "覆盖捕获偏差", "变异检测、NGS-QC", "病因-基因")
S("长读长测序分析_LongRead", "bioinfo-longread", "长读长测序分析", "LongRead", "A", "P2",
  ["长读长", "ONT", "PacBio"], ["long-read FASTQ"], ["NanoMethViz"], ["minimap2", "Medaka"],
  "ONT/PacBio", "组装/校正/甲基化", "比对→校正→组装或甲基化", "质量图", "错误率模型依赖版本", "组装、SV", "—")

# B
S("剪接与异构体分析_AlternativeSplicing", "bioinfo-splicing", "剪接与异构体分析", "AlternativeSplicing", "B", "P0",
  ["剪接", "rMATS", "异构体"], ["BAM"], ["ggplot2"], ["rMATS", "LeafCutter"],
  "RNA-seq BAM", "差异剪接/异构体", "定量→差异剪接→功能注释", "火山/sashimi", "深度不足假阴性", "转录组、ncRNA", "病因-基因")
S("非编码RNA分析_ncRNA", "bioinfo-ncrna", "非编码RNA分析", "ncRNA", "B", "P0",
  ["miRNA", "lncRNA", "circRNA", "非编码"], ["小RNA/RNA-seq"], ["clusterProfiler", "ggplot2"], [],
  "miRNA-seq 或注释表达矩阵", "非编码 RNA 定量与靶基因", "定量→差异→靶预测→富集", "火山/网络", "靶预测假阳性高", "ceRNA、转录组", "病因-基因")
S("核糖体图谱分析_Ribo-seq", "bioinfo-riboseq", "核糖体图谱分析", "Ribo-seq", "B", "P1",
  ["Ribo-seq", "翻译效率"], ["Ribo-seq BAM"], ["ORFik"], [],
  "核糖体足迹测序", "翻译效率、ORF", "比对→足迹→TE→ORF", "metagene", "需匹配 RNA-seq 对照", "转录组", "病因-基因")
S("RNA编辑与修饰_RNAEditing", "bioinfo-rna-editing", "RNA编辑与修饰", "RNAEditing", "B", "P2",
  ["RNA编辑", "m6A", "MeRIP"], ["BAM", "IP"], ["exomePeak2"], ["REDItools"],
  "RNA-seq 或 MeRIP", "A-to-I 或 m6A 峰", "call 位点/峰→差异→注释", "峰注释图", "区分 SNV 与编辑", "转录组、表观", "病因-基因")
S("转录因子与调控网络_TF-Network", "bioinfo-tf-network", "转录因子与调控网络", "TF-Network", "B", "P0",
  ["转录因子", "GRN", "SCENIC", "motif"], ["表达", "ATAC"], ["decoupleR", "ggplot2"], ["HOMER"],
  "表达矩阵或单细胞", "TF 活性与调控网络", "motif/regulon→活性评分→网络", "TF 活性热图", "推断非直接结合证据", "ChIP、ATAC、虚拟敲除", "病因-基因")
S("ATAC专论_ATAC-seq", "bioinfo-atac", "ATAC专论", "ATAC-seq", "B", "P1",
  ["ATAC", "染色质开放"], ["ATAC FASTQ"], ["Signac", "ggplot2"], ["MACS2", "Bowtie2"],
  "ATAC-seq", "开放染色质专用（异于 ChIP）", "比对→peak→差异→motif", "峰注释/足迹", "需线粒体过滤等 QC", "ChIP、单细胞多组学", "病因-基因")
S("DNA甲基化分析_WGBS-RRBS", "bioinfo-methylation", "DNA甲基化分析", "WGBS-RRBS", "B", "P0",
  ["甲基化", "WGBS", "RRBS", "EPIC", "450K"], ["bedGraph", "idat"], ["bsseq", "minfi", "DSS", "ggplot2"], [],
  "WGBS/RRBS 或 Illumina 芯片", "CpG 差异甲基化（含 EPIC）", "导入→QC→DMP/DMR→注释富集", "曼哈顿/火山", "细胞组成混杂", "转录组、液体活检", "病因-基因")
S("HiC三维基因组_HiC", "bioinfo-hic", "HiC三维基因组", "HiC", "B", "P1",
  ["Hi-C", "TAD", "三维基因组"], [".hic", ".cool"], ["GenomicInteractions"], ["Juicer", "cooler"],
  "Hi-C 接触图", "TAD/compartment/loop", "矩阵→归一化→TAD/loop→与基因关联", "接触热图", "分辨率与深度", "HiChIP、转录组", "病因-基因")

# C
S("单细胞多组学_scMultiome", "bioinfo-scmultiome", "单细胞多组学", "scMultiome", "C", "P1",
  ["multiome", "CITE-seq"], ["h5", "RDS"], ["Seurat", "Signac"], [],
  "RNA+ATAC 或 CITE", "单细胞内多模态", "质控→联合降维→注释→峰-基因链", "UMAP 双模态", "模态权重", "scRNA、ATAC", "病因-细胞")
S("单细胞轨迹与命运_Trajectory", "bioinfo-trajectory", "单细胞轨迹与命运", "Trajectory", "C", "P1",
  ["轨迹", "monocle", "velocity", "拟时"], ["Seurat"], ["monocle3", "slingshot", "ggplot2"], ["velocyto", "scVelo"],
  "已注释单细胞", "分化轨迹与 RNA 速度", "选根→拟时→差异沿轨迹→velocity 可选", "轨迹 UMAP", "轨迹假设依赖根选择", "scRNA、TF 网络", "病因-细胞")
S("细胞通讯分析_CellCommunication", "bioinfo-cell-communication", "细胞通讯分析", "CellCommunication", "C", "P0",
  ["细胞通讯", "CellChat", "配体受体"], ["Seurat"], ["CellChat", "ggplot2"], [],
  "带细胞类型注释的 scRNA", "配体-受体通讯（从延展独立）", "L-R 数据库→推断→比较条件→出图", "圈图/气泡", "推断非空间证实", "scRNA、空间进阶", "病因-细胞")
S("空间转录组进阶_SpatialAdvanced", "bioinfo-spatial-advanced", "空间转录组进阶", "SpatialAdvanced", "C", "P2",
  ["空间转录组", "Visium", "Xenium", "MERFISH"], ["空间对象"], ["Seurat", "Giotto"], [],
  "Visium/Xenium 等", "高分辨空间与反卷积", "QC→聚类→反卷积→共定位", "空间着色图", "分辨率平台差异大", "scRNA、细胞通讯", "病因-细胞")
S("单细胞整合与图谱_AtlasIntegration", "bioinfo-atlas", "单细胞整合与图谱", "AtlasIntegration", "C", "P2",
  ["图谱整合", "scVI", "query atlas"], ["多批次 scRNA"], ["Seurat", "harmony"], ["scvi-tools"],
  "多数据集单细胞", "批次整合与 query 映射", "整合→校正检查→投影注释", "整合 UMAP", "过度校正抹生物学差异", "BatchCorrection、scRNA", "病因-细胞")

# D E F
S("磷酸化与PTM蛋白组_PTM-Proteomics", "bioinfo-ptm", "磷酸化与PTM蛋白组", "PTM-Proteomics", "D", "P2",
  ["磷酸化", "PTM"], ["修饰肽表"], ["limma", "ggplot2"], [],
  "磷酸化/泛素化富集定量", "PTM 位点差异", "过滤→差异→激酶/基序→通路", "火山/基序", "需区分总量与修饰", "蛋白质组", "病因-基因")
S("脂质组分析_Lipidomics", "bioinfo-lipidomics", "脂质组分析", "Lipidomics", "D", "P2",
  ["脂质组", "lipidomics"], ["脂质峰表"], ["lipidr", "ropls", "ggplot2"], [],
  "脂质定量表", "脂质类别差异（从代谢拆出）", "注释→归一化→多元统计→通路", "同代谢组图", "异构体鉴定难", "代谢组", "病因-代谢物")
S("代谢通量分析_Fluxomics", "bioinfo-fluxomics", "代谢通量分析", "Fluxomics", "D", "P2",
  ["代谢通量", "FBA", "13C"], ["模型"], [], ["COBRApy"],
  "约束模型或 13C 数据", "通量估计", "模型→约束→FBA/MFA→解读", "通量条图", "模型假设强", "代谢组", "病因-代谢物")
S("宏基因组分析_Metagenomics", "bioinfo-metagenomics", "宏基因组分析", "Metagenomics", "E", "P1",
  ["宏基因组", "Kraken", "HUMAnN"], ["WGS reads"], ["ggplot2"], ["Kraken2", "HUMAnN", "MetaBAT"],
  "宏基因组测序", "物种/功能/MAG", "质控→分类/组装分箱→功能", "丰度堆叠", "宿主污染", "16S、宏转录组", "病因-细胞")
S("宏转录组分析_Metatranscriptomics", "bioinfo-metatranscriptomics", "宏转录组分析", "Metatranscriptomics", "E", "P2",
  ["宏转录组"], ["群落 RNA"], ["ggplot2"], ["HUMAnN"],
  "群落 RNA-seq", "菌群转录活性", "去宿主→定量→差异功能", "同宏基因组图", "rRNA 去除效率", "宏基因组", "病因-细胞")
S("病毒组与病原检测_Virome", "bioinfo-virome", "病毒组与病原检测", "Virome", "E", "P2",
  ["病毒组", "病原"], ["reads"], [], ["VirSorter", "blast"],
  "病毒富集或宏基因组", "病毒鉴定", "组装→病毒预测→注释", "丰度图", "数据库不全", "宏基因组", "—")
S("耐药与毒力基因_AMR-Virulence", "bioinfo-amr", "耐药与毒力基因", "AMR-Virulence", "E", "P2",
  ["耐药", "AMR", "毒力", "CARD"], ["基因组"], [], ["ABRicate", "CARD"],
  "细菌基因组", "耐药毒力基因筛查", "比对 CARD/VFDB→报告", "存在/缺失热图", "存在≠表达", "宏基因组", "—")
S("免疫浸润与免疫治疗_ImmuneInfiltration", "bioinfo-immune-infiltration", "免疫浸润与免疫治疗", "ImmuneInfiltration", "F", "P0",
  ["免疫浸润", "CIBERSORT", "TIDE", "ssGSEA"], ["表达矩阵"], ["GSVA", "ggplot2"], ["CIBERSORTx"],
  "bulk 表达", "免疫细胞比例与免疫治疗相关评分", "反卷积→评分→与临床关联", "堆叠/箱线", "反卷积依赖签名", "生存、scRNA", "病因-细胞")
S("新抗原与免疫组库_Neoantigen-TCR", "bioinfo-neoantigen", "新抗原与免疫组库", "Neoantigen-TCR", "F", "P1",
  ["新抗原", "TCR", "BCR"], ["VCF", "FASTQ"], [], ["netMHCpan", "MiXCR"],
  "突变 VCF+HLA；或 TCR 测序", "新抗原预测与组库多样性", "HLA→肽段→结合预测；或组库克隆型", "亲和力分布", "预测需实验验证", "HLA 分型、TMB", "药物-细胞")
S("肿瘤突变负荷与特征_TMB-Signature", "bioinfo-tmb", "肿瘤突变负荷与特征", "TMB-Signature", "F", "P1",
  ["TMB", "mutation signature", "sigminer"], ["VCF"], ["sigminer", "ggplot2"], [],
  "体细胞 VCF", "TMB 与突变特征", "计 TMB→签名分解→解读", "签名条图", "WES 与 panel 换算", "变异检测、免疫治疗", "病因-基因")
S("肿瘤异质性与克隆演化_ClonalEvolution", "bioinfo-clonal", "肿瘤异质性与克隆演化", "ClonalEvolution", "F", "P2",
  ["克隆演化", "PyClone", "异质性"], ["VAF"], [], ["PyClone"],
  "多区域/纵向突变 VAF", "克隆结构", "聚类克隆→系统树→解读", "鱼图", "纯度拷贝数校正关键", "CNV、变异", "病因-基因")
S("药物敏感性与GDSC_DrugResponse", "bioinfo-drug-response", "药物敏感性与GDSC", "DrugResponse", "F", "P1",
  ["GDSC", "药敏", "oncoPredict"], ["表达矩阵"], ["oncoPredict", "ggplot2"], [],
  "肿瘤表达谱", "表达预测药敏（非对接）", "训练/查询模型→IC50 预测→关联", "药敏热图", "细胞系外推有限", "CMap、生存", "药物-基因")

# G
S("基因集富集与通路_GSEA-Pathway", "bioinfo-gsea-pathway", "基因集富集与通路", "GSEA-Pathway", "G", "P0",
  ["GSEA", "GO", "KEGG", "GSVA", "富集"], ["基因列表", "有序列表"], ["clusterProfiler", "GSVA", "enrichplot", "ggplot2"], [],
  "DEG 或有序 logFC", "ORA/GSEA/GSVA（供任意组学调用）", "ID 映射→ORA/GSEA→作图", "dotplot/barplot/GSEA 曲线", "基因集选择影响结果", "全部组学下游", "解释")
S("共表达网络WGCNA_WGCNA", "bioinfo-wgcna", "共表达网络WGCNA", "WGCNA", "G", "P0",
  ["WGCNA", "共表达", "模块"], ["表达矩阵"], ["WGCNA", "ggplot2"], [],
  "bulk 表达样本足够", "共表达模块与性状关联", "软阈值→模块→hub→富集", "树状图/模块性状", "样本少不稳定", "转录组、ML 标志物", "解释")
S("蛋白质互作网络_PPI-Network", "bioinfo-ppi", "蛋白质互作网络", "PPI-Network", "G", "P0",
  ["PPI", "STRING", "互作网络"], ["基因列表"], ["STRINGdb", "igraph", "ggplot2"], ["Cytoscape"],
  "基因/蛋白列表", "疾病基因 PPI（不含成分网络药理）", "STRING→过滤→拓扑→hub", "网络图", "数据库偏倚", "网络药理边界、GSEA", "解释")
S("孟德尔随机化_MendelianRandomization", "bioinfo-mr", "孟德尔随机化", "MendelianRandomization", "G", "P0",
  ["孟德尔随机化", "MR", "TwoSampleMR"], ["GWAS 汇总"], ["TwoSampleMR", "MendelianRandomization"], [],
  "暴露/结局 GWAS summary", "因果推断工具变量", "选 IV→协调→MR 方法→敏感性", "散点/森林", "水平多效性", "GWAS、coloc", "预测")
S("共定位与TWAS_Coloc-TWAS", "bioinfo-coloc-twas", "共定位与TWAS", "Coloc-TWAS", "G", "P2",
  ["coloc", "TWAS", "共定位"], ["GWAS", "eQTL"], ["coloc"], [],
  "GWAS 与 eQTL 汇总统计", "共定位与转录组关联", "coloc/TWAS→候选基因", "区域图", "LD 与共享因果", "eQTL、MR", "病因-基因")
S("机器学习生物标志物_ML-Biomarker", "bioinfo-ml-biomarker", "机器学习生物标志物", "ML-Biomarker", "G", "P0",
  ["机器学习", "标志物", "随机森林", "LASSO"], ["表达", "临床"], ["caret", "glmnet", "ggplot2"], [],
  "特征矩阵+标签", "特征选择与预测模型（防泄漏）", "分割→选择→训练→验证→解释", "ROC/重要性", "必须独立验证防泄漏", "ROC、生存", "预测")

# I J K
S("放射组学与病理组学_Radiomics-Pathomics", "bioinfo-radiomics", "放射组学与病理组学", "Radiomics-Pathomics", "I", "P2",
  ["放射组学", "病理组学"], ["影像特征"], ["ggplot2"], [],
  "影像/病理特征表", "组学特征与预后", "特征提取→筛选→模型", "同 ML 图", "中心效应", "生存、ROC", "临床")
S("单细胞质谱流式_CyTOF", "bioinfo-cytof", "单细胞质谱流式", "CyTOF", "I", "P2",
  ["CyTOF", "质谱流式"], ["fcs"], ["FlowSOM", "ggplot2"], [],
  "CyTOF FCS", "蛋白水平单细胞分群", "预处理→降维→分群→差异", "UMAP", "面板设计限制", "scRNA", "病因-细胞")
S("糖组学分析_Glycomics", "bioinfo-glycomics", "糖组学分析", "Glycomics", "I", "P2",
  ["糖组学", "糖蛋白"], ["糖谱"], ["ggplot2"], [],
  "糖链定量", "糖修饰谱", "注释→差异→通路", "热图", "鉴定难度高", "蛋白组", "病因-代谢物")
S("相互作用组AP-MS_Interactomics", "bioinfo-interactomics", "相互作用组AP-MS", "Interactomics", "I", "P2",
  ["AP-MS", "互作组"], ["质谱鉴定表"], ["ggplot2"], [],
  "亲和纯化质谱", "物理互作置信网络", "对照过滤→评分→网络", "网络图", "非特异结合", "PPI", "解释")
S("实验设计与统计功效_StudyDesign", "bioinfo-study-design", "实验设计与统计功效", "StudyDesign", "J", "P1",
  ["实验设计", "样本量", "功效"], ["设计参数"], ["pwr"], [],
  "研究问题与效应量假设", "开题前样本量与重复设计", "效应量→功效/样本量→设计表", "功效曲线", "效应量常低估", "编排技能", "基础")
S("批次校正与整合_BatchCorrection", "bioinfo-batch", "批次校正与整合", "BatchCorrection", "J", "P1",
  ["批次校正", "ComBat", "Harmony"], ["多批次矩阵"], ["sva", "harmony", "limma"], [],
  "多批次组学", "技术批次去除", "诊断批次→校正→检查残留生物学", "PCA 前后对比", "过度校正风险", "多组学、atlas", "基础")
S("文献与数据库检索_Literature-DB", "bioinfo-literature-db", "文献与数据库检索", "Literature-DB", "J", "P2",
  ["文献检索", "DisGeNET", "OpenTargets", "TCMSP"], ["关键词"], [], [],
  "科学问题关键词", "证据与数据库检索策略", "关键词→库检索→证据表", "可选表图", "库覆盖与更新", "网络药理、编排", "基础")
S("可复现工作流_ReproducibleWorkflow", "bioinfo-repro-workflow", "可复现工作流", "ReproducibleWorkflow", "J", "P2",
  ["Snakemake", "Nextflow", "可复现", "容器"], ["流水线"], ["sessioninfo"], ["Snakemake", "Nextflow", "Docker"],
  "分析脚本集", "可复现编排与环境固定", "容器化→工作流→会话信息", "DAG 图可选", "环境漂移", "全部技能", "基础")
S("NGS质控与比对_NGS-QC-Alignment", "bioinfo-ngs-qc", "NGS质控与比对", "NGS-QC-Alignment", "K", "P0",
  ["FastQC", "MultiQC", "比对", "BAM"], ["FASTQ"], [], ["FastQC", "MultiQC", "BWA", "STAR", "samtools"],
  "原始 FASTQ", "各测序技能公共前置", "FastQC→修剪→比对→BAM 统计", "MultiQC 报告", "质量阈值依实验", "几乎所有测序技能", "基础")
S("基因芯片表达分析_Microarray", "bioinfo-microarray", "基因芯片表达分析", "Microarray", "K", "P1",
  ["芯片", "Affymetrix", "microarray"], ["CEL", "系列矩阵"], ["affy", "limma", "ggplot2"], [],
  "GEO 芯片", "芯片归一化 DEG（并列 RNA-seq）", "读入→RMA→limma→富集", "火山/热图", "探针注释版本", "GEO、GSEA", "病因-基因")
S("RNA融合基因检测_FusionGene", "bioinfo-fusion", "RNA融合基因检测", "FusionGene", "K", "P1",
  ["融合基因", "STAR-Fusion", "Arriba"], ["RNA FASTQ"], ["ggplot2"], ["STAR-Fusion", "Arriba"],
  "肿瘤 RNA-seq", "融合检出（勿并入普通 DEG）", "比对→融合 call→过滤注释", "融合示意图", "假阳性过滤关键", "SV、肿瘤", "病因-基因")
S("CUT与Tag分析_CUTnTag", "bioinfo-cutntag", "CUT与Tag分析", "CUTnTag", "K", "P1",
  ["CUT&Tag", "CUT&RUN"], ["FASTQ"], ["ggplot2"], ["MACS2", "Bowtie2"],
  "CUT&Tag/RUN", "低细胞表观峰（并列 ChIP）", "比对→peak→差异→注释", "同 ChIP 图", "IgG 对照", "ChIP、ATAC", "病因-基因")
S("染色质环与HiChIP_ChromatinLoop", "bioinfo-chromatin-loop", "染色质环与HiChIP", "ChromatinLoop", "K", "P2",
  ["HiChIP", "ChIA-PET", "染色质环"], ["pairs"], [], ["HiCCUPS"],
  "HiChIP 等", "蛋白锚定染色质环（异于 Hi-C）", "处理→loop calling→基因关联", "loop 图", "与 Hi-C 分辨率不同", "HiC、ChIP", "病因-基因")
S("新生转录组_NascentRNA", "bioinfo-nascent-rna", "新生转录组", "NascentRNA", "K", "P2",
  ["GRO-seq", "PRO-seq", "TT-seq"], ["BAM"], ["ggplot2"], [],
  "新生转录测序", "转录动力学", "比对→信号→基因体分析", "metagene", "实验难度高", "转录组、TF", "病因-基因")
S("ceRNA网络分析_ceRNA", "bioinfo-cerna", "ceRNA网络分析", "ceRNA", "K", "P0",
  ["ceRNA", "miRNA海绵", "竞争内源"], ["表达", "miRNA"], ["igraph", "ggplot2"], [],
  "miRNA 与 mRNA/lncRNA 表达", "山水 miR 轴常用竞争网络", "相关/共享 miRNA→网络→验证相关性", "网络图", "相关≠海绵机制", "ncRNA、转录组", "病因-基因")
S("外泌体与液体活检_LiquidBiopsy", "bioinfo-liquid-biopsy", "外泌体与液体活检", "LiquidBiopsy", "K", "P2",
  ["外泌体", "液体活检", "cfDNA", "ctDNA"], ["体液组学"], ["limma", "ggplot2"], [],
  "外泌体 RNA 或 cfDNA", "液体活检标志物", "预处理→差异→诊断/预后关联", "ROC/箱线", "预处理批次敏感", "ROC、甲基化", "临床")
S("荟萃分析_MetaAnalysis", "bioinfo-meta-analysis", "荟萃分析", "MetaAnalysis", "K", "P0",
  ["荟萃", "meta", "森林图", "异质性"], ["多研究效应量"], ["meta", "metafor", "ggplot2"], [],
  "多队列效应量或 DEG 方向", "从 GEO-TCGA 拆出的荟萃方法", "效应量→固定/随机→异质性→森林图", "森林图", "异质性须报告", "GEO-TCGA、生存", "比较")
S("生存分析与预后模型_Survival", "bioinfo-survival", "生存分析与预后模型", "Survival", "K", "P0",
  ["生存", "KM", "Cox", "预后", "列线图"], ["临床随访", "表达"], ["survival", "survminer", "rms", "ggplot2"], [],
  "时间+事件+特征", "从 GEO-TCGA 拆出；KM/Cox/列线图", "KM→单/多因素 Cox→列线图→校准", "KM/森林/列线图", "最优截断防数据挖掘", "GEO-TCGA、ROC、ML", "预测")
S("诊断效能ROC_DiagnosticROC", "bioinfo-diagnostic-roc", "诊断效能ROC", "DiagnosticROC", "K", "P0",
  ["ROC", "AUC", "诊断", "截断"], ["连续标志物", "二分类"], ["pROC", "ggplot2"], [],
  "标志物与金标准标签", "诊断预测独立技能", "ROC→AUC→截断→校准", "ROC 曲线", "需独立队列", "生存、ML、液体活检", "预测")
S("分子分型与共识聚类_MolecularSubtyping", "bioinfo-subtyping", "分子分型与共识聚类", "MolecularSubtyping", "K", "P1",
  ["分子分型", "共识聚类", "ConsensusClusterPlus"], ["表达矩阵"], ["ConsensusClusterPlus", "ggplot2"], [],
  "肿瘤表达谱", "无监督亚型", "一致性聚类→标志基因→临床关联", "一致性热图", "k 选择主观性", "生存、免疫浸润", "病因-基因")
S("CRISPR筛选分析_CRISPRscreen", "bioinfo-crispr-screen", "CRISPR筛选分析", "CRISPRscreen", "K", "P2",
  ["CRISPR", "MAGeCK", "筛选"], ["count 表"], ["ggplot2"], ["MAGeCK"],
  "CRISPR 文库计数", "功能基因组 hit", "MAGeCK→hit→通路", "火山", "文库覆盖", "GSEA", "病因-基因")
S("虚拟敲除与扰动_InSilicoKO", "bioinfo-insilico-ko", "虚拟敲除与扰动", "InSilicoKO", "K", "P1",
  ["虚拟敲除", "in silico KO", "CellOracle"], ["GRN", "DEG"], ["ggplot2"], [],
  "TF 网络+表达", "从 DEG-UMAP 延展独立", "regulon/GRN→扰动模拟→表型基因逆转评估", "扰动前后对比", "模型假设强", "TF 网络、细胞通讯", "预测")
S("跨物种基因映射_CrossSpecies", "bioinfo-cross-species", "跨物种基因映射", "CrossSpecies", "K", "P1",
  ["跨物种", "ortholog", "babelgene"], ["多基因列表"], ["babelgene", "ggplot2"], [],
  "人鼠等 DEG 列表", "书清延展独立：保守失调基因", "映射直系同源→交集→富集", "韦恩", "一对多同源", "转录组、GSEA", "解释")
S("eQTL与QTL作图_eQTL", "bioinfo-eqtl", "eQTL与QTL作图", "eQTL", "K", "P2",
  ["eQTL", "QTL", "矩阵EQTL"], ["基因型", "表达"], ["MatrixEQTL"], [],
  "同一样本基因型+表达", "表达数量性状位点", "关联→多重校正→注释", "位点图", "样本量需求大", "coloc、GWAS", "病因-基因")
S("多基因风险评分_PRS", "bioinfo-prs", "多基因风险评分", "PRS", "K", "P2",
  ["PRS", "多基因风险", "PRSice"], ["GWAS", "基因型"], [], ["PRSice-2", "LDpred2"],
  "GWAS 与目标队列基因型", "与 GWAS 关联分析分开", "权重→计算 PRS→表型关联", "分位数风险", "人群转移性", "GWAS、生存", "预测")
S("群体遗传学_PopulationGenetics", "bioinfo-popgen", "群体遗传学", "PopulationGenetics", "K", "P2",
  ["群体遗传", "Fst", "admixture"], ["基因型"], [], ["PLINK", "ADMIXTURE"],
  "群体基因型", "GWAS 上游结构", "QC→PCA→Fst/admixture", "PCA 图", "采样偏差", "GWAS", "基础")
S("系统发育分析_Phylogenetics", "bioinfo-phylo", "系统发育分析", "Phylogenetics", "K", "P2",
  ["系统发育", "建树", "MSA"], ["序列"], ["ape", "ggtree"], ["MAFFT", "IQ-TREE"],
  "核酸/蛋白序列", "进化树与分型", "MSA→建树→注释", "树图", "模型选择", "病原、病毒组", "—")
S("单细胞组成差异_scComposition", "bioinfo-sc-composition", "单细胞组成差异", "scComposition", "K", "P1",
  ["组成差异", "miloR", "scCODA", "propeller"], ["单细胞元数据"], ["miloR", "ggplot2"], [],
  "多样本 scRNA 细胞类型比例", "异于找 DEG 的组成检验", "计数→组成模型→差异类型", "DA 图", "样本重复关键", "scRNA", "病因-细胞")
S("HLA分型_HLA-Typing", "bioinfo-hla", "HLA分型", "HLA-Typing", "K", "P2",
  ["HLA", "OptiType", "HLA分型"], ["WES/RNA"], [], ["OptiType", "HLA-HD"],
  "测序 reads", "新抗原/移植前置", "分型→四位结果表", "报告表", "分辨率依赖数据", "新抗原", "基础")
S("时间序列组学_TimeSeriesOmics", "bioinfo-timeseries", "时间序列组学", "TimeSeriesOmics", "K", "P2",
  ["时间序列", "纵向", "剂量时间"], ["多时间点表达"], ["limma", "ggplot2"], [],
  "时间/剂量设计", "动态差异表达", "spline/Impulse→聚类模式→富集", "轨迹线图", "时间点稀疏", "转录组", "比较")
S("同源建模_HomologyModeling", "bioinfo-homology-modeling", "同源建模", "HomologyModeling", "K", "P2",
  ["同源建模", "MODELLER"], ["序列"], ["bio3d"], ["MODELLER"],
  "无实验结构靶点", "与 AlphaFold 并列补全结构", "模板搜索→建模→评估→对接", "结构图", "低同源不可靠", "蛋白结构、对接", "药物-基因")


def write_skill(s: tuple) -> dict:
    (
        folder,
        sid,
        zh,
        en,
        sec,
        pri,
        intents,
        dtypes,
        pkgs,
        cli,
        sources,
        when,
        steps,
        viz,
        interpret,
        combine,
        purpose,
    ) = s
    base = FOUND if folder in FOUNDATION_FOLDERS else OMICS
    d = base / folder
    d.mkdir(parents=True, exist_ok=True)
    scripts = d / "脚本_scripts"
    scripts.mkdir(exist_ok=True)

    pkg_lines = []
    if pkgs:
        for p in pkgs:
            pkg_lines.append(f"| 分析 | `{p}` | 核心 R 包 | |")
    else:
        pkg_lines.append("| （本技能以 CLI/网页为主） | — | 见 CLI 列 | |")
    for c in cli:
        pkg_lines.append(f"| 上游/主分析 | `{c}` | CLI 工具 | 非 R |")
    pkg_lines.append(
        "| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |"
    )
    pkg_table = "\n".join(pkg_lines)

    viz_link = (
        "../统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md"
        if folder in FOUNDATION_FOLDERS
        else "../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md"
    )

    md = f"""---
name: {sid}
description: >-
  {zh} / {en}：{when}。工具：{', '.join(pkgs + cli) or '见正文'}。
  触发：{', '.join(intents[:6])}。
---

# {zh} / {en}

## 1. 数据来源

{sources}

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- {when}
- 山水用途层标签：{purpose}

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

{steps}

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
{pkg_table}

## 6. 数据可视化

{viz}；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

{interpret}

## 8. 能否结合其它生信

{combine}；出图强制 [统一可视化规范]({viz_link})。
"""
    (d / f"技能说明_{folder}.md").write_text(md, encoding="utf-8")

    pkgs_r = list(pkgs) if pkgs else ["ggplot2"]
    if "ggplot2" not in pkgs_r:
        pkgs_r.append("ggplot2")
    pkgs_vec = ", ".join(f'"{p}"' for p in pkgs_r)
    cli_msg = ", ".join(cli) if cli else "无（见技能说明）"
    fun = "run_" + en.replace("-", "_").lower() + "_skeleton"

    r = f"""# {zh} 骨架 status=skeleton；包检查；出图 source 出版级出图
find_project_root <- function(start = getwd()) {{
  p <- normalizePath(start, winslash = "/", mustWork = FALSE)
  for (i in 1:8) {{
    if (file.exists(file.path(p, "RProject.Rproj"))) return(p)
    parent <- dirname(p); if (identical(parent, p)) break; p <- parent
  }}
  stop("未找到 RProject.Rproj")
}}
check_r_packages <- function(pkgs) {{
  missing <- pkgs[!vapply(pkgs, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
  if (length(missing)) stop("缺少 R 包: ", paste(missing, collapse = ", "), call. = FALSE)
  invisible(TRUE)
}}
source_pub_viz <- function(project_root = find_project_root()) {{
  f <- file.path(project_root, "生信分析技能_BioinformaticsSkills", "00_基础_Foundation",
                 "统一可视化规范_VizStandards", "脚本_scripts", "出版级出图_PublicationPlot.R")
  stopifnot("缺少出版级出图" = file.exists(f))
  source(f, encoding = "UTF-8")
}}
{fun} <- function(input_path = NULL, out_dir = tempfile("bioinfo_"),
                  project_root = find_project_root()) {{
  pkgs <- c({pkgs_vec})
  present <- pkgs[vapply(pkgs, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
  missing <- setdiff(pkgs, present)
  if (length(missing)) message("【骨架】未安装（可稍后安装）: ", paste(missing, collapse = ", "))
  if (length(present)) check_r_packages(present)
  source_pub_viz(project_root)
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  message("【骨架】{zh} input=", input_path, " out=", out_dir)
  message("【骨架】CLI 期望: {cli_msg}")
  invisible(list(status = "skeleton", skill = "{sid}", pkgs_checked = present, out_dir = out_dir))
}}
if (sys.nframe() == 0L && !interactive()) message("加载 {fun}()")
"""
    (scripts / "运行骨架_runSkeleton.R").write_text(r, encoding="utf-8")
    (scripts / "说明_README.md").write_text(
        f"# {zh}\n\n骨架入口：`运行骨架_runSkeleton.R`。完整流程见上级技能说明。\n",
        encoding="utf-8",
    )

    rel = str(d.relative_to(ROOT)).replace("\\", "/")
    return {
        "id": sid,
        "folder": folder,
        "path": rel,
        "doc": f"技能说明_{folder}.md",
        "title_zh": zh,
        "title_en": en,
        "section": sec,
        "priority": pri,
        "research_intents": intents,
        "data_types": dtypes,
        "r_packages": pkgs,
        "cli_tools": cli,
        "purpose_layer": purpose,
    }


def main():
    meta = []
    for s in SKILLS:
        meta.append(write_skill(s))
        print("OK", s[0])
    out = ROOT / "_generated_skills_meta.json"
    out.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL", len(meta), "->", out)


if __name__ == "__main__":
    main()
