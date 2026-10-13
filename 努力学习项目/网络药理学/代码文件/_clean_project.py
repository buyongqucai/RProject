# -*- coding: utf-8 -*-
"""Clean 努力学习项目/网络药理学: keep raw data + core scripts; drop junk."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学")

def rm(p: Path) -> None:
    if not p.exists():
        return
    if p.is_dir():
        shutil.rmtree(p, ignore_errors=True)
        print("RMDIR", p.relative_to(ROOT).as_posix())
    else:
        p.unlink(missing_ok=True)
        print("RM", p.relative_to(ROOT).as_posix())


def clear_dir(p: Path) -> None:
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)
        return
    for c in list(p.iterdir()):
        rm(c)
    p.mkdir(parents=True, exist_ok=True)
    print("CLEARED", p.relative_to(ROOT).as_posix())


def main() -> None:
    # 1) drop archives / caches / old delivery
    for name in ("_归档", "_cache", "交付文件"):
        rm(ROOT / name)

    # 2) drop generated results (will rebuild)
    res = ROOT / "代码文件" / "结果文件"
    for sub in ("图片文件", "数据文件", "报告文件"):
        clear_dir(res / sub)

    # 3) drop regenerable skill contracts in 数据文件/ (keep 上游_* + optional caches)
    data = ROOT / "数据文件"
    keep_names = {
        "DATA_SOURCE.md",
        "PROVENANCE.json",
        "富集GO_BPCCMF_Bubble.csv",
        "富集KEGG_TopPathways.csv",
        "19_PPI互作_StringInteractions_score900.tsv",
        "PPI互作_StringInteractions.tsv",
    }
    keep_dirs = {"上游_疾病", "上游_药物"}
    if data.exists():
        for p in list(data.iterdir()):
            if p.is_dir() and p.name in keep_dirs:
                continue
            if p.is_file() and p.name in keep_names:
                continue
            if p.is_file() and p.suffix.lower() in {".csv", ".tsv", ".json", ".md", ".txt"}:
                # drop other top-level regenerable tables; 02 will rebuild
                if p.name not in keep_names:
                    rm(p)
            elif p.is_dir() and p.name not in keep_dirs:
                rm(p)

    # 4) drop legacy / one-off scripts
    code = ROOT / "代码文件"
    for name in (
        "01_run_uc_skill_plots.R",
        "12_replot_hctp_only.R",
    ):
        rm(code / name)

    # 5) recreate empty dirs expected by layout
    for d in (
        ROOT / "_归档",
        ROOT / "交付文件",
        res / "图片文件",
        res / "数据文件",
        res / "报告文件",
    ):
        d.mkdir(parents=True, exist_ok=True)

    print("KEEP 上游_*/enrichment/PPI cache / 参考_交付原图 / 微生信上传 / core scripts")
    print("DONE clean")


if __name__ == "__main__":
    main()
