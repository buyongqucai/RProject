# -*- coding: utf-8 -*-
"""Phase E: English-only plot face text; bilingual filenames unchanged.

- Patch run_sample.R labs/ggtitle/axis/legend Chinese → English
- Patch phase C/D templates
- Rerun all samples
- Audit SVG + scripts
"""
from __future__ import annotations

import re
import subprocess
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(r"E:/RProject/生信分析技能_BioinformaticsSkills")
VAL_DIR = ROOT / "07_分类验证_Validation"
CJK = re.compile(r"[\u4e00-\u9fff]")

# Exact string replacements for plot-face text (order: longer first)
PLOT_FACE_REPLACEMENTS: list[tuple[str, str]] = [
    (
        'name = "接触"',
        'name = "Contact frequency"',
    ),
    (
        'title = "接触矩阵（示意·BLOCKED）"',
        'title = "Contact matrix (schematic · BLOCKED)"',
    ),
    (
        'subtitle = "非真实Hi-C；仅验证交付命名与主题图类型"',
        'subtitle = "Toy schematic (not real Hi-C); delivery naming check"',
    ),
    (
        'x = "区间i", y = "区间j"',
        'x = "Bin i", y = "Bin j"',
    ),
    (
        'labs(title = "模块-性状相关", fill = "相关")',
        'labs(title = "Module–trait correlation", fill = "Correlation")',
    ),
    (
        'labs(title = "差异蛋白Top15", x = "logFC（疾病-健康）")',
        'labs(title = "Top 15 differential proteins", x = "logFC (disease − healthy)")',
    ),
    (
        'labs(title = "契约阻塞桩（示意·BLOCKED）", y = "是否通过", x = NULL)',
        'labs(title = "Contract stub (schematic · BLOCKED)", y = "Pass (0/1)", x = NULL)',
    ),
    (
        'labs(title = "火山图（处理对照）", x = "logFC", y = "-log10(p)")',
        'labs(title = "Volcano plot (Treat vs Control)", x = "logFC", y = "-log10(p)")',
    ),
    (
        'labs(title = "PCA图（处理对照）")',
        'labs(title = "PCA (Treat vs Control)")',
    ),
    (
        'labs(title = "样本数核对", y = "样本数", x = NULL)',
        'labs(title = "Sample count check", y = "n samples", x = NULL)',
    ),
    (
        'labs(title = "出版级散点示意", color = "组")',
        'labs(title = "Publication scatter (demo)", color = "Group")',
    ),
    (
        'labs(title = "交付规范规则覆盖度", x = NULL, y = "得分")',
        'labs(title = "Delivery rule coverage", x = NULL, y = "Score")',
    ),
]

# Also used in phase templates with slight variants
TEMPLATE_REPLACEMENTS = PLOT_FACE_REPLACEMENTS + [
    (
        'labs(title = "接触矩阵（示意·BLOCKED）", x = "区间i", y = "区间j")',
        'labs(title = "Contact matrix (schematic · BLOCKED)", x = "Bin i", y = "Bin j")',
    ),
]


def list_run_samples() -> list[Path]:
    return sorted(ROOT.rglob("01_样例_sample/代码文件/run_sample.R"))


def patch_text(text: str, pairs: list[tuple[str, str]]) -> tuple[str, int]:
    n = 0
    for old, new in pairs:
        if old in text:
            c = text.count(old)
            text = text.replace(old, new)
            n += c
    return text, n


def plot_face_cjk_lines(path: Path) -> list[tuple[int, str]]:
    """CJK inside labs()/scale_* name / ggtitle / xlab/ylab string args."""
    lines = path.read_text(encoding="utf-8").splitlines()
    bad: list[tuple[int, str]] = []
    for i, line in enumerate(lines, 1):
        if not CJK.search(line):
            continue
        if line.strip().startswith("#"):
            continue
        # plot face APIs
        if re.search(
            r"(labs\s*\(|ggtitle\s*\(|xlab\s*\(|ylab\s*\(|"
            r"scale_fill_[a-z_]+\s*\(|scale_color_[a-z_]+\s*\(|"
            r"scale_colour_[a-z_]+\s*\(|annotate\s*\(|"
            r"geom_text\s*\(|geom_label\s*\()",
            line,
        ):
            bad.append((i, line.strip()[:200]))
            continue
        # name/title/subtitle/x/y/fill/color string with CJK on same line as aes-ish
        if re.search(
            r"""(title|subtitle|name|x|y|fill|colour|color)\s*=\s*["'][^"']*[\u4e00-\u9fff]""",
            line,
        ):
            bad.append((i, line.strip()[:200]))
    return bad


def patch_all_scripts() -> dict:
    stats = {"run_sample_files": 0, "run_sample_replacements": 0, "template_replacements": 0}
    remaining: list[str] = []

    for p in list_run_samples():
        text = p.read_text(encoding="utf-8")
        new, n = patch_text(text, PLOT_FACE_REPLACEMENTS)
        if n:
            p.write_text(new, encoding="utf-8", newline="\n")
            stats["run_sample_files"] += 1
            stats["run_sample_replacements"] += n
        left = plot_face_cjk_lines(p if n == 0 else p)
        # re-read after write
        left = plot_face_cjk_lines(p)
        if left:
            remaining.append(f"{p.relative_to(ROOT).as_posix()}: {left}")

    for name in [
        "_phaseC_delivery_rerun.py",
        "_phaseC_pending_rerun.py",
        "_phaseD_bilingual_naming.py",
        "_phaseD_refresh_report.py",
        "_phaseB_sample_batch.py",
    ]:
        p = ROOT / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        new, n = patch_text(text, TEMPLATE_REPLACEMENTS)
        # doc line updates
        new2 = new.replace(
            "图面标题须单语（优先简洁中文）——二者不可混用。",
            "图面文字 English only（禁止中文）；文件名仍中英对照——二者不可混用。",
        )
        new2 = new2.replace(
            "文件名强制中英对照；图面标题须单语（优先简洁中文）——二者不可混用。",
            "文件名强制中英对照；图面文字 English only（禁止中文）——二者不可混用。",
        )
        if new2 != text:
            p.write_text(new2, encoding="utf-8", newline="\n")
            stats["template_replacements"] += n + (1 if new2 != new else 0)

    stats["remaining_plot_cjk"] = remaining
    return stats


def run_one(skill_rel: str, timeout: int = 180) -> str:
    sample = ROOT / skill_rel / "01_样例_sample" / "代码文件"
    script = sample / "run_sample.R"
    if not script.exists():
        return "FAIL"
    try:
        r = subprocess.run(
            ["Rscript", "run_sample.R"],
            cwd=str(sample),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "FAIL"
    status_file = ROOT / skill_rel / "01_样例_sample" / "结果文件" / "报告文件" / "STATUS.txt"
    if status_file.exists():
        st = status_file.read_text(encoding="utf-8", errors="replace").strip().splitlines()
        if st and st[0] in {"PASS", "BLOCKED", "FAIL"}:
            return st[0]
    if r.returncode != 0:
        return "FAIL"
    return "PASS"


def list_skills() -> list[str]:
    rels = []
    for p in ROOT.rglob("01_样例_sample"):
        if not p.is_dir():
            continue
        skill = p.parent
        try:
            rel = skill.relative_to(ROOT).as_posix()
        except ValueError:
            continue
        if rel.startswith("07_"):
            continue
        if (p / "代码文件" / "run_sample.R").exists():
            rels.append(rel)
    return sorted(set(rels))


def audit_svg_cjk() -> list[str]:
    hits = []
    for p in ROOT.rglob("01_样例_sample/结果文件/图片文件/*.svg"):
        t = p.read_text(encoding="utf-8", errors="replace")
        if CJK.search(t):
            hits.append(p.relative_to(ROOT).as_posix())
    return hits


def main() -> None:
    print("=== patch scripts ===")
    stats = patch_all_scripts()
    print(stats)

    skills = list_skills()
    print(f"=== rerun {len(skills)} samples ===")
    results = []
    t0 = time.time()
    for i, rel in enumerate(skills, 1):
        st = run_one(rel)
        results.append((rel, st))
        print(f"[{i}/{len(skills)}] {st}  {rel}")
    counts = Counter(s for _, s in results)
    print("COUNTS", dict(counts), "elapsed_s", round(time.time() - t0, 1))

    # post audit
    rem = []
    for p in list_run_samples():
        left = plot_face_cjk_lines(p)
        if left:
            rem.append((p.relative_to(ROOT).as_posix(), left))
    svg_hits = audit_svg_cjk()
    print("remaining plot-face CJK scripts:", len(rem))
    for path, lines in rem:
        print(path, lines)
    print("SVG with CJK:", len(svg_hits))
    for h in svg_hits:
        print(" ", h)

    out = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "patch_stats": {k: v for k, v in stats.items() if k != "remaining_plot_cjk"},
        "remaining_before_rerun": stats.get("remaining_plot_cjk"),
        "counts": dict(counts),
        "results": [{"skill": a, "status": b} for a, b in results],
        "remaining_plot_cjk_after": rem,
        "svg_cjk": svg_hits,
    }
    VAL_DIR.mkdir(parents=True, exist_ok=True)
    (VAL_DIR / "phaseE_english_plotface.json").write_text(
        __import__("json").dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("wrote", VAL_DIR / "phaseE_english_plotface.json")


if __name__ == "__main__":
    main()
