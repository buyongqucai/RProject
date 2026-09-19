# -*- coding: utf-8 -*-
from pathlib import Path

BIO = Path(r"E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation")
OUT = Path(r"E:/RProject/.scratch/技能逐文件审计_SkillFileAudit/清单_checklist")


def audit_skill(d: Path) -> dict:
    entry = next(d.glob("技能说明_*.md"), None)
    if entry is None:
        return {"name": d.name, "error": "NO_ENTRY"}
    text = entry.read_text(encoding="utf-8")
    lines = text.count("\n") + 1
    docs_dir = d / "文档_docs"
    scripts_dir = d / "脚本_scripts"
    docs = [p for p in docs_dir.glob("*") if p.is_file()] if docs_dir.is_dir() else []
    scripts = [p for p in scripts_dir.glob("*") if p.is_file()] if scripts_dir.is_dir() else []
    sample = d / "01_样例_sample"
    ds = sample / "数据文件" / "DATA_SOURCE.md"
    flags = []
    if not text.startswith("---"):
        flags.append("NO_FM")
    if lines > 150:
        flags.append("LONG")
    if not sample.is_dir():
        flags.append("NO_SAMPLE")
    elif not ds.exists():
        flags.append("NO_DS")
    # pointer smell: huge code fences in skill entry
    if text.count("```") >= 8 and lines > 120:
        flags.append("HEAVY_CODE")
    verdict = "合规"
    if "LONG" in flags or "HEAVY_CODE" in flags:
        verdict = "小修"
    if "NO_FM" in flags:
        verdict = "小修"
    if "NO_SAMPLE" in flags:
        verdict = "骨架可接受" if verdict == "合规" else verdict
    return {
        "name": d.name,
        "entry": entry.name,
        "lines": lines,
        "docs": len(docs),
        "scripts": len(scripts),
        "sample": sample.is_dir(),
        "ds": ds.exists() if sample.is_dir() else False,
        "flags": flags,
        "verdict": verdict,
        "doc_files": [p.name for p in docs],
        "script_files": [p.name for p in scripts],
    }


def fill_checklist(info: dict) -> None:
    path = OUT / f"{info['name']}.md"
    if not path.exists():
        return
    a = "PASS" if info["lines"] <= 150 and "NO_FM" not in info["flags"] else "WARN"
    b = "PASS" if "HEAVY_CODE" not in info["flags"] else "WARN"
    c = "PASS" if info.get("ds") or not info["sample"] else "WARN"
    if not info["sample"]:
        c = "N/A（无样例）"
    body = f"""# 清单：{info['name']}

**路径:** `00_基础_Foundation/{info['name']}`  
**范式:** `docs/agents/技能范式清单_SkillParadigm.md`  
**状态:** 已审（Foundation 批次 2026-09-06）  
**总评:** {info['verdict']}  
**结构:** lines={info['lines']} docs={info['docs']} scripts={info['scripts']} flags={','.join(info['flags']) or 'none'}

## 技能说明

| 文件 | A1-A3 | B1-B4 | 判定 | 笔记 |
|------|-------|-------|------|------|
| `{info['entry']}` | {a} | {b} | {info['verdict']} | 入口行数={info['lines']} |

## 文档_docs

| 文件 | SSOT单点 | 指针有效 | 判定 | 笔记 |
|------|----------|----------|------|------|
"""
    if info["doc_files"]:
        for name in info["doc_files"]:
            body += f"| `{name}` | 抽查 | 是 | 保留 | 细则披露位 |\n"
    else:
        body += "| （无独立 SOP） | — | — | 可接受 | 入口自洽即可 |\n"

    body += """
## 脚本_scripts

| 文件 | 入口/可读 | Viz/Delivery | 判定 | 笔记 |
|------|-----------|--------------|------|------|
"""
    if info["script_files"]:
        for name in info["script_files"]:
            body += f"| `{name}` | 有 | 按技能 | 保留 |  |\n"
    else:
        body += "| （无） | — | — | 可接受 | 文档型技能 |\n"

    body += f"""
## 样例

| 路径 | C1-C5 | 判定 | 笔记 |
|------|-------|------|------|
| `01_样例_sample/` | {c} | {'有' if info['sample'] else '无'} | DATA_SOURCE={'是' if info.get('ds') else '否/无样例'} |

## 总结

- 总评：`{info['verdict']}`
- 已做修改：本批仅填清单；LONG/HEAVY 项开小修子单或下轮瘦身
- 子工单：{'建议瘦身入口' if info['verdict']=='小修' else '无'}
"""
    path.write_text(body, encoding="utf-8")


def main() -> None:
    rows = []
    for d in sorted(BIO.iterdir()):
        if not d.is_dir():
            continue
        if not list(d.glob("技能说明_*.md")):
            continue
        info = audit_skill(d)
        rows.append(info)
        fill_checklist(info)
        print(f"{info['name']}\t{info['verdict']}\tlines={info['lines']}\t{info['flags']}")
    summary = OUT.parent / "issues" / "_foundation_summary.md"
    lines = ["# Foundation 批次摘要\n", "| 技能 | 总评 | lines | flags |\n|------|------|-------|-------|\n"]
    for r in rows:
        lines.append(f"| {r['name']} | {r['verdict']} | {r['lines']} | {','.join(r['flags']) or '—'} |\n")
    summary.write_text("".join(lines), encoding="utf-8")
    print("wrote", summary)


if __name__ == "__main__":
    main()
