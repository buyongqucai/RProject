# -*- coding: utf-8 -*-
"""Rebuild catalog + landscape + index + workflows after taxonomy merge."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OMICS = ROOT / "01_组学_Omics"
FOUND = ROOT / "00_基础_Foundation"
PIPE = ROOT / "06_已落地流水线_ProductionPipelines"


def parse_frontmatter(md_path: Path) -> dict:
    text = md_path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    name = md_path.parent.name
    sid = None
    desc = ""
    if m:
        block = m.group(1)
        nm = re.search(r"^name:\s*(\S+)", block, re.M)
        if nm:
            sid = nm.group(1).strip()
        # description first line after description: >-
        dm = re.search(r"description:\s*>-\s*\n((?:  .*\n)+)", block)
        if dm:
            desc = " ".join(x.strip() for x in dm.group(1).splitlines())
    if not sid:
        sid = "bioinfo-" + re.sub(r"[^a-z0-9]+", "-", name.split("_")[-1].lower()).strip("-")
    return {"id": sid, "desc": desc, "folder": name, "text": text}


def collect_skills() -> list[dict]:
    skills = []
    # group
    skills.append(
        {
            "id": "bioinfo-skill-group",
            "path": ".",
            "doc": "技能组总说明_BioinformaticsSkills.md",
            "title_zh": "生信分析技能",
            "title_en": "BioinformaticsSkills",
            "triggers": ["生信", "组学"],
            "research_intents": ["路由"],
            "data_types": [],
            "inputs": [],
            "outputs": [],
            "r_packages": [],
            "cli_tools": [],
            "combines_with": [],
            "requires": [],
            "depends_on": [],
        }
    )
    for base in (FOUND, OMICS, PIPE):
        if not base.exists():
            continue
        for d in sorted(base.iterdir()):
            if not d.is_dir():
                continue
            docs = list(d.glob("技能说明_*.md"))
            if not docs:
                continue
            doc = docs[0]
            meta = parse_frontmatter(doc)
            rel = str(d.relative_to(ROOT)).replace("\\", "/")
            parts = d.name.split("_", 1)
            zh = parts[0]
            en = parts[1] if len(parts) > 1 else parts[0]
            # extract triggers from description roughly
            triggers = re.findall(r"触发：([^。\n]+)", meta["desc"])
            trig_list = []
            if triggers:
                trig_list = [t.strip() for t in re.split(r"[,，、]", triggers[0]) if t.strip()]
            if not trig_list:
                trig_list = [zh, en]
            requires = ["bioinfo-viz-standards"]
            if any(x in d.name for x in ("GEO", "公共", "Survival", "液体", "真实性")):
                if "真实性" not in d.name and "可视化" not in d.name and "编排" not in d.name:
                    requires.append("data-authenticity-verification")
            if "编排" in d.name or "真实性" in d.name or "可视化" in d.name:
                requires = [] if "编排" in d.name or "真实性" in d.name else []
            if "可视化" in d.name:
                requires = []
            if "编排" in d.name:
                requires = []
            if "真实性" in d.name:
                requires = []
            skills.append(
                {
                    "id": meta["id"],
                    "path": rel,
                    "doc": doc.name,
                    "title_zh": zh,
                    "title_en": en,
                    "triggers": trig_list[:10],
                    "research_intents": trig_list[:10],
                    "data_types": [],
                    "inputs": [],
                    "outputs": ["结果表", "出版级图"],
                    "r_packages": [],
                    "cli_tools": [],
                    "combines_with": [],
                    "requires": requires,
                    "depends_on": requires,
                }
            )
    return skills


def main():
    merge_map = json.loads((ROOT / "_merge_map.json").read_text(encoding="utf-8"))
    skills = collect_skills()
    cat = {
        "group": "生信分析技能_BioinformaticsSkills",
        "root": "生信分析技能_BioinformaticsSkills",
        "project_path": "E:/RProject/生信分析技能_BioinformaticsSkills",
        "cursor_entry": ".cursor/skills/生信分析技能_BioinformaticsSkills/SKILL.md",
        "naming_rule": "中文_English",
        "skill_doc_pattern": "技能说明_<文件夹名>.md",
        "group_doc": "技能组总说明_BioinformaticsSkills.md",
        "naming_spec": "项目结构规范_ProjectLayout.md",
        "workflows_file": "工作流_workflows.json",
        "landscape_file": "技能全景清单_SkillLandscape.md",
        "deprecated_folders": merge_map["deprecated_folders"],
        "viz_rules": {
            "min_dpi": 600,
            "formats": ["svg", "png"],
            "cjk": True,
            "no_label_overlap": True,
        },
        "skills": skills,
    }
    # GEO combines
    for s in skills:
        if s["id"] == "bioinfo-geo-tcga":
            s["combines_with"] = [
                "bioinfo-survival",
                "bioinfo-meta-analysis",
                "bioinfo-diagnostic-roc",
                "bioinfo-rnaseq",
            ]
            s["requires"] = [
                "bioinfo-viz-standards",
                "data-authenticity-verification",
            ]
            s["depends_on"] = s["requires"]

    (ROOT / "技能目录_skill-catalog.json").write_text(
        json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("catalog skills", len(skills))

    # Landscape exclusive table
    # categorize by path keywords
    cats_order = [
        ("基础", ["Foundation", "研究方案", "可视化", "真实性", "实验设计", "批次", "文献", "可复现", "NGS质控"]),
        ("数据获取", ["公共库", "GEO-TCGA"]),
        ("基因组变异", ["变异", "CNV", "结构变异", "组装", "长读长", "融合", "肿瘤体细胞"]),
        ("转录调控", ["转录组", "剪接", "非编码", "Ribo", "RNA编辑", "TF", "ATAC", "甲基化", "三维基因组", "新生", "剂量", "芯片", "表观"]),
        ("单细胞空间", ["单细胞", "空间", "细胞通讯", "scRNA", "CyTOF", "多组学_sc"]),
        ("蛋白代谢", ["蛋白", "代谢", "糖组"]),
        ("微生物", ["16S", "宏基因组", "Microbiome"]),
        ("免疫肿瘤", ["免疫", "新抗原", "分子分型"]),
        ("系统方法", ["GSEA", "WGCNA", "PPI", "孟德尔", "遗传关联下游", "机器学习", "荟萃", "跨物种", "多组学联合", "CRISPR", "虚拟敲除"]),
        ("药物计算", ["网络药理", "对接", "动力学", "结构与建模", "类药", "CMap", "GDSC", "药敏"]),
        ("临床预测", ["生存", "诊断", "液体", "放射"]),
        ("生产流水线", ["DEG-UMAP", "差异分析与UMAP"]),
    ]

    def bucket(path: str, title: str) -> str:
        blob = path + title
        for name, keys in cats_order:
            for k in keys:
                if k in blob:
                    return name
        return "其它"

    lines = [
        "# 技能全景清单 / Skill Landscape（去重后互斥分类）",
        "",
        "SSOT：本文件 + `技能目录_skill-catalog.json`。",
        "原则：可合并则合并；一方法一技能；边界写清「不包含」。",
        "",
        f"当前技能文档数：**{len(skills)-1}**（不含组入口）；已弃用目录见 catalog.`deprecated_folders`。",
        "",
    ]
    by = {n: [] for n, _ in cats_order}
    by["其它"] = []
    for s in skills:
        if s["id"] == "bioinfo-skill-group":
            continue
        b = bucket(s["path"], s["title_zh"])
        by.setdefault(b, []).append(s)

    for name, _ in cats_order:
        lines.append(f"## {name}")
        lines.append("")
        lines.append("| 技能目录 | id | 触发词摘要 |")
        lines.append("|----------|-----|------------|")
        for s in sorted(by.get(name, []), key=lambda x: x["path"]):
            folder = s["path"].split("/")[-1]
            trig = "、".join(s["triggers"][:5])
            lines.append(f"| `{folder}` | `{s['id']}` | {trig} |")
        lines.append("")

    if by.get("其它"):
        lines.append("## 其它")
        lines.append("")
        lines.append("| 技能目录 | id |")
        lines.append("|----------|-----|")
        for s in by["其它"]:
            lines.append(f"| `{s['path'].split('/')[-1]}` | `{s['id']}` |")
        lines.append("")

    lines += [
        "## 已合并（deprecated → 现行）",
        "",
        "| 旧目录 | 并入 |",
        "|--------|------|",
    ]
    for old, new in sorted(merge_map["deprecated_folders"].items()):
        lines.append(f"| `{old}` | `{new}` |")
    lines += [
        "",
        "## 明确不合并（边界）",
        "",
        "- 网络药理 / 分子对接 / 分子动力学",
        "- ATAC vs 表观峰检测(ChIP/CUT&Tag)",
        "- Survival / Meta / ROC / ML-Biomarker",
        "- CMap vs GDSC 药敏",
        "- RNA 融合 vs DNA SV",
        "- GEO-TCGA（下载队列）vs Survival",
        "",
    ]
    (ROOT / "技能全景清单_SkillLandscape.md").write_text("\n".join(lines), encoding="utf-8")
    print("landscape ok")

    # Index
    index = """# 生信分析技能 INDEX / Bioinformatics Skills Index

实体根：`E:/RProject/生信分析技能_BioinformaticsSkills/`  
全景（去重后）：[技能全景清单_SkillLandscape.md](技能全景清单_SkillLandscape.md)  
目录：[技能目录_skill-catalog.json](技能目录_skill-catalog.json)  
工作流：[工作流_workflows.json](工作流_workflows.json)  
验证沙盒：[07_分类验证_Validation/](07_分类验证_Validation/)

## 按研究目的

| 研究目的 | 技能组合 |
|----------|----------|
| 任意方案 | 研究方案编排 |
| 机制+细胞 | scRNA-Spatial → 转录组 ± 细胞通讯 ± 单细胞进阶 |
| 预后标志物 | GEO-TCGA → 生存 ± 诊断ROC |
| 药物靶点 | 网络药理 → 蛋白结构与建模 → 分子对接 → 分子动力学 ± 类药性与QSAR |
| 代谢脂质 | 代谢组分析（含脂质/通量） ± 转录组 |
| 甲基化 | DNA甲基化 ± 转录组 ± GSEA |
| ncRNA/ceRNA | 非编码与ceRNA ± 转录组 |
| 免疫 | 免疫浸润 ± 生存 ± 单细胞 |
| 群落病原 | 宏基因组与病原 或 16S |
| 四数据集生产 | DEG-UMAP 流水线 |

## 弃用目录

见 `技能目录_skill-catalog.json` → `deprecated_folders`（勿再新建同名技能）。
"""
    (ROOT / "索引_INDEX.md").write_text(index, encoding="utf-8")

    # Workflows — update drug and others to new ids
    wf = {
        "group": "生信分析技能_BioinformaticsSkills",
        "description": "去重后工作流模板",
        "orchestrator": "00_基础_Foundation/研究方案编排_ResearchOrchestrator/技能说明_研究方案编排_ResearchOrchestrator.md",
        "workflows": [
            {
                "id": "wf-drug-target-gene",
                "title_zh": "药物-基因层：网络药理→对接→MD",
                "skill_ids": [
                    "bioinfo-research-orchestrator",
                    "bioinfo-network-pharmacology",
                    "bioinfo-protein-structure",
                    "bioinfo-molecular-docking",
                    "bioinfo-molecular-dynamics",
                    "bioinfo-admet-qsar",
                    "bioinfo-viz-standards",
                ],
                "notes": "结构与建模已合并；ADMET+QSAR 已合并。",
            },
            {
                "id": "wf-prognosis-survival",
                "title_zh": "预后：GEO→生存/ROC",
                "skill_ids": [
                    "bioinfo-research-orchestrator",
                    "data-authenticity-verification",
                    "bioinfo-geo-tcga",
                    "bioinfo-survival",
                    "bioinfo-diagnostic-roc",
                    "bioinfo-viz-standards",
                ],
            },
            {
                "id": "wf-mechanism-scrna",
                "title_zh": "机制+单细胞",
                "skill_ids": [
                    "bioinfo-research-orchestrator",
                    "data-authenticity-verification",
                    "bioinfo-scrna-spatial",
                    "bioinfo-scrna-advanced",
                    "bioinfo-cell-communication",
                    "bioinfo-rnaseq",
                    "bioinfo-viz-standards",
                ],
            },
            {
                "id": "wf-metabolomics-rna",
                "title_zh": "代谢脂质+转录",
                "skill_ids": [
                    "bioinfo-research-orchestrator",
                    "bioinfo-metabolomics",
                    "bioinfo-rnaseq",
                    "bioinfo-gsea-pathway",
                    "bioinfo-viz-standards",
                ],
            },
            {
                "id": "wf-cerna-mir",
                "title_zh": "非编码与ceRNA",
                "skill_ids": [
                    "bioinfo-research-orchestrator",
                    "bioinfo-ncrna-cerna",
                    "bioinfo-rnaseq",
                    "bioinfo-viz-standards",
                ],
            },
            {
                "id": "wf-metagenome",
                "title_zh": "宏基因组与病原",
                "skill_ids": [
                    "bioinfo-research-orchestrator",
                    "bioinfo-metagenome-pathogen",
                    "bioinfo-viz-standards",
                ],
            },
            {
                "id": "wf-scm-deg-umap",
                "title_zh": "脓毒症心肌病四数据集",
                "skill_ids": [
                    "bioinfo-research-orchestrator",
                    "data-authenticity-verification",
                    "differential-analysis-and-umap",
                    "bioinfo-viz-standards",
                ],
            },
        ],
    }
    (ROOT / "工作流_workflows.json").write_text(
        json.dumps(wf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("workflows", len(wf["workflows"]))


if __name__ == "__main__":
    main()
