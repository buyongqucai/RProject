# -*- coding: utf-8 -*-
"""One-shot: rename 样例_sample -> 01_样例_sample; lift nested results; update refs."""
from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(r"E:/RProject/生信分析技能_BioinformaticsSkills")
OLD = "样例_sample"
NEW = "01_样例_sample"

SKIP_NAMES = {
    "_fix_sample_layout.py",
    "_phaseB_sample_batch.py",
    "_layout_migrate_phaseA.py",
}


def fix_nested_and_rename() -> tuple[int, int]:
    nested_fixed = 0
    samples = [p for p in ROOT.rglob(OLD) if p.is_dir()]
    for sample in samples:
        nested = sample / "代码文件" / "结果文件"
        if nested.is_dir():
            files = [f for f in nested.rglob("*") if f.is_file()]
            if files:
                dest = sample / "结果文件"
                dest.mkdir(exist_ok=True)
                for f in files:
                    rel = f.relative_to(nested)
                    target = dest / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if not target.exists():
                        shutil.move(str(f), str(target))
                    else:
                        f.unlink()
            shutil.rmtree(nested)
            nested_fixed += 1

    renamed = 0
    samples = sorted(
        [p for p in ROOT.rglob(OLD) if p.is_dir()],
        key=lambda p: len(p.parts),
        reverse=True,
    )
    for sample in samples:
        new_path = sample.parent / NEW
        if new_path.exists():
            print("SKIP exists:", new_path.relative_to(ROOT).as_posix())
            continue
        sample.rename(new_path)
        renamed += 1
    return nested_fixed, renamed


def update_text_refs() -> int:
    """Replace 样例_sample with 01_样例_sample in docs/scripts (avoid double prefix)."""
    exts = {".md", ".json", ".R", ".r", ".py", ".txt", ".html", ".csv"}
    updated = 0
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.name in SKIP_NAMES:
            continue
        if path.suffix not in exts:
            continue
        # skip generated binary-ish or huge; html reports OK for path mention
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if OLD not in text:
            continue
        # avoid turning 01_样例_sample into 01_01_样例_sample
        new_text = text.replace(f"01_{OLD}", "\0PLACEHOLDER\0")
        new_text = new_text.replace(OLD, NEW)
        new_text = new_text.replace("\0PLACEHOLDER\0", NEW)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8", newline="\n")
            updated += 1
            print("UPDATED:", path.relative_to(ROOT).as_posix())
    return updated


def verify() -> None:
    remaining_old = [p for p in ROOT.rglob(OLD) if p.is_dir()]
    new_count = [p for p in ROOT.rglob(NEW) if p.is_dir()]
    still_nested = []
    for p in ROOT.rglob("结果文件"):
        if not p.is_dir():
            continue
        parts = p.parts
        for i, part in enumerate(parts):
            if part == "代码文件" and i + 1 < len(parts) and parts[i + 1] == "结果文件":
                still_nested.append(p)
                break
    print("remaining_old=", len(remaining_old))
    print("new_count=", len(new_count))
    print("still_nested=", len(still_nested))
    ex = ROOT / "01_组学_Omics/转录组分析_RNA-seq" / NEW
    if ex.exists():
        print("example_children=", sorted(c.name for c in ex.iterdir()))
        code = ex / "代码文件"
        print("code_children=", sorted(c.name for c in code.iterdir()) if code.exists() else None)


def main() -> None:
    nested_fixed, renamed = fix_nested_and_rename()
    print(f"NESTED_FIXED={nested_fixed}")
    print(f"RENAMED={renamed}")
    updated = update_text_refs()
    print(f"TEXT_UPDATED={updated}")
    verify()


if __name__ == "__main__":
    main()
