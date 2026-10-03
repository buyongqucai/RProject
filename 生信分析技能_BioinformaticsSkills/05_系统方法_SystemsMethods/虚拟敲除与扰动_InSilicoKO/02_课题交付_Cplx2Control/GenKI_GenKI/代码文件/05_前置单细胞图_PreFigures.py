"""Pre-knockout figures for Control PEP and NF1. English labels, PNG and SVG."""

from __future__ import annotations

import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc
import scipy.io
import scipy.sparse

GENES = ["Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21"]
SUBTYPES = ("PEP", "NF1")
COLORS = {"PEP": "#5B8FA8", "NF1": "#C17B7B"}
RESULT = Path(r"C:\Users\10540\Desktop\琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO\GenKI_GenKI\结果文件")
FIG = RESULT / "图片文件"
DPI = 600


def read_subtype(subtype: str):
    folder = RESULT / f"输入_{subtype}"
    genes = (folder / "genes.tsv").read_text(encoding="utf-8").splitlines()
    cells = (folder / "cells.tsv").read_text(encoding="utf-8").splitlines()
    raw = (folder / "counts.mtx").read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    matrix = scipy.io.mmread(io.BytesIO(raw)).T.tocsr()
    return matrix, genes, cells


def save(fig, stem: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / f"{stem}.png", dpi=DPI, bbox_inches="tight", facecolor="white")
    fig.savefig(FIG / f"{stem}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    pieces = []
    rows = []
    for subtype in SUBTYPES:
        matrix, genes, cells = read_subtype(subtype)
        names = list(genes)
        adata = sc.AnnData(matrix)
        adata.obs_names = [f"{subtype}_{cell}" for cell in cells]
        adata.var_names = names
        adata.obs["subtype"] = subtype
        pieces.append(adata)
        for gene in GENES:
            if gene not in names:
                detected = 0
            else:
                detected = int((matrix[:, names.index(gene)] > 0).sum())
            rows.append(
                {
                    "subtype": subtype,
                    "gene": gene,
                    "cells": matrix.shape[0],
                    "detected_cells": detected,
                    "detection_percent": 100.0 * detected / matrix.shape[0],
                }
            )
    pd.DataFrame(rows).to_csv(RESULT / "00_检出_PEP_NF1.csv", index=False)

    adata = sc.concat(pieces, join="outer", fill_value=0)
    adata.X = scipy.sparse.csr_matrix(adata.X)
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    sc.pp.highly_variable_genes(adata, n_top_genes=2000, flavor="seurat")
    sc.pp.pca(adata, n_comps=30, mask_var="highly_variable")
    sc.pp.neighbors(adata, n_pcs=30)
    sc.tl.umap(adata, random_state=8096)

    fig, ax = plt.subplots(figsize=(6.2, 5.2))
    for subtype in SUBTYPES:
        mask = adata.obs["subtype"].to_numpy() == subtype
        ax.scatter(
            adata.obsm["X_umap"][mask, 0],
            adata.obsm["X_umap"][mask, 1],
            s=6,
            c=COLORS[subtype],
            linewidths=0,
            label=subtype,
            rasterized=True,
        )
    ax.set_xlabel("UMAP 1")
    ax.set_ylabel("UMAP 2")
    ax.set_title("GSE197289 Control: PEP and NF1")
    ax.legend(frameon=False, markerscale=3, loc="upper left", bbox_to_anchor=(1.02, 1))
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    save(fig, "02_UMAP_PEP_NF1")

    table = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    x = np.arange(len(GENES))
    width = 0.36
    for offset, subtype in enumerate(SUBTYPES):
        part = table[table["subtype"] == subtype].set_index("gene").loc[GENES]
        ax.bar(
            x + (offset - 0.5) * width,
            part["detection_percent"],
            width=width,
            color=COLORS[subtype],
            label=subtype,
        )
    ax.set_xticks(x)
    ax.set_xticklabels(GENES, rotation=30, ha="right")
    ax.set_ylabel("Detection (%)")
    ax.set_title("Gene detection in Control PEP and NF1")
    ax.legend(frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    save(fig, "03_Detection_PEP_NF1")

    fig, axes = plt.subplots(2, 3, figsize=(9.5, 6.2), sharey=False)
    for ax, gene in zip(axes.ravel(), GENES):
        data = []
        labels = []
        for subtype in SUBTYPES:
            values = adata[adata.obs["subtype"] == subtype, gene].X
            if scipy.sparse.issparse(values):
                values = values.toarray()
            data.append(np.asarray(values).ravel())
            labels.append(subtype)
        parts = ax.violinplot(data, showmedians=True, widths=0.8)
        for body, subtype in zip(parts["bodies"], SUBTYPES):
            body.set_facecolor(COLORS[subtype])
            body.set_alpha(0.8)
        ax.set_xticks([1, 2])
        ax.set_xticklabels(labels)
        ax.set_title(gene)
        ax.set_ylabel("log1p normalized")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    fig.suptitle("Expression of planned knockout genes")
    fig.tight_layout()
    save(fig, "02_Violin_KnockGenes")
    print("FIGURES_DONE", FIG)


if __name__ == "__main__":
    main()
