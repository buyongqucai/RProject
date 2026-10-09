# -*- coding: utf-8 -*-
"""婷婷 GenKI 结果图：KL 柱 / 排名散点 / 富集柱（对齐琪乐无穷可用图种）。"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DESKTOP = Path(r"C:\Users\10540\Desktop\婷婷\虚拟敲除")
SUBTYPE = "TREM2 macrophage"
ROOT = DESKTOP / "结果文件" / SUBTYPE / "GenKI"
CROSS = DESKTOP / "结果文件" / "_跨亚群" / "GenKI" / "图片文件"
DPI = 600
PRIMARY = "AHR"


def save(fig, folder: Path, stem: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / f"{stem}.png", dpi=DPI, bbox_inches="tight", facecolor="white")
    fig.savefig(folder / f"{stem}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def gene_dirs():
    if not ROOT.exists():
        return []
    out = []
    for p in ROOT.iterdir():
        if not p.is_dir() or p.name.startswith("_"):
            continue
        kl = p / "数据文件" / "KL排序_RankKL.csv"
        if kl.exists():
            out.append(p)
    return sorted(out, key=lambda x: x.name)


def plot_kl_bar(gene_dir: Path) -> None:
    resp = gene_dir / "数据文件" / "响应基因_Responsive.csv"
    fig_dir = gene_dir / "图片文件"
    if not resp.exists():
        (gene_dir / "报告文件").mkdir(parents=True, exist_ok=True)
        (gene_dir / "报告文件" / "05_出图_无响应基因.txt").write_text("no responsive genes\n", encoding="utf-8")
        return
    df = pd.read_csv(resp)
    if "gene" not in df.columns:
        return
    df = df[df["gene"].astype(str) != gene_dir.name].copy()
    if df.empty:
        (gene_dir / "报告文件").mkdir(parents=True, exist_ok=True)
        (gene_dir / "报告文件" / "05_出图_仅靶基因自身.txt").write_text("only knockout gene passed\n", encoding="utf-8")
        return
    df = df.sort_values("KL", ascending=False).head(15)
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    y = np.arange(len(df))
    ax.barh(y, np.log10(df["KL"].clip(lower=1e-12)), color="#C17B7B", edgecolor="white")
    ax.set_yticks(y)
    ax.set_yticklabels(df["gene"].astype(str), fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("log10 KL")
    ax.set_title(f"{SUBTYPE} · {gene_dir.name} · top responsive (excl. target)")
    save(fig, fig_dir, f"04_柱状图_KL_{gene_dir.name}")
    save(fig, CROSS, f"04_柱状图_KL_{gene_dir.name}")


def plot_rank(gene_dir: Path) -> None:
    path = gene_dir / "数据文件" / "KL排序_RankKL.csv"
    if not path.exists():
        return
    df = pd.read_csv(path)
    fig, ax = plt.subplots(figsize=(6.8, 5.0))
    ax.scatter(df["rank"], np.log10(df["KL"].clip(lower=1e-12)), s=8, c="#C4A574", linewidths=0)
    if "hit" in df.columns:
        hit = df[df["hit"] > 950]
        if len(hit):
            ax.scatter(
                hit["rank"],
                np.log10(hit["KL"].clip(lower=1e-12)),
                s=18,
                c="#C17B7B",
                linewidths=0,
                label="hit > 950",
            )
            ax.legend(frameon=False, fontsize=9)
    ax.set_xlabel("rank (KL high → low)")
    ax.set_ylabel("log10 KL")
    ax.set_title(f"{SUBTYPE} · {gene_dir.name} · rank vs KL")
    save(fig, gene_dir / "图片文件", f"09_散点图_RankKL_{gene_dir.name}")
    save(fig, CROSS, f"09_散点图_RankKL_{gene_dir.name}")


def plot_enrich(gene_dir: Path) -> None:
    go = gene_dir / "数据文件" / "富集_GO.csv"
    fig_dir = gene_dir / "图片文件"
    if not go.exists() or go.stat().st_size < 10:
        (gene_dir / "报告文件").mkdir(parents=True, exist_ok=True)
        (gene_dir / "报告文件" / "05_富集_无通过条目.txt").write_text("no GO rows\n", encoding="utf-8")
        return
    df = pd.read_csv(go)
    if df.empty or "p.adjust" not in df.columns:
        (gene_dir / "报告文件").mkdir(parents=True, exist_ok=True)
        (gene_dir / "报告文件" / "05_富集_无通过条目.txt").write_text("empty GO\n", encoding="utf-8")
        return
    df = df[df["p.adjust"] < 0.05].copy()
    if "qvalue" in df.columns:
        df = df[df["qvalue"] < 0.2]
    if df.empty:
        (gene_dir / "报告文件").mkdir(parents=True, exist_ok=True)
        (gene_dir / "报告文件" / "05_富集_无通过条目.txt").write_text("no term passed BH\n", encoding="utf-8")
        return
    lab = "Description" if "Description" in df.columns else df.columns[0]
    df = df.sort_values("p.adjust").head(12)
    fig, ax = plt.subplots(figsize=(8.0, 5.2))
    y = np.arange(len(df))
    ax.barh(y, -np.log10(df["p.adjust"].clip(lower=1e-300)), color="#6B8F71", edgecolor="white")
    ax.set_yticks(y)
    ax.set_yticklabels(df[lab].astype(str).str.slice(0, 55), fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel(r"$-\log_{10}$(p.adjust)")
    ax.set_title(f"{SUBTYPE} · {gene_dir.name} · GO terms passing threshold")
    save(fig, fig_dir, f"05_柱状图_GO_{gene_dir.name}")
    save(fig, CROSS, f"05_柱状图_GO_{gene_dir.name}")


def main() -> None:
    dirs = gene_dirs()
    if not dirs:
        print("NO_GENKI_RESULTS_YET")
        return
    for d in dirs:
        plot_kl_bar(d)
        plot_rank(d)
        plot_enrich(d)
        print("PLOTTED", d.name)
    print("GENKI_FIGS_DONE")


if __name__ == "__main__":
    main()
