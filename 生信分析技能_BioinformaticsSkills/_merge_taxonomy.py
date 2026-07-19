# -*- coding: utf-8 -*-
"""Merge overlapping bioinfo skills per taxonomy plan. Deletes absorbed dirs."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OMICS = ROOT / "01_组学_Omics"
FOUND = ROOT / "00_基础_Foundation"

# absorbed_folder -> keep_folder (relative under OMICS unless noted)
# After merge: write merged skill doc at keep, delete absorbed dirs

MERGES = [
    # (new_or_keep_folder, list_of_source_folders, title_zh, title_en, skill_id, triggers, content_extra)
]


def skill_md(
    sid: str,
    zh: str,
    en: str,
    triggers: list[str],
    sources: str,
    when: str,
    steps: str,
    pkgs: list[str],
    cli: list[str],
    viz: str,
    interpret: str,
    combine: str,
    purpose: str,
    not_include: str,
    absorbed: list[str],
) -> str:
    pkg_lines = []
    if pkgs:
        for p in pkgs:
            pkg_lines.append(f"| 分析 | `{p}` | 核心 R 包 | |")
    else:
        pkg_lines.append("| （CLI/网页为主） | — | 见 CLI | |")
    for c in cli:
        pkg_lines.append(f"| 上游/主分析 | `{c}` | CLI | 非 R |")
    pkg_lines.append("| 出图 | `ggplot2` + 出版级出图 | DPI≥600 | 可视化规范 |")
    pkg_table = "\n".join(pkg_lines)
    abs_txt = "、".join(f"`{a}`" for a in absorbed) if absorbed else "无"
    return f"""---
name: {sid}
description: >-
  {zh} / {en}：{when}。触发：{', '.join(triggers[:8])}。
  已合并：{abs_txt}。
---

# {zh} / {en}

## 1. 数据来源

{sources}

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组官方或实验记录可核对；禁止编造结果数字。

## 3. 何时选用本技能

- {when}
- 山水用途层：{purpose}
- **不包含（边界）**：{not_include}

不适用：应改用边界中列出的独立技能。

## 4. 数据处理方法

{steps}

### 已合并原技能触发词

{abs_txt} 的触发需求一律走本技能（见 catalog `deprecated_ids`）。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
{pkg_table}

## 6. 数据可视化

{viz}；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

{interpret}

## 8. 能否结合其它生信

{combine}；出图强制统一可视化规范。
"""


def write_skill_dir(folder: str, md: str, pkgs: list[str]) -> Path:
    d = OMICS / folder
    d.mkdir(parents=True, exist_ok=True)
    scripts = d / "脚本_scripts"
    scripts.mkdir(exist_ok=True)
    (d / f"技能说明_{folder}.md").write_text(md, encoding="utf-8")
    pkgs_r = list(pkgs) if pkgs else ["ggplot2"]
    if "ggplot2" not in pkgs_r:
        pkgs_r.append("ggplot2")
    pkgs_vec = ", ".join(f'"{p}"' for p in pkgs_r)
    r = f"""# {folder} 骨架 status=skeleton
find_project_root <- function(start = getwd()) {{
  p <- normalizePath(start, winslash = "/", mustWork = FALSE)
  for (i in 1:8) {{
    if (file.exists(file.path(p, "RProject.Rproj"))) return(p)
    parent <- dirname(p); if (identical(parent, p)) break; p <- parent
  }}
  stop("未找到 RProject.Rproj")
}}
source_pub_viz <- function(project_root = find_project_root()) {{
  f <- file.path(project_root, "生信分析技能_BioinformaticsSkills", "00_基础_Foundation",
                 "统一可视化规范_VizStandards", "脚本_scripts", "出版级出图_PublicationPlot.R")
  stopifnot(file.exists(f)); source(f, encoding = "UTF-8")
}}
run_merged_skeleton <- function(input_path = NULL, out_dir = tempfile("bioinfo_"),
                                project_root = find_project_root()) {{
  pkgs <- c({pkgs_vec})
  present <- pkgs[vapply(pkgs, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
  missing <- setdiff(pkgs, present)
  if (length(missing)) message("【骨架】未安装: ", paste(missing, collapse = ", "))
  source_pub_viz(project_root)
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  message("【骨架】{folder} input=", input_path, " out=", out_dir)
  invisible(list(status = "skeleton", folder = "{folder}", pkgs_checked = present))
}}
if (sys.nframe() == 0L && !interactive()) message("加载 run_merged_skeleton()")
"""
    (scripts / "运行骨架_runSkeleton.R").write_text(r, encoding="utf-8")
    (scripts / "说明_README.md").write_text(
        f"# {folder}\n\n合并后技能骨架。见上级技能说明。\n", encoding="utf-8"
    )
    return d


def rm_dirs(names: list[str]) -> None:
    for n in names:
        p = OMICS / n
        if p.exists():
            shutil.rmtree(p)
            print("REMOVED", n)
        else:
            print("MISS", n)


def main():
    deprecated: dict[str, str] = {}
    created: list[dict] = []

    # 1 Protein structure + homology
    folder = "蛋白结构与建模_ProteinStructure"
    absorbed = ["蛋白结构预测与口袋_ProteinStructure", "同源建模_HomologyModeling"]
    md = skill_md(
        "bioinfo-protein-structure",
        "蛋白结构与建模",
        "ProteinStructure",
        ["AlphaFold", "PDB", "口袋", "同源建模", "MODELLER"],
        "UniProt/PDB/AlphaFold DB；无实验结构时用同源建模模板。",
        "对接前置：结构获取、口袋检测、同源建模补全。",
        "取结构(AF/PDB)→质控(pLDDT)→口袋(fpocket)→必要时 MODELLER 同源建模→交给对接。",
        ["bio3d"],
        ["fpocket", "MODELLER"],
        "结构卡通/口袋示意",
        "预测结构标明置信度；低同源建模不可靠。",
        "分子对接、分子动力学、网络药理",
        "药物-基因",
        "不做对接打分（→分子对接）；不做 MD 轨迹（→分子动力学）",
        absorbed,
    )
    # remove old first if name collision - old was 蛋白结构预测与口袋_ProteinStructure
    rm_dirs(absorbed)
    write_skill_dir(folder, md, ["bio3d", "ggplot2"])
    for a in absorbed:
        deprecated[a] = folder
    created.append({"id": "bioinfo-protein-structure", "folder": folder, "absorbed": absorbed})

    # 2 3D genome
    folder = "三维基因组分析_3DGenome"
    absorbed = ["HiC三维基因组_HiC", "染色质环与HiChIP_ChromatinLoop"]
    md = skill_md(
        "bioinfo-3d-genome",
        "三维基因组分析",
        "3DGenome",
        ["Hi-C", "TAD", "HiChIP", "ChIA-PET", "染色质环"],
        "Hi-C 接触图 (.hic/.cool)；HiChIP/ChIA-PET pairs。",
        "三维接触、TAD/compartment、蛋白锚定 loop。",
        "小节A Hi-C：矩阵→归一化→TAD/loop；小节B HiChIP：loop calling→基因关联。",
        ["GenomicInteractions", "ggplot2"],
        ["Juicer", "cooler", "HiCCUPS"],
        "接触热图/loop 图",
        "分辨率与深度决定可解析尺度。",
        "ChIP/ATAC、转录组",
        "病因-基因",
        "靶向结合 peak 请用表观峰检测；开放染色质用 ATAC",
        absorbed,
    )
    rm_dirs(absorbed)
    write_skill_dir(folder, md, ["GenomicInteractions", "ggplot2"])
    for a in absorbed:
        deprecated[a] = folder
    created.append({"id": "bioinfo-3d-genome", "folder": folder, "absorbed": absorbed})

    # 3 ChIP + CUT&Tag — rewrite existing ChIP folder, remove CUT&Tag
    folder = "表观遗传ChIP-seq_Epigenomics"
    absorbed = ["CUT与Tag分析_CUTnTag"]
    md = skill_md(
        "bioinfo-chipseq",
        "表观峰检测ChIP与CUT",
        "ChIP-CUTnTag",
        ["ChIP-seq", "CUT&Tag", "CUT&RUN", "peak", "DiffBind"],
        "ChIP/CUT&Tag/CUT&RUN FASTQ 或 peak；须有 Input/IgG 记录。",
        "靶向结合/组蛋白修饰峰检测与差异（含 CUT&Tag）。",
        "FastQC→比对→MACS2→DiffBind/csaw→ChIPseeker；按实验类型选 ChIP 或 CUT&Tag 参数。",
        ["DiffBind", "csaw", "ChIPseeker", "ggplot2"],
        ["FastQC", "Bowtie2", "MACS2"],
        "峰注释饼图、差异火山、profile",
        "近端基因≠直接靶；无对照须写局限。",
        "ATAC（开放染色质独立）、三维基因组、转录组",
        "病因-基因",
        "ATAC 开放染色质；Hi-C/HiChIP 三维接触",
        absorbed + ["原名表观遗传ChIP-seq（目录名保留兼容）"],
    )
    rm_dirs(absorbed)
    # keep folder name for path stability
    write_skill_dir(folder, md, ["DiffBind", "ChIPseeker", "ggplot2"])
    deprecated["CUT与Tag分析_CUTnTag"] = folder
    deprecated["表观峰检测_ChIP-CUTnTag"] = folder  # alias name in plan
    created.append({"id": "bioinfo-chipseq", "folder": folder, "absorbed": absorbed})

    # 4 Variant + WES
    folder = "变异检测与外显子组_Variant-WES"
    absorbed = ["变异检测与注释_VariantCalling", "全外显子组分析_WES"]
    md = skill_md(
        "bioinfo-variant-wes",
        "变异检测与外显子组",
        "Variant-WES",
        ["变异检测", "VCF", "GATK", "WES", "外显子组", "SNV"],
        "WGS/WES BAM 或 VCF；WES 为捕获场景。",
        "SNV/Indel 检测、过滤、注释与 WES 致病性排序。",
        "QC→比对→GATK call→filter→注释；WES 可加 Exomiser 排序。",
        ["VariantAnnotation", "ggplot2"],
        ["GATK", "bcftools", "Exomiser"],
        "Ti/Tv、Venn",
        "覆盖度与假阳性；捕获偏差（WES）。",
        "CNV、SV、TMB/肿瘤体细胞景观、NGS-QC",
        "病因-基因",
        "大结构变异→结构变异分析；RNA 融合→RNA融合基因检测",
        absorbed,
    )
    rm_dirs(absorbed)
    write_skill_dir(folder, md, ["VariantAnnotation", "ggplot2"])
    for a in absorbed:
        deprecated[a] = folder
    created.append({"id": "bioinfo-variant-wes", "folder": folder, "absorbed": absorbed})

    # 5 Metagenome cluster
    folder = "宏基因组与病原_Metagenome-Pathogen"
    absorbed = [
        "宏基因组分析_Metagenomics",
        "宏转录组分析_Metatranscriptomics",
        "病毒组与病原检测_Virome",
        "耐药与毒力基因_AMR-Virulence",
    ]
    md = skill_md(
        "bioinfo-metagenome-pathogen",
        "宏基因组与病原",
        "Metagenome-Pathogen",
        ["宏基因组", "宏转录组", "病毒组", "AMR", "Kraken", "HUMAnN", "CARD"],
        "群落 WGS/RNA reads；细菌基因组（AMR）。",
        "物种/功能/MAG、宏转录、病毒鉴定、耐药毒力筛查。",
        "模式：metagenome / metatranscriptome / virome / AMR；质控→分类或组装→功能或 CARD/VFDB。",
        ["ggplot2"],
        ["Kraken2", "HUMAnN", "MetaBAT", "VirSorter", "ABRicate"],
        "丰度堆叠/热图",
        "宿主污染；存在≠表达（AMR）。",
        "16S（扩增子独立）、代谢组",
        "病因-细胞",
        "16S amplicon 用微生物组16S技能",
        absorbed,
    )
    rm_dirs(absorbed)
    write_skill_dir(folder, md, ["ggplot2"])
    for a in absorbed:
        deprecated[a] = folder
    created.append({"id": "bioinfo-metagenome-pathogen", "folder": folder, "absorbed": absorbed})

    # 6 ncRNA + ceRNA
    folder = "非编码与ceRNA_ncRNA-ceRNA"
    absorbed = ["非编码RNA分析_ncRNA", "ceRNA网络分析_ceRNA"]
    md = skill_md(
        "bioinfo-ncrna-cerna",
        "非编码与ceRNA",
        "ncRNA-ceRNA",
        ["miRNA", "lncRNA", "circRNA", "ceRNA", "非编码"],
        "小 RNA/RNA-seq；miRNA 与 mRNA/lncRNA 表达。",
        "非编码定量、靶基因与 ceRNA 竞争网络。",
        "定量→差异→靶预测→（可选）ceRNA 网络与相关性验证。",
        ["clusterProfiler", "igraph", "ggplot2"],
        [],
        "火山/网络图",
        "靶预测与 ceRNA 相关≠机制证实。",
        "转录组、生存、网络药理",
        "病因-基因",
        "编码基因 DEG 主分析→转录组技能",
        absorbed,
    )
    rm_dirs(absorbed)
    write_skill_dir(folder, md, ["clusterProfiler", "igraph", "ggplot2"])
    for a in absorbed:
        deprecated[a] = folder
    created.append({"id": "bioinfo-ncrna-cerna", "folder": folder, "absorbed": absorbed})

    # 7 ADMET + QSAR
    folder = "类药性与QSAR_ADMET-QSAR"
    absorbed = ["ADMET与类药性评价_ADMET", "QSAR与药效团_QSAR-Pharmacophore"]
    md = skill_md(
        "bioinfo-admet-qsar",
        "类药性与QSAR",
        "ADMET-QSAR",
        ["ADMET", "Lipinski", "QSAR", "药效团", "类药性"],
        "化合物 SMILES；已知活性集（QSAR）。",
        "类药过滤、ADMET 预测与 QSAR/药效团扩展。",
        "描述符→Lipinski/ADMET→（可选）QSAR 建模与药效团匹配。",
        [],
        ["SwissADME", "pkCSM", "RDKit"],
        "雷达图/观测预测散点",
        "网页预测非实验值；注意过拟合。",
        "网络药理、分子对接",
        "药物-基因",
        "对接打分→分子对接；MD→分子动力学",
        absorbed,
    )
    rm_dirs(absorbed)
    write_skill_dir(folder, md, ["ggplot2"])
    for a in absorbed:
        deprecated[a] = folder
    created.append({"id": "bioinfo-admet-qsar", "folder": folder, "absorbed": absorbed})

    # 8 Tumor somatic
    folder = "肿瘤体细胞景观_TumorSomatic"
    absorbed = ["肿瘤突变负荷与特征_TMB-Signature", "肿瘤异质性与克隆演化_ClonalEvolution"]
    md = skill_md(
        "bioinfo-tumor-somatic",
        "肿瘤体细胞景观",
        "TumorSomatic",
        ["TMB", "mutation signature", "克隆演化", "PyClone", "sigminer"],
        "体细胞 VCF；多区域/纵向 VAF。",
        "TMB、突变特征与克隆演化解读。",
        "计 TMB→签名分解→（可选）克隆聚类/鱼图。",
        ["sigminer", "ggplot2"],
        ["PyClone"],
        "签名条图/鱼图",
        "WES 与 panel 换算；纯度/拷贝数校正关键。",
        "变异检测、CNV、RNA融合、免疫浸润",
        "病因-基因",
        "CNV 分段主分析→拷贝数变异；融合→RNA融合基因检测",
        absorbed,
    )
    rm_dirs(absorbed)
    write_skill_dir(folder, md, ["sigminer", "ggplot2"])
    for a in absorbed:
        deprecated[a] = folder
    created.append({"id": "bioinfo-tumor-somatic", "folder": folder, "absorbed": absorbed})

    # 9 Proteomics + PTM + AP-MS — rewrite proteomics folder
    folder = "蛋白质组分析_Proteomics"
    absorbed = ["磷酸化与PTM蛋白组_PTM-Proteomics", "相互作用组AP-MS_Interactomics"]
    md = skill_md(
        "bioinfo-proteomics",
        "蛋白组与PTM",
        "Proteomics-PTM",
        ["蛋白质组", "LFQ", "TMT", "DIA", "磷酸化", "PTM", "AP-MS", "PPI质谱"],
        "MaxQuant/Spectronaut 定量；修饰肽表；AP-MS 鉴定表。",
        "蛋白定量差异、PTM 位点、AP-MS 物理互作。",
        "过滤→limma/MSstats→富集；PTM 小节；AP-MS 对照过滤→网络。",
        ["limma", "MSstats", "clusterProfiler", "STRINGdb", "ggplot2"],
        ["MaxQuant", "FragPipe"],
        "火山/热图/网络",
        "区分总量与修饰；AP-MS 非特异结合。",
        "转录组、代谢组、PPI 网络技能（知识库 PPI≠AP-MS）",
        "病因-基因",
        "仅知识库 STRING 网络且无质谱→蛋白质互作网络_PPI-Network",
        absorbed,
    )
    rm_dirs(absorbed)
    write_skill_dir(folder, md, ["limma", "ggplot2"])
    for a in absorbed:
        deprecated[a] = folder
    created.append({"id": "bioinfo-proteomics", "folder": folder, "absorbed": absorbed})

    # 10 Metabolomics + lipid + flux
    folder = "代谢组分析_Metabolomics"
    absorbed = ["脂质组分析_Lipidomics", "代谢通量分析_Fluxomics"]
    md = skill_md(
        "bioinfo-metabolomics",
        "代谢与脂质",
        "Metabolomics-Lipid",
        ["代谢组", "OPLS-DA", "脂质组", "lipidomics", "通量", "FBA"],
        "LC-MS/GC-MS 峰表；脂质定量表；约束模型/13C（通量小节）。",
        "小分子/脂质差异与可选通量估计。",
        "导入→归一化→PCA/OPLS-DA→VIP；脂质小节；通量小节（COBRA）。",
        ["ropls", "mixOmics", "lipidr", "limma", "ggplot2"],
        ["COBRApy"],
        "PCA/VIP/热图",
        "鉴定置信度；通量模型假设强。",
        "转录组、网络药理、多组学",
        "病因-代谢物",
        "蛋白酶层→蛋白组；菌群组成→16S/宏基因组",
        absorbed,
    )
    rm_dirs(absorbed)
    write_skill_dir(folder, md, ["ropls", "ggplot2"])
    for a in absorbed:
        deprecated[a] = folder
    created.append({"id": "bioinfo-metabolomics", "folder": folder, "absorbed": absorbed})

    # 11 scRNA advanced
    folder = "单细胞进阶方法_scRNA-Advanced"
    absorbed = [
        "单细胞轨迹与命运_Trajectory",
        "单细胞组成差异_scComposition",
        "单细胞整合与图谱_AtlasIntegration",
    ]
    md = skill_md(
        "bioinfo-scrna-advanced",
        "单细胞进阶方法",
        "scRNA-Advanced",
        ["轨迹", "monocle", "velocity", "miloR", "scCODA", "图谱整合", "scVI"],
        "已注释 Seurat；多样本比例；多批次对象。",
        "轨迹/RNA 速度、组成差异、图谱整合（主入口仍为 scRNA-Spatial）。",
        "小节：Trajectory / Composition / AtlasIntegration。",
        ["monocle3", "slingshot", "miloR", "Seurat", "harmony", "ggplot2"],
        ["velocyto", "scVelo", "scvi-tools"],
        "轨迹 UMAP / DA 图 / 整合 UMAP",
        "根选择与过度校正风险。",
        "单细胞与空间转录组分析_scRNA-Spatial（主入口）、细胞通讯",
        "病因-细胞",
        "标准 QC/聚类/注释→主技能 scRNA-Spatial；通讯→细胞通讯分析",
        absorbed,
    )
    rm_dirs(absorbed)
    write_skill_dir(folder, md, ["Seurat", "ggplot2"])
    for a in absorbed:
        deprecated[a] = folder
    created.append({"id": "bioinfo-scrna-advanced", "folder": folder, "absorbed": absorbed})

    # 12 Genetic downstream
    folder = "遗传关联下游_GeneticDownstream"
    absorbed = ["eQTL与QTL作图_eQTL", "共定位与TWAS_Coloc-TWAS", "多基因风险评分_PRS"]
    md = skill_md(
        "bioinfo-genetic-downstream",
        "遗传关联下游",
        "GeneticDownstream",
        ["eQTL", "QTL", "coloc", "TWAS", "PRS", "PRSice"],
        "基因型+表达；GWAS 与 eQTL 汇总；目标队列基因型。",
        "GWAS 之后的 eQTL、共定位/TWAS、PRS。",
        "小节：eQTL → coloc/TWAS → PRS。",
        ["MatrixEQTL", "coloc", "ggplot2"],
        ["PRSice-2", "LDpred2"],
        "位点图/区域图/分位数风险",
        "样本量与人群转移性。",
        "GWAS、孟德尔随机化（MR 独立）",
        "病因-基因/预测",
        "全基因组关联主分析→GWAS；因果 MR→孟德尔随机化",
        absorbed,
    )
    rm_dirs(absorbed)
    write_skill_dir(folder, md, ["coloc", "ggplot2"])
    for a in absorbed:
        deprecated[a] = folder
    created.append({"id": "bioinfo-genetic-downstream", "folder": folder, "absorbed": absorbed})

    # 13 Rename time series → dose-time (keep folder rename)
    old_ts = OMICS / "时间序列组学_TimeSeriesOmics"
    folder = "剂量反应与时间序列_DoseTime"
    absorbed = ["时间序列组学_TimeSeriesOmics"]
    md = skill_md(
        "bioinfo-dose-time",
        "剂量反应与时间序列",
        "DoseTime",
        ["时间序列", "纵向", "剂量时间", "dose-response"],
        "多时间点/剂量表达矩阵。",
        "动态差异与剂量反应表达模式。",
        "设计矩阵→limma spline/Impulse→模式聚类→富集。",
        ["limma", "ggplot2"],
        [],
        "轨迹线图",
        "时间点稀疏时谨慎解读。",
        "转录组、GSEA",
        "比较",
        "单时间点两组 DEG→转录组技能",
        absorbed,
    )
    if old_ts.exists():
        shutil.rmtree(old_ts)
    write_skill_dir(folder, md, ["limma", "ggplot2"])
    deprecated["时间序列组学_TimeSeriesOmics"] = folder
    created.append({"id": "bioinfo-dose-time", "folder": folder, "absorbed": absorbed})

    # HLA into neoantigen — rewrite neoantigen, remove HLA
    folder = "新抗原与免疫组库_Neoantigen-TCR"
    absorbed = ["HLA分型_HLA-Typing"]
    md = skill_md(
        "bioinfo-neoantigen",
        "新抗原与免疫组库",
        "Neoantigen-TCR",
        ["新抗原", "TCR", "BCR", "HLA", "OptiType", "netMHCpan"],
        "突变 VCF；WES/RNA（HLA 前置）；TCR/BCR 测序。",
        "HLA 分型前置 + 新抗原预测 + 免疫组库。",
        "HLA 分型→肽段→MHC 结合预测；或 MiXCR 组库克隆型。",
        ["ggplot2"],
        ["OptiType", "HLA-HD", "netMHCpan", "MiXCR"],
        "亲和力分布",
        "预测需实验验证。",
        "肿瘤体细胞景观、免疫浸润",
        "药物-细胞",
        "仅做体细胞 TMB/签名→肿瘤体细胞景观",
        absorbed,
    )
    rm_dirs(absorbed)
    write_skill_dir(folder, md, ["ggplot2"])
    deprecated["HLA分型_HLA-Typing"] = folder
    created.append({"id": "bioinfo-neoantigen", "folder": folder, "absorbed": absorbed})

    out = {
        "deprecated_folders": deprecated,
        "created": created,
    }
    (ROOT / "_merge_map.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("DONE merges", len(created), "deprecated", len(deprecated))


if __name__ == "__main__":
    main()
