# -*- coding: utf-8 -*-
"""Ensure delivery_sample_paths() is called after PlotNaming.R is sourced."""
from __future__ import annotations

import re
from pathlib import Path

BIO = Path(r"E:\RProject\生信分析技能_BioinformaticsSkills")

BLOCK_RE = re.compile(
    r"paths <- delivery_sample_paths\(sample_root\)\n"
    r"data_dir <- paths\$raw_dir\n"
    r"fig_dir <- paths\$fig_dir\n"
    r"tab_dir <- paths\$tab_dir\n"
    r"rep_dir <- paths\$rep_dir\n"
    r"(?:for \(d in c\([^)]+\)\) dir\.create\(d, recursive = TRUE, showWarnings = FALSE\)\n)?",
)

SRC_RE = re.compile(
    r"source\([^\n]*PlotNaming\.R[^\n]*\)\n"
)


def fix_file(rfile: Path) -> str:
    text = rfile.read_text(encoding="utf-8")
    if "delivery_sample_paths" not in text:
        return "skip"
    idx_paths = text.find("paths <- delivery_sample_paths")
    idx_src = text.find("PlotNaming.R")
    if idx_paths < 0 or idx_src < 0:
        return "skip"
    if idx_paths >= idx_src:
        return "ok"
    m = BLOCK_RE.search(text)
    if not m:
        return "no_block"
    block = m.group(0)
    text2 = text[: m.start()] + text[m.end() :]
    src = SRC_RE.search(text2)
    if not src:
        return "no_src"
    insert_at = src.end()
    text2 = text2[:insert_at] + "\n" + block + text2[insert_at:]
    # dedupe accidental double blocks
    text2 = re.sub(
        r"(paths <- delivery_sample_paths\(sample_root\)\n"
        r"data_dir <- paths\$raw_dir\n"
        r"fig_dir <- paths\$fig_dir\n"
        r"tab_dir <- paths\$tab_dir\n"
        r"rep_dir <- paths\$rep_dir\n"
        r"(?:for \(d in c\([^)]+\)\) dir\.create\(d, recursive = TRUE, showWarnings = FALSE\)\n)?)"
        r"\1",
        r"\1",
        text2,
    )
    rfile.write_text(text2, encoding="utf-8")
    return "fixed"


def main():
    counts = {}
    for rfile in BIO.rglob("01_样例_sample/代码文件/*.R"):
        st = fix_file(rfile)
        counts[st] = counts.get(st, 0) + 1
        if st in ("fixed", "no_block", "no_src"):
            print(st, rfile.relative_to(BIO))
    print("SUMMARY", counts)


if __name__ == "__main__":
    main()
