# -*- coding: utf-8 -*-
"""Refresh 验证总报告 after cleaning legacy *_样例报告_*.html."""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(r"E:/RProject/生信分析技能_BioinformaticsSkills")
VAL = ROOT / "07_分类验证_Validation"


def has_cjk(name: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", name))


def main() -> None:
    total = ok = 0
    bad: list[str] = []
    for f in ROOT.rglob("*"):
        if "结果文件" not in str(f) or not f.is_file():
            continue
        if f.suffix.lower() not in {".csv", ".png", ".svg", ".html"}:
            continue
        total += 1
        if has_cjk(f.name):
            ok += 1
        else:
            bad.append(f.relative_to(ROOT).as_posix())

    results = []
    for p in sorted(ROOT.rglob("STATUS.txt")):
        if "结果文件" not in str(p):
            continue
        skill_dir = p.parents[3]
        rel = skill_dir.relative_to(ROOT).as_posix()
        status = p.read_text(encoding="utf-8", errors="replace").strip().splitlines()[0].strip()
        prefer = p.parent / "样例报告_SampleReport_v1.html"
        report = prefer.relative_to(ROOT).as_posix() if prefer.exists() else "—"
        results.append({"path": rel, "status": status, "report": report})

    ctr = Counter(r["status"] for r in results)
    now = datetime.now().isoformat(timespec="seconds")
    lines = [
        "# 验证总报告 / Per-Skill Sample Validation",
        "",
        f"- **更新时间**：{now}",
        "- **布局版本**：catalog + 统一交付规范（中英对照命名 Phase D）",
        f"- **本轮重跑数**：{len(results)}",
        f"- **PASS**：{ctr.get('PASS', 0)}",
        f"- **BLOCKED**：{ctr.get('BLOCKED', 0)}",
        f"- **FAIL**：{ctr.get('FAIL', 0)}",
        f"- **结果文件中英对照**：{ok}/{total}（无中文前缀剩余 {len(bad)}）",
        "",
        "## 关于 Cursor/Git「未跟踪 Untracked」",
        "",
        "「未跟踪」是 **Git 对尚未 `git add` / 未 commit 新文件** 的状态标记，**不是**文件扩展名。",
        "样例 `结果文件/` 产物默认未入库属正常；若需纳入版本库再由用户 `git add`。",
        "**不要擅自 `git commit`**，除非用户明确要求。详见",
        "`00_基础_Foundation/统一交付规范_DeliveryStandards/技能说明_统一交付规范_DeliveryStandards.md` §1。",
        "",
        "## 规范合规审计（Phase D）",
        "",
        "### 问1：执行样例时是否引用其它 skill 规范？",
        "",
        "**结论：是。** `run_sample.R` 强制按序 source：VizStandards → DeliveryStandards → 本技能 `脚本_scripts`。",
        "",
        "### 问2：文件命名",
        "",
        "**结论：强制** `{中文语义}_{EnglishCamelOrPascal}.{ext}`",
        "（例：`火山图_TreatVsControl_Volcano.png`、`审计后检_AuditPost.csv`、`样例报告_SampleReport_v1.html`）。",
        "禁止 `sample_*.csv` / `toy_*.csv` / 纯英文交付名。",
        "",
        "### 问3：期刊出图",
        "",
        "**结论：见 VizStandards** — DPI≥600、SVG+PNG、单栏约 85–90 mm、色盲友好、按分析类型选图。",
        "",
        "## 本轮重跑结果",
        "",
        "| 技能 | 状态 | 报告 |",
        "|------|------|------|",
    ]
    for r in results:
        lines.append(f"| `{r['path']}` | **{r['status']}** | `{r['report']}` |")
    lines += [
        "",
        "### FAIL 明细",
        "",
        "- （无）" if ctr.get("FAIL", 0) == 0 else "",
        "",
        "## 如何重跑",
        "",
        "```bash",
        "python E:/RProject/生信分析技能_BioinformaticsSkills/_phaseD_bilingual_naming.py",
        "```",
        "",
    ]
    VAL.mkdir(exist_ok=True)
    (VAL / "验证总报告.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    (VAL / "phaseD_bilingual_results.json").write_text(
        json.dumps(
            {
                "generated_at": now,
                "results": results,
                "naming": {
                    "total": total,
                    "with_cjk": ok,
                    "without_cjk": len(bad),
                    "bad_examples": bad[:20],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("skills", len(results), dict(ctr), "naming", ok, "/", total, "bad", len(bad))


if __name__ == "__main__":
    main()
