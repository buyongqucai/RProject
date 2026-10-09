# -*- coding: utf-8 -*-
"""婷婷：单细胞前置图 + Knk 扰动图（对齐琪乐无穷可用图种）。"""
from __future__ import annotations

import gzip
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
import scanpy as sc
import scipy.sparse

RAW = Path(r"C:\Users\10540\Desktop\婷婷\虚拟敲除\数据文件")
RES = Path(r"C:\Users\10540\Desktop\婷婷\虚拟敲除\结果文件")
CROSS_KNK = RES / "_跨亚群" / "scTenifoldKnk_1.4.3_GPU" / "图片文件"
CROSS_KNK_DATA = RES / "_跨亚群" / "scTenifoldKnk_1.4.3_GPU" / "数据文件"
CROSS_GENKI = RES / "_跨亚群" / "GenKI" / "图片文件"
DPI = 600
SUBTYPES = ["TREM2 macrophage", "M1-like macrophage", "M2-like macrophage"]
COLORS = {
    "TREM2 macrophage": "#C17B7B",
    "M1-like macrophage": "#5B8FA8",
    "M2-like macrophage": "#6B8F71",
}
# TREM2 module (paper-like)
TREM2_SCORE = ["APOE", "CTSB", "TREM2", "CD68", "GPNMB", "LPL", "SPP1", "LGALS3", "TYROBP"]


def save(fig, folder: Path, stem: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / f"{stem}.png", dpi=DPI, bbox_inches="tight", facecolor="white")
    fig.savefig(folder / f"{stem}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def load_adata():
    meta = pd.read_csv(gzip.open(RAW / "01_细胞注释_CellMeta_GSE175817.csv.gz"), low_memory=False)
    # RDS via rpy2 unavailable — use already-exported h5ad if any; else call R once
    h5 = RAW / "myeloid_for_figs.h5ad"
    if not h5.exists():
        raise FileNotFoundError("run export_h5ad first")
    adata = sc.read_h5ad(h5)
    return adata, meta


def export_h5ad_via_r() -> None:
    script = RAW.parent / "代码文件" / "_tmp_export_h5ad.R"
    script.write_text(
        r"""
suppressPackageStartupMessages(library(Matrix))
raw <- "C:/Users/10540/Desktop/婷婷/虚拟敲除/数据文件"
meta <- read.csv(gzfile(file.path(raw, "01_细胞注释_CellMeta_GSE175817.csv.gz")), check.names=FALSE)
counts <- readRDS(gzcon(gzfile(file.path(raw, "02_表达矩阵_Counts_GSE175817.RDS.gz"), "rb")))
keep <- meta$celltype %in% c("TREM2 macrophage","M1-like macrophage","M2-like macrophage")
meta <- meta[keep,,drop=FALSE]
mat <- counts[, meta$cell_id, drop=FALSE]
dir.create(file.path(raw, "_fig_mtx"), showWarnings=FALSE, recursive=TRUE)
Matrix::writeMM(mat, file.path(raw, "_fig_mtx", "counts.mtx"))
writeLines(rownames(mat), file.path(raw, "_fig_mtx", "genes.tsv"), useBytes=TRUE)
writeLines(colnames(mat), file.path(raw, "_fig_mtx", "cells.tsv"), useBytes=TRUE)
write.csv(meta, file.path(raw, "_fig_mtx", "meta.csv"), row.names=FALSE)
message("MTX_OK")
""",
        encoding="utf-8",
    )
    import subprocess

    rscript = Path(r"E:\R-4.6.0\bin\Rscript.exe")
    subprocess.run([str(rscript), str(script)], check=True)


def build_adata_from_mtx():
    import scipy.io
    import io

    folder = RAW / "_fig_mtx"
    if not (folder / "counts.mtx").exists():
        export_h5ad_via_r()
    genes = (folder / "genes.tsv").read_text(encoding="utf-8").splitlines()
    cells = (folder / "cells.tsv").read_text(encoding="utf-8").splitlines()
    meta = pd.read_csv(folder / "meta.csv")
    raw = (folder / "counts.mtx").read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    matrix = scipy.io.mmread(io.BytesIO(raw)).T.tocsr()
    adata = sc.AnnData(matrix)
    adata.obs_names = cells
    adata.var_names = genes
    meta = meta.set_index("cell_id").loc[cells]
    adata.obs = meta.copy()
    return adata


def prefigures(adata) -> None:
    CROSS_KNK.mkdir(parents=True, exist_ok=True)
    CROSS_KNK_DATA.mkdir(parents=True, exist_ok=True)
    # restrict lesional for main UMAP story + all mac for comparison
    ad = adata.copy()
    sc.pp.normalize_total(ad, target_sum=1e4)
    sc.pp.log1p(ad)
    sc.pp.highly_variable_genes(ad, n_top_genes=2000, flavor="seurat_v3")
    sc.pp.pca(ad, n_comps=30, mask_var="highly_variable")
    sc.pp.neighbors(ad, n_pcs=30)
    sc.tl.umap(ad, random_state=8096)

    fig, ax = plt.subplots(figsize=(6.8, 5.4))
    for st in SUBTYPES:
        m = ad.obs["celltype"].to_numpy() == st
        ax.scatter(
            ad.obsm["X_umap"][m, 0],
            ad.obsm["X_umap"][m, 1],
            s=5,
            c=COLORS[st],
            linewidths=0,
            label=st,
            rasterized=True,
        )
    ax.set_title("GSE175817 myeloid macrophages (author labels)")
    ax.set_xlabel("UMAP 1")
    ax.set_ylabel("UMAP 2")
    ax.legend(frameon=False, markerscale=3, fontsize=8, loc="upper left", bbox_to_anchor=(1.02, 1))
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    save(fig, CROSS_KNK, "02_散点图_巨噬细胞UMAP_Celltype")

    # stim split
    fig, ax = plt.subplots(figsize=(6.8, 5.4))
    for stim, c in [("Lesional", "#C17B7B"), ("Nonlesional", "#5B8FA8")]:
        m = ad.obs["stim"].to_numpy() == stim
        ax.scatter(ad.obsm["X_umap"][m, 0], ad.obsm["X_umap"][m, 1], s=5, c=c, linewidths=0, label=stim, rasterized=True)
    ax.set_title("Lesional vs non-lesional")
    ax.set_xlabel("UMAP 1")
    ax.set_ylabel("UMAP 2")
    ax.legend(frameon=False, markerscale=3)
    ax.set_xticks([])
    ax.set_yticks([])
    save(fig, CROSS_KNK, "02_散点图_皮损对照UMAP_Stim")

    # AHR feature
    if "AHR" in ad.var_names:
        fig, ax = plt.subplots(figsize=(6.2, 5.2))
        vals = ad[:, "AHR"].X
        vals = np.asarray(vals.todense() if scipy.sparse.issparse(vals) else vals).ravel()
        sca = ax.scatter(ad.obsm["X_umap"][:, 0], ad.obsm["X_umap"][:, 1], c=vals, s=5, cmap="viridis", linewidths=0, rasterized=True)
        fig.colorbar(sca, ax=ax, fraction=0.046, pad=0.04, label="log1p(AHR)")
        ax.set_title("AHR expression")
        ax.set_xticks([])
        ax.set_yticks([])
        save(fig, CROSS_KNK, "02_散点图_AHR表达UMAP_AhrFeature")

    # violin AHR by subtype × stim
    rows = []
    x = ad[:, "AHR"].X if "AHR" in ad.var_names else None
    if x is not None:
        vals = np.asarray(x.todense() if scipy.sparse.issparse(x) else x).ravel()
        for i in range(ad.n_obs):
            rows.append({"celltype": ad.obs["celltype"].iloc[i], "stim": ad.obs["stim"].iloc[i], "AHR": vals[i]})
        df = pd.DataFrame(rows)
        fig, ax = plt.subplots(figsize=(8.5, 4.8))
        order = SUBTYPES
        positions = []
        data = []
        labels = []
        pos = 1
        for st in order:
            for stim in ["Lesional", "Nonlesional"]:
                v = df[(df.celltype == st) & (df.stim == stim)]["AHR"].to_numpy()
                data.append(v)
                positions.append(pos)
                labels.append(f"{st.split()[0]}\n{stim[:3]}")
                pos += 1
            pos += 0.5
        ax.violinplot(data, positions=positions, showmeans=False, showmedians=True, widths=0.8)
        ax.set_xticks(positions)
        ax.set_xticklabels(labels, fontsize=7)
        ax.set_ylabel("log1p(AHR)")
        ax.set_title("AHR by macrophage subtype and lesion status")
        save(fig, CROSS_KNK, "02_小提琴图_AHR亚群皮损_TargetViolin")

    # detection table for lesional AHR
    det_rows = []
    raw_counts = adata.X
    if scipy.sparse.issparse(raw_counts):
        ahr_raw = np.asarray(raw_counts[:, list(adata.var_names).index("AHR")].todense()).ravel() if "AHR" in adata.var_names else np.zeros(adata.n_obs)
    else:
        ahr_raw = raw_counts[:, list(adata.var_names).index("AHR")] if "AHR" in adata.var_names else np.zeros(adata.n_obs)
    for st in SUBTYPES:
        for stim in ["Lesional", "Nonlesional"]:
            m = (adata.obs["celltype"].to_numpy() == st) & (adata.obs["stim"].to_numpy() == stim)
            n = int(m.sum())
            d = int((ahr_raw[m] > 0).sum()) if n else 0
            det_rows.append({"celltype": st, "stim": stim, "cells": n, "AHR_detected": d, "pct": 100 * d / n if n else 0})
    det = pd.DataFrame(det_rows)
    det.to_csv(CROSS_KNK_DATA / "03_检出率_AHR_TargetDetection.csv", index=False)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    les = det[det.stim == "Lesional"]
    ax.bar(range(len(les)), les["pct"], color=[COLORS[s] for s in les["celltype"]], edgecolor="#333")
    ax.set_xticks(range(len(les)))
    ax.set_xticklabels([s.replace(" macrophage", "") for s in les["celltype"]], rotation=20, ha="right")
    ax.set_ylabel("AHR detection (%)")
    ax.set_title("Lesional macrophage AHR detection")
    save(fig, CROSS_KNK, "03_柱状图_AHR检出率_TargetDetectionBar")

    # polarization-ish: TREM2 module score
    genes = [g for g in TREM2_SCORE if g in ad.var_names]
    if genes:
        sc.tl.score_genes(ad, gene_list=genes, score_name="trem2_score", use_raw=False)
        fig, ax = plt.subplots(figsize=(6.2, 5.2))
        sca = ax.scatter(
            ad.obsm["X_umap"][:, 0],
            ad.obsm["X_umap"][:, 1],
            c=ad.obs["trem2_score"],
            s=5,
            cmap="magma",
            linewidths=0,
            rasterized=True,
        )
        fig.colorbar(sca, ax=ax, fraction=0.046, pad=0.04, label="TREM2 module score")
        ax.set_title("Polarization-related TREM2 module (scRNA)")
        ax.set_xticks([])
        ax.set_yticks([])
        save(fig, CROSS_KNK, "02_散点图_TREM2模块分_PolarizationScore")
        ad.obs[["celltype", "stim", "trem2_score"]].to_csv(
            CROSS_KNK_DATA / "05_极化_TREM2模块分.csv"
        )


def knk_gene_plots() -> None:
    for subtype in ["TREM2 macrophage", "M2-like macrophage"]:
        dr = RES / subtype / "scTenifoldKnk_1.4.3_GPU" / "AHR" / "数据文件" / "扰动_Dr.csv"
        if not dr.exists():
            continue
        df = pd.read_csv(dr)
        fig_dir = RES / subtype / "scTenifoldKnk_1.4.3_GPU" / "AHR" / "图片文件"
        fig_dir.mkdir(parents=True, exist_ok=True)
        df = df.sort_values("distance", ascending=False).reset_index(drop=True)
        df["rank"] = np.arange(1, len(df) + 1)
        fig, ax = plt.subplots(figsize=(6.2, 4.8))
        ax.scatter(df["rank"], df["distance"], s=8, c="#5B8FA8", linewidths=0, rasterized=True)
        hit = df[df["p.adj"] < 0.05]
        if len(hit):
            ax.scatter(hit["rank"], hit["distance"], s=28, c="#C0392B", linewidths=0, label="FDR<0.05")
            for _, r in hit.head(8).iterrows():
                ax.annotate(r["gene"], (r["rank"], r["distance"]), fontsize=7, xytext=(4, 4), textcoords="offset points")
        ax.set_xlabel("Rank")
        ax.set_ylabel("Distance")
        ax.set_title(f"Knk 1.4.3 GPU · {subtype} · AHR")
        ax.legend(frameon=False, fontsize=8)
        save(fig, fig_dir, f"04_散点图_扰动排名_{subtype.split()[0]}_AHR")
        # bar top genes
        top = df.head(15)
        fig, ax = plt.subplots(figsize=(6.5, 4.8))
        ax.barh(top["gene"][::-1], top["distance"][::-1], color="#6B8F71", edgecolor="#333")
        ax.set_xlabel("Distance")
        ax.set_title(f"Top DR genes · {subtype.split()[0]} AHR")
        save(fig, fig_dir, f"04_柱状图_扰动基因_{subtype.split()[0]}_AHR")
        # enrich if any
        go = RES / subtype / "scTenifoldKnk_1.4.3_GPU" / "AHR" / "数据文件" / "富集_GO.csv"
        if go.exists():
            gdf = pd.read_csv(go)
            if len(gdf):
                gdf = gdf.sort_values("p.adjust").head(12)
                fig, ax = plt.subplots(figsize=(7.2, 4.8))
                ax.barh(gdf["Description"][::-1], -np.log10(gdf["p.adjust"][::-1]), color="#5B8FA8")
                ax.set_xlabel(r"$-\log_{10}$(p.adjust)")
                ax.set_title(f"GO passers · {subtype.split()[0]} AHR")
                save(fig, fig_dir, f"05_柱状图_GO通过_{subtype.split()[0]}_AHR")
            else:
                note = fig_dir.parent / "报告文件" / "05_富集_无通过条目.txt"
                note.parent.mkdir(parents=True, exist_ok=True)
                note.write_text("No GO/KEGG terms passed BH p<0.05 and q<0.2.\n", encoding="utf-8")


def knk_schematic() -> None:
    """流程图已废弃。数形结合见 11_Knk原理图_数形结合.py。"""
    script = Path(__file__).resolve().parent / "11_Knk原理图_数形结合.py"
    if script.exists():
        import runpy

        runpy.run_path(str(script), run_name="__main__")
        return
    raise FileNotFoundError(script)


def main() -> None:
    adata = build_adata_from_mtx()
    prefigures(adata)
    knk_gene_plots()
    knk_schematic()
    print("FIGS_DONE")


if __name__ == "__main__":
    main()
