# -*- coding: utf-8 -*-
"""Resplit SkillFileAudit into one ticket per skill."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(r"E:/RProject")
BIO = ROOT / "生信分析技能_BioinformaticsSkills"
FEAT = ROOT / ".scratch" / "技能逐文件审计_SkillFileAudit"
ISSUES = FEAT / "issues"
ARCHIVE = FEAT / "_归档" / "issues_by_category"
CHECKLIST = FEAT / "清单_checklist"

# Foundation skills completed in prior batch (match folder names under 00_基础_Foundation)
DONE_FOUNDATION = {
    p.name
    for p in (ROOT / "生信分析技能_BioinformaticsSkills" / "00_基础_Foundation").iterdir()
    if p.is_dir() and list(p.glob("技能说明_*.md"))
}


def en_slug(folder: str) -> str:
    m = re.search(r"_([A-Za-z0-9][A-Za-z0-9\-]*)$", folder)
    if m:
        return m.group(1)
    return re.sub(r"[^\w\-]+", "-", folder)[:40]


def main() -> None:
    entries = sorted(BIO.rglob("技能说明_*.md"))
    skills = [(e.parent.name, e.parent.relative_to(BIO).as_posix(), e.parent) for e in entries]
    assert len(skills) == 70, len(skills)

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    ISSUES.mkdir(parents=True, exist_ok=True)

    # Archive old category / summary tickets
    for p in list(ISSUES.glob("*.md")):
        shutil.move(str(p), str(ARCHIVE / p.name))

    board_rows = []
    for i, (name, rel, path) in enumerate(skills, start=1):
        nn = f"{i:02d}"
        slug = en_slug(name)
        fname = f"{nn}-audit-{slug}.md"
        checklist = CHECKLIST / f"{name}.md"
        done = name in DONE_FOUNDATION
        label = "已完成" if done else "待Agent处理"
        blocked = "None（可立即开始）"
        checks = (
            "- [x] 清单总评已填\n"
            "- [x] 小修已落地或无需小修\n"
            "- [x] BOARD 本行已更新\n"
            if done
            else "- [ ] 打开并填完对应清单（逐文件）\n"
            "- [ ] 小修当场改；大修另开子单\n"
            "- [ ] 清单总评 ≠ 待填；更新 BOARD\n"
        )
        note = ""
        if done:
            note = "\n## Notes\n\nFoundation 批次已审（2026-09-06）；Delivery 细则已披露到命名门禁文档。\n"
        frozen = ""
        if "MolecularDocking" in name or "MolecularDynamics" in name or "NetworkPharmacology" in name:
            frozen = "\n- FROZEN 技能：只查双源/指针，不解冻改视觉\n"

        body = f"""# {nn}: 审计 {name}

**类别:** enhancement
**标签:** {label}
**Blocked by:** {blocked}
**技能路径:** `{rel}`
**清单:** `清单_checklist/{name}.md`

**What to build:** 按 `docs/agents/技能范式清单_SkillParadigm.md` 对该技能 **逐文件** 勾选并必要小修，使清单总评可归档。

{checks}{frozen}{note}"""
        (ISSUES / fname).write_text(body, encoding="utf-8")
        board_rows.append((nn, name, slug, label, fname))

    # BOARD
    lines = [
        "# BOARD — 技能逐文件审计（一技能一工单）\n\n",
        f"**总数:** {len(board_rows)}  |  **已完成:** {sum(1 for r in board_rows if r[3]=='已完成')}  |  "
        f"**待Agent处理:** {sum(1 for r in board_rows if r[3]=='待Agent处理')}\n\n",
        "| NN | 技能 | 标签 | 工单文件 |\n|----|------|------|----------|\n",
    ]
    for nn, name, slug, label, fname in board_rows:
        lines.append(f"| {nn} | `{name}` | {label} | `{fname}` |\n")

    frontier = [r for r in board_rows if r[3] == "待Agent处理"][:5]
    lines.append("\n**Frontier（示例前 5 张待办）:** " + ", ".join(f"{r[0]}-{r[2]}" for r in frontier) + "\n")
    lines.append("\n旧「按类别」工单已移至 `_归档/issues_by_category/`。\n")
    (FEAT / "BOARD.md").write_text("".join(lines), encoding="utf-8")

    readme = f"""# 技能逐文件审计（70）

**标签:** 待Agent处理（进行中）
**类别:** enhancement
**日期:** 2026-09-06
**粒度:** **一技能一工单**（你已确认）

## Goal

对每个领域技能按 [`技能范式清单_SkillParadigm.md`](../../docs/agents/技能范式清单_SkillParadigm.md) **逐文件**勾选；小修当场改，大修开子单。

## 方法

1. `python .scratch/技能逐文件审计_SkillFileAudit/scripts/gen_checklists.py` — 刷新清单骨架
2. 认领 `issues/NN-audit-*.md`（标签 `待Agent处理`，Blocked by 均为 None → 可并行）
3. 填 `清单_checklist/<技能文件夹>.md` → 工单标 `已完成` → 更新 `BOARD.md`
4. 可选：`python .scratch/技能逐文件审计_SkillFileAudit/scripts/regen_per_skill_tickets.py` — 重建工单（慎用）

## 进度

见 [`BOARD.md`](BOARD.md)。Foundation 9 张已标完成；其余 61 张待认领。

## Out of scope

- 不重跑全部样例（除非清单要求且你点名）
- 不解冻 FROZEN（除非单独口令）
"""
    (FEAT / "README.md").write_text(readme, encoding="utf-8")
    print(f"wrote {len(board_rows)} tickets; done={sum(1 for r in board_rows if r[3]=='已完成')}")


if __name__ == "__main__":
    main()
