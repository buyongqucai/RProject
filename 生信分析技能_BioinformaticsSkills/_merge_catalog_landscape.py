# -*- coding: utf-8 -*-
"""Merge generated skills into catalog; write landscape, workflows, index helpers."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    meta = json.loads((ROOT / "_generated_skills_meta.json").read_text(encoding="utf-8"))
    cat_path = ROOT / "技能目录_skill-catalog.json"
    cat = json.loads(cat_path.read_text(encoding="utf-8-sig"))
    existing_ids = {s["id"] for s in cat["skills"]}

    for s in cat["skills"]:
        s.setdefault("research_intents", s.get("triggers", []))
        s.setdefault("data_types", [])
        s.setdefault("inputs", [])
        s.setdefault("outputs", [])
        s.setdefault("r_packages", [])
        s.setdefault("cli_tools", [])
        s.setdefault("combines_with", [])
        s.setdefault("requires", s.get("depends_on", []))

    if not any(s["id"] == "bioinfo-research-orchestrator" for s in cat["skills"]):
        cat["skills"].insert(
            1,
            {
                "id": "bioinfo-research-orchestrator",
                "path": "00_基础_Foundation/研究方案编排_ResearchOrchestrator",
                "doc": "技能说明_研究方案编排_ResearchOrchestrator.md",
                "title_zh": "研究方案编排",
                "title_en": "ResearchOrchestrator",
                "triggers": ["研究目的", "分析方案"],
                "research_intents": ["方案规划"],
                "data_types": [],
                "inputs": [],
                "outputs": ["7章计划"],
                "r_packages": [],
                "cli_tools": [],
                "combines_with": ["*"],
                "requires": [],
                "depends_on": [],
            },
        )

    new_n = 0
    for m in meta:
        if m["id"] in existing_ids:
            continue
        requires = ["bioinfo-viz-standards"]
        folder = m["folder"]
        if any(x in folder for x in ("公共", "Survival", "荟萃", "液体", "GEO")):
            requires.append("data-authenticity-verification")
        cat["skills"].append(
            {
                "id": m["id"],
                "path": m["path"],
                "doc": m["doc"],
                "title_zh": m["title_zh"],
                "title_en": m["title_en"],
                "triggers": m["research_intents"][:8],
                "research_intents": m["research_intents"],
                "data_types": m["data_types"],
                "inputs": m["data_types"],
                "outputs": ["结果表", "出版级图"],
                "r_packages": m["r_packages"],
                "cli_tools": m["cli_tools"],
                "combines_with": [],
                "requires": requires,
                "depends_on": requires,
                "section": m["section"],
                "priority": m["priority"],
                "purpose_layer": m.get("purpose_layer", ""),
            }
        )
        existing_ids.add(m["id"])
        new_n += 1

    # GEO crosslink
    for s in cat["skills"]:
        if s["id"] == "bioinfo-geo-tcga":
            s["combines_with"] = list(
                dict.fromkeys(
                    (s.get("combines_with") or [])
                    + [
                        "bioinfo-survival",
                        "bioinfo-meta-analysis",
                        "bioinfo-diagnostic-roc",
                        "bioinfo-rnaseq",
                    ]
                )
            )
            s["outputs"] = ["队列矩阵", "元数据", "可接 Survival/Meta/ROC"]

    cat_path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("catalog total", len(cat["skills"]), "newly added", new_n)

    # Landscape
    lines = [
        "# 技能全景清单 / Skill Landscape",
        "",
        "SSOT：本文件 + `技能目录_skill-catalog.json`。",
        "结构：`00_基础_Foundation` / `01_组学_Omics` / `06_已落地流水线_ProductionPipelines`（不改顶层）。",
        "原则：**一方法一技能**；山水用途层：病因/药物 × 基因/代谢物/细胞。",
        "",
        "## 已有核心",
        "",
        "| 区 | 技能 |",
        "|----|------|",
        "| 基础 | 研究方案编排、统一可视化、数据真实性 |",
        "| 组学 | 转录组、单细胞/空转、ChIP、蛋白、代谢、16S、GWAS、GEO-TCGA、多组学 |",
        "| 流水线 | 差异分析与UMAP（DEG-UMAP） |",
        "",
        "## 本轮新建（按优先级）",
        "",
        "| 优先级 | 目录 | 用途层 |",
        "|--------|------|--------|",
    ]
    for m in sorted(meta, key=lambda x: (x["priority"], x["folder"])):
        lines.append(
            f"| {m['priority']} | `{m['folder']}` | {m.get('purpose_layer', '')} |"
        )
    lines += [
        "",
        "## 并入关系",
        "",
        "- EPIC/450K → `DNA甲基化分析_WGBS-RRBS`",
        "- 富集作图 → `基因集富集与通路_GSEA-Pathway`",
        "- GEO-TCGA 保留下载/队列；生存/荟萃/ROC 用独立技能",
        "- DEG-UMAP 延展 → GSEA / WGCNA / 细胞通讯 / TF / 虚拟敲除 / 跨物种 独立技能",
        "",
        f"本轮新建目录数：**{len(meta)}**；目录条目总数见 skill-catalog。",
        "",
    ]
    (ROOT / "技能全景清单_SkillLandscape.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print("landscape written")

    # Workflows
    wf_path = ROOT / "工作流_workflows.json"
    wf = json.loads(wf_path.read_text(encoding="utf-8-sig"))
    extra = [
        {
            "id": "wf-drug-target-gene",
            "title_zh": "药物-基因层：网络药理→对接→MD",
            "title_en": "Drug target gene chain",
            "research_intents": ["药靶", "中药", "分子对接", "网络药理", "MD"],
            "skill_ids": [
                "bioinfo-research-orchestrator",
                "bioinfo-network-pharmacology",
                "bioinfo-protein-structure",
                "bioinfo-molecular-docking",
                "bioinfo-molecular-dynamics",
                "bioinfo-admet",
                "bioinfo-viz-standards",
            ],
            "notes": "山水药物-基因层；对接后可选 MD；ADMET 作筛选漏斗。",
        },
        {
            "id": "wf-prognosis-survival",
            "title_zh": "预后：GEO队列→生存/ROC",
            "title_en": "Prognosis survival ROC",
            "research_intents": ["预后", "生存", "Cox", "ROC"],
            "skill_ids": [
                "bioinfo-research-orchestrator",
                "data-authenticity-verification",
                "bioinfo-geo-tcga",
                "bioinfo-survival",
                "bioinfo-diagnostic-roc",
                "bioinfo-viz-standards",
            ],
            "notes": "GEO-TCGA 只做队列；KM/Cox/ROC 走独立技能。",
        },
        {
            "id": "wf-immune-therapy",
            "title_zh": "免疫微环境与治疗相关",
            "title_en": "Immune infiltration",
            "research_intents": ["免疫浸润", "TIDE", "CIBERSORT"],
            "skill_ids": [
                "bioinfo-research-orchestrator",
                "bioinfo-immune-infiltration",
                "bioinfo-survival",
                "bioinfo-scrna-spatial",
                "bioinfo-viz-standards",
            ],
            "notes": "bulk 浸润 + 可选单细胞验证 + 生存。",
        },
        {
            "id": "wf-methylation-rna",
            "title_zh": "甲基化 + 转录",
            "title_en": "Methylation RNA",
            "research_intents": ["甲基化", "EPIC", "WGBS"],
            "skill_ids": [
                "bioinfo-research-orchestrator",
                "bioinfo-methylation",
                "bioinfo-rnaseq",
                "bioinfo-gsea-pathway",
                "bioinfo-viz-standards",
            ],
            "notes": "DMR 与 DEG 同通路叙事。",
        },
        {
            "id": "wf-cerna-mir",
            "title_zh": "ceRNA / miRNA 调控轴",
            "title_en": "ceRNA miRNA",
            "research_intents": ["ceRNA", "miRNA", "非编码"],
            "skill_ids": [
                "bioinfo-research-orchestrator",
                "bioinfo-ncrna",
                "bioinfo-cerna",
                "bioinfo-rnaseq",
                "bioinfo-viz-standards",
            ],
            "notes": "对齐山水 miR 证据链。",
        },
    ]
    have = {w["id"] for w in wf["workflows"]}
    for e in extra:
        if e["id"] not in have:
            wf["workflows"].append(e)
    wf_path.write_text(json.dumps(wf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("workflows", len(wf["workflows"]))


if __name__ == "__main__":
    main()
