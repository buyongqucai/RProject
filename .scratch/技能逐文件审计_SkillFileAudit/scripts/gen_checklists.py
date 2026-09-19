"""Generate per-skill checklist stubs for SkillParadigm file-by-file audit."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BIO = ROOT / "生信分析技能_BioinformaticsSkills"
OUT = Path(__file__).resolve().parents[1] / "清单_checklist"

SECTIONS = """
## 技能说明

| 文件 | A1-A3 | B1-B4 | 判定 | 笔记 |
|------|-------|-------|------|------|
| `{entry}` |  |  |  |  |

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
{sample_rows}

## 总结

- 总评：`待填`（合规 / 小修 / 大修 / 骨架可接受）
- 已做修改：
- 子工单：
"""


def rel(p: Path, start: Path) -> str:
    try:
        return p.relative_to(start).as_posix()
    except ValueError:
        return p.as_posix()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    entries = sorted(BIO.rglob("技能说明_*.md"))
    print(f"skills={len(entries)} out={OUT}")
    for entry in entries:
        skill_dir = entry.parent
        slug = skill_dir.name
        docs = sorted((skill_dir / "文档_docs").glob("*")) if (skill_dir / "文档_docs").is_dir() else []
        scripts = sorted((skill_dir / "脚本_scripts").glob("*")) if (skill_dir / "脚本_scripts").is_dir() else []
        sample = skill_dir / "01_样例_sample"
        sample_bits: list[str] = []
        if sample.is_dir():
            ds = sample / "数据文件" / "DATA_SOURCE.md"
            sample_bits.append(f"| `{rel(sample, skill_dir)}/` |  |  |  |")
            if ds.exists():
                sample_bits.append(f"| `{rel(ds, skill_dir)}` |  |  |  |")
        else:
            sample_bits.append("| （无样例目录） |  |  | 显式待建? |")

        docs_rows = (
            "\n".join(f"| `{rel(p, skill_dir)}` |  |  |  |  |" for p in docs if p.is_file())
            or "| （无） |  |  |  |  |"
        )
        script_rows = (
            "\n".join(f"| `{rel(p, skill_dir)}` |  |  |  |  |" for p in scripts if p.is_file())
            or "| （无） |  |  |  |  |"
        )

        body = f"""# 清单：{slug}

**路径:** `{rel(skill_dir, BIO)}`  
**范式:** `docs/agents/技能范式清单_SkillParadigm.md`  
**状态:** 待填

{SECTIONS.format(
    entry=entry.name,
    docs_rows=docs_rows,
    script_rows=script_rows,
    sample_rows=chr(10).join(sample_bits),
)}
"""
        out_path = OUT / f"{slug}.md"
        out_path.write_text(body.replace("\r\n", "\n"), encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()
