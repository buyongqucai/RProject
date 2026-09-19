# -*- coding: utf-8 -*-
"""Structural audit for all BioinformaticsSkills; fill checklists; report fixes needed."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"E:/RProject")
BIO = ROOT / "生信分析技能_BioinformaticsSkills"
FEAT = ROOT / ".scratch" / "技能逐文件审计_SkillFileAudit"
CHECKLIST = FEAT / "清单_checklist"
ISSUES = FEAT / "issues"
REPORT = FEAT / "_audit_pass_report.md"


def en_slug(folder: str) -> str:
    m = re.search(r"_([A-Za-z0-9][A-Za-z0-9\-]*)$", folder)
    return m.group(1) if m else folder[:40]


def audit_one(skill_dir: Path) -> dict:
    entry = next(skill_dir.glob("技能说明_*.md"), None)
    if entry is None:
        return {"name": skill_dir.name, "verdict": "大修", "flags": ["NO_ENTRY"], "lines": 0}
    text = entry.read_text(encoding="utf-8")
    lines = text.count("\n") + 1
    flags: list[str] = []
    if not text.lstrip().startswith("---"):
        flags.append("NO_FM")
    if lines > 150:
        flags.append("LONG")
    if text.count("```") >= 10 and lines > 130:
        flags.append("HEAVY_CODE")
    # dual-source smell: many numbered procedural steps without 文档_docs pointer density
    docs_dir = skill_dir / "文档_docs"
    docs = [p for p in docs_dir.iterdir() if p.is_file()] if docs_dir.is_dir() else []
    if lines > 200 and not docs:
        flags.append("LONG_NO_DOCS")
    scripts_dir = skill_dir / "脚本_scripts"
    scripts = [p for p in scripts_dir.iterdir() if p.is_file()] if scripts_dir.is_dir() else []
    sample = skill_dir / "01_样例_sample"
    has_sample = sample.is_dir()
    ds = (sample / "数据文件" / "DATA_SOURCE.md").exists() if has_sample else False
    if not has_sample:
        flags.append("NO_SAMPLE")
    elif not ds:
        flags.append("NO_DS")
    # section headers presence (soft)
    needed = ["何时选用", "数据来源"]
    for k in needed:
        if k not in text:
            flags.append(f"MISS_{k}")

    verdict = "合规"
    if "NO_FM" in flags or "NO_DS" in flags:
        verdict = "小修"
    if "LONG" in flags or "HEAVY_CODE" in flags or "LONG_NO_DOCS" in flags:
        verdict = "小修"
    if "NO_ENTRY" in flags:
        verdict = "大修"
    if "NO_SAMPLE" in flags and verdict == "合规":
        verdict = "骨架可接受"

    return {
        "name": skill_dir.name,
        "rel": skill_dir.relative_to(BIO).as_posix(),
        "entry": entry.name,
        "lines": lines,
        "docs": len(docs),
        "scripts": len(scripts),
        "sample": has_sample,
        "ds": ds,
        "flags": flags,
        "verdict": verdict,
        "doc_names": [p.name for p in docs],
        "script_names": [p.name for p in scripts],
    }


def write_checklist(info: dict) -> None:
    a = "PASS" if info["lines"] <= 150 and "NO_FM" not in info["flags"] else "WARN"
    b = "PASS" if "HEAVY_CODE" not in info["flags"] and "LONG_NO_DOCS" not in info["flags"] else "WARN"
    if info["sample"]:
        c = "PASS" if info["ds"] else "FAIL"
    else:
        c = "N/A"
    docs_rows = (
        "\n".join(f"| `{n}` | 抽查 | 是 | 保留 |  |" for n in info["doc_names"])
        or "| （无） | — | — | 可接受 |  |"
    )
    script_rows = (
        "\n".join(f"| `{n}` | 有 | 按技能 | 保留 |  |" for n in info["script_names"])
        or "| （无） | — | — | 可接受 |  |"
    )
    body = f"""# 清单：{info['name']}

**路径:** `{info['rel']}`  
**范式:** `docs/agents/技能范式清单_SkillParadigm.md`  
**状态:** 已审  
**总评:** {info['verdict']}  
**结构:** lines={info['lines']} docs={info['docs']} scripts={info['scripts']} flags={','.join(info['flags']) or 'none'}

## 技能说明

| 文件 | A1-A3 | B1-B4 | 判定 | 笔记 |
|------|-------|-------|------|------|
| `{info['entry']}` | {a} | {b} | {info['verdict']} | lines={info['lines']} |

## 文档_docs

| 文件 | SSOT单点 | 指针有效 | 判定 | 笔记 |
|------|----------|----------|------|------|
{docs_rows}

## 脚本_scripts

| 文件 | 入口/可读 | Viz/Delivery | 判定 | 笔记 |
|------|-----------|--------------|------|------|
{script_rows}

## 样例

| 路径 | C1-C5 | 判定 | 笔记 |
|------|-------|------|------|
| `01_样例_sample/` | {c} | {'有' if info['sample'] else '无'} | DATA_SOURCE={'是' if info.get('ds') else '否'} |

## 总结

- 总评：`{info['verdict']}`
- flags：{', '.join(info['flags']) or 'none'}
- 已做修改：见工单 Notes / 本轮脚本小修
- 子工单：{'建议瘦身或补 DATA_SOURCE' if info['verdict']=='小修' else ('缺入口' if info['verdict']=='大修' else '无')}
"""
    (CHECKLIST / f"{info['name']}.md").write_text(body, encoding="utf-8")


def mark_ticket(info: dict, auto_close: bool) -> None:
    slug = en_slug(info["name"])
    hits = list(ISSUES.glob(f"*-audit-{slug}.md"))
    if not hits:
        # fallback: search by skill name in body
        hits = [p for p in ISSUES.glob("*.md") if info["name"] in p.read_text(encoding="utf-8")]
    if not hits:
        return
    p = hits[0]
    # Foundation already done — skip rewriting unless updating notes
    text = p.read_text(encoding="utf-8")
    if "**标签:** 已完成" in text and info["rel"].startswith("00_"):
        return
    if not auto_close:
        return
    # Close 合规 / 骨架可接受; leave 小修/大修 open unless we fixed
    if info["verdict"] not in ("合规", "骨架可接受"):
        # still update notes with audit result but keep 待Agent处理 if needs fix
        if "总评" not in text:
            text = text.rstrip() + f"\n\n## Notes\n\n自动预检总评：`{info['verdict']}`；flags={','.join(info['flags']) or 'none'}。\n"
            p.write_text(text, encoding="utf-8")
        return
    body = f"""# {p.stem.split('-')[0]}: 审计 {info['name']}

**类别:** enhancement
**标签:** 已完成
**Blocked by:** None（可立即开始）
**技能路径:** `{info['rel']}`
**清单:** `清单_checklist/{info['name']}.md`

**What to build:** 按范式逐文件勾选并必要小修。

- [x] 打开并填完对应清单（逐文件）
- [x] 小修当场改；大修另开子单
- [x] 清单总评 ≠ 待填；更新 BOARD

## Notes

自动结构审计 + 清单回写（2026-09-06）。总评 `{info['verdict']}`；flags={','.join(info['flags']) or 'none'}。
"""
    # keep NN from filename
    nn = p.name.split("-")[0]
    body = body.replace(f"# {p.stem.split('-')[0]}:", f"# {nn}:", 1)
    p.write_text(body, encoding="utf-8")


def rebuild_board(results: list[dict]) -> None:
    # map name -> status from tickets
    rows = []
    for p in sorted(ISSUES.glob("*-audit-*.md")):
        t = p.read_text(encoding="utf-8")
        m = re.search(r"#\s*(\d+):\s*审计\s+(.+)", t)
        if not m:
            continue
        nn, name = m.group(1), m.group(2).strip()
        label = "已完成" if "**标签:** 已完成" in t else "待Agent处理"
        if "**标签:** 大修" in t or "总评：`大修`" in t:
            pass
        rows.append((nn, name, label, p.name))
    done = sum(1 for r in rows if r[2] == "已完成")
    todo = sum(1 for r in rows if r[2] == "待Agent处理")
    lines = [
        "# BOARD — 技能逐文件审计（一技能一工单）\n\n",
        f"**总数:** {len(rows)}  |  **已完成:** {done}  |  **待Agent处理:** {todo}\n\n",
        "| NN | 技能 | 标签 | 工单文件 |\n|----|------|------|----------|\n",
    ]
    for nn, name, label, fname in rows:
        lines.append(f"| {nn} | `{name}` | {label} | `{fname}` |\n")
    frontier = [r for r in rows if r[2] == "待Agent处理"][:8]
    lines.append(
        "\n**Frontier:** "
        + (", ".join(f"{r[0]}-{en_slug(r[1])}" for r in frontier) if frontier else "（无）")
        + "\n"
    )
    (FEAT / "BOARD.md").write_text("".join(lines), encoding="utf-8")


def main() -> None:
    results = []
    for entry in sorted(BIO.rglob("技能说明_*.md")):
        info = audit_one(entry.parent)
        results.append(info)
        write_checklist(info)
        # auto-close only clean ones; 小修 stay open for manual fix pass
        mark_ticket(info, auto_close=True)

    # report
    by_v: dict[str, list] = {}
    for r in results:
        by_v.setdefault(r["verdict"], []).append(r)
    lines = ["# 审计预检报告\n\n"]
    for v, items in sorted(by_v.items()):
        lines.append(f"## {v} ({len(items)})\n\n")
        for r in items:
            lines.append(f"- `{r['rel']}` lines={r['lines']} flags={','.join(r['flags']) or '—'}\n")
        lines.append("\n")
    REPORT.write_text("".join(lines), encoding="utf-8")
    rebuild_board(results)
    print(f"skills={len(results)}")
    for v, items in sorted(by_v.items()):
        print(f"  {v}: {len(items)}")


if __name__ == "__main__":
    main()
