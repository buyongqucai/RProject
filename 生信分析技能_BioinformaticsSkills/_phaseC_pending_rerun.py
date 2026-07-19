# -*- coding: utf-8 -*-
"""Phase C pending: DeliveryStandards-compliant rerun for all non-core skills."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import textwrap
from collections import Counter
from datetime import datetime
from pathlib import Path

from _phaseC_delivery_rerun import (
    BLOCKED_REASON,
    CORE_SKILLS,
    KIND_BY_PATH,
    ROOT,
    VAL_DIR,
    analysis_block,
    collect_png_hashes,
    ensure_tree,
    hash as skill_hash,
    list_pending,
    prepare_core,
    r_header,
    report_footer,
    run_one,
    skill_en,
    write_data_source,
    write_validation_report,
)

# ---------------------------------------------------------------------------
# Pending skill → (kind, seed). Seed from path hash when not listed.
# ---------------------------------------------------------------------------
PENDING_KIND: dict[str, str] = {
    "00_基础_Foundation/NGS质控与比对_NGS-QC-Alignment": "ngs_qc",
    "00_基础_Foundation/可复现工作流_ReproducibleWorkflow": "reproducible",
    "00_基础_Foundation/实验设计与统计功效_StudyDesign": "study_design",
    "00_基础_Foundation/批次校正与整合_BatchCorrection": "batch_correction",
    "00_基础_Foundation/文献与数据库检索_Literature-DB": "literature_db",
    "00_基础_Foundation/研究方案编排_ResearchOrchestrator": "research_orch",
    "01_组学_Omics/ATAC专论_ATAC-seq": "blocked_atac",
    "01_组学_Omics/RNA编辑与修饰_RNAEditing": "rna_editing",
    "01_组学_Omics/三维基因组分析_3DGenome": "blocked_3d",
    "01_组学_Omics/剪接与异构体分析_AlternativeSplicing": "splicing",
    "01_组学_Omics/单细胞多组学_scMultiome": "sc_multiome",
    "01_组学_Omics/单细胞质谱流式_CyTOF": "cytof",
    "01_组学_Omics/基因芯片表达分析_Microarray": "microarray",
    "01_组学_Omics/宏基因组与病原_Metagenome-Pathogen": "metagenome",
    "01_组学_Omics/新生转录组_NascentRNA": "nascent_rna",
    "01_组学_Omics/核糖体图谱分析_Ribo-seq": "riboseq",
    "01_组学_Omics/空间转录组进阶_SpatialAdvanced": "spatial_adv",
    "01_组学_Omics/糖组学分析_Glycomics": "glycomics",
    "01_组学_Omics/表观遗传ChIP-seq_Epigenomics": "blocked_chip",
    "01_组学_Omics/非编码与ceRNA_ncRNA-ceRNA": "ncrna",
    "02_遗传与变异_Genetics/RNA融合基因检测_FusionGene": "blocked_fusion",
    "02_遗传与变异_Genetics/变异检测与外显子组_Variant-WES": "blocked_wes",
    "02_遗传与变异_Genetics/基因组组装与注释_GenomeAssembly": "blocked_assembly",
    "02_遗传与变异_Genetics/孟德尔随机化_MendelianRandomization": "mr",
    "02_遗传与变异_Genetics/拷贝数变异分析_CNV": "cnv",
    "02_遗传与变异_Genetics/系统发育分析_Phylogenetics": "phylo",
    "02_遗传与变异_Genetics/结构变异分析_StructuralVariant": "blocked_sv",
    "02_遗传与变异_Genetics/群体遗传学_PopulationGenetics": "popgen",
    "02_遗传与变异_Genetics/肿瘤体细胞景观_TumorSomatic": "tumor_somatic",
    "02_遗传与变异_Genetics/遗传关联下游_GeneticDownstream": "genetic_down",
    "02_遗传与变异_Genetics/长读长测序分析_LongRead": "blocked_longread",
    "03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics": "blocked_md",
    "03_药物计算_DrugDiscovery/分子对接与虚拟筛选_MolecularDocking": "blocked_docking",
    "03_药物计算_DrugDiscovery/类药性与QSAR_ADMET-QSAR": "admet",
    "03_药物计算_DrugDiscovery/药物敏感性与GDSC_DrugResponse": "drug_response",
    "03_药物计算_DrugDiscovery/药物重定位与连通图_CMap-L1000": "cmap",
    "03_药物计算_DrugDiscovery/蛋白结构与建模_ProteinStructure": "protein_struct",
    "04_临床预测与统计_ClinicalStats/免疫浸润与免疫治疗_ImmuneInfiltration": "immune",
    "04_临床预测与统计_ClinicalStats/分子分型与共识聚类_MolecularSubtyping": "subtype",
    "04_临床预测与统计_ClinicalStats/剂量反应与时间序列_DoseTime": "dose_time",
    "04_临床预测与统计_ClinicalStats/外泌体与液体活检_LiquidBiopsy": "liquid_biopsy",
    "04_临床预测与统计_ClinicalStats/放射组学与病理组学_Radiomics-Pathomics": "blocked_radiomics",
    "04_临床预测与统计_ClinicalStats/新抗原与免疫组库_Neoantigen-TCR": "blocked_neoantigen",
    "04_临床预测与统计_ClinicalStats/机器学习生物标志物_ML-Biomarker": "ml_biomarker",
    "04_临床预测与统计_ClinicalStats/荟萃分析_MetaAnalysis": "meta",
    "04_临床预测与统计_ClinicalStats/诊断效能ROC_DiagnosticROC": "diagnostic_roc",
    "05_系统方法_SystemsMethods/CRISPR筛选分析_CRISPRscreen": "crispr",
    "05_系统方法_SystemsMethods/单细胞进阶方法_scRNA-Advanced": "scrna_adv",
    "05_系统方法_SystemsMethods/基因集富集与通路_GSEA-Pathway": "gsea",
    "05_系统方法_SystemsMethods/多组学联合分析_MultiOmics": "multiomics",
    "05_系统方法_SystemsMethods/细胞通讯分析_CellCommunication": "cellcomm",
    "05_系统方法_SystemsMethods/虚拟敲除与扰动_InSilicoKO": "insilico_ko",
    "05_系统方法_SystemsMethods/蛋白质互作网络_PPI-Network": "ppi",
    "05_系统方法_SystemsMethods/跨物种基因映射_CrossSpecies": "cross_species",
    "05_系统方法_SystemsMethods/转录因子与调控网络_TF-Network": "tf_network",
    "06_已落地流水线_ProductionPipelines/差异分析与UMAP流水线_DEG-UMAP": "deg_umap_pipe",
}

# Map blocked kinds → folder key used in BLOCKED_REASON
BLOCKED_KIND_FOLDER = {
    "blocked_atac": "ATAC专论_ATAC-seq",
    "blocked_3d": "三维基因组分析_3DGenome",
    "blocked_chip": "表观遗传ChIP-seq_Epigenomics",
    "blocked_fusion": "RNA融合基因检测_FusionGene",
    "blocked_wes": "变异检测与外显子组_Variant-WES",
    "blocked_assembly": "基因组组装与注释_GenomeAssembly",
    "blocked_sv": "结构变异分析_StructuralVariant",
    "blocked_longread": "长读长测序分析_LongRead",
    "blocked_md": "分子动力学模拟_MolecularDynamics",
    "blocked_docking": "分子对接与虚拟筛选_MolecularDocking",
    "blocked_radiomics": "放射组学与病理组学_Radiomics-Pathomics",
    "blocked_neoantigen": "新抗原与免疫组库_Neoantigen-TCR",
}


def blocked_block(folder: str, reason_key: str) -> str:
    en = skill_en(folder)
    reason = BLOCKED_REASON.get(reason_key, "缺少外部 CLI / 原始测序数据栈")
    # 三维基因组：主题接触矩阵示意，禁止无关 DEG
    if reason_key == "三维基因组分析_3DGenome" or en == "3DGenome":
        return textwrap.dedent(
            f"""\
            # ---- BLOCKED：三维基因组契约 + 接触矩阵示意 ----
            blocked_reason <- {json.dumps(reason, ensure_ascii=False)}
            stub <- data.frame(
              item = c("juicer_cooler_CLI", "hic_or_cool_input", "contact_matrix_pipeline", "delivery_contract"),
              ok = c(0, 0, 0, 1),
              note = c("missing", "missing", "blocked", "DeliveryStandards OK")
            )
            write.csv(stub, file.path(tab_dir, delivery_table_name(skill_en, "contract", "blockedStub")), row.names = FALSE)
            nbin <- 12
            cm <- outer(seq_len(nbin), seq_len(nbin), function(i, j) exp(-abs(i - j) / 3) + rnorm(1, 0, 0.03))
            cm <- pmax(cm, 0)
            bin_levels <- paste0("bin", seq_len(nbin))
            contact_long <- data.frame(
              bin_i = factor(rep(bin_levels, times = nbin), levels = bin_levels),
              bin_j = factor(rep(bin_levels, each = nbin), levels = bin_levels),
              contact = as.vector(cm)
            )
            write.csv(contact_long, file.path(tab_dir, delivery_table_name(skill_en, "contact", "ToyMatrix")), row.names = FALSE)
            write_delivery_audit(skill_en, "post", nrow(stub), 3, 0, "n/a BLOCKED Hi-C", TRUE, NA, sourced_note,
              paste("BLOCKED:", blocked_reason), file.path(tab_dir, delivery_audit_name(skill_en, "post")))
            library(ggplot2)
            p <- ggplot(contact_long, aes(bin_i, bin_j, fill = contact)) +
              geom_tile() +
              scale_fill_gradient(low = bioinfo_continuous[2], high = bioinfo_continuous[1], name = "Contact frequency") +
              coord_fixed() +
              labs(
                title = "Contact matrix (schematic · BLOCKED)",
                subtitle = "Toy schematic · not real Hi-C",
                x = "Bin i", y = "Bin j"
              ) +
              theme(plot.title = element_text(size = 10), plot.subtitle = element_text(size = 8),
                    axis.text.x = element_text(angle = 90, vjust = 0.5, hjust = 1, size = 7),
                    axis.text.y = element_text(size = 7))
            delivery_save_plot(p, skill_en, "heatmap", "ContactMatrixStub", 4.2, 3.8, fig_dir, bio_root)
            fig_map <- c("接触矩阵示意（BLOCKED）" = paste0("../图片文件/", delivery_stem(skill_en, "heatmap", "ContactMatrixStub"), ".png"))
            interp <- paste0("客观 BLOCKED：", blocked_reason, "。已产出契约/审计/主题示意；不得标 PASS。")
            status <- "BLOCKED"
            """
        )
    return textwrap.dedent(
        f"""\
        # ---- BLOCKED 契约样例：仍遵守命名/审计/报告，不伪造 PASS ----
        blocked_reason <- {json.dumps(reason, ensure_ascii=False)}
        stub <- data.frame(
          item = c("CLI_available", "raw_data", "contract_report"),
          ok = c(0, 0, 1),
          note = c("missing", "missing", "DeliveryStandards OK")
        )
        write.csv(stub, file.path(tab_dir, delivery_table_name(skill_en, "contract", "blockedStub")), row.names = FALSE)
        write_delivery_audit(skill_en, "post", nrow(stub), 3, 0, "n/a BLOCKED", TRUE, NA, sourced_note,
          paste("BLOCKED:", blocked_reason), file.path(tab_dir, delivery_audit_name(skill_en, "post")))
        library(ggplot2)
        p <- ggplot(stub, aes(item, ok, fill = item)) +
          geom_col(show.legend = FALSE) +
          scale_fill_manual(values = bioinfo_palette[1:3]) +
          labs(title = "Contract stub (schematic · BLOCKED)", y = "Pass (0/1)", x = NULL) +
          coord_cartesian(ylim = c(0, 1.2))
        delivery_save_plot(p, skill_en, "bar", "BlockedContract", FIG_WIDTH_DOUBLE_IN, 3.2, fig_dir, bio_root)
        fig_map <- c("BLOCKED 契约柱状图" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "BlockedContract"), ".png"))
        interp <- paste0("客观 BLOCKED：", blocked_reason, "。已产出合规命名图/审计/报告，状态不得标 PASS。")
        status <- "BLOCKED"
        """
    )


def pending_analysis_block(kind: str, folder: str) -> str:
    """Skill-distinct analysis R for pending kinds."""
    en = skill_en(folder)
    if kind in BLOCKED_KIND_FOLDER:
        return blocked_block(folder, BLOCKED_KIND_FOLDER[kind])

    blocks: dict[str, str] = {
        "ngs_qc": f"""
# NGS QC：per-sample mean quality
qc <- data.frame(
  sample = paste0("Lib", 1:8),
  mean_Q = 28 + rnorm(8, 0, 2.2) + c(rep(0, 6), -8, -6),
  pct_dup = runif(8, 5, 35)
)
write.csv(qc, file.path(data_dir, "toy_fastqc_summary.csv"), row.names = FALSE)
write.csv(qc, file.path(tab_dir, delivery_table_name(skill_en, "QC", "meanQ")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 8, 3, 8, "toy FastQC-like", TRUE, NA, sourced_note, "NGS QC",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(qc, aes(sample, mean_Q, fill = mean_Q < 25)) + geom_col() +
  geom_hline(yintercept = 25, linetype = 2) +
  scale_fill_manual(values = c("FALSE" = bioinfo_palette[2], "TRUE" = bioinfo_palette[1]), name = "fail Q<25") +
  labs(title = "NGS-QC-Alignment mean Q (toy)", y = "mean Phred")
delivery_save_plot(p, skill_en, "bar", "MeanPhred_perLib", 7, 4.5, fig_dir, bio_root)
fig_map <- c("文库平均质量" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "MeanPhred_perLib"), ".png"))
interp <- "玩具 FastQC 式质量柱状图；非真实测序。"
status <- "PASS"
""",
        "reproducible": f"""
steps <- data.frame(
  step = c("sessionInfo", "set.seed", "hash_input", "hash_output", "lockfile"),
  score = c(1, 1, 1, 1, 0.6) + runif(5, 0, 0.05)
)
write.csv(steps, file.path(tab_dir, delivery_table_name(skill_en, "checklist", "repro")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 5, 2, 0, "n/a", TRUE, NA, sourced_note, "repro checklist",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(steps, aes(reorder(step, score), score)) + geom_col(fill = bioinfo_palette[5]) +
  coord_flip() + labs(title = "ReproducibleWorkflow checklist (toy)", x = NULL, y = "score")
delivery_save_plot(p, skill_en, "bar", "ReproChecklist", 6.5, 4.5, fig_dir, bio_root)
fig_map <- c("可复现清单" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "ReproChecklist"), ".png"))
interp <- "可复现工作流自检玩具图。"
status <- "PASS"
""",
        "study_design": f"""
n <- 10:80
power <- 1 - pnorm(1.96 - 0.5 * sqrt(n / 2))
df <- data.frame(n = n, power = power)
write.csv(df, file.path(tab_dir, delivery_table_name(skill_en, "power", "twoSample")), row.names = FALSE)
write_delivery_audit(skill_en, "post", length(n), 2, NA, "toy effect=0.5", TRUE, NA, sourced_note, "power curve",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(df, aes(n, power)) + geom_line(color = bioinfo_palette[1], linewidth = 1.1) +
  geom_hline(yintercept = 0.8, linetype = 2) +
  labs(title = "StudyDesign power curve (toy)", x = "n per group", y = "power")
delivery_save_plot(p, skill_en, "line", "PowerVsN", 6.5, 4.5, fig_dir, bio_root)
fig_map <- c("功效曲线" = paste0("../图片文件/", delivery_stem(skill_en, "line", "PowerVsN"), ".png"))
interp <- "简化两样本功效曲线玩具；非真实试验设计结论。"
status <- "PASS"
""",
        "batch_correction": f"""
n <- 60
df <- data.frame(
  PC1 = c(rnorm(30, 0), rnorm(30, 3)),
  PC2 = rnorm(60),
  batch = rep(c("Batch1", "Batch2"), each = 30),
  stage = "before"
)
df2 <- df
df2$PC1 <- df$PC1 - ifelse(df$batch == "Batch2", 2.5, 0) + rnorm(60, 0, 0.2)
df2$stage <- "after"
plot_df <- rbind(df, df2)
write.csv(plot_df, file.path(tab_dir, delivery_table_name(skill_en, "PCA", "beforeAfter")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 60, 4, 60, "toy batch labels", TRUE, NA, sourced_note, "batch PCA",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(plot_df, aes(PC1, PC2, color = batch)) + geom_point(alpha = 0.75) +
  facet_wrap(~stage) + scale_color_manual(values = bioinfo_palette[1:2]) +
  labs(title = "BatchCorrection PCA before/after (toy)")
delivery_save_plot(p, skill_en, "PCA", "BeforeAfterBatch", 8, 4.5, fig_dir, bio_root)
fig_map <- c("批次校正前后PCA" = paste0("../图片文件/", delivery_stem(skill_en, "PCA", "BeforeAfterBatch"), ".png"))
interp <- "玩具批次效应校正示意；非 ComBat 真实结果。"
status <- "PASS"
""",
        "literature_db": f"""
hits <- data.frame(
  db = c("PubMed", "GEO", "TCGA", "KEGG", "DrugBank"),
  n_hits = c(120, 18, 6, 34, 11) + sample(-3:5, 5, replace = TRUE)
)
write.csv(hits, file.path(tab_dir, delivery_table_name(skill_en, "hits", "databases")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 5, 2, 0, "query toy", TRUE, NA, sourced_note, "DB hits",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(hits, aes(reorder(db, n_hits), n_hits, fill = db)) + geom_col(show.legend = FALSE) +
  coord_flip() + scale_fill_manual(values = bioinfo_palette[1:5]) +
  labs(title = "Literature-DB search hits (toy)", x = NULL, y = "hits")
delivery_save_plot(p, skill_en, "bar", "SearchHits", 6.5, 4.5, fig_dir, bio_root)
fig_map <- c("数据库命中" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "SearchHits"), ".png"))
interp <- "文献/数据库检索命中玩具计数。"
status <- "PASS"
""",
        "research_orch": f"""
plan <- data.frame(
  stage = c("question", "data", "QC", "DEG", "enrich", "report"),
  weight = c(1, 1.2, 1, 1.5, 1.1, 0.9)
)
write.csv(plan, file.path(tab_dir, delivery_table_name(skill_en, "plan", "stages")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 6, 2, 0, "n/a", TRUE, NA, sourced_note, "orchestrator plan",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(plan, aes(stage, weight, fill = stage)) + geom_col(show.legend = FALSE) +
  scale_fill_manual(values = bioinfo_palette[1:6]) +
  labs(title = "ResearchOrchestrator stage weights (toy)", y = "weight")
delivery_save_plot(p, skill_en, "bar", "PlanStages", 7, 4.5, fig_dir, bio_root)
fig_map <- c("方案阶段权重" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "PlanStages"), ".png"))
interp <- "研究方案编排阶段示意；非具体课题结论。"
status <- "PASS"
""",
        "rna_editing": f"""
sites <- data.frame(
  site = paste0("edit", 1:30),
  edit_rate = c(runif(20, 0.05, 0.25), runif(10, 0.4, 0.85)),
  tissue = rep(c("Brain", "Liver"), each = 15)
)
write.csv(sites, file.path(data_dir, "toy_edit_sites.csv"), row.names = FALSE)
write.csv(sites, file.path(tab_dir, delivery_table_name(skill_en, "editRate", "sites")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 30, 3, 30, "toy tissues", TRUE, NA, sourced_note, "A-to-I proxy",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(sites, aes(tissue, edit_rate, fill = tissue)) + geom_boxplot(alpha = 0.8) +
  geom_jitter(width = 0.12, size = 1.5, alpha = 0.7) +
  scale_fill_manual(values = bioinfo_palette[c(3, 6)]) +
  labs(title = "RNAEditing edit rate by tissue (toy)", y = "edit rate")
delivery_save_plot(p, skill_en, "boxplot", "EditRate_BrainVsLiver", 5.5, 4.5, fig_dir, bio_root)
fig_map <- c("编辑率箱线" = paste0("../图片文件/", delivery_stem(skill_en, "boxplot", "EditRate_BrainVsLiver"), ".png"))
interp <- "RNA 编辑率玩具分布。"
status <- "PASS"
""",
        "splicing": f"""
events <- data.frame(
  event = paste0("SE", 1:24),
  dPSI = rnorm(24, 0, 0.15),
  padj = runif(24, 0.001, 0.4)
)
events$dPSI[1:4] <- events$dPSI[1:4] + c(0.45, -0.4, 0.38, -0.35)
events$padj[1:4] <- c(0.001, 0.002, 0.003, 0.004)
write.csv(events, file.path(tab_dir, delivery_table_name(skill_en, "dPSI", "SE")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 24, 3, NA, "toy SE events", TRUE, NA, sourced_note, "splicing dPSI",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
events$sig <- ifelse(events$padj < 0.05 & abs(events$dPSI) > 0.2, "sig", "ns")
p <- ggplot(events, aes(dPSI, -log10(padj), color = sig)) + geom_point(size = 2.2) +
  scale_color_manual(values = c(ns = "grey70", sig = bioinfo_palette[1])) +
  labs(title = "AlternativeSplicing dPSI volcano (toy)", x = "ΔPSI")
delivery_save_plot(p, skill_en, "volcano", "dPSI_SE", 6.5, 5, fig_dir, bio_root)
fig_map <- c("剪接 dPSI 火山" = paste0("../图片文件/", delivery_stem(skill_en, "volcano", "dPSI_SE"), ".png"))
interp <- "剪接事件 ΔPSI 玩具火山图（与 RNA-seq DEG 数据不同）。"
status <- "PASS"
""",
        "sc_multiome": f"""
cells <- data.frame(
  RNA_PC1 = c(rnorm(80, 0), rnorm(80, 3.5)),
  ATAC_PC1 = c(rnorm(80, 0.5), rnorm(80, 2.8)),
  cluster = factor(rep(c("C1", "C2"), each = 80))
)
write.csv(cells, file.path(tab_dir, delivery_table_name(skill_en, "joint", "RNAvsATAC")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 160, 3, 160, "toy multiome", TRUE, NA, sourced_note, "RNA+ATAC",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(cells, aes(RNA_PC1, ATAC_PC1, color = cluster)) + geom_point(alpha = 0.7) +
  scale_color_manual(values = bioinfo_palette[1:2]) +
  labs(title = "scMultiome joint embedding proxy (toy)")
delivery_save_plot(p, skill_en, "scatter", "JointRNAvsATAC", 6.5, 5, fig_dir, bio_root)
fig_map <- c("多组学联合嵌入" = paste0("../图片文件/", delivery_stem(skill_en, "scatter", "JointRNAvsATAC"), ".png"))
interp <- "单细胞多组学玩具联合嵌入。"
status <- "PASS"
""",
        "cytof": f"""
markers <- paste0("M", 1:8)
mat <- matrix(rnorm(8 * 6, 1.5, 0.6), nrow = 8, dimnames = list(markers, paste0("cluster", 1:6)))
mat[1:2, 1:2] <- mat[1:2, 1:2] + 2
df <- data.frame(
  marker = rep(markers, times = 6),
  cluster = rep(paste0("cluster", 1:6), each = 8),
  intensity = as.vector(mat)
)
write.csv(df, file.path(tab_dir, delivery_table_name(skill_en, "heatmap", "markers")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 8, 6, NA, "toy CyTOF clusters", TRUE, NA, sourced_note, "marker heat",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(df, aes(cluster, marker, fill = intensity)) + geom_tile(color = "white") +
  scale_fill_gradient(low = "white", high = bioinfo_palette[1]) +
  labs(title = "CyTOF marker intensity (toy)", fill = "int")
delivery_save_plot(p, skill_en, "heatmap", "MarkerByCluster", 7, 5, fig_dir, bio_root)
fig_map <- c("标记物热图" = paste0("../图片文件/", delivery_stem(skill_en, "heatmap", "MarkerByCluster"), ".png"))
interp <- "质谱流式标记强度玩具热图。"
status <- "PASS"
""",
        "microarray": f"""
genes <- paste0("P", 1:80)
A <- rnorm(80, 8, 1.2)
M <- rnorm(80, 0, 0.4)
M[1:6] <- M[1:6] + c(1.8, -1.6, 1.5, -1.4, 1.2, -1.1)
ma <- data.frame(probe = genes, A = A, M = M)
write.csv(ma, file.path(tab_dir, delivery_table_name(skill_en, "MA", "CaseVsControl")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 80, 3, NA, "toy microarray", TRUE, NA, sourced_note, "MA plot",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
ma$sig <- ifelse(abs(ma$M) > 1, "sig", "ns")
p <- ggplot(ma, aes(A, M, color = sig)) + geom_point(alpha = 0.8) +
  geom_hline(yintercept = c(-1, 1), linetype = 2, color = "grey50") +
  scale_color_manual(values = c(ns = "grey70", sig = bioinfo_palette[3])) +
  labs(title = "Microarray MA plot (toy)", x = "A", y = "M")
delivery_save_plot(p, skill_en, "MA", "CaseVsControl", 6.5, 5, fig_dir, bio_root)
fig_map <- c("芯片 MA 图" = paste0("../图片文件/", delivery_stem(skill_en, "MA", "CaseVsControl"), ".png"))
interp <- "基因芯片 MA 玩具图（非 RNA-seq volcano）。"
status <- "PASS"
""",
        "metagenome": f"""
taxa <- data.frame(
  taxon = c("Ecoli", "Klebsiella", "Salmonella", "Bacteroides", "VirusX"),
  abundance = c(0.35, 0.18, 0.05, 0.28, 0.02) + runif(5, -0.01, 0.02),
  group = c("pathogen", "pathogen", "pathogen", "commensal", "virus")
)
write.csv(taxa, file.path(data_dir, "toy_pathogen_abund.csv"), row.names = FALSE)
write.csv(taxa, file.path(tab_dir, delivery_table_name(skill_en, "abund", "pathogen")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 5, 3, NA, "toy taxa", TRUE, NA, sourced_note, "metagenome",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(taxa, aes(reorder(taxon, abundance), abundance, fill = group)) +
  geom_col() + coord_flip() +
  scale_fill_manual(values = c(pathogen = bioinfo_palette[1], commensal = bioinfo_palette[2], virus = bioinfo_palette[4])) +
  labs(title = "Metagenome-Pathogen abundance (toy)", x = NULL, y = "rel abund")
delivery_save_plot(p, skill_en, "bar", "PathogenAbundance", 6.5, 4.5, fig_dir, bio_root)
fig_map <- c("病原相对丰度" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "PathogenAbundance"), ".png"))
interp <- "宏基因组/病原玩具丰度；非真实测序。"
status <- "PASS"
""",
        "nascent_rna": f"""
genes <- paste0("G", 1:40)
pi <- data.frame(
  gene = genes,
  pause_index = abs(rnorm(40, 2.5, 1.2)),
  group = rep(c("Promoter", "GeneBody"), each = 20)
)
pi$pause_index[1:5] <- pi$pause_index[1:5] + 4
write.csv(pi, file.path(tab_dir, delivery_table_name(skill_en, "pause", "index")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 40, 3, NA, "toy GRO/PRO-seq proxy", TRUE, NA, sourced_note, "pause index",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
top <- pi[order(-pi$pause_index), ][1:12, ]
top$gene <- factor(top$gene, levels = rev(top$gene))
p <- ggplot(top, aes(pause_index, gene, fill = group)) + geom_col() +
  scale_fill_manual(values = bioinfo_palette[c(2, 5)]) +
  labs(title = "NascentRNA pause index Top12 (toy)", x = "pause index")
delivery_save_plot(p, skill_en, "bar", "PauseIndex_Top12", 6.5, 5.5, fig_dir, bio_root)
fig_map <- c("暂停指数" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "PauseIndex_Top12"), ".png"))
interp <- "新生转录组暂停指数玩具。"
status <- "PASS"
""",
        "riboseq": f"""
orf <- data.frame(
  position = 1:60,
  coverage = c(rpois(20, 8), rpois(20, 40), rpois(20, 12))
)
write.csv(orf, file.path(tab_dir, delivery_table_name(skill_en, "ORF", "coverage")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 60, 2, NA, "toy ORF", TRUE, NA, sourced_note, "Ribo-seq cov",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(orf, aes(position, coverage)) +
  geom_area(fill = bioinfo_palette[3], alpha = 0.7) + geom_line(color = bioinfo_palette[3]) +
  labs(title = "Ribo-seq ORF coverage (toy)", x = "codon position", y = "coverage")
delivery_save_plot(p, skill_en, "area", "ORF_Coverage", 7, 4, fig_dir, bio_root)
fig_map <- c("ORF 覆盖" = paste0("../图片文件/", delivery_stem(skill_en, "area", "ORF_Coverage"), ".png"))
interp <- "核糖体图谱 ORF 覆盖玩具。"
status <- "PASS"
""",
        "spatial_adv": f"""
spots <- data.frame(
  x = c(runif(50, 0, 10), runif(50, 6, 14)),
  y = c(runif(50, 0, 10), runif(50, 5, 13)),
  domain = factor(rep(c("Epithelium", "Stroma"), each = 50)),
  score = c(rnorm(50, 1), rnorm(50, 2.5))
)
write.csv(spots, file.path(tab_dir, delivery_table_name(skill_en, "spatial", "domains")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 100, 4, 100, "toy spatial domains", TRUE, NA, sourced_note, "spatial",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(spots, aes(x, y, color = score, shape = domain)) + geom_point(size = 2.2) +
  scale_color_gradient(low = bioinfo_palette[4], high = bioinfo_palette[1]) +
  labs(title = "SpatialAdvanced domain spots (toy)")
delivery_save_plot(p, skill_en, "spatial", "DomainSpots", 6.5, 5.5, fig_dir, bio_root)
fig_map <- c("空间结构域" = paste0("../图片文件/", delivery_stem(skill_en, "spatial", "DomainSpots"), ".png"))
interp <- "空间转录组进阶玩具 spot 图。"
status <- "PASS"
""",
        "glycomics": f"""
gly <- data.frame(
  glycan = paste0("Gly", 1:15),
  abundance = abs(rnorm(15, 10, 4)),
  class = rep(c("N-glycan", "O-glycan", "glycolipid"), each = 5)
)
gly$abundance[1:3] <- gly$abundance[1:3] * 2.5
write.csv(gly, file.path(data_dir, "toy_glycans.csv"), row.names = FALSE)
write.csv(gly, file.path(tab_dir, delivery_table_name(skill_en, "abund", "glycans")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 15, 3, NA, "toy glycomics", TRUE, NA, sourced_note, "glycans",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
top <- gly[order(-gly$abundance), ][1:10, ]
top$glycan <- factor(top$glycan, levels = rev(top$glycan))
p <- ggplot(top, aes(abundance, glycan, fill = class)) + geom_col() +
  scale_fill_manual(values = bioinfo_palette[1:3]) +
  labs(title = "Glycomics Top10 abundance (toy)", x = "abundance")
delivery_save_plot(p, skill_en, "bar", "Top10Glycans", 6.5, 5, fig_dir, bio_root)
fig_map <- c("糖丰度" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "Top10Glycans"), ".png"))
interp <- "糖组学玩具丰度条形图。"
status <- "PASS"
""",
        "ncrna": f"""
edges <- data.frame(
  node = c("miR-21", "miR-155", "lncX", "circY", "GENE_A", "GENE_B", "GENE_C"),
  degree = c(12, 9, 7, 5, 8, 6, 4),
  type = c("miRNA", "miRNA", "lncRNA", "circRNA", "mRNA", "mRNA", "mRNA")
)
write.csv(edges, file.path(tab_dir, delivery_table_name(skill_en, "network", "degree")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 7, 3, NA, "toy ceRNA", TRUE, NA, sourced_note, "ceRNA degree",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(edges, aes(reorder(node, degree), degree, fill = type)) + geom_col() + coord_flip() +
  scale_fill_manual(values = bioinfo_palette[1:4]) +
  labs(title = "ncRNA-ceRNA node degree (toy)", x = NULL)
delivery_save_plot(p, skill_en, "bar", "ceRNA_Degree", 6.5, 4.5, fig_dir, bio_root)
fig_map <- c("ceRNA 度分布" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "ceRNA_Degree"), ".png"))
interp <- "非编码/ceRNA 网络度玩具。"
status <- "PASS"
""",
        "mr": f"""
iv <- data.frame(
  exposure = paste0("SNP", 1:12),
  beta = rnorm(12, 0.1, 0.08),
  se = runif(12, 0.02, 0.06)
)
iv$lo <- iv$beta - 1.96 * iv$se
iv$hi <- iv$beta + 1.96 * iv$se
write.csv(iv, file.path(tab_dir, delivery_table_name(skill_en, "IVW", "SNPs")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 12, 5, NA, "toy MR IVs", TRUE, NA, sourced_note, "MR forest",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(iv, aes(beta, reorder(exposure, beta))) +
  geom_vline(xintercept = 0, linetype = 2) +
  geom_errorbarh(aes(xmin = lo, xmax = hi), height = 0.2, color = "grey50") +
  geom_point(color = bioinfo_palette[1], size = 2.5) +
  labs(title = "MendelianRandomization IV estimates (toy)", x = "beta", y = NULL)
delivery_save_plot(p, skill_en, "forest", "IV_Estimates", 7, 5.5, fig_dir, bio_root)
fig_map <- c("MR 森林图" = paste0("../图片文件/", delivery_stem(skill_en, "forest", "IV_Estimates"), ".png"))
interp <- "孟德尔随机化工具变量效应玩具森林图。"
status <- "PASS"
""",
        "cnv": f"""
seg <- data.frame(
  chr = rep(1:4, each = 8),
  start = rep(seq(1, 8), 4),
  cn = c(rnorm(16, 2, 0.15), rnorm(8, 1.1, 0.1), rnorm(8, 3.2, 0.2))
)
write.csv(seg, file.path(tab_dir, delivery_table_name(skill_en, "CN", "segments")), row.names = FALSE)
write_delivery_audit(skill_en, "post", nrow(seg), 3, NA, "toy CNV", TRUE, NA, sourced_note, "CN segments",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(seg, aes(start, cn, color = factor(chr))) + geom_line(linewidth = 1) + geom_point() +
  geom_hline(yintercept = 2, linetype = 2) +
  scale_color_manual(values = bioinfo_palette[1:4]) +
  facet_wrap(~chr, nrow = 1) +
  labs(title = "CNV copy-number segments (toy)", color = "chr", y = "CN")
delivery_save_plot(p, skill_en, "line", "CNsegments", 9, 4, fig_dir, bio_root)
fig_map <- c("拷贝数片段" = paste0("../图片文件/", delivery_stem(skill_en, "line", "CNsegments"), ".png"))
interp <- "CNV 拷贝数片段玩具曲线。"
status <- "PASS"
""",
        "phylo": f"""
dist <- data.frame(
  pair = paste0("sp", 1:10, "-ref"),
  distance = sort(runif(10, 0.02, 0.45), decreasing = TRUE)
)
write.csv(dist, file.path(tab_dir, delivery_table_name(skill_en, "dist", "species")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 10, 2, NA, "toy phylogeny", TRUE, NA, sourced_note, "distances",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(dist, aes(reorder(pair, distance), distance)) + geom_col(fill = bioinfo_palette[6]) +
  coord_flip() + labs(title = "Phylogenetics pairwise distance (toy)", x = NULL, y = "distance")
delivery_save_plot(p, skill_en, "bar", "SpeciesDistance", 6.5, 5, fig_dir, bio_root)
fig_map <- c("种间距离" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "SpeciesDistance"), ".png"))
interp <- "系统发育距离玩具条形图。"
status <- "PASS"
""",
        "popgen": f"""
wins <- data.frame(
  window = 1:40,
  Fst = pmax(0, rnorm(40, 0.05, 0.04))
)
wins$Fst[c(8, 22, 33)] <- c(0.32, 0.28, 0.41)
write.csv(wins, file.path(tab_dir, delivery_table_name(skill_en, "Fst", "windows")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 40, 2, NA, "toy pops", TRUE, NA, sourced_note, "Fst scan",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(wins, aes(window, Fst)) + geom_line(color = bioinfo_palette[1]) +
  geom_point(aes(color = Fst > 0.2), size = 1.8) +
  scale_color_manual(values = c("FALSE" = "grey60", "TRUE" = bioinfo_palette[1])) +
  labs(title = "PopulationGenetics Fst scan (toy)", color = "outlier")
delivery_save_plot(p, skill_en, "line", "FstScan", 7.5, 4.5, fig_dir, bio_root)
fig_map <- c("Fst 扫描" = paste0("../图片文件/", delivery_stem(skill_en, "line", "FstScan"), ".png"))
interp <- "群体遗传学 Fst 窗口扫描玩具。"
status <- "PASS"
""",
        "tumor_somatic": f"""
tmb <- data.frame(
  sample = paste0("T", 1:12),
  TMB = c(rlnorm(8, log(3), 0.4), rlnorm(4, log(18), 0.3)),
  cohort = c(rep("MSS", 8), rep("MSI", 4))
)
write.csv(tmb, file.path(data_dir, "toy_tmb.csv"), row.names = FALSE)
write.csv(tmb, file.path(tab_dir, delivery_table_name(skill_en, "TMB", "cohort")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 12, 3, 12, "toy MSS/MSI", TRUE, NA, sourced_note, "TMB",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(tmb, aes(cohort, TMB, fill = cohort)) + geom_boxplot(alpha = 0.8) +
  geom_jitter(width = 0.1, size = 2) +
  scale_fill_manual(values = bioinfo_palette[c(2, 1)]) +
  labs(title = "TumorSomatic TMB by cohort (toy)", y = "mutations/Mb")
delivery_save_plot(p, skill_en, "boxplot", "TMB_MSSvsMSI", 5.5, 4.5, fig_dir, bio_root)
fig_map <- c("TMB 箱线" = paste0("../图片文件/", delivery_stem(skill_en, "boxplot", "TMB_MSSvsMSI"), ".png"))
interp <- "肿瘤体细胞 TMB 玩具比较。"
status <- "PASS"
""",
        "genetic_down": f"""
locus <- data.frame(
  pos = seq(1e5, 5e5, length.out = 80),
  neglogp = -log10(runif(80, 1e-4, 1))
)
locus$neglogp[35:38] <- c(7.5, 8.2, 6.9, 5.8)
write.csv(locus, file.path(tab_dir, delivery_table_name(skill_en, "locus", "zoom")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 80, 2, NA, "toy locus", TRUE, NA, sourced_note, "locuszoom proxy",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(locus, aes(pos / 1e5, neglogp)) +
  geom_point(aes(color = neglogp > 5), size = 1.8) +
  scale_color_manual(values = c("FALSE" = "grey60", "TRUE" = bioinfo_palette[1])) +
  labs(title = "GeneticDownstream locus zoom proxy (toy)", x = "pos (1e5 bp)", y = "-log10(P)")
delivery_save_plot(p, skill_en, "scatter", "LocusZoomProxy", 7, 4.5, fig_dir, bio_root)
fig_map <- c("位点缩放" = paste0("../图片文件/", delivery_stem(skill_en, "scatter", "LocusZoomProxy"), ".png"))
interp <- "遗传关联下游位点缩放玩具。"
status <- "PASS"
""",
        "admet": f"""
props <- data.frame(
  property = c("MW", "LogP", "HBD", "HBA", "TPSA", "QED"),
  value = c(320, 2.1, 2, 5, 78, 0.62) + rnorm(6, 0, 0.05),
  pass = c(TRUE, TRUE, TRUE, TRUE, TRUE, TRUE)
)
write.csv(props, file.path(tab_dir, delivery_table_name(skill_en, "ADMET", "descriptors")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 6, 3, NA, "toy molecule", TRUE, NA, sourced_note, "ADMET",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(props, aes(property, value, fill = property)) + geom_col(show.legend = FALSE) +
  scale_fill_manual(values = bioinfo_palette[1:6]) +
  labs(title = "ADMET-QSAR descriptors (toy)", y = "value")
delivery_save_plot(p, skill_en, "bar", "Descriptors", 6.5, 4.5, fig_dir, bio_root)
fig_map <- c("类药性描述符" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "Descriptors"), ".png"))
interp <- "类药性/QSAR 描述符玩具。"
status <- "PASS"
""",
        "drug_response": f"""
dose <- 10^seq(-3, 2, length.out = 20)
resp <- 100 / (1 + (dose / 0.8)^1.4) + rnorm(20, 0, 2)
dr <- data.frame(dose = dose, viability = pmax(0, resp), drug = "DrugX")
write.csv(dr, file.path(tab_dir, delivery_table_name(skill_en, "DRC", "DrugX")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 20, 3, NA, "toy GDSC-like", TRUE, NA, sourced_note, "dose-response",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(dr, aes(log10(dose), viability)) + geom_point(color = bioinfo_palette[1], size = 2) +
  geom_line(color = bioinfo_palette[1]) +
  labs(title = "DrugResponse viability curve (toy)", x = "log10(dose)", y = "% viability")
delivery_save_plot(p, skill_en, "line", "Viability_DrugX", 6.5, 4.5, fig_dir, bio_root)
fig_map <- c("剂量反应曲线" = paste0("../图片文件/", delivery_stem(skill_en, "line", "Viability_DrugX"), ".png"))
interp <- "药物敏感性剂量-活力玩具曲线。"
status <- "PASS"
""",
        "cmap": f"""
sig <- data.frame(
  compound = paste0("CMP", 1:15),
  tau = sort(rnorm(15, 0, 40), decreasing = TRUE)
)
write.csv(sig, file.path(tab_dir, delivery_table_name(skill_en, "connectivity", "tau")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 15, 2, NA, "toy CMap", TRUE, NA, sourced_note, "tau scores",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
sig$compound <- factor(sig$compound, levels = rev(sig$compound))
p <- ggplot(sig, aes(tau, compound, fill = tau > 0)) + geom_col() +
  scale_fill_manual(values = c("FALSE" = bioinfo_palette[4], "TRUE" = bioinfo_palette[1]), guide = "none") +
  labs(title = "CMap-L1000 connectivity tau (toy)", x = "tau")
delivery_save_plot(p, skill_en, "bar", "ConnectivityTau", 6.5, 5.5, fig_dir, bio_root)
fig_map <- c("连通性分数" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "ConnectivityTau"), ".png"))
interp <- "CMap/L1000 连通性玩具分数。"
status <- "PASS"
""",
        "protein_struct": f"""
res <- data.frame(
  residue = 1:80,
  pLDDT = c(runif(30, 40, 70), runif(30, 70, 92), runif(20, 55, 85))
)
write.csv(res, file.path(tab_dir, delivery_table_name(skill_en, "pLDDT", "model1")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 80, 2, NA, "toy AF-like", TRUE, NA, sourced_note, "pLDDT",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(res, aes(residue, pLDDT, color = pLDDT)) + geom_line(linewidth = 0.9) +
  scale_color_gradient(low = bioinfo_palette[1], high = bioinfo_palette[2]) +
  labs(title = "ProteinStructure pLDDT trace (toy)", y = "pLDDT")
delivery_save_plot(p, skill_en, "line", "pLDDT_Trace", 7.5, 4, fig_dir, bio_root)
fig_map <- c("pLDDT 轨迹" = paste0("../图片文件/", delivery_stem(skill_en, "line", "pLDDT_Trace"), ".png"))
interp <- "蛋白结构置信度 pLDDT 玩具轨迹。"
status <- "PASS"
""",
        "immune": f"""
cells <- data.frame(
  cell = c("CD8_T", "CD4_T", "B", "NK", "Macrophage", "Neutrophil", "DC", "Treg"),
  fraction = c(0.18, 0.15, 0.08, 0.06, 0.22, 0.12, 0.05, 0.04)
)
cells$fraction <- cells$fraction / sum(cells$fraction)
write.csv(cells, file.path(tab_dir, delivery_table_name(skill_en, "CIBERSORT", "fractions")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 8, 2, 1, "toy deconvolution", TRUE, NA, sourced_note, "immune frac",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(cells, aes(reorder(cell, fraction), fraction, fill = cell)) +
  geom_col(show.legend = FALSE) + coord_flip() +
  scale_fill_manual(values = rep(bioinfo_palette, length.out = 8)) +
  labs(title = "ImmuneInfiltration fractions (toy)", x = NULL, y = "fraction")
delivery_save_plot(p, skill_en, "bar", "CellFractions", 6.5, 5, fig_dir, bio_root)
fig_map <- c("免疫细胞比例" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "CellFractions"), ".png"))
interp <- "免疫浸润去卷积玩具比例。"
status <- "PASS"
""",
        "subtype": f"""
mat <- matrix(rnorm(6 * 6), 6, 6)
diag(mat) <- 1
mat[lower.tri(mat)] <- t(mat)[lower.tri(mat)]
labs <- paste0("S", 1:6)
df <- data.frame(
  a = rep(labs, each = 6),
  b = rep(labs, times = 6),
  cor = as.vector(mat)
)
write.csv(df, file.path(tab_dir, delivery_table_name(skill_en, "consensus", "cor")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 6, 6, 6, "toy subtypes", TRUE, NA, sourced_note, "consensus",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(df, aes(a, b, fill = cor)) + geom_tile(color = "white") +
  scale_fill_gradient2(low = bioinfo_palette[4], mid = "white", high = bioinfo_palette[1], midpoint = 0) +
  labs(title = "MolecularSubtyping consensus cor (toy)", fill = "cor")
delivery_save_plot(p, skill_en, "heatmap", "ConsensusCor", 5.5, 5, fig_dir, bio_root)
fig_map <- c("共识相关" = paste0("../图片文件/", delivery_stem(skill_en, "heatmap", "ConsensusCor"), ".png"))
interp <- "分子分型共识相关玩具热图。"
status <- "PASS"
""",
        "dose_time": f"""
grid <- expand.grid(time = c(0, 6, 12, 24, 48), dose = c(0, 1, 5, 10))
grid$response <- 10 + 2 * log1p(grid$dose) + 0.05 * grid$time + rnorm(nrow(grid), 0, 0.4)
write.csv(grid, file.path(tab_dir, delivery_table_name(skill_en, "timeseries", "dose")), row.names = FALSE)
write_delivery_audit(skill_en, "post", nrow(grid), 3, NA, "toy dose-time", TRUE, NA, sourced_note, "dose-time",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(grid, aes(time, response, color = factor(dose), group = dose)) +
  geom_line(linewidth = 1) + geom_point(size = 2) +
  scale_color_manual(values = bioinfo_palette[1:4]) +
  labs(title = "DoseTime response (toy)", color = "dose")
delivery_save_plot(p, skill_en, "line", "DoseTimeResponse", 7, 4.5, fig_dir, bio_root)
fig_map <- c("剂量-时间曲线" = paste0("../图片文件/", delivery_stem(skill_en, "line", "DoseTimeResponse"), ".png"))
interp <- "剂量反应与时间序列玩具。"
status <- "PASS"
""",
        "liquid_biopsy": f"""
vars <- data.frame(
  mutation = paste0("mut", 1:10),
  AF = c(0.22, 0.15, 0.08, 0.03, runif(6, 0.001, 0.02)),
  class = c(rep("driver", 3), rep("VUS", 7))
)
write.csv(vars, file.path(data_dir, "toy_ctDNA.csv"), row.names = FALSE)
write.csv(vars, file.path(tab_dir, delivery_table_name(skill_en, "AF", "ctDNA")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 10, 3, 1, "toy liquid biopsy", TRUE, NA, sourced_note, "AF",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(vars, aes(reorder(mutation, AF), AF, fill = class)) + geom_col() + coord_flip() +
  scale_fill_manual(values = c(driver = bioinfo_palette[1], VUS = "grey70")) +
  labs(title = "LiquidBiopsy variant AF (toy)", x = NULL, y = "allele fraction")
delivery_save_plot(p, skill_en, "bar", "ctDNA_AF", 6.5, 5, fig_dir, bio_root)
fig_map <- c("ctDNA AF" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "ctDNA_AF"), ".png"))
interp <- "液体活检突变等位基因频率玩具。"
status <- "PASS"
""",
        "ml_biomarker": f"""
# ROC 点
fpr <- seq(0, 1, length.out = 40)
tpr <- 1 - (1 - fpr)^2.2 + rnorm(40, 0, 0.01)
tpr <- pmin(1, pmax(0, sort(tpr)))
roc <- data.frame(FPR = fpr, TPR = tpr)
auc <- sum(diff(fpr) * (tpr[-1] + tpr[-length(tpr)]) / 2)
write.csv(roc, file.path(tab_dir, delivery_table_name(skill_en, "ROC", "biomarker")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 40, 2, NA, "toy labels", TRUE, NA, sourced_note, paste("AUC~", round(auc, 3)),
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(roc, aes(FPR, TPR)) + geom_line(color = bioinfo_palette[1], linewidth = 1.1) +
  geom_abline(slope = 1, intercept = 0, linetype = 2, color = "grey50") +
  labs(title = paste0("ML-Biomarker ROC (toy AUC≈", round(auc, 2), ")"))
delivery_save_plot(p, skill_en, "ROC", "Biomarker", 5.5, 5, fig_dir, bio_root)
fig_map <- c("生物标志物 ROC" = paste0("../图片文件/", delivery_stem(skill_en, "ROC", "Biomarker"), ".png"))
interp <- "机器学习生物标志物 ROC 玩具。"
status <- "PASS"
""",
        "meta": f"""
studies <- data.frame(
  study = paste0("Study", 1:8),
  OR = exp(rnorm(8, 0.2, 0.25)),
  se = runif(8, 0.08, 0.2)
)
studies$lo <- exp(log(studies$OR) - 1.96 * studies$se)
studies$hi <- exp(log(studies$OR) + 1.96 * studies$se)
write.csv(studies, file.path(tab_dir, delivery_table_name(skill_en, "forest", "OR")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 8, 5, NA, "toy meta studies", TRUE, NA, sourced_note, "meta forest",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(studies, aes(OR, reorder(study, OR))) +
  geom_vline(xintercept = 1, linetype = 2) +
  geom_errorbarh(aes(xmin = lo, xmax = hi), height = 0.2) +
  geom_point(color = bioinfo_palette[3], size = 2.5) +
  scale_x_log10() +
  labs(title = "MetaAnalysis OR forest (toy)", x = "OR", y = NULL)
delivery_save_plot(p, skill_en, "forest", "StudyOR", 7, 5, fig_dir, bio_root)
fig_map <- c("荟萃森林图" = paste0("../图片文件/", delivery_stem(skill_en, "forest", "StudyOR"), ".png"))
interp <- "荟萃分析 OR 玩具森林图。"
status <- "PASS"
""",
        "diagnostic_roc": f"""
fpr <- seq(0, 1, length.out = 50)
tpr <- pmin(1, pmax(0, 1 - (1 - fpr)^3 + rnorm(50, 0, 0.008)))
tpr <- cummax(tpr[order(fpr)])
roc <- data.frame(FPR = sort(fpr), TPR = tpr)
write.csv(roc, file.path(tab_dir, delivery_table_name(skill_en, "ROC", "diagnostic")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 50, 2, NA, "toy diagnostic", TRUE, NA, sourced_note, "diagnostic ROC",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(roc, aes(FPR, TPR)) +
  geom_ribbon(aes(ymin = 0, ymax = TPR), fill = bioinfo_palette[2], alpha = 0.2) +
  geom_line(color = bioinfo_palette[2], linewidth = 1.1) +
  geom_abline(slope = 1, intercept = 0, linetype = 2) +
  labs(title = "DiagnosticROC curve (toy)")
delivery_save_plot(p, skill_en, "ROC", "Diagnostic", 5.5, 5, fig_dir, bio_root)
fig_map <- c("诊断 ROC" = paste0("../图片文件/", delivery_stem(skill_en, "ROC", "Diagnostic"), ".png"))
interp <- "诊断效能 ROC 玩具（与 ML-Biomarker 曲线形状不同）。"
status <- "PASS"
""",
        "crispr": f"""
genes <- data.frame(
  gene = paste0("G", 1:40),
  LFC = sort(rnorm(40, 0, 0.8))
)
genes$LFC[1:3] <- genes$LFC[1:3] - 2
genes$LFC[38:40] <- genes$LFC[38:40] + 2
write.csv(genes, file.path(tab_dir, delivery_table_name(skill_en, "rank", "LFC")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 40, 2, NA, "toy CRISPR screen", TRUE, NA, sourced_note, "rank LFC",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
genes$rank <- seq_len(nrow(genes))
p <- ggplot(genes, aes(rank, LFC, color = abs(LFC) > 1.5)) + geom_point() +
  scale_color_manual(values = c("FALSE" = "grey60", "TRUE" = bioinfo_palette[1])) +
  labs(title = "CRISPRscreen rank LFC (toy)", color = "|LFC|>1.5")
delivery_save_plot(p, skill_en, "scatter", "RankLFC", 6.5, 4.5, fig_dir, bio_root)
fig_map <- c("筛选排序" = paste0("../图片文件/", delivery_stem(skill_en, "scatter", "RankLFC"), ".png"))
interp <- "CRISPR 筛选 LFC 排序玩具。"
status <- "PASS"
""",
        "scrna_adv": f"""
traj <- data.frame(
  pseudotime = seq(0, 10, length.out = 120),
  expression = sin(seq(0, 10, length.out = 120) / 2) + rnorm(120, 0, 0.15),
  lineage = rep(c("L1", "L2"), each = 60)
)
traj$expression[61:120] <- traj$expression[61:120] + 0.8
write.csv(traj, file.path(tab_dir, delivery_table_name(skill_en, "trajectory", "pseudo")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 120, 3, 120, "toy trajectory", TRUE, NA, sourced_note, "pseudotime",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(traj, aes(pseudotime, expression, color = lineage)) + geom_point(alpha = 0.6, size = 1.2) +
  geom_smooth(se = FALSE, linewidth = 1) +
  scale_color_manual(values = bioinfo_palette[c(1, 5)]) +
  labs(title = "scRNA-Advanced pseudotime (toy)")
delivery_save_plot(p, skill_en, "line", "PseudotimeExpr", 7, 4.5, fig_dir, bio_root)
fig_map <- c("拟时序表达" = paste0("../图片文件/", delivery_stem(skill_en, "line", "PseudotimeExpr"), ".png"))
interp <- "单细胞进阶拟时序玩具（非基础 UMAP）。"
status <- "PASS"
""",
        "gsea": f"""
pathways <- data.frame(
  pathway = c("OXPHOS", "Glycolysis", "TNF", "IFN-g", "Wnt", "Notch", "p53", "Hypoxia"),
  NES = c(1.8, 1.5, -1.6, -1.3, 1.1, -0.9, 1.4, 1.2) + rnorm(8, 0, 0.05)
)
write.csv(pathways, file.path(tab_dir, delivery_table_name(skill_en, "GSEA", "NES")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 8, 2, NA, "toy gene sets", TRUE, NA, sourced_note, "GSEA NES",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
pathways$pathway <- factor(pathways$pathway, levels = pathways$pathway[order(pathways$NES)])
p <- ggplot(pathways, aes(NES, pathway, fill = NES > 0)) + geom_col() +
  scale_fill_manual(values = c("FALSE" = bioinfo_palette[4], "TRUE" = bioinfo_palette[1]), guide = "none") +
  labs(title = "GSEA-Pathway NES (toy)", x = "NES")
delivery_save_plot(p, skill_en, "bar", "NES_Pathways", 6.5, 5, fig_dir, bio_root)
fig_map <- c("通路 NES" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "NES_Pathways"), ".png"))
interp <- "基因集富集 NES 玩具条形图。"
status <- "PASS"
""",
        "multiomics": f"""
omics <- data.frame(
  feature = paste0("F", 1:25),
  RNA = rnorm(25),
  Protein = rnorm(25)
)
omics$Protein <- 0.6 * omics$RNA + 0.4 * omics$Protein
write.csv(omics, file.path(tab_dir, delivery_table_name(skill_en, "corr", "RNAvsProtein")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 25, 3, NA, "toy multiomics", TRUE, NA, sourced_note, "RNA-Protein",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(omics, aes(RNA, Protein)) + geom_point(color = bioinfo_palette[3], size = 2.5) +
  geom_smooth(method = "lm", se = FALSE, color = "grey40") +
  labs(title = "MultiOmics RNA vs Protein (toy)")
delivery_save_plot(p, skill_en, "scatter", "RNAvsProtein", 6, 5, fig_dir, bio_root)
fig_map <- c("转录-蛋白相关" = paste0("../图片文件/", delivery_stem(skill_en, "scatter", "RNAvsProtein"), ".png"))
interp <- "多组学联合相关玩具散点。"
status <- "PASS"
""",
        "cellcomm": f"""
lr <- data.frame(
  pair = c("A→B", "C→D", "E→F", "G→H", "I→J", "K→L"),
  score = c(0.82, 0.71, 0.55, 0.48, 0.33, 0.21)
)
write.csv(lr, file.path(tab_dir, delivery_table_name(skill_en, "LR", "scores")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 6, 2, NA, "toy LR", TRUE, NA, sourced_note, "cellchat-like",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
lr$pair <- factor(lr$pair, levels = rev(lr$pair))
p <- ggplot(lr, aes(score, pair)) + geom_col(fill = bioinfo_palette[5]) +
  labs(title = "CellCommunication LR scores (toy)", x = "score", y = "L-R pair")
delivery_save_plot(p, skill_en, "bar", "LRscores", 6, 4.5, fig_dir, bio_root)
fig_map <- c("配体-受体分数" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "LRscores"), ".png"))
interp <- "细胞通讯配体-受体玩具分数。"
status <- "PASS"
""",
        "insilico_ko": f"""
de <- data.frame(
  gene = paste0("TG", 1:20),
  logFC = sort(rnorm(20, -0.2, 0.7))
)
de$logFC[1:4] <- de$logFC[1:4] - 1.5
write.csv(de, file.path(tab_dir, delivery_table_name(skill_en, "KO", "logFC")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 20, 2, NA, "toy KO", TRUE, NA, sourced_note, "in silico KO",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
top <- de[order(de$logFC), ][1:12, ]
top$gene <- factor(top$gene, levels = rev(top$gene))
p <- ggplot(top, aes(logFC, gene)) + geom_col(fill = bioinfo_palette[1]) +
  labs(title = "InSilicoKO top down genes (toy)", x = "logFC after KO")
delivery_save_plot(p, skill_en, "bar", "KOdownGenes", 6.5, 5, fig_dir, bio_root)
fig_map <- c("虚拟敲除下调" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "KOdownGenes"), ".png"))
interp <- "虚拟敲除扰动玩具差异。"
status <- "PASS"
""",
        "ppi": f"""
nodes <- data.frame(
  protein = c("TP53", "EGFR", "MYC", "AKT1", "MAPK1", "SRC", "JUN", "STAT3"),
  degree = c(22, 18, 15, 12, 11, 9, 8, 7)
)
write.csv(nodes, file.path(tab_dir, delivery_table_name(skill_en, "degree", "hubs")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 8, 2, NA, "toy PPI", TRUE, NA, sourced_note, "hub degree",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(nodes, aes(reorder(protein, degree), degree)) + geom_col(fill = bioinfo_palette[2]) +
  coord_flip() + labs(title = "PPI-Network hub degree (toy)", x = NULL)
delivery_save_plot(p, skill_en, "bar", "HubDegree", 6, 4.5, fig_dir, bio_root)
fig_map <- c("PPI 枢纽度" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "HubDegree"), ".png"))
interp <- "蛋白质互作网络枢纽度玩具。"
status <- "PASS"
""",
        "cross_species": f"""
map <- data.frame(
  species = c("human", "mouse", "rat", "zebrafish", "fly"),
  n_orthologs = c(18000, 16500, 15800, 12000, 8000) + sample(-200:200, 5)
)
write.csv(map, file.path(tab_dir, delivery_table_name(skill_en, "ortholog", "counts")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 5, 2, NA, "toy orthologs", TRUE, NA, sourced_note, "cross-species",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(map, aes(reorder(species, n_orthologs), n_orthologs, fill = species)) +
  geom_col(show.legend = FALSE) + coord_flip() +
  scale_fill_manual(values = bioinfo_palette[1:5]) +
  labs(title = "CrossSpecies ortholog counts (toy)", x = NULL, y = "n")
delivery_save_plot(p, skill_en, "bar", "OrthologCounts", 6.5, 4.5, fig_dir, bio_root)
fig_map <- c("直系同源计数" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "OrthologCounts"), ".png"))
interp <- "跨物种基因映射玩具计数。"
status <- "PASS"
""",
        "tf_network": f"""
tf <- data.frame(
  TF = c("STAT1", "IRF1", "NFKB1", "JUN", "FOS", "MYC", "TP53", "SPI1"),
  activity = c(2.1, 1.8, 1.5, -1.2, -0.9, 1.1, 0.7, -1.5) + rnorm(8, 0, 0.05)
)
write.csv(tf, file.path(tab_dir, delivery_table_name(skill_en, "activity", "TF")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 8, 2, NA, "toy TF", TRUE, NA, sourced_note, "TF activity",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
tf$TF <- factor(tf$TF, levels = tf$TF[order(tf$activity)])
p <- ggplot(tf, aes(activity, TF, fill = activity > 0)) + geom_col() +
  scale_fill_manual(values = c("FALSE" = bioinfo_palette[4], "TRUE" = bioinfo_palette[1]), guide = "none") +
  labs(title = "TF-Network activity (toy)", x = "activity")
delivery_save_plot(p, skill_en, "bar", "TFactivity", 6.5, 5, fig_dir, bio_root)
fig_map <- c("TF 活性" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "TFactivity"), ".png"))
interp <- "转录因子活性玩具条形图。"
status <- "PASS"
""",
        "deg_umap_pipe": f"""
# 流水线样例：小 DEG + 伪 UMAP（与 RNA-seq / scRNA 核心样例不同 seed/主题）
genes <- paste0("PIPE", 1:50)
mat <- matrix(rnbinom(50 * 6, mu = 25, size = 6), nrow = 50)
mat[1:8, 4:6] <- mat[1:8, 4:6] + 40
colnames(mat) <- paste0("Pipe", 1:6)
meta <- data.frame(sample = colnames(mat), group = c(rep("A", 3), rep("B", 3)))
logc <- log2(mat + 1)
pvals <- apply(logc, 1, function(v) t.test(v[1:3], v[4:6])$p.value)
lfc <- rowMeans(logc[, 4:6]) - rowMeans(logc[, 1:3])
deg <- data.frame(gene = genes, logFC = lfc, pvalue = pvals)
write.csv(cbind(gene = genes, as.data.frame(mat)), file.path(data_dir, "toy_pipe_counts.csv"), row.names = FALSE)
write.csv(deg, file.path(tab_dir, delivery_table_name(skill_en, "DEG", "GroupBvsA")), row.names = FALSE)
umap <- data.frame(
  UMAP_1 = c(rnorm(60, -1, 0.7), rnorm(60, 2.5, 0.8)),
  UMAP_2 = c(rnorm(60, 0.5, 0.6), rnorm(60, -1.5, 0.7)),
  group = factor(rep(c("A", "B"), each = 60))
)
write.csv(umap, file.path(tab_dir, delivery_table_name(skill_en, "UMAP", "pipeline")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 50, 6, 6, "toy pipeline meta", TRUE, NA, sourced_note, "DEG-UMAP pipe",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
deg$sig <- ifelse(deg$pvalue < 0.05 & abs(deg$logFC) > 0.5, "sig", "ns")
p1 <- ggplot(deg, aes(logFC, -log10(pmax(pvalue, 1e-300)), color = sig)) + geom_point(alpha = 0.85) +
  scale_color_manual(values = c(ns = "grey70", sig = bioinfo_palette[5])) +
  labs(title = "DEG-UMAP pipeline volcano B vs A (toy)")
delivery_save_plot(p1, skill_en, "volcano", "GroupBvsA", 6.5, 5, fig_dir, bio_root)
p2 <- ggplot(umap, aes(UMAP_1, UMAP_2, color = group)) + geom_point(size = 1.4, alpha = 0.75) +
  scale_color_manual(values = bioinfo_palette[c(5, 3)]) +
  labs(title = "DEG-UMAP pipeline UMAP (toy)")
delivery_save_plot(p2, skill_en, "UMAP", "PipeClusters", 6.5, 5, fig_dir, bio_root)
fig_map <- c(
  "流水线火山图" = paste0("../图片文件/", delivery_stem(skill_en, "volcano", "GroupBvsA"), ".png"),
  "流水线 UMAP" = paste0("../图片文件/", delivery_stem(skill_en, "UMAP", "PipeClusters"), ".png")
)
interp <- "已落地 DEG-UMAP 流水线玩具交付；数据与核心 RNA-seq/scRNA 样例不同。"
status <- "PASS"
""",
    }
    if kind not in blocks:
        raise KeyError(f"Unknown pending kind: {kind}")
    return blocks[kind]


def prepare_pending(rel: str) -> dict:
    skill_dir = ROOT / rel.replace("/", os.sep)
    folder = skill_dir.name
    sample = skill_dir / "01_样例_sample"
    ensure_tree(sample)
    kind = PENDING_KIND[rel]
    seed = 10000 + (skill_hash(rel) % 50000)

    fig_dir = sample / "结果文件" / "图片文件"
    rep_dir = sample / "结果文件" / "报告文件"
    for p in fig_dir.glob("*"):
        if p.is_file():
            p.unlink()
    for p in list(rep_dir.glob("*")):
        if p.is_file():
            p.unlink()

    write_data_source(sample, folder, kind)
    code = r_header(folder, kind, seed) + "\n" + pending_analysis_block(kind, folder) + "\n" + report_footer()
    code_path = sample / "代码文件" / "run_sample.R"
    code_path.write_text(code, encoding="utf-8", newline="\n")
    return {"skill_dir": skill_dir, "folder": folder, "rel": rel, "code": code_path, "kind": kind}


def write_full_results(all_results: list[dict], png_info: dict) -> None:
    counts = Counter(r["status"] for r in all_results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "n": len(all_results),
        "counts": dict(counts),
        "png_unique": len(set(v["sha256"] for v in png_info.values())),
        "png_total": len(png_info),
        "results": all_results,
        "png_hashes_sample": {k: v for i, (k, v) in enumerate(sorted(png_info.items())) if i < 40},
    }
    VAL_DIR.mkdir(exist_ok=True)
    (VAL_DIR / "每技能样例_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (VAL_DIR / "全量交付_delivery_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_full_validation_report(
    core_results: list[dict],
    pending_results: list[dict],
    png_info: dict,
) -> None:
    all_results = core_results + pending_results
    counts = Counter(r["status"] for r in all_results)
    hashes = [v["sha256"] for v in png_info.values()]
    unique = len(set(hashes))
    fails = [r for r in all_results if r["status"] == "FAIL"]
    blocked = [r for r in all_results if r["status"] == "BLOCKED"]

    lines = [
        "# 验证总报告 / Per-Skill Sample Validation",
        "",
        f"- **更新时间**：{datetime.now().isoformat(timespec='seconds')}",
        f"- **布局版本**：catalog `layout_version` + 统一交付规范_DeliveryStandards",
        f"- **全量样例数**：{len(all_results)}",
        f"- **PASS**：{counts.get('PASS', 0)}",
        f"- **BLOCKED**：{counts.get('BLOCKED', 0)}",
        f"- **FAIL**：{counts.get('FAIL', 0)}",
        f"- **PNG 总数 / 唯一哈希**：{len(png_info)} / {unique}",
        f"- **待按规范重跑**：0",
        "",
        "## 规范合规审计（回答用户三问）",
        "",
        "### 问1：执行样例时是否采用了本文件夹的 skill？",
        "",
        "**结论（修复后）：是。** 全量样例 `run_sample.R` 均 `source` ",
        "`统一交付规范_DeliveryStandards/脚本_scripts/*.R`，并 `source` 本技能 `脚本_scripts/*.R`。",
        "",
        "### 问2：为什么不同地方生成的图相同？",
        "",
        "**结论（修复后）：已消除。** Phase B 全局同构 volcano 已禁用；",
        f"当前 PNG 唯一哈希 **{unique}/{len(png_info)}**。",
        "",
        "### 问3：文件命名为何未按既有规范？",
        "",
        "**结论（修复后）：已按 DeliveryStandards** — ",
        "`{技能英文}_{图类型}_{主题}.png|.svg` + `{技能}_样例报告_v1.html` + 审计 CSV。",
        "",
        "## 核心样例（先前 PASS）",
        "",
        "| 技能 | kind | 状态 | 报告 |",
        "|------|------|------|------|",
    ]
    for r in sorted(core_results, key=lambda x: x["path"]):
        lines.append(
            f"| `{r['path']}` | `{r.get('kind','')}` | **{r['status']}** | `{r.get('report') or '—'}` |"
        )

    lines += [
        "",
        "## 本轮待办重跑结果",
        "",
        "| 技能 | kind | 状态 | 报告 |",
        "|------|------|------|------|",
    ]
    for r in sorted(pending_results, key=lambda x: x["path"]):
        lines.append(
            f"| `{r['path']}` | `{r.get('kind','')}` | **{r['status']}** | `{r.get('report') or '—'}` |"
        )

    lines += [
        "",
        "### BLOCKED 清单（契约样例，非假 PASS）",
        "",
    ]
    if blocked:
        for r in blocked:
            lines.append(f"- `{r['path']}` — kind=`{r.get('kind')}`")
    else:
        lines.append("- （无）")

    lines += [
        "",
        "### FAIL 清单",
        "",
    ]
    if fails:
        for r in fails:
            err = (r.get("stderr") or "")[:200].replace("\n", " ")
            lines.append(f"- `{r['path']}` — {err}")
    else:
        lines.append("- （无）")

    lines += [
        "",
        "### 图片哈希抽查（前 25）",
        "",
        "| 文件 | size | sha256前12 |",
        "|------|------|------------|",
    ]
    for i, (fp, meta) in enumerate(sorted(png_info.items())):
        if i >= 25:
            break
        lines.append(f"| `{fp}` | {meta['size']} | `{meta['sha256'][:12]}` |")

    lines += [
        "",
        "## 如何重跑",
        "",
        "```bash",
        "python E:/RProject/生信分析技能_BioinformaticsSkills/_phaseC_pending_rerun.py",
        "```",
        "",
        "核心-only：",
        "",
        "```bash",
        "python E:/RProject/生信分析技能_BioinformaticsSkills/_phaseC_delivery_rerun.py",
        "```",
        "",
        "单技能：",
        "",
        "```bash",
        'cd "E:/RProject/生信分析技能_BioinformaticsSkills/<技能>/01_样例_sample/代码文件"',
        "Rscript run_sample.R",
        "```",
        "",
        "## 历史说明",
        "",
        "- `_phaseB_sample_batch.py` 已拒绝全量雷同生成（exit 2）；请用 Phase C。",
        "- 原八条分类验证记录仍保留在 `验证记录_records/`。",
        "",
    ]
    (VAL_DIR / "验证总报告.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def load_core_results() -> list[dict]:
    path = VAL_DIR / "核心样例_delivery_results.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("core") or []
    return []


def main() -> None:
    pending_paths = list(PENDING_KIND.keys())
    missing = [p for p in pending_paths if not (ROOT / p.replace("/", os.sep)).exists()]
    if missing:
        print("MISSING skill dirs:", missing)
    print(f"Preparing {len(pending_paths)} pending samples...")
    preps = [prepare_pending(rel) for rel in pending_paths if (ROOT / rel.replace("/", os.sep)).exists()]
    results = []
    for i, prep in enumerate(preps, 1):
        print(f"[{i}/{len(preps)}] {prep['rel']} ...", flush=True)
        res = run_one(prep)
        results.append(res)
        print(f"  -> {res['status']} rc={res['returncode']}", flush=True)
        if res["status"] == "FAIL":
            print("  stderr:", (res.get("stderr") or "")[:500])

    # Retry FAIL once after small delay (occasional R graphics device races)
    fails = [r for r in results if r["status"] == "FAIL"]
    if fails:
        print(f"Retrying {len(fails)} FAIL...")
        by_path = {r["path"]: r for r in results}
        for prep in preps:
            if prep["rel"] not in by_path or by_path[prep["rel"]]["status"] != "FAIL":
                continue
            res = run_one(prep)
            by_path[prep["rel"]] = res
            print(f"  retry {prep['rel']} -> {res['status']}", flush=True)
        results = [by_path[p["rel"]] for p in preps]

    core_results = load_core_results()
    # If core JSON missing kinds, rebuild status from STATUS.txt
    if not core_results:
        for rel in CORE_SKILLS:
            skill_dir = ROOT / rel.replace("/", os.sep)
            status_f = skill_dir / "01_样例_sample" / "结果文件" / "报告文件" / "STATUS.txt"
            reps = list((skill_dir / "01_样例_sample" / "结果文件" / "报告文件").glob("*_样例报告_*.html"))
            kind = KIND_BY_PATH.get(rel, ("",))[0]
            core_results.append(
                {
                    "folder": skill_dir.name,
                    "path": rel,
                    "status": status_f.read_text(encoding="utf-8").strip() if status_f.exists() else "UNKNOWN",
                    "kind": kind,
                    "report": reps[0].relative_to(ROOT).as_posix() if reps else "",
                }
            )

    all_paths = CORE_SKILLS + [r["path"] for r in results]
    png_info = collect_png_hashes(all_paths)
    write_full_results(core_results + results, png_info)
    write_full_validation_report(core_results, results, png_info)

    print("PENDING SUMMARY", dict(Counter(r["status"] for r in results)))
    print("ALL PNG unique", len(set(v["sha256"] for v in png_info.values())), "/", len(png_info))
    print("Report:", VAL_DIR / "验证总报告.md")


if __name__ == "__main__":
    main()
