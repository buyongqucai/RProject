# -*- coding: utf-8 -*-
"""Migrate 01_样例_sample: nest 结果文件 under 代码文件; optional numbering."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

BIO = Path(r"E:\RProject\生信分析技能_BioinformaticsSkills")

# High-traffic samples to fully migrate (folder layout + path rewrite)
HIGH_TRAFFIC = [
    BIO / "00_基础_Foundation" / "统一交付规范_DeliveryStandards" / "01_样例_sample",
    BIO / "00_基础_Foundation" / "统一可视化规范_VizStandards" / "01_样例_sample",
    BIO / "01_组学_Omics" / "转录组分析_RNA-seq" / "01_样例_sample",
    BIO / "01_组学_Omics" / "公共库挖掘_GEO-TCGA" / "01_样例_sample",
    BIO / "01_组学_Omics" / "基因芯片表达分析_Microarray" / "01_样例_sample",
    BIO / "05_系统方法_SystemsMethods" / "基因集富集与通路_GSEA-Pathway" / "01_样例_sample",
    BIO / "04_临床预测与统计_ClinicalStats" / "生存分析与预后模型_Survival" / "01_样例_sample",
    BIO / "06_已落地流水线_ProductionPipelines" / "差异分析和UMAP流水线_DEG-UMAP" / "01_样例_sample",
]

NETPHARM = (
    BIO
    / "03_药物计算_DrugDiscovery"
    / "网络药理学_NetworkPharmacology"
    / "01_样例_sample"
)

# NetPharm figure rename map (basename without ext -> numbered stem)
NP_FIG = {
    "韦恩图_DiseaseDatabases_Venn": "01_韦恩图_DiseaseDatabases_Venn",
    "韦恩图_DrugDisease_Venn": "02_韦恩图_DrugDisease_Venn",
    "柱状图_PerHerbDiseaseOverlap_Bar": "03_柱状图_PerHerbDiseaseOverlap_Bar",
    "柱状图_CompoundDiseaseOverlap_Bar": "04_柱状图_CompoundDiseaseOverlap_Bar",
    "柱状图_CompoundDiseaseOverlapByHerb_Bar": "05_柱状图_CompoundDiseaseOverlapByHerb_Bar",
    "气泡图_GO_BPCCMF_Bubble": "06_气泡图_GO_BPCCMF_Bubble",
    "柱状图_GO_BPCCMF_Bar": "07_柱状图_GO_BPCCMF_Bar",
    "棒棒糖图_KEGG_Pathways_Lollipop": "08_棒棒糖图_KEGG_Pathways_Lollipop",
    "柱状图_KEGG_Pathways_Bar": "09_柱状图_KEGG_Pathways_Bar",
    "圈图_KEGG_Circos": "10_圈图_KEGG_Circos",
    "网络图_HerbCompoundTargetPathway_Network": "11_网络图_HerbCompoundTargetPathway_Network",
    "网络图_HerbCompoundTargetPathway_Ellipse_Network": "12_网络图_HerbCompoundTargetPathway_Ellipse_Network",
    "网络图_StringPPI_Network": "13_网络图_StringPPI_Network",
    "网络图_StringPPI_Concentric_Network": "14_网络图_StringPPI_Concentric_Network",
    "网络图_StringPPI_Degree_Network": "15_网络图_StringPPI_Degree_Network",
}

NP_TAB = {
    "审计后检_AuditPost.csv": "01_审计后检_AuditPost.csv",
    "药物疾病交集_DrugDiseaseOverlap.csv": "02_药物疾病交集_DrugDiseaseOverlap.csv",
    "单药疾病交集汇总_PerHerbOverlapSummary.csv": "03_单药疾病交集汇总_PerHerbOverlapSummary.csv",
    "全部单药靶点_AllHerbTargets.csv": "04_全部单药靶点_AllHerbTargets.csv",
    "全部单药疾病交集_AllHerbDiseaseOverlaps.csv": "05_全部单药疾病交集_AllHerbDiseaseOverlaps.csv",
    "成分疾病交集靶点_CompoundDiseaseOverlapTargets.csv": "06_成分疾病交集靶点_CompoundDiseaseOverlapTargets.csv",
    "成分疾病交集汇总_CompoundDiseaseOverlapSummary.csv": "07_成分疾病交集汇总_CompoundDiseaseOverlapSummary.csv",
    "成分疾病交集质控_CompoundOverlapQC.csv": "08_成分疾病交集质控_CompoundOverlapQC.csv",
    "成分靶点表_CompoundTargets.csv": "09_成分靶点表_CompoundTargets.csv",
    "疾病靶点按库_DiseaseGenesByDB.csv": "10_疾病靶点按库_DiseaseGenesByDB.csv",
    "疾病靶点按库_VennFull_DiseaseGenesByDB.csv": "11_疾病靶点按库_VennFull_DiseaseGenesByDB.csv",
    "交集核对_OverlapIntegrity.csv": "12_交集核对_OverlapIntegrity.csv",
    "网络边_HerbCompoundTargetPathway_Cytoscape.csv": "13_网络边_HerbCompoundTargetPathway_Cytoscape.csv",
    "网络节点_HerbCompoundTargetPathway_Cytoscape.csv": "14_网络节点_HerbCompoundTargetPathway_Cytoscape.csv",
    "网络边_CompoundGene_Cytoscape.csv": "15_网络边_CompoundGene_Cytoscape.csv",
    "网络节点_CompoundGene_Cytoscape.csv": "16_网络节点_CompoundGene_Cytoscape.csv",
    "网络边_network.csv": "17_网络边_network.csv",
    "网络节点类型_type.csv": "18_网络节点类型_type.csv",
    "PPI互作_StringInteractions_score900.tsv": "19_PPI互作_StringInteractions_score900.tsv",
    "PPI互作_StringInteractions.tsv": "20_PPI互作_StringInteractions.tsv",
    "外部图断点清单_ExternalFigureBreakpoints.csv": "21_外部图断点清单_ExternalFigureBreakpoints.csv",
}

NP_SCRIPTS = {
    "run_sample.R": "01_run_sample.R",
    "run_network_preview.R": "02_run_network_preview.R",
    "regen_hctp_layouts.R": "03_regen_hctp_layouts.R",
}

PATH_BLOCK_OLD = re.compile(
    r"data_dir\s*<-\s*file\.path\(sample_root,\s*\"数据文件\"\)\s*\n"
    r"fig_dir\s*<-\s*file\.path\(sample_root,\s*\"结果文件\",\s*\"图片文件\"\)\s*\n"
    r"tab_dir\s*<-\s*file\.path\(sample_root,\s*\"结果文件\",\s*\"数据文件\"\)\s*\n"
    r"rep_dir\s*<-\s*file\.path\(sample_root,\s*\"结果文件\",\s*\"报告文件\"\)\s*\n"
    r"for \(d in c\([^)]+\)\) dir\.create\(d, recursive = TRUE, showWarnings = FALSE\)",
    re.MULTILINE,
)

PATH_BLOCK_NEW = """paths <- delivery_sample_paths(sample_root)
data_dir <- paths$raw_dir
fig_dir <- paths$fig_dir
tab_dir <- paths$tab_dir
rep_dir <- paths$rep_dir
for (d in c(data_dir, fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)"""

README_STUB = """# 样例目录说明 / Sample layout

本样例已按 DeliveryStandards 约定：

- `数据文件/` = **原始/raw 输入 only**
- `代码文件/` = 脚本；**结果**在 `代码文件/结果文件/`
- 文件名可用流水线序号前缀 `01_`、`02_`…

规范 SSOT：`00_基础_Foundation/统一交付规范_DeliveryStandards/文档_docs/样例目录与命名_SampleLayoutNaming.md`

运行（若已编号）：

```bash
Rscript 代码文件/01_run_sample.R
```

若仍为 `run_sample.R`，则：

```bash
Rscript 代码文件/run_sample.R
```
"""


def move_results_under_code(sample: Path) -> str:
    legacy = sample / "结果文件"
    code = sample / "代码文件"
    nested = code / "结果文件"
    if not code.exists():
        return "skip_no_code"
    if nested.exists():
        if legacy.exists():
            return "nested_exists_legacy_remain"
        return "already_nested"
    if not legacy.exists():
        return "no_results"
    code.mkdir(parents=True, exist_ok=True)
    shutil.move(str(legacy), str(nested))
    return "moved"


def rename_map(dir_path: Path, mapping: dict[str, str], is_stem: bool = False) -> list[str]:
    done = []
    if not dir_path.exists():
        return done
    for p in list(dir_path.iterdir()):
        if not p.is_file():
            continue
        if is_stem:
            stem, ext = p.stem, p.suffix
            if stem in mapping:
                dest = dir_path / f"{mapping[stem]}{ext}"
                if dest != p and not dest.exists():
                    p.rename(dest)
                    done.append(f"{p.name} -> {dest.name}")
        else:
            if p.name in mapping:
                dest = dir_path / mapping[p.name]
                if dest != p and not dest.exists():
                    p.rename(dest)
                    done.append(f"{p.name} -> {dest.name}")
    return done


def patch_r_paths(sample: Path) -> list[str]:
    code = sample / "代码文件"
    patched = []
    if not code.exists():
        return patched
    for rfile in code.glob("*.R"):
        text = rfile.read_text(encoding="utf-8")
        orig = text
        # Ensure delivery source before paths if using delivery_sample_paths
        if "delivery_sample_paths" not in text and 'file.path(sample_root, "结果文件"' in text:
            # Replace common 4-line path block
            if PATH_BLOCK_OLD.search(text):
                text = PATH_BLOCK_OLD.sub(PATH_BLOCK_NEW, text)
            else:
                # looser replacements
                text = text.replace(
                    'fig_dir <- file.path(sample_root, "结果文件", "图片文件")',
                    "fig_dir <- paths$fig_dir",
                )
                text = text.replace(
                    'tab_dir <- file.path(sample_root, "结果文件", "数据文件")',
                    "tab_dir <- paths$tab_dir",
                )
                text = text.replace(
                    'rep_dir <- file.path(sample_root, "结果文件", "报告文件")',
                    "rep_dir <- paths$rep_dir",
                )
                text = text.replace(
                    'data_dir <- file.path(sample_root, "数据文件")',
                    "data_dir <- paths$raw_dir",
                )
                if "paths <- delivery_sample_paths" not in text and "paths$fig_dir" in text:
                    # insert after sample_root assignment block — find first data_dir/paths usage
                    text = text.replace(
                        "data_dir <- paths$raw_dir",
                        "paths <- delivery_sample_paths(sample_root)\ndata_dir <- paths$raw_dir",
                        1,
                    )
            # If paths used but PlotNaming not sourced yet, leave as-is (scripts usually source delivery first)
        # Fix fallback run_sample.R self-path after rename
        if text != orig:
            rfile.write_text(text, encoding="utf-8")
            patched.append(rfile.name)
    return patched


def write_readme(sample: Path) -> None:
    readme = sample / "README_样例目录.md"
    if not readme.exists():
        readme.write_text(README_STUB, encoding="utf-8")


def migrate_netpharm() -> dict:
    sample = NETPHARM
    report = {"sample": str(sample), "move": None, "figs": [], "tabs": [], "scripts": [], "patched": []}
    report["move"] = move_results_under_code(sample)
    code = sample / "代码文件"
    fig = code / "结果文件" / "图片文件"
    tab = code / "结果文件" / "数据文件"
    report["figs"] = rename_map(fig, NP_FIG, is_stem=True)
    report["tabs"] = rename_map(tab, NP_TAB, is_stem=False)
    for old, new in NP_SCRIPTS.items():
        src = code / old
        dst = code / new
        if src.exists() and not dst.exists():
            src.rename(dst)
            report["scripts"].append(f"{old} -> {new}")
    # Remove Rplots.pdf noise if present
    rp = code / "Rplots.pdf"
    if rp.exists():
        rp.unlink()
        report["scripts"].append("removed Rplots.pdf")
    write_readme(sample)
    return report


def migrate_high_traffic() -> list[dict]:
    out = []
    for sample in HIGH_TRAFFIC:
        if not sample.exists():
            out.append({"sample": str(sample), "status": "missing"})
            continue
        move = move_results_under_code(sample)
        # number run_sample.R if present and unnumbered
        code = sample / "代码文件"
        rs = code / "run_sample.R"
        rs01 = code / "01_run_sample.R"
        scripts = []
        if rs.exists() and not rs01.exists():
            rs.rename(rs01)
            scripts.append("run_sample.R -> 01_run_sample.R")
        patched = patch_r_paths(sample)
        # After rename, also patch 01_run_sample.R if paths still legacy
        for rfile in code.glob("*.R"):
            text = rfile.read_text(encoding="utf-8")
            orig = text
            if 'file.path(sample_root, "结果文件"' in text:
                text = text.replace(
                    'data_dir <- file.path(sample_root, "数据文件")',
                    "paths <- delivery_sample_paths(sample_root)\ndata_dir <- paths$raw_dir",
                )
                text = text.replace(
                    'fig_dir <- file.path(sample_root, "结果文件", "图片文件")',
                    "fig_dir <- paths$fig_dir",
                )
                text = text.replace(
                    'tab_dir <- file.path(sample_root, "结果文件", "数据文件")',
                    "tab_dir <- paths$tab_dir",
                )
                text = text.replace(
                    'rep_dir <- file.path(sample_root, "结果文件", "报告文件")',
                    "rep_dir <- paths$rep_dir",
                )
                # collapse duplicate paths <- if any
                text = re.sub(
                    r"paths <- delivery_sample_paths\(sample_root\)\s*\npaths <- delivery_sample_paths\(sample_root\)",
                    "paths <- delivery_sample_paths(sample_root)",
                    text,
                )
                if text != orig:
                    rfile.write_text(text, encoding="utf-8")
                    if rfile.name not in patched:
                        patched.append(rfile.name)
            # fix normalizePath("run_sample.R" -> 01
            if rfile.name.startswith("01_") and 'normalizePath("run_sample.R"' in text:
                text2 = text.replace(
                    'normalizePath("run_sample.R"',
                    'normalizePath("01_run_sample.R"',
                )
                if text2 != text:
                    rfile.write_text(text2, encoding="utf-8")
        write_readme(sample)
        out.append(
            {
                "sample": str(sample.relative_to(BIO)),
                "move": move,
                "scripts": scripts,
                "patched": patched,
                "status": "done",
            }
        )
    return out


def list_all_samples() -> list[Path]:
    return sorted(BIO.rglob("01_样例_sample"))


def main():
    np_report = migrate_netpharm()
    ht = migrate_high_traffic()
    # remaining: move only + README stub (lightweight)
    pending = []
    done_paths = {NETPHARM.resolve()} | {p.resolve() for p in HIGH_TRAFFIC if p.exists()}
    light = []
    for sample in list_all_samples():
        if sample.resolve() in done_paths:
            continue
        move = move_results_under_code(sample)
        write_readme(sample)
        # light path patch
        code = sample / "代码文件"
        patched = []
        if code.exists():
            for rfile in code.glob("*.R"):
                text = rfile.read_text(encoding="utf-8")
                orig = text
                if 'file.path(sample_root, "结果文件"' in text:
                    if "delivery_sample_paths" not in text:
                        text = text.replace(
                            'data_dir <- file.path(sample_root, "数据文件")',
                            "paths <- delivery_sample_paths(sample_root)\ndata_dir <- paths$raw_dir",
                        )
                    text = text.replace(
                        'fig_dir <- file.path(sample_root, "结果文件", "图片文件")',
                        "fig_dir <- paths$fig_dir",
                    )
                    text = text.replace(
                        'tab_dir <- file.path(sample_root, "结果文件", "数据文件")',
                        "tab_dir <- paths$tab_dir",
                    )
                    text = text.replace(
                        'rep_dir <- file.path(sample_root, "结果文件", "报告文件")',
                        "rep_dir <- paths$rep_dir",
                    )
                    text = re.sub(
                        r"paths <- delivery_sample_paths\(sample_root\)\s*\npaths <- delivery_sample_paths\(sample_root\)",
                        "paths <- delivery_sample_paths(sample_root)",
                        text,
                    )
                    if text != orig:
                        rfile.write_text(text, encoding="utf-8")
                        patched.append(rfile.name)
        status = "migrated_layout" if move == "moved" else move
        if move in ("moved", "already_nested"):
            light.append({"sample": str(sample.relative_to(BIO)), "move": move, "patched": patched})
        else:
            pending.append({"sample": str(sample.relative_to(BIO)), "move": move, "patched": patched})

    import json

    print(
        json.dumps(
            {"netpharm": np_report, "high_traffic": ht, "light": light, "other": pending},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
