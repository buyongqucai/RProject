# -*- coding: utf-8 -*-
"""Flatten Tingting desktop KO tree into a simpler delivery layout."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(r"C:\Users\10540\Desktop\婷婷\虚拟敲除")
DATA = ROOT / "数据文件"
CODE = ROOT / "代码文件"
RES = ROOT / "结果文件"


def ensure(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def move_to(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if dst.exists():
        if src.is_dir() and dst.is_dir():
            for child in src.iterdir():
                move_to(child, dst / child.name)
            try:
                src.rmdir()
            except OSError:
                pass
            return
        print("SKIP exists", dst)
        return
    ensure(dst.parent)
    shutil.move(str(src), str(dst))
    print("MOVE", src.relative_to(ROOT), "->", dst.relative_to(ROOT))


def main() -> None:
    assert ROOT.is_dir(), ROOT

    # --- 数据文件：只留分析用矩阵 ---
    trace = ensure(DATA / "_溯源")
    for name in [
        "GSE175817_meta_donorlesional.csv.gz",
        "GSE175817_meta_myeloid.csv.gz",
        "GSM5348400_donor3.csv.gz",
        "filelist.txt",
    ]:
        move_to(DATA / name, trace / name)
    move_to(DATA / "_作者注释Rdata", trace / "作者注释Rdata")
    move_to(DATA / "_fig_mtx", trace / "fig_mtx")

    # --- 代码：归档 NFKB1 与缓存 ---
    arch = ensure(CODE / "_归档")
    move_to(CODE / "完整版_143GPU_FullVersion_NFKB1", arch / "完整版_143GPU_FullVersion_NFKB1")
    for pyc in CODE.rglob("__pycache__"):
        shutil.rmtree(pyc, ignore_errors=True)
        print("RM", pyc.relative_to(ROOT))

    # --- 结果：00_报告 / 01_合看 / 02_亚群 ---
    reports = ensure(RES / "00_报告")
    cross_new = ensure(RES / "01_合看")
    subtypes = ensure(RES / "02_亚群")

    old_cross = RES / "_跨亚群"
    if old_cross.is_dir():
        # reports first
        old_rpt = old_cross / "课题报告_ProjectReports" / "报告文件"
        if old_rpt.is_dir():
            for f in old_rpt.iterdir():
                move_to(f, reports / f.name)
            # remove empty shells later
        for name in [
            "GenKI",
            "GSEA全排序_RankedGSEA",
            "scTenifoldKnk_1.4.3_GPU",
            "富集汇总_EnrichSummary",
        ]:
            move_to(old_cross / name, cross_new / name)
        # leftover STATUS etc.
        for f in list(old_cross.iterdir()):
            if f.name == "课题报告_ProjectReports":
                continue
            move_to(f, cross_new / f.name)
        # drop empty project reports shell
        pr = old_cross / "课题报告_ProjectReports"
        if pr.exists():
            shutil.rmtree(pr, ignore_errors=True)
        try:
            old_cross.rmdir()
            print("RMDIR _跨亚群")
        except OSError:
            # leftover junk
            move_to(old_cross, RES / "_归档_跨亚群残留")

    for name in ["TREM2 macrophage", "M2-like macrophage"]:
        move_to(RES / name, subtypes / name)

    # root portal
    portal = ROOT / "00_从这里打开_报告入口.html"
    portal.write_text(
        """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"/>
<meta http-equiv="refresh" content="0; url=结果文件/00_报告/index_报告入口.html"/>
<title>婷婷虚拟敲除 · 报告入口</title></head>
<body style="font-family:Microsoft YaHei,sans-serif;padding:2rem;line-height:1.8">
<p>正在打开报告… 若未跳转请点：
<a href="结果文件/00_报告/index_报告入口.html">结果文件/00_报告/index_报告入口.html</a></p>
<p>目录说明见同级 <code>存放说明.md</code>。</p>
</body></html>
""",
        encoding="utf-8",
    )
    print("WRITE", portal.name)

    # code README
    (CODE / "README_代码入口.md").write_text(
        """# 代码入口（婷婷）

| 用途 | 路径 |
|------|------|
| Knk 1.4.3 GPU 一键 | `完整版_143GPU_FullVersion/run_all_一键运行.py` |
| GenKI AHR | `genki_tingting_ahr.py` / `genki_tingting_ahr_m2.py` |
| 导出髓系矩阵 | `00_从作者髓系导出_ExportMyeloid.R` |
| 汇总双报告 | `14_汇总与双报告_MakeReports.py` |
| 全排序 GSEA | `16_全排序GSEA_RankGsea.R` + `17_全排序GSEA出图与报告_PlotGseaReport.py` |

NFKB1 试跑已移到 `_归档/`。结果写到桌面 `结果文件/02_亚群/` 与 `01_合看/`。
""",
        encoding="utf-8",
    )

    print("DONE reorg")


if __name__ == "__main__":
    main()
