# -*- coding: utf-8 -*-
"""Phase A: restructure BioinformaticsSkills top-level layout."""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(r"E:/RProject/生信分析技能_BioinformaticsSkills")
OLD_OMICS = ROOT / "01_组学_Omics"
OLD_PIPE = ROOT / "02_已落地流水线_ProductionPipelines"
OLD_VAL = ROOT / "03_分类验证_Validation"

# folder_name -> (new_top, category_key)
CATEGORY_MAP: dict[str, tuple[str, str]] = {
    # 01 Omics — true omics
    "ATAC专论_ATAC-seq": ("01_组学_Omics", "omics"),
    "DNA甲基化分析_WGBS-RRBS": ("01_组学_Omics", "omics"),
    "RNA编辑与修饰_RNAEditing": ("01_组学_Omics", "omics"),
    "三维基因组分析_3DGenome": ("01_组学_Omics", "omics"),
    "代谢组分析_Metabolomics": ("01_组学_Omics", "omics"),
    "公共库挖掘_GEO-TCGA": ("01_组学_Omics", "omics"),
    "剪接与异构体分析_AlternativeSplicing": ("01_组学_Omics", "omics"),
    "单细胞与空间转录组分析_scRNA-Spatial": ("01_组学_Omics", "omics"),
    "单细胞多组学_scMultiome": ("01_组学_Omics", "omics"),
    "单细胞质谱流式_CyTOF": ("01_组学_Omics", "omics"),
    "基因芯片表达分析_Microarray": ("01_组学_Omics", "omics"),
    "宏基因组与病原_Metagenome-Pathogen": ("01_组学_Omics", "omics"),
    "微生物组16S分析_Microbiome16S": ("01_组学_Omics", "omics"),
    "新生转录组_NascentRNA": ("01_组学_Omics", "omics"),
    "核糖体图谱分析_Ribo-seq": ("01_组学_Omics", "omics"),
    "空间转录组进阶_SpatialAdvanced": ("01_组学_Omics", "omics"),
    "糖组学分析_Glycomics": ("01_组学_Omics", "omics"),
    "蛋白质组分析_Proteomics": ("01_组学_Omics", "omics"),
    "表观遗传ChIP-seq_Epigenomics": ("01_组学_Omics", "omics"),
    "转录组分析_RNA-seq": ("01_组学_Omics", "omics"),
    "非编码与ceRNA_ncRNA-ceRNA": ("01_组学_Omics", "omics"),
    # 02 Genetics
    "RNA融合基因检测_FusionGene": ("02_遗传与变异_Genetics", "genetics"),
    "全基因组关联分析_GWAS": ("02_遗传与变异_Genetics", "genetics"),
    "变异检测与外显子组_Variant-WES": ("02_遗传与变异_Genetics", "genetics"),
    "基因组组装与注释_GenomeAssembly": ("02_遗传与变异_Genetics", "genetics"),
    "孟德尔随机化_MendelianRandomization": ("02_遗传与变异_Genetics", "genetics"),
    "拷贝数变异分析_CNV": ("02_遗传与变异_Genetics", "genetics"),
    "系统发育分析_Phylogenetics": ("02_遗传与变异_Genetics", "genetics"),
    "结构变异分析_StructuralVariant": ("02_遗传与变异_Genetics", "genetics"),
    "群体遗传学_PopulationGenetics": ("02_遗传与变异_Genetics", "genetics"),
    "肿瘤体细胞景观_TumorSomatic": ("02_遗传与变异_Genetics", "genetics"),
    "遗传关联下游_GeneticDownstream": ("02_遗传与变异_Genetics", "genetics"),
    "长读长测序分析_LongRead": ("02_遗传与变异_Genetics", "genetics"),
    # 03 Drug
    "分子动力学模拟_MolecularDynamics": ("03_药物计算_DrugDiscovery", "drug"),
    "分子对接与虚拟筛选_MolecularDocking": ("03_药物计算_DrugDiscovery", "drug"),
    "类药性与QSAR_ADMET-QSAR": ("03_药物计算_DrugDiscovery", "drug"),
    "网络药理学_NetworkPharmacology": ("03_药物计算_DrugDiscovery", "drug"),
    "药物敏感性与GDSC_DrugResponse": ("03_药物计算_DrugDiscovery", "drug"),
    "药物重定位与连通图_CMap-L1000": ("03_药物计算_DrugDiscovery", "drug"),
    "蛋白结构与建模_ProteinStructure": ("03_药物计算_DrugDiscovery", "drug"),
    # 04 Clinical
    "免疫浸润与免疫治疗_ImmuneInfiltration": ("04_临床预测与统计_ClinicalStats", "clinical"),
    "分子分型与共识聚类_MolecularSubtyping": ("04_临床预测与统计_ClinicalStats", "clinical"),
    "剂量反应与时间序列_DoseTime": ("04_临床预测与统计_ClinicalStats", "clinical"),
    "外泌体与液体活检_LiquidBiopsy": ("04_临床预测与统计_ClinicalStats", "clinical"),
    "放射组学与病理组学_Radiomics-Pathomics": ("04_临床预测与统计_ClinicalStats", "clinical"),
    "新抗原与免疫组库_Neoantigen-TCR": ("04_临床预测与统计_ClinicalStats", "clinical"),
    "机器学习生物标志物_ML-Biomarker": ("04_临床预测与统计_ClinicalStats", "clinical"),
    "生存分析与预后模型_Survival": ("04_临床预测与统计_ClinicalStats", "clinical"),
    "荟萃分析_MetaAnalysis": ("04_临床预测与统计_ClinicalStats", "clinical"),
    "诊断效能ROC_DiagnosticROC": ("04_临床预测与统计_ClinicalStats", "clinical"),
    # 05 Systems
    "CRISPR筛选分析_CRISPRscreen": ("05_系统方法_SystemsMethods", "systems"),
    "共表达网络WGCNA_WGCNA": ("05_系统方法_SystemsMethods", "systems"),
    "单细胞进阶方法_scRNA-Advanced": ("05_系统方法_SystemsMethods", "systems"),
    "基因集富集与通路_GSEA-Pathway": ("05_系统方法_SystemsMethods", "systems"),
    "多组学联合分析_MultiOmics": ("05_系统方法_SystemsMethods", "systems"),
    "细胞通讯分析_CellCommunication": ("05_系统方法_SystemsMethods", "systems"),
    "虚拟敲除与扰动_InSilicoKO": ("05_系统方法_SystemsMethods", "systems"),
    "蛋白质互作网络_PPI-Network": ("05_系统方法_SystemsMethods", "systems"),
    "跨物种基因映射_CrossSpecies": ("05_系统方法_SystemsMethods", "systems"),
    "转录因子与调控网络_TF-Network": ("05_系统方法_SystemsMethods", "systems"),
}

FOUNDATION_CAT = "foundation"
PIPELINE_CAT = "pipeline"
VALIDATION_TOP = "07_分类验证_Validation"
PIPELINE_TOP = "06_已落地流水线_ProductionPipelines"

PATH_REPLACEMENTS = [
    ("02_已落地流水线_ProductionPipelines", PIPELINE_TOP),
    ("03_分类验证_Validation", VALIDATION_TOP),
]


def ensure_dirs() -> None:
    for top in [
        "02_遗传与变异_Genetics",
        "03_药物计算_DrugDiscovery",
        "04_临床预测与统计_ClinicalStats",
        "05_系统方法_SystemsMethods",
    ]:
        (ROOT / top).mkdir(exist_ok=True)


def move_skill(folder: str, new_top: str) -> tuple[str, str]:
    src = OLD_OMICS / folder
    dst = ROOT / new_top / folder
    if not src.exists():
        # already moved?
        if dst.exists():
            return f"01_组学_Omics/{folder}", f"{new_top}/{folder}"
        raise FileNotFoundError(src)
    if new_top == "01_组学_Omics":
        return f"01_组学_Omics/{folder}", f"01_组学_Omics/{folder}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        raise FileExistsError(dst)
    shutil.move(str(src), str(dst))
    return f"01_组学_Omics/{folder}", f"{new_top}/{folder}"


def rename_top_dirs() -> list[tuple[str, str]]:
    mapping = []
    if OLD_PIPE.exists() and not (ROOT / PIPELINE_TOP).exists():
        shutil.move(str(OLD_PIPE), str(ROOT / PIPELINE_TOP))
        mapping.append(("02_已落地流水线_ProductionPipelines", PIPELINE_TOP))
    elif (ROOT / PIPELINE_TOP).exists():
        mapping.append(("02_已落地流水线_ProductionPipelines", PIPELINE_TOP))
    if OLD_VAL.exists() and not (ROOT / VALIDATION_TOP).exists():
        shutil.move(str(OLD_VAL), str(ROOT / VALIDATION_TOP))
        mapping.append(("03_分类验证_Validation", VALIDATION_TOP))
    elif (ROOT / VALIDATION_TOP).exists():
        mapping.append(("03_分类验证_Validation", VALIDATION_TOP))
    return mapping


def rewrite_file_text(path: Path, extra: list[tuple[str, str]] | None = None) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return False
    orig = text
    pairs = list(PATH_REPLACEMENTS)
    if extra:
        pairs.extend(extra)
    # longest first for skill path prefixes
    pairs.sort(key=lambda x: len(x[0]), reverse=True)
    for a, b in pairs:
        text = text.replace(a, b)
    if text != orig:
        path.write_text(text, encoding="utf-8", newline="\n")
        return True
    return False


def update_catalog(skill_moves: dict[str, str]) -> None:
    cat_path = ROOT / "技能目录_skill-catalog.json"
    data = json.loads(cat_path.read_text(encoding="utf-8"))
    data["layout_version"] = "2026-07-layout-v2"
    data["layout"] = {
        "00_基础_Foundation": "foundation",
        "01_组学_Omics": "omics",
        "02_遗传与变异_Genetics": "genetics",
        "03_药物计算_DrugDiscovery": "drug",
        "04_临床预测与统计_ClinicalStats": "clinical",
        "05_系统方法_SystemsMethods": "systems",
        "06_已落地流水线_ProductionPipelines": "pipeline",
        "07_分类验证_Validation": "validation",
    }
    folder_to_cat = {k: v[1] for k, v in CATEGORY_MAP.items()}
    for sk in data.get("skills", []):
        p = sk.get("path", "")
        # apply global renames
        for a, b in PATH_REPLACEMENTS:
            p = p.replace(a, b)
        # skill moves from omics
        for old, new in skill_moves.items():
            if p == old or p.startswith(old + "/"):
                p = new + p[len(old) :]
        sk["path"] = p
        # category
        if p == ".":
            sk["category"] = "group"
        elif p.startswith("00_基础_Foundation"):
            sk["category"] = FOUNDATION_CAT
        elif p.startswith(PIPELINE_TOP) or "ProductionPipelines" in p:
            sk["category"] = PIPELINE_CAT
        elif p.startswith(VALIDATION_TOP):
            sk["category"] = "validation"
        else:
            # match by folder basename
            folder = Path(p).name if p else ""
            sk["category"] = folder_to_cat.get(folder, "omics")
    cat_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_migration_doc(moves: list[tuple[str, str]]) -> None:
    lines = [
        "# 目录重构说明 / Layout Migration",
        "",
        "版本：`layout_version = 2026-07-layout-v2`",
        "",
        "## 目标顶层",
        "",
        "```",
        "00_基础_Foundation/",
        "01_组学_Omics/                    # 仅真正组学",
        "02_遗传与变异_Genetics/",
        "03_药物计算_DrugDiscovery/",
        "04_临床预测与统计_ClinicalStats/",
        "05_系统方法_SystemsMethods/",
        "06_已落地流水线_ProductionPipelines/  # 原 02",
        "07_分类验证_Validation/            # 原 03",
        "```",
        "",
        "## 旧 → 新映射",
        "",
        "| 旧路径 | 新路径 |",
        "|--------|--------|",
    ]
    for a, b in sorted(moves, key=lambda x: x[0]):
        if a != b:
            lines.append(f"| `{a}` | `{b}` |")
    lines += [
        "",
        "## 分类原则",
        "",
        "- **omics**：测序/组学数据类型本体（转录、单细胞、蛋白、代谢、表观、微生物等）",
        "- **genetics**：变异、组装、GWAS/群体/MR/系统发育等",
        "- **drug**：网络药理、对接、MD、结构、ADMET、CMap、GDSC",
        "- **clinical**：生存/ROC/Meta/ML/分型/液体活检/放射组学/免疫浸润/新抗原/DoseTime",
        "- **systems**：可被多组学调用的方法层（GSEA、WGCNA、PPI、通讯、虚拟敲除等）",
        "",
        "脚本：`_layout_migrate_phaseA.py`",
        "",
    ]
    (ROOT / "目录重构说明_LayoutMigration.md").write_text(
        "\n".join(lines), encoding="utf-8", newline="\n"
    )


def rewrite_landscape() -> None:
    """Rewrite SkillLandscape section headers to new taxonomy."""
    path = ROOT / "技能全景清单_SkillLandscape.md"
    text = path.read_text(encoding="utf-8")
    # Update intro count line stays; rewrite category sections by regenerating from map
    sections = {
        "foundation": ("## 基础 / Foundation（`00_基础_Foundation`）", []),
        "omics": ("## 组学 / Omics（`01_组学_Omics`）", []),
        "genetics": ("## 遗传与变异 / Genetics（`02_遗传与变异_Genetics`）", []),
        "drug": ("## 药物计算 / DrugDiscovery（`03_药物计算_DrugDiscovery`）", []),
        "clinical": ("## 临床预测与统计 / ClinicalStats（`04_临床预测与统计_ClinicalStats`）", []),
        "systems": ("## 系统方法 / SystemsMethods（`05_系统方法_SystemsMethods`）", []),
        "pipeline": ("## 生产流水线 / ProductionPipelines（`06_已落地流水线_ProductionPipelines`）", []),
    }
    # parse existing table rows for folder|id|triggers
    row_re = re.compile(
        r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*(.*?)\s*\|$"
    )
    folder_meta: dict[str, tuple[str, str]] = {}
    for line in text.splitlines():
        m = row_re.match(line.strip())
        if not m:
            continue
        folder, sid, trig = m.group(1), m.group(2), m.group(3)
        if folder in ("技能目录",) or sid == "id":
            continue
        folder_meta[folder] = (sid, trig)

    # foundation from known list
    foundation_folders = [
        "NGS质控与比对_NGS-QC-Alignment",
        "可复现工作流_ReproducibleWorkflow",
        "实验设计与统计功效_StudyDesign",
        "批次校正与整合_BatchCorrection",
        "数据真实性验证_DataAuthenticity",
        "文献与数据库检索_Literature-DB",
        "研究方案编排_ResearchOrchestrator",
        "统一可视化规范_VizStandards",
    ]
    for f in foundation_folders:
        if f in folder_meta:
            sections["foundation"][1].append((f, *folder_meta[f]))
    for folder, (top, cat) in CATEGORY_MAP.items():
        if folder in folder_meta:
            sections[cat][1].append((folder, *folder_meta[folder]))
    # pipeline
    if "差异分析与UMAP流水线_DEG-UMAP" in folder_meta:
        sections["pipeline"][1].append(
            ("差异分析与UMAP流水线_DEG-UMAP", *folder_meta["差异分析与UMAP流水线_DEG-UMAP"])
        )

    # keep deprecated block from old file
    dep_idx = text.find("## 已合并（deprecated")
    other_idx = text.find("## 明确不合并")
    tail = ""
    if dep_idx >= 0:
        tail = text[dep_idx:]

    out = [
        "# 技能全景清单 / Skill Landscape（去重后互斥分类）",
        "",
        "SSOT：本文件 + `技能目录_skill-catalog.json`。",
        "原则：可合并则合并；一方法一技能；边界写清「不包含」。",
        "",
        "布局版本：`layout_version = 2026-07-layout-v2`（见 [目录重构说明_LayoutMigration.md](目录重构说明_LayoutMigration.md)）。",
        "",
        f"当前技能文档数：**{sum(len(v[1]) for v in sections.values())}**（不含组入口）；已弃用目录见 catalog.`deprecated_folders`。",
        "",
    ]
    for key in ["foundation", "omics", "genetics", "drug", "clinical", "systems", "pipeline"]:
        title, rows = sections[key]
        out.append(title)
        out.append("")
        out.append("| 技能目录 | id | 触发词摘要 |")
        out.append("|----------|-----|------------|")
        for folder, sid, trig in sorted(rows, key=lambda x: x[0]):
            out.append(f"| `{folder}` | `{sid}` | {trig} |")
        out.append("")
    if tail:
        out.append(tail.rstrip() + "\n")
    else:
        out.append("")
    path.write_text("\n".join(out), encoding="utf-8", newline="\n")


def update_index_and_group_docs() -> None:
    index = ROOT / "索引_INDEX.md"
    t = index.read_text(encoding="utf-8")
    t = t.replace("03_分类验证_Validation", VALIDATION_TOP)
    t = t.replace("02_已落地流水线_ProductionPipelines", PIPELINE_TOP)
    if "目录布局" not in t:
        t = t.replace(
            "## 按研究目的",
            "## 目录布局（v2）\n\n"
            "- `00_基础_Foundation` / `01_组学_Omics` / `02_遗传与变异_Genetics` / "
            "`03_药物计算_DrugDiscovery` / `04_临床预测与统计_ClinicalStats` / "
            "`05_系统方法_SystemsMethods` / `06_已落地流水线_ProductionPipelines` / "
            f"`{VALIDATION_TOP}`\n"
            "- 映射表：[目录重构说明_LayoutMigration.md](目录重构说明_LayoutMigration.md)\n\n"
            "## 按研究目的",
        )
    index.write_text(t, encoding="utf-8", newline="\n")

    group = ROOT / "技能组总说明_BioinformaticsSkills.md"
    g = group.read_text(encoding="utf-8")
    g = g.replace("03_分类验证_Validation", VALIDATION_TOP)
    g = g.replace("02_已落地流水线_ProductionPipelines", PIPELINE_TOP)
    old_table = """## 子目录

| 区 | 说明 |
|----|------|
| `00_基础_Foundation/` | 编排、可视化、真实性 |
| `01_组学_Omics/` | 组学分析技能 |
| `02_已落地流水线_ProductionPipelines/` | DEG-UMAP 生产流水线 |"""
    new_table = f"""## 子目录

| 区 | 说明 |
|----|------|
| `00_基础_Foundation/` | 编排、可视化、真实性、实验设计、批次、NGS质控、文献、可复现 |
| `01_组学_Omics/` | 真正组学（转录/单细胞/蛋白/代谢/表观/微生物等） |
| `02_遗传与变异_Genetics/` | 变异、组装、GWAS、群体、MR、系统发育等 |
| `03_药物计算_DrugDiscovery/` | 网络药理、对接、MD、结构、ADMET、CMap、GDSC |
| `04_临床预测与统计_ClinicalStats/` | 生存/ROC/Meta/ML/分型/液体活检等 |
| `05_系统方法_SystemsMethods/` | GSEA、WGCNA、PPI、通讯、虚拟敲除等跨组学方法 |
| `{PIPELINE_TOP}/` | DEG-UMAP 生产流水线（原 02） |
| `{VALIDATION_TOP}/` | 分类验证与每技能样例总表（原 03） |"""
    # try replace with already-updated pipe path variants
    if "| `01_组学_Omics/` | 组学分析技能 |" in g:
        g = re.sub(
            r"## 子目录\n\n\| 区 \| 说明 \|\n\|----\|------\|\n(?:\|.*\|\n)+",
            new_table + "\n",
            g,
            count=1,
        )
    elif old_table in g:
        g = g.replace(old_table, new_table)
    else:
        g = re.sub(
            r"## 子目录\n\n\| 区 \| 说明 \|\n\|----\|------\|\n(?:\|.*\|\n)+",
            new_table + "\n",
            g,
            count=1,
        )
    group.write_text(g, encoding="utf-8", newline="\n")


def update_cursor_entry() -> None:
    p = Path(r"E:/RProject/.cursor/skills/生信分析技能_BioinformaticsSkills/SKILL.md")
    if p.exists():
        rewrite_file_text(p)


def build_skill_path_extras(moves: list[tuple[str, str]]) -> list[tuple[str, str]]:
    extras = []
    for old, new in moves:
        if old != new:
            extras.append((old, new))
    return extras


def walk_rewrite(extras: list[tuple[str, str]]) -> int:
    n = 0
    skip_dirs = {".git", "__pycache__", "样例_sample", "01_样例_sample"}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".cursor")]
        for fn in filenames:
            if not fn.endswith((".md", ".json", ".R", ".py", ".txt", ".Rmd")):
                continue
            # skip this migrator itself after run? still ok
            if fn.startswith("_layout_migrate"):
                continue
            fp = Path(dirpath) / fn
            if rewrite_file_text(fp, extras):
                n += 1
    return n


def main() -> None:
    ensure_dirs()
    moves: list[tuple[str, str]] = []
    skill_moves: dict[str, str] = {}

    # list current omics skills
    if OLD_OMICS.exists():
        folders = sorted(
            [d.name for d in OLD_OMICS.iterdir() if d.is_dir()]
        )
    else:
        folders = []

    missing = []
    for folder in folders:
        if folder not in CATEGORY_MAP:
            missing.append(folder)
            continue
        new_top, _cat = CATEGORY_MAP[folder]
        old_p, new_p = move_skill(folder, new_top)
        moves.append((old_p, new_p))
        skill_moves[old_p] = new_p

    if missing:
        raise SystemExit(f"Unmapped folders: {missing}")

    moves.extend(rename_top_dirs())
    # also record pipeline skill path
    moves.append(
        (
            "02_已落地流水线_ProductionPipelines/差异分析与UMAP流水线_DEG-UMAP",
            f"{PIPELINE_TOP}/差异分析与UMAP流水线_DEG-UMAP",
        )
    )

    extras = build_skill_path_extras(moves)
    update_catalog(skill_moves)
    rewrite_landscape()
    update_index_and_group_docs()
    update_cursor_entry()
    n = walk_rewrite(extras)

    write_migration_doc(moves)

    # also update project layout doc if present
    layout = ROOT / "项目结构规范_ProjectLayout.md"
    if layout.exists():
        rewrite_file_text(layout, extras)

    print(f"Moved {len(skill_moves)} skills; rewrote {n} files")
    print("Top-level now:", sorted([p.name for p in ROOT.iterdir() if p.is_dir()]))
    for top in [
        "01_组学_Omics",
        "02_遗传与变异_Genetics",
        "03_药物计算_DrugDiscovery",
        "04_临床预测与统计_ClinicalStats",
        "05_系统方法_SystemsMethods",
        PIPELINE_TOP,
        VALIDATION_TOP,
    ]:
        p = ROOT / top
        if p.exists():
            print(f"  {top}: {len([x for x in p.iterdir() if x.is_dir()])}")


if __name__ == "__main__":
    main()
