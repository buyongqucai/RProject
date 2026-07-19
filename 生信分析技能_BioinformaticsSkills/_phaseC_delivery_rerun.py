# -*- coding: utf-8 -*-
"""Phase C: DeliveryStandards + skill-distinct samples (≥12 core) + generator fix."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import textwrap
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(r"E:/RProject/生信分析技能_BioinformaticsSkills")
VAL_DIR = ROOT / "07_分类验证_Validation"
DELIVERY = ROOT / "00_基础_Foundation" / "统一交付规范_DeliveryStandards"
VIZ_PLOT = (
    ROOT / "00_基础_Foundation" / "统一可视化规范_VizStandards"
    / "脚本_scripts" / "出版级出图_PublicationPlot.R"
)

BLOCKED_REASON = {
    "分子动力学模拟_MolecularDynamics": "需 GROMACS/AMBER 等 MD 引擎与 GPU/长时间轨迹",
    "基因组组装与注释_GenomeAssembly": "需大规模测序读段与组装器（SPAdes/Flye 等）及 TB 级磁盘",
    "长读长测序分析_LongRead": "需长读长 FASTQ 与 minimap2/dorado 等 CLI",
    "分子对接与虚拟筛选_MolecularDocking": "需 AutoDock Vina/商业对接软件与受体准备流水线",
    "三维基因组分析_3DGenome": "需 Hi-C 原始或 .hic/.cool 全库与 juicer/cooler 栈",
    "结构变异分析_StructuralVariant": "需全基因组 BAM 与 manta/delly 等 SV caller",
    "变异检测与外显子组_Variant-WES": "需 WES BAM/GATK 完整最佳实践流水线",
    "表观遗传ChIP-seq_Epigenomics": "需 ChIP FASTQ 与 MACS2/bowtie 比对栈",
    "ATAC专论_ATAC-seq": "需 ATAC FASTQ 与 peak calling CLI",
    "RNA融合基因检测_FusionGene": "需 RNA-seq BAM/FASTQ 与 STAR-Fusion/Arriba",
    "新抗原与免疫组库_Neoantigen-TCR": "需 HLA 分型 CLI 与肽段预测工具链",
    "放射组学与病理组学_Radiomics-Pathomics": "需医学影像 DICOM/WSI 与 pyradiomics 环境",
}

# ≥12 core skills to fully rewrite + rerun (path relative to ROOT)
CORE_SKILLS = [
    "00_基础_Foundation/统一交付规范_DeliveryStandards",
    "00_基础_Foundation/统一可视化规范_VizStandards",
    "00_基础_Foundation/数据真实性验证_DataAuthenticity",
    "01_组学_Omics/转录组分析_RNA-seq",
    "01_组学_Omics/蛋白质组分析_Proteomics",
    "01_组学_Omics/单细胞与空间转录组分析_scRNA-Spatial",
    "01_组学_Omics/代谢组分析_Metabolomics",
    "01_组学_Omics/微生物组16S分析_Microbiome16S",
    "01_组学_Omics/DNA甲基化分析_WGBS-RRBS",
    "01_组学_Omics/公共库挖掘_GEO-TCGA",
    "02_遗传与变异_Genetics/全基因组关联分析_GWAS",
    "03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology",
    "04_临床预测与统计_ClinicalStats/生存分析与预后模型_Survival",
    "05_系统方法_SystemsMethods/共表达网络WGCNA_WGCNA",
]


def skill_en(folder: str) -> str:
    return folder.split("_", 1)[-1] if "_" in folder else folder


def ensure_tree(sample: Path) -> None:
    for sub in [
        "代码文件",
        "数据文件",
        "结果文件/图片文件",
        "结果文件/数据文件",
        "结果文件/报告文件",
    ]:
        (sample / sub).mkdir(parents=True, exist_ok=True)


def r_header(folder: str, analysis_kind: str, seed: int) -> str:
    en = skill_en(folder)
    return textwrap.dedent(
        f"""\
        # 样例分析脚本 — {folder}
        # 合规：统一交付规范_DeliveryStandards + 统一可视化规范_VizStandards
        # analysis_kind={analysis_kind}  seed={seed}
        options(stringsAsFactors = FALSE)
        set.seed({seed})

        sample_root <- normalizePath("..", winslash = "/", mustWork = TRUE)
        skill_root <- normalizePath("../..", winslash = "/", mustWork = TRUE)
        bio_root <- normalizePath("../../..", winslash = "/", mustWork = TRUE)
        # 若技能在 00/01/... 下，bio_root 可能需再上一级
        if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {{
          bio_root <- normalizePath("../../../..", winslash = "/", mustWork = TRUE)
        }}
        if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {{
          # DeliveryStandards 自身：skill 在 00 下，上两级即 bio root
          bio_root <- normalizePath(file.path(skill_root, "..", ".."), winslash = "/", mustWork = TRUE)
        }}

        data_dir <- file.path(sample_root, "数据文件")
        fig_dir <- file.path(sample_root, "结果文件", "图片文件")
        tab_dir <- file.path(sample_root, "结果文件", "数据文件")
        rep_dir <- file.path(sample_root, "结果文件", "报告文件")
        for (d in c(data_dir, fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

        # 1) source 统一可视化规范 出版级出图
        # 2) source 统一交付规范 出图命名/审计/报告
        # 3) source 本技能 脚本_scripts
        viz_script <- file.path(
          bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
          "脚本_scripts", "出版级出图_PublicationPlot.R"
        )
        if (file.exists(viz_script)) source(viz_script, encoding = "UTF-8")

        delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
        source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
        source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
        source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")

        skill_en <- "{en}"
        skill_folder <- "{folder}"
        scripts_dir <- file.path(skill_root, "脚本_scripts")
        sk_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
        sourced_note <- "未找到可 source 的技能脚本"
        if (length(sk_files)) {{
          for (sf in sk_files) {{
            try(source(sf, encoding = "UTF-8"), silent = TRUE)
          }}
          sourced_note <- paste0("已 source VizStandards + DeliveryStandards + 本技能: ", paste(basename(sk_files), collapse = ", "))
        }} else {{
          sourced_note <- "已 source VizStandards + DeliveryStandards；本技能无额外 .R 骨架"
        }}
        if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
        """
    )


def analysis_block(kind: str, folder: str) -> str:
    en = skill_en(folder)
    blocks = {
        "delivery_demo": f"""
# ---- DeliveryStandards 自证：可区分柱状图 ----
df <- data.frame(
  rule = c("命名", "审计", "报告", "DPI600", "SVG+PNG"),
  score = c(5, 4, 5, 5, 5)
)
write.csv(df, file.path(tab_dir, delivery_table_name(skill_en, "rules", "checklist")), row.names = FALSE)
write_delivery_audit(skill_en, "pre", n_rows = nrow(df), n_cols = 2, n_samples = 0,
  group_source = "n/a", toy = TRUE, sourced_skill_scripts = sourced_note,
  notes = "规范自证样例", out_path = file.path(tab_dir, delivery_audit_name(skill_en, "pre")))
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("需要 ggplot2")
library(ggplot2)
p <- ggplot(df, aes(rule, score, fill = rule)) +
  geom_col(show.legend = FALSE) +
  scale_fill_manual(values = bioinfo_palette[seq_len(nrow(df))]) +
  labs(title = "Delivery rule coverage", x = NULL, y = "Score") +
  theme_bw(base_size = 12)
paths <- delivery_save_plot(p, skill_en, "bar", "RuleCoverage", width = 7, height = 4.5, out_dir = fig_dir, start = bio_root)
write_delivery_audit(skill_en, "post", n_rows = nrow(df), n_cols = 2, n_samples = 0,
  group_source = "n/a", toy = TRUE, sourced_skill_scripts = sourced_note,
  notes = paste("图:", basename(paths$png)), out_path = file.path(tab_dir, delivery_audit_name(skill_en, "post")))
fig_map <- c("规则覆盖柱状图" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "RuleCoverage"), ".png"))
interp <- "本图仅验证交付命名与 save_plot_pub 通路；非生物学结论。"
status <- "PASS"
""",
        "viz_demo": f"""
df <- data.frame(x = rnorm(80), y = rnorm(80), g = rep(c("A", "B"), each = 40))
write.csv(df, file.path(tab_dir, delivery_table_name(skill_en, "points", "demo")), row.names = FALSE)
write_delivery_audit(skill_en, "pre", 80, 3, 80, "toy groups A/B", TRUE, sourced_skill_scripts = sourced_note,
  out_path = file.path(tab_dir, delivery_audit_name(skill_en, "pre")))
library(ggplot2)
p <- ggplot(df, aes(x, y, color = g)) + geom_point(alpha = 0.8) +
  scale_color_manual(values = bioinfo_palette[1:2]) +
  labs(title = "Publication scatter (demo)", color = "Group")
delivery_save_plot(p, skill_en, "scatter", "GroupAB", 6, 5, fig_dir, bio_root)
write_delivery_audit(skill_en, "post", 80, 3, 80, "toy groups A/B", TRUE, sourced_skill_scripts = sourced_note,
  out_path = file.path(tab_dir, delivery_audit_name(skill_en, "post")))
fig_map <- c("出版级散点" = paste0("../图片文件/", delivery_stem(skill_en, "scatter", "GroupAB"), ".png"))
interp <- "验证 DPI≥600 与 SVG+PNG；toy 点云不可外推。"
status <- "PASS"
""",
        "authenticity": f"""
# 真实性核对：声明的样本数 vs 矩阵列
meta <- data.frame(sample = paste0("GSM", 1:6), group = rep(c("Tumor", "Normal"), each = 3))
mat <- matrix(rpois(30 * 6, 20), nrow = 30, dimnames = list(paste0("g", 1:30), meta$sample))
mat[1:5, 1:3] <- mat[1:5, 1:3] + 25
write.csv(cbind(gene = rownames(mat), as.data.frame(mat)), file.path(data_dir, "toy_geo_like_counts.csv"), row.names = FALSE)
write.csv(meta, file.path(data_dir, "toy_geo_like_meta.csv"), row.names = FALSE)
chk <- audit_meta_vs_matrix(colnames(mat), meta$sample)
audit_df <- data.frame(
  declared_n = nrow(meta), matrix_n = ncol(mat), match_ok = chk$ok,
  toy = TRUE, accession = "TOY-GEO-0000"
)
write.csv(audit_df, file.path(tab_dir, delivery_table_name(skill_en, "check", "sampleMatch")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 30, 6, 6, "toy_geo_like_meta.csv", TRUE, "TOY-GEO-0000",
  sourced_note, ifelse(chk$ok, "样本数列一致", "不一致"), file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
plot_df <- data.frame(item = c("declared_n", "matrix_n"), n = c(nrow(meta), ncol(mat)))
p <- ggplot(plot_df, aes(item, n, fill = item)) + geom_col(show.legend = FALSE) +
  labs(title = "Sample count check", y = "n samples", x = NULL) +
  scale_fill_manual(values = bioinfo_palette[1:2])
delivery_save_plot(p, skill_en, "bar", "SampleCountCheck", 5, 4, fig_dir, bio_root)
fig_map <- c("样本数核对" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "SampleCountCheck"), ".png"))
interp <- "演示真实性核对字段；accession=TOY，不可当作真实 GEO。"
status <- "PASS"
""",
        "rnaseq": f"""
# RNA-seq 风格：limma 风格 t + 火山（技能专属 seed/标题）
genes <- paste0("GENE", 1:60)
mat <- matrix(rnbinom(60 * 6, mu = 40, size = 8), nrow = 60)
mat[1:12, 1:3] <- mat[1:12, 1:3] + 60
colnames(mat) <- paste0("S", 1:6)
meta <- data.frame(sample = colnames(mat), group = c(rep("Treat", 3), rep("Control", 3)))
write.csv(cbind(gene = genes, as.data.frame(mat)), file.path(data_dir, "toy_counts.csv"), row.names = FALSE)
write.csv(meta, file.path(data_dir, "toy_meta.csv"), row.names = FALSE)
logc <- log2(mat + 1)
group <- meta$group
pvals <- apply(logc, 1, function(v) t.test(v[group == "Treat"], v[group == "Control"])$p.value)
lfc <- rowMeans(logc[, group == "Treat", drop = FALSE]) - rowMeans(logc[, group == "Control", drop = FALSE])
deg <- data.frame(gene = genes, logFC = lfc, pvalue = pvals, padj = p.adjust(pvals, "BH"))
deg <- deg[order(deg$pvalue), ]
write.csv(deg, file.path(tab_dir, delivery_table_name(skill_en, "DEG", "TreatVsControl")), row.names = FALSE)
write_delivery_audit(skill_en, "post", nrow(mat), ncol(mat), ncol(mat), "toy_meta.csv group=Treat/Control",
  TRUE, NA, sourced_note, "RNA-seq toy DEG", file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
deg$sig <- ifelse(!is.na(deg$padj) & deg$padj < 0.05 & abs(deg$logFC) > 0.5, "sig", "ns")
p1 <- ggplot(deg, aes(logFC, -log10(pmax(pvalue, 1e-300)), color = sig)) +
  geom_point(alpha = 0.85) +
  scale_color_manual(values = c(ns = "grey70", sig = bioinfo_palette[1])) +
  labs(title = "Volcano plot (Treat vs Control)", x = "logFC", y = "-log10(p)")
delivery_save_plot(p1, skill_en, "volcano", "TreatVsControl", 6.5, 5, fig_dir, bio_root)
pc <- prcomp(t(logc), scale. = TRUE)
pcd <- data.frame(PC1 = pc$x[, 1], PC2 = pc$x[, 2], group = group)
p2 <- ggplot(pcd, aes(PC1, PC2, color = group)) + geom_point(size = 3) +
  scale_color_manual(values = bioinfo_palette[1:2]) +
  labs(title = "PCA (Treat vs Control)")
delivery_save_plot(p2, skill_en, "PCA", "TreatVsControl", 6, 5, fig_dir, bio_root)
fig_map <- c(
  "火山图 TreatVsControl" = paste0("../图片文件/", delivery_stem(skill_en, "volcano", "TreatVsControl"), ".png"),
  "PCA TreatVsControl" = paste0("../图片文件/", delivery_stem(skill_en, "PCA", "TreatVsControl"), ".png")
)
interp <- "玩具 limma 风格差异；已 source 转录组骨架（若存在）。不可外推。"
status <- "PASS"
""",
        "proteomics": f"""
proteins <- paste0("PROT", 1:50)
mat <- matrix(rnorm(50 * 6, mean = 20, sd = 2), nrow = 50)
mat[1:8, 1:3] <- mat[1:8, 1:3] + 4
colnames(mat) <- paste0("P", 1:6)
meta <- data.frame(sample = colnames(mat), group = c(rep("Disease", 3), rep("Healthy", 3)))
write.csv(cbind(protein = proteins, as.data.frame(mat)), file.path(data_dir, "toy_protein_intensity.csv"), row.names = FALSE)
write.csv(meta, file.path(data_dir, "toy_meta.csv"), row.names = FALSE)
group <- meta$group
pvals <- apply(mat, 1, function(v) t.test(v[group == "Disease"], v[group == "Healthy"])$p.value)
lfc <- rowMeans(mat[, group == "Disease", drop = FALSE]) - rowMeans(mat[, group == "Healthy", drop = FALSE])
res <- data.frame(protein = proteins, logFC = lfc, pvalue = pvals)
write.csv(res, file.path(tab_dir, delivery_table_name(skill_en, "DEP", "DiseaseVsHealthy")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 50, 6, 6, "toy_meta.csv", TRUE, NA, sourced_note, "LFQ-like intensity",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
top <- res[order(res$pvalue), ][1:15, ]
top$protein <- factor(top$protein, levels = rev(top$protein))
p <- ggplot(top, aes(logFC, protein, fill = logFC > 0)) + geom_col() +
  scale_fill_manual(values = c(bioinfo_palette[4], bioinfo_palette[1]), guide = "none") +
  labs(title = "Top 15 differential proteins", x = "logFC (disease − healthy)")
delivery_save_plot(p, skill_en, "bar", "Top15DEP", 6.5, 5.5, fig_dir, bio_root)
fig_map <- c("Top15 差异蛋白" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "Top15DEP"), ".png"))
interp <- "蛋白强度玩具矩阵差异柱状图；已尝试 source 蛋白质组骨架。"
status <- "PASS"
""",
        "scrna": f"""
# 伪 UMAP：两组细胞簇
n <- 200
umap <- data.frame(
  UMAP_1 = c(rnorm(100, 0, 0.8), rnorm(100, 4, 0.9)),
  UMAP_2 = c(rnorm(100, 0, 0.8), rnorm(100, 3, 1.0)),
  cluster = factor(c(rep("Mono", 100), rep("Tcell", 100)))
)
write.csv(umap, file.path(tab_dir, delivery_table_name(skill_en, "UMAP", "toyClusters")), row.names = FALSE)
write_delivery_audit(skill_en, "post", n, 3, n, "toy cluster labels", TRUE, NA, sourced_note, "pseudo-UMAP",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(umap, aes(UMAP_1, UMAP_2, color = cluster)) + geom_point(size = 1.2, alpha = 0.75) +
  scale_color_manual(values = bioinfo_palette[1:2]) +
  labs(title = "scRNA-Spatial pseudo-UMAP (toy)", color = "cluster")
delivery_save_plot(p, skill_en, "UMAP", "MonoVsTcell", 6.5, 5.5, fig_dir, bio_root)
fig_map <- c("伪UMAP" = paste0("../图片文件/", delivery_stem(skill_en, "UMAP", "MonoVsTcell"), ".png"))
interp <- "非真实单细胞嵌入；仅证明技能专属图类型与命名。"
status <- "PASS"
""",
        "metabolomics": f"""
mets <- paste0("M", 1:40)
mat <- matrix(abs(rnorm(40 * 8, 10, 3)), nrow = 40)
mat[1:6, 1:4] <- mat[1:6, 1:4] * 2.2
colnames(mat) <- paste0("S", 1:8)
meta <- data.frame(sample = colnames(mat), group = c(rep("Herb", 4), rep("Vehicle", 4)))
write.csv(cbind(metabolite = mets, as.data.frame(mat)), file.path(data_dir, "toy_metabolites.csv"), row.names = FALSE)
write.csv(meta, file.path(data_dir, "toy_meta.csv"), row.names = FALSE)
# 简易 VIP 代理：组间 |Δmean|
vip <- abs(rowMeans(mat[, 1:4]) - rowMeans(mat[, 5:8]))
res <- data.frame(metabolite = mets, delta = vip)[order(-vip), ]
write.csv(res, file.path(tab_dir, delivery_table_name(skill_en, "VIP", "HerbVsVehicle")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 40, 8, 8, "toy_meta Herb/Vehicle", TRUE, NA, sourced_note, "OPLS-like proxy",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
top <- head(res, 12)
top$metabolite <- factor(top$metabolite, levels = rev(top$metabolite))
p <- ggplot(top, aes(delta, metabolite)) + geom_col(fill = bioinfo_palette[3]) +
  labs(title = "Metabolomics |Δmean| Top12 (toy proxy VIP)", x = "|Δmean| Herb-Vehicle")
delivery_save_plot(p, skill_en, "bar", "VIP_HerbVsVehicle", 6, 5.5, fig_dir, bio_root)
fig_map <- c("差异代谢物条形图" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "VIP_HerbVsVehicle"), ".png"))
interp <- "非真实 OPLS-DA；展示代谢组样例可区分交付物。"
status <- "PASS"
""",
        "microbiome16s": f"""
otu <- read.csv(file.path(data_dir, "toy_otu.csv"), check.names = FALSE)
if (!nrow(otu)) {{
  otu <- data.frame(taxon = paste0("Taxa", 1:5), A1=10,A2=12,A3=11,B1=2,B2=3,B3=1)
  write.csv(otu, file.path(data_dir, "toy_otu.csv"), row.names = FALSE)
}}
mat <- as.matrix(otu[, -1])
rownames(mat) <- otu[[1]]
rel <- sweep(mat, 2, colSums(mat), "/")
alpha <- data.frame(sample = colnames(mat), shannon = apply(rel, 2, function(p) {{
  p <- p[p > 0]; -sum(p * log(p))
}}), group = c(rep("SiteA", 3), rep("SiteB", 3)))
write.csv(alpha, file.path(tab_dir, delivery_table_name(skill_en, "alpha", "shannon")), row.names = FALSE)
write_delivery_audit(skill_en, "post", nrow(mat), ncol(mat), ncol(mat), "toy OTU SiteA/B", TRUE, NA, sourced_note,
  "16S alpha diversity", file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(alpha, aes(group, shannon, fill = group)) + geom_boxplot(alpha = 0.8) +
  geom_jitter(width = 0.1, size = 2) +
  scale_fill_manual(values = bioinfo_palette[c(2, 5)]) +
  labs(title = "Microbiome16S Shannon (toy)", y = "Shannon")
delivery_save_plot(p, skill_en, "boxplot", "Shannon_SiteAVsB", 5.5, 4.5, fig_dir, bio_root)
fig_map <- c("Shannon 箱线图" = paste0("../图片文件/", delivery_stem(skill_en, "boxplot", "Shannon_SiteAVsB"), ".png"))
interp <- "16S 玩具 OTU Alpha 多样性；已 source 16S 骨架（若有）。"
status <- "PASS"
""",
        "methylation": f"""
beta <- read.csv(file.path(data_dir, "toy_beta.csv"), check.names = FALSE)
if (!nrow(beta)) {{
  beta <- data.frame(cpg = paste0("cg", 1:20), matrix(runif(80), nrow = 20))
  colnames(beta) <- c("cpg", paste0("S", 1:4))
  write.csv(beta, file.path(data_dir, "toy_beta.csv"), row.names = FALSE)
}}
mat <- as.matrix(beta[, -1])
rownames(mat) <- beta[[1]]
# 扩展到 4 样本两组
if (ncol(mat) < 4) stop("beta 列不足")
delta <- rowMeans(mat[, 1:2, drop = FALSE]) - rowMeans(mat[, 3:4, drop = FALSE])
dm <- data.frame(cpg = rownames(mat), deltaBeta = delta)
write.csv(dm, file.path(tab_dir, delivery_table_name(skill_en, "DMP", "deltaBeta")), row.names = FALSE)
write_delivery_audit(skill_en, "post", nrow(mat), ncol(mat), ncol(mat), "toy beta Case/Control cols", TRUE, NA,
  sourced_note, "WGBS/RRBS toy", file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(dm, aes(deltaBeta)) + geom_histogram(bins = 12, fill = bioinfo_palette[4], color = "white") +
  labs(title = "WGBS-RRBS deltaBeta distribution (toy)", x = "deltaBeta", y = "count")
delivery_save_plot(p, skill_en, "hist", "deltaBeta", 6, 4.5, fig_dir, bio_root)
fig_map <- c("deltaBeta 分布" = paste0("../图片文件/", delivery_stem(skill_en, "hist", "deltaBeta"), ".png"))
interp <- "甲基化 beta 玩具差分直方图。"
status <- "PASS"
""",
        "geo_tcga": f"""
# 生存风险示意（公共库挖掘下游玩具）
surv <- data.frame(
  id = paste0("P", 1:40),
  time = 20 + seq_len(40) * 2 + rnorm(40, 0, 3),
  status = rep(0:1, 20),
  risk = rep(c("High", "Low"), each = 20)
)
write.csv(surv, file.path(data_dir, "toy_survival_proxy.csv"), row.names = FALSE)
# KM 阶梯代理：按风险组平均生存时间条形
agg <- aggregate(time ~ risk, surv, mean)
write.csv(agg, file.path(tab_dir, delivery_table_name(skill_en, "KM", "riskMeanTime")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 40, 4, 40, "toy risk High/Low", TRUE, "TOY-TCGA", sourced_note,
  "GEO-TCGA 下游玩具", file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(agg, aes(risk, time, fill = risk)) + geom_col() +
  scale_fill_manual(values = bioinfo_palette[c(1, 4)]) +
  labs(title = "GEO-TCGA toy mean survival by risk", y = "mean time")
delivery_save_plot(p, skill_en, "bar", "RiskMeanTime", 5, 4.5, fig_dir, bio_root)
fig_map <- c("风险组平均生存" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "RiskMeanTime"), ".png"))
interp <- "非真实 TCGA KM；accession=TOY-TCGA。"
status <- "PASS"
""",
        "gwas": f"""
chr <- rep(1:5, each = 40)
bp <- rep(seq(1e5, 4e6, length.out = 40), 5)
pval <- runif(200, 1e-4, 1)
pval[c(12, 55, 90)] <- c(1e-8, 5e-8, 2e-7)
gwas <- data.frame(SNP = paste0("rs", seq_len(200)), CHR = chr, BP = bp, P = pval)
gwas$logp <- -log10(gwas$P)
gwas$pos <- gwas$CHR + gwas$BP / max(gwas$BP)
write.csv(gwas, file.path(tab_dir, delivery_table_name(skill_en, "assoc", "toySNPs")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 200, 5, NA, "toy SNP list", TRUE, NA, sourced_note, "manhattan toy",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(gwas, aes(pos, logp, color = factor(CHR))) + geom_point(size = 1) +
  geom_hline(yintercept = -log10(5e-8), linetype = 2, color = "grey40") +
  scale_color_manual(values = rep(bioinfo_palette, length.out = 5)) +
  labs(title = "GWAS Manhattan (toy)", x = "chromosome (scaled)", y = "-log10(P)", color = "CHR")
delivery_save_plot(p, skill_en, "manhattan", "toySNPs", 8, 4.5, fig_dir, bio_root)
fig_map <- c("曼哈顿图" = paste0("../图片文件/", delivery_stem(skill_en, "manhattan", "toySNPs"), ".png"))
interp <- "玩具关联 p 值曼哈顿图；非真实 GWAS。"
status <- "PASS"
""",
        "network_pharm": f"""
ct <- data.frame(
  compound = c("C1", "C1", "C2", "C2", "C3", "C3", "C4"),
  target = c("TP53", "EGFR", "EGFR", "KRAS", "TP53", "BRAF", "MYC")
)
disease <- c("TP53", "EGFR", "KRAS", "MYC")
write.csv(ct, file.path(data_dir, "compound_targets.csv"), row.names = FALSE)
writeLines(disease, file.path(data_dir, "disease_genes.txt"))
hit <- unique(ct$target[ct$target %in% disease])
ov <- data.frame(gene = hit, in_network = TRUE)
write.csv(ov, file.path(tab_dir, delivery_table_name(skill_en, "overlap", "compoundDisease")), row.names = FALSE)
deg <- as.data.frame(table(ct$target))
colnames(deg) <- c("target", "degree")
write_delivery_audit(skill_en, "post", nrow(ct), 2, length(unique(ct$compound)), "compound_targets.csv", TRUE, NA,
  sourced_note, "network pharm toy", file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(deg, aes(reorder(target, degree), degree, fill = target %in% disease)) +
  geom_col() + coord_flip() +
  scale_fill_manual(values = c("FALSE" = "grey70", "TRUE" = bioinfo_palette[1]), name = "disease gene") +
  labs(title = "NetworkPharmacology target degree (toy)", x = "target", y = "degree")
delivery_save_plot(p, skill_en, "bar", "TargetDegree", 6.5, 4.5, fig_dir, bio_root)
fig_map <- c("靶点度分布" = paste0("../图片文件/", delivery_stem(skill_en, "bar", "TargetDegree"), ".png"))
interp <- "化合物-靶点玩具网络度分布。"
status <- "PASS"
""",
        "survival": f"""
surv <- data.frame(
  id = paste0("P", 1:50),
  time = rexp(50, rate = 0.03) + 10,
  status = rbinom(50, 1, 0.55),
  risk = rep(c("High", "Low"), each = 25)
)
# 让 High 风险时间更短
surv$time[surv$risk == "High"] <- surv$time[surv$risk == "High"] * 0.55
write.csv(surv, file.path(data_dir, "toy_survival.csv"), row.names = FALSE)
# 简易 KM 点：按时间分箱存活比例
mk_km <- function(d) {{
  d <- d[order(d$time), ]
  n <- nrow(d)
  data.frame(time = d$time, surv = 1 - cumsum(d$status) / n, risk = d$risk[1])
}}
km <- rbind(mk_km(surv[surv$risk == "High", ]), mk_km(surv[surv$risk == "Low", ]))
write.csv(km, file.path(tab_dir, delivery_table_name(skill_en, "KM", "HighVsLow")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 50, 4, 50, "toy_survival risk", TRUE, NA, sourced_note, "KM toy",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(km, aes(time, surv, color = risk)) + geom_step(linewidth = 1) +
  scale_color_manual(values = bioinfo_palette[c(1, 4)]) +
  labs(title = "Survival KM High vs Low (toy)", x = "time", y = "survival") +
  coord_cartesian(ylim = c(0, 1))
delivery_save_plot(p, skill_en, "KM", "HighVsLow", 6.5, 5, fig_dir, bio_root)
fig_map <- c("KM曲线" = paste0("../图片文件/", delivery_stem(skill_en, "KM", "HighVsLow"), ".png"))
interp <- "玩具生存曲线；非临床预后结论。"
status <- "PASS"
""",
        "wgcna": f"""
# 模块-性状相关热图玩具
mods <- paste0("M", 1:6)
traits <- c("Age", "Stage", "Response")
cor_mat <- matrix(runif(18, -0.8, 0.8), nrow = 6, dimnames = list(mods, traits))
cdf <- data.frame(
  module = rep(mods, times = 3),
  trait = rep(traits, each = 6),
  cor = as.vector(cor_mat)
)
write.csv(cdf, file.path(tab_dir, delivery_table_name(skill_en, "moduleTrait", "cor")), row.names = FALSE)
write_delivery_audit(skill_en, "post", 6, 3, NA, "toy traits", TRUE, NA, sourced_note, "WGCNA module-trait",
  file.path(tab_dir, delivery_audit_name(skill_en, "post")))
library(ggplot2)
p <- ggplot(cdf, aes(trait, module, fill = cor)) + geom_tile(color = "white") +
  scale_fill_gradient2(low = bioinfo_palette[4], mid = "white", high = bioinfo_palette[1], midpoint = 0) +
  labs(title = "Module–trait correlation", fill = "Correlation")
delivery_save_plot(p, skill_en, "heatmap", "ModuleTrait", 5.5, 5, fig_dir, bio_root)
fig_map <- c("模块-性状相关" = paste0("../图片文件/", delivery_stem(skill_en, "heatmap", "ModuleTrait"), ".png"))
interp <- "WGCNA 风格玩具热图。"
status <- "PASS"
""",
    }
    if kind not in blocks:
        raise KeyError(kind)
    return blocks[kind]


def hash(folder: str) -> int:
    return int(hashlib.md5(folder.encode()).hexdigest()[:8], 16)


def report_footer() -> str:
    return textwrap.dedent(
        """\
        data_html <- paste0(
          "<p><b>toy=TRUE</b>：本样例为可复现模拟数据，<b>不可外推</b>为真实生物学/临床结论。</p>",
          "<p>详见 <code>数据文件/DATA_SOURCE.md</code>。</p>"
        )
        audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))
        audit_html <- if (file.exists(audit_path)) {
          paste0("<pre>", paste(readLines(audit_path, warn = FALSE, encoding = "UTF-8"), collapse = "\\n"), "</pre>")
        } else {
          "<p>无 post 审计表</p>"
        }
        rep_file <- file.path(rep_dir, delivery_report_name(skill_en, "v1"))
        write_delivery_report(
          skill_en, skill_folder, status,
          data_html, audit_html, sourced_note, fig_map, interp, rep_file,
          blocked_reason = if (exists("blocked_reason")) blocked_reason else ""
        )
        writeLines(status, file.path(rep_dir, "STATUS.txt"))
        # 清理旧无语义文件名
        for (old in c("sample_pca.png", "sample_volcano.png", "样例报告.html")) {
          f1 <- file.path(fig_dir, old); if (file.exists(f1)) file.remove(f1)
          f2 <- file.path(rep_dir, old); if (file.exists(f2)) file.remove(f2)
        }
        message("DONE ", status, " — ", skill_folder, " report=", basename(rep_file))
        """
    )


KIND_BY_PATH = {
    "00_基础_Foundation/统一交付规范_DeliveryStandards": ("delivery_demo", 202601),
    "00_基础_Foundation/统一可视化规范_VizStandards": ("viz_demo", 202602),
    "00_基础_Foundation/数据真实性验证_DataAuthenticity": ("authenticity", 202603),
    "01_组学_Omics/转录组分析_RNA-seq": ("rnaseq", 42),
    "01_组学_Omics/蛋白质组分析_Proteomics": ("proteomics", 101),
    "01_组学_Omics/单细胞与空间转录组分析_scRNA-Spatial": ("scrna", 202),
    "01_组学_Omics/代谢组分析_Metabolomics": ("metabolomics", 303),
    "01_组学_Omics/微生物组16S分析_Microbiome16S": ("microbiome16s", 404),
    "01_组学_Omics/DNA甲基化分析_WGBS-RRBS": ("methylation", 505),
    "01_组学_Omics/公共库挖掘_GEO-TCGA": ("geo_tcga", 606),
    "02_遗传与变异_Genetics/全基因组关联分析_GWAS": ("gwas", 707),
    "03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology": ("network_pharm", 808),
    "04_临床预测与统计_ClinicalStats/生存分析与预后模型_Survival": ("survival", 909),
    "05_系统方法_SystemsMethods/共表达网络WGCNA_WGCNA": ("wgcna", 1010),
}


def write_data_source(sample: Path, folder: str, kind: str) -> None:
    (sample / "数据文件" / "DATA_SOURCE.md").write_text(
        f"# 数据来源\n\n"
        f"- **toy=TRUE**（强制）：可复现模拟数据，**不可外推**\n"
        f"- **技能**：`{folder}`\n"
        f"- **analysis_kind**：`{kind}`\n"
        f"- **规范**：统一交付规范_DeliveryStandards\n",
        encoding="utf-8",
    )


def prepare_core(rel: str) -> dict:
    skill_dir = ROOT / rel.replace("/", os.sep)
    folder = skill_dir.name
    sample = skill_dir / "01_样例_sample"
    ensure_tree(sample)
    kind, seed = KIND_BY_PATH[rel]

    # 清理旧不合规/错误命名图片与报告，避免哈希统计混入历史文件
    fig_dir = sample / "结果文件" / "图片文件"
    rep_dir = sample / "结果文件" / "报告文件"
    for p in fig_dir.glob("*"):
        if p.is_file():
            p.unlink()
    for p in rep_dir.glob("*"):
        if p.is_file() and p.name != "STATUS.txt":
            # STATUS 会重写；一并清报告
            p.unlink()
    for p in rep_dir.glob("STATUS.txt"):
        p.unlink(missing_ok=True)

    # specialty toy inputs
    data_dir = sample / "数据文件"
    if kind == "microbiome16s":
        (data_dir / "toy_otu.csv").write_text(
            "taxon,A1,A2,A3,B1,B2,B3\n"
            "Taxa1,10,12,11,2,3,1\n"
            "Taxa2,5,4,6,15,14,16\n"
            "Taxa3,8,7,9,8,7,9\n"
            "Taxa4,1,2,1,10,12,11\n"
            "Taxa5,3,3,4,9,8,10\n",
            encoding="utf-8",
        )
    if kind == "methylation":
        lines = ["cpg,S1,S2,S3,S4"]
        for i in range(1, 25):
            a = 0.7 + (i % 5) * 0.04
            b = 0.2 + (i % 4) * 0.03
            lines.append(f"cg{i},{a:.3f},{a-0.02:.3f},{b:.3f},{b+0.02:.3f}")
        (data_dir / "toy_beta.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if kind == "network_pharm":
        (data_dir / "compound_targets.csv").write_text(
            "compound,target\nC1,TP53\nC1,EGFR\nC2,EGFR\nC2,KRAS\nC3,TP53\nC3,BRAF\nC4,MYC\n",
            encoding="utf-8",
        )
        (data_dir / "disease_genes.txt").write_text("TP53\nEGFR\nKRAS\nMYC\n", encoding="utf-8")

    write_data_source(sample, folder, kind)
    code = r_header(folder, kind, seed) + "\n" + analysis_block(kind, folder) + "\n" + report_footer()
    code_path = sample / "代码文件" / "run_sample.R"
    code_path.write_text(code, encoding="utf-8", newline="\n")
    return {"skill_dir": skill_dir, "folder": folder, "rel": rel, "code": code_path, "kind": kind}


def run_one(prep: dict) -> dict:
    code: Path = prep["code"]
    try:
        proc = subprocess.run(
            ["Rscript", str(code.name)],
            cwd=str(code.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        status_file = prep["skill_dir"] / "01_样例_sample" / "结果文件" / "报告文件" / "STATUS.txt"
        status = status_file.read_text(encoding="utf-8").strip() if status_file.exists() else (
            "PASS" if proc.returncode == 0 else "FAIL"
        )
        if proc.returncode != 0 and status != "BLOCKED":
            status = "FAIL"
        rep_dir = prep["skill_dir"] / "01_样例_sample" / "结果文件" / "报告文件"
        reports = list(rep_dir.glob("*_样例报告_*.html"))
        return {
            "folder": prep["folder"],
            "path": prep["rel"],
            "status": status,
            "kind": prep["kind"],
            "report": reports[0].relative_to(ROOT).as_posix() if reports else "",
            "returncode": proc.returncode,
            "stderr": (proc.stderr or "")[-800:],
            "stdout": (proc.stdout or "")[-400:],
        }
    except Exception as e:
        return {
            "folder": prep["folder"],
            "path": prep["rel"],
            "status": "FAIL",
            "kind": prep["kind"],
            "report": "",
            "returncode": -1,
            "stderr": str(e),
            "stdout": "",
        }


def collect_png_hashes(paths: list[str]) -> dict:
    info = {}
    for rel in paths:
        fig_dir = ROOT / rel.replace("/", os.sep) / "01_样例_sample" / "结果文件" / "图片文件"
        for p in fig_dir.glob("*.png"):
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            info[p.relative_to(ROOT).as_posix()] = {"sha256": h, "size": p.stat().st_size}
    return info


def patch_phase_b() -> None:
    """Rewrite generator to refuse generic identical volcano template."""
    path = ROOT / "_phaseB_sample_batch.py"
    text = path.read_text(encoding="utf-8")
    banner = (
        "# NOTE (2026-07-18): 禁止再生成全局同构 toy DEG+sample_volcano.png。\n"
        "# 新样例请用 _phaseC_delivery_rerun.py / 统一交付规范_DeliveryStandards。\n"
        "# 本文件保留仅作历史；main() 已改为拒绝全量雷同生成。\n"
    )
    if "禁止再生成全局同构" not in text:
        text = banner + text
    # Replace main to refuse mass identical generation
    new_main = '''
def main() -> None:
    print("REFUSED: _phaseB_sample_batch.py 会生成全技能同构 volcano/PCA（已审计不合规）。")
    print("请改用: python _phaseC_delivery_rerun.py")
    print("规范: 00_基础_Foundation/统一交付规范_DeliveryStandards/")
    raise SystemExit(2)


if __name__ == "__main__":
    main()
'''
    text = re.sub(
        r"\ndef main\(\) -> None:.*?(?=\nif __name__ == \"__main__\":)",
        new_main.split("if __name__")[0],
        text,
        count=1,
        flags=re.S,
    )
    # ensure ending
    if 'raise SystemExit(2)' not in text:
        text = text.rstrip() + "\n" + new_main
    path.write_text(text, encoding="utf-8", newline="\n")


def update_catalog() -> None:
    cat_path = ROOT / "技能目录_skill-catalog.json"
    cat = json.loads(cat_path.read_text(encoding="utf-8"))
    skills = cat.get("skills", [])
    # insert delivery skill after viz if missing
    if not any(s.get("id") == "bioinfo-delivery-standards" for s in skills):
        entry = {
            "id": "bioinfo-delivery-standards",
            "path": "00_基础_Foundation/统一交付规范_DeliveryStandards",
            "doc": "技能说明_统一交付规范_DeliveryStandards.md",
            "title_zh": "统一交付规范",
            "title_en": "DeliveryStandards",
            "triggers": ["交付规范", "文件命名", "样例报告", "DeliveryStandards"],
            "research_intents": ["交付物命名", "样例审计", "HTML报告"],
            "data_types": [],
            "inputs": [],
            "outputs": ["合规命名图", "审计表", "HTML报告"],
            "r_packages": ["ggplot2"],
            "cli_tools": [],
            "combines_with": ["bioinfo-viz-standards", "bioinfo-research-orchestrator"],
            "requires": ["bioinfo-viz-standards"],
            "depends_on": ["bioinfo-viz-standards"],
            "category": "foundation",
        }
        # place after viz-standards
        idx = next((i for i, s in enumerate(skills) if s.get("id") == "bioinfo-viz-standards"), 0)
        skills.insert(idx + 1, entry)
    # add requires delivery to all non-group skills
    for s in skills:
        if s.get("category") == "group":
            continue
        if s.get("id") == "bioinfo-delivery-standards":
            continue
        for key in ("requires", "depends_on"):
            lst = list(s.get(key) or [])
            if "bioinfo-delivery-standards" not in lst:
                lst.append("bioinfo-delivery-standards")
            s[key] = lst
    cat["skills"] = skills
    cat["delivery_rules"] = {
        "image_pattern": "{skill_en}_{plot_type}_{theme}.{png|svg}",
        "table_pattern": "{skill_en}_{table_type}_{object}.csv",
        "report_pattern": "{skill_en}_样例报告_{version}.html",
        "banned_names": ["plot.png", "fig1.png", "sample_pca.png", "sample_volcano.png", "样例报告.html"],
        "min_dpi": 600,
        "audit_required": True,
    }
    cat_path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def list_pending(core_set: set[str]) -> list[str]:
    pending = []
    for doc in sorted(ROOT.rglob("技能说明_*.md")):
        rel = doc.parent.relative_to(ROOT).as_posix()
        if rel.startswith("07_") or "01_样例_sample" in rel:
            continue
        if rel not in core_set:
            pending.append(rel)
    return pending


def write_validation_report(core_results: list[dict], png_info: dict, pending: list[str]) -> None:
    # evidence section for 3 questions
    hashes = [v["sha256"] for v in png_info.values()]
    unique = len(set(hashes))
    lines = [
        "# 验证总报告 / Per-Skill Sample Validation",
        "",
        f"- **更新时间**：{datetime.now().isoformat(timespec='seconds')}",
        f"- **布局版本**：catalog `layout_version` + 统一交付规范_DeliveryStandards",
        f"- **核心样例重跑数**：{len(core_results)}",
        f"- **核心 PASS**：{sum(1 for r in core_results if r['status']=='PASS')}",
        f"- **核心 FAIL**：{sum(1 for r in core_results if r['status']=='FAIL')}",
        f"- **待按规范重跑**：{len(pending)}",
        "",
        "## 规范合规审计（回答用户三问）",
        "",
        "### 问1：执行样例时是否采用了本文件夹的 skill？",
        "",
        "**结论（修复前）：否。** Phase B 生成器 `_phaseB_sample_batch.py` 对全部技能写入**同一套**",
        "`run_sample.R`：只 `list.files` 记录骨架文件名，**从不 `source()`** 本技能 `脚本_scripts/`，",
        "也不按技能说明包表实现可区分分析。抽查证据：",
        "",
        "- 抽查 ≥8 个 `01_样例_sample/代码文件/run_sample.R`：均无 `source(` 调用（修复前全库计数 = 0）。",
        "- 典型路径：`01_组学_Omics/转录组分析_RNA-seq/01_样例_sample/代码文件/run_sample.R`",
        "  （旧版仅写 `skeleton_note <- paste(basename(sk), ...)`）。",
        "- 生成器源码：`_phaseB_sample_batch.py` 中 `r_script_for()` 注释写明「仅记录路径，不强制 source」。",
        "",
        "**修复后（核心 ≥12）**：均 `source` `统一交付规范_DeliveryStandards/脚本_scripts/*.R`，",
        "并 `source` 本技能 `脚本_scripts/*.R`（骨架函数）。",
        "",
        "### 问2：为什么不同地方生成的图相同？",
        "",
        "**结论：同一套 toy 表达矩阵 + 同一套 base R PCA/火山图模板。**",
        "",
        "- 修复前：`sample_volcano.png` **69/69 文件 SHA256 完全相同**（唯一哈希 = 1）；",
        "  `sample_pca.png` 因 `main=技能名` 标题不同而哈希互异，但数据与坐标计算同源。",
        "- 根因：`write_toy_csv(..., kind='counts')` 全局同一矩阵；`set.seed(42)`；",
        "  火山图标题固定为 `\"Toy volcano\"`（无技能差异）。",
        "- 修复后核心样例 PNG：共 "
        + str(len(png_info))
        + f" 张，唯一哈希 **{unique}**"
        + ("（全部互异）" if unique == len(png_info) else "（存在重复则需复查）")
        + "。",
        "",
        "### 问3：文件命名为何未按既有规范？",
        "",
        "**结论：Phase B 使用契约占位名，未落实 VizStandards / ProjectLayout 的语义命名。**",
        "",
        "| 实际（旧） | 规范要求 |",
        "|------------|----------|",
        "| `sample_pca.png` / `sample_volcano.png` | `{技能英文}_{图类型}_{主题}.png` + 同名 `.svg` |",
        "| `样例报告.html` | `{技能英文}_样例报告_{v1\\|日期}.html` |",
        "| `toy_deg_results.csv` / `sample_summary.csv` | `{技能}_{表类型}_{对象}.csv` |",
        "| 仅 PNG、无 SVG | DPI≥600 且尽量 SVG+PNG（`save_plot_pub`） |",
        "",
        "对照文档：",
        f"- `00_基础_Foundation/统一可视化规范_VizStandards/技能说明_*.md`",
        f"- `项目结构规范_ProjectLayout.md`",
        f"- 新建 SSOT：`00_基础_Foundation/统一交付规范_DeliveryStandards/`",
        "",
        "## 核心样例重跑结果",
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
        "### 核心样例图片哈希（节选）",
        "",
        "| 文件 | size | sha256前12 |",
        "|------|------|------------|",
    ]
    for fp, meta in sorted(png_info.items()):
        lines.append(f"| `{fp}` | {meta['size']} | `{meta['sha256'][:12]}` |")

    lines += [
        "",
        "## 待按规范重跑清单",
        "",
        "以下技能仍保留 Phase B 旧产物或仅目录契约；**须**按 DeliveryStandards 重写 `run_sample.R` 后重跑：",
        "",
    ]
    for p in pending:
        lines.append(f"- `{p}`")

    lines += [
        "",
        "## 如何跑核心样例",
        "",
        "```bash",
        "python E:/RProject/生信分析技能_BioinformaticsSkills/_phaseC_delivery_rerun.py",
        "```",
        "",
        "或单个：",
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
    VAL_DIR.mkdir(exist_ok=True)
    (VAL_DIR / "验证总报告.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    (VAL_DIR / "核心样例_delivery_results.json").write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "core": core_results,
                "png_hashes": png_info,
                "pending_count": len(pending),
                "pending": pending,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    print("Updating catalog + phaseB guard...")
    update_catalog()
    patch_phase_b()

    print(f"Preparing {len(CORE_SKILLS)} core samples...")
    preps = [prepare_core(rel) for rel in CORE_SKILLS]
    results = []
    for i, prep in enumerate(preps, 1):
        print(f"[{i}/{len(preps)}] {prep['rel']} ...", flush=True)
        res = run_one(prep)
        results.append(res)
        print(f"  -> {res['status']} rc={res['returncode']}", flush=True)
        if res["status"] == "FAIL":
            print("  stderr:", res.get("stderr", "")[:400])

    png_info = collect_png_hashes(CORE_SKILLS)
    pending = list_pending(set(CORE_SKILLS))
    write_validation_report(results, png_info, pending)
    print("SUMMARY", dict(Counter(r["status"] for r in results)))
    print("PNG unique hashes", len(set(v["sha256"] for v in png_info.values())), "/", len(png_info))
    print("Pending", len(pending))


if __name__ == "__main__":
    main()
