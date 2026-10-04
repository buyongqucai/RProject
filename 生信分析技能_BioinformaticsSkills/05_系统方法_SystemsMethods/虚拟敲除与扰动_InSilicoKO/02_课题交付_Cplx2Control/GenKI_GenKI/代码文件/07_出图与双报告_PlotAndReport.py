"""Figures and two HTML reviews for the PEP/NF1 GenKI run.

English labels, PNG+SVG at 600 dpi. No invented network edges.
"""

from __future__ import annotations

import html
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\10540\Desktop\琪乐无穷\虚拟敲除\结果文件")
FIG = ROOT / "图片文件"
REPORT = ROOT / "报告文件"
DPI = 600
SUBTYPES = ("PEP", "NF1")
CONTROLS = {"PEP": "Abcc8", "NF1": "Gm15551"}
PEP_COLOR = "#5B8FA8"
NF1_COLOR = "#C17B7B"
BAR_COLOR = "#6B8F71"
MARK_COLOR = "#8B7BA8"
SAND_COLOR = "#D4A574"


def save(fig, stem: str) -> str:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / f"{stem}.png", dpi=DPI, bbox_inches="tight", facecolor="white")
    fig.savefig(FIG / f"{stem}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return stem


def style_ax(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=8)


def gene_dir(subtype: str, gene: str) -> Path:
    return ROOT / subtype / "GenKI" / gene


def partners(subtype: str, gene: str) -> pd.DataFrame:
    path = gene_dir(subtype, gene) / "响应基因_Responsive.csv"
    if not path.exists():
        return pd.DataFrame(columns=["gene", "KL", "hit", "hit_fraction", "rank"])
    frame = pd.read_csv(path)
    return frame[frame["gene"].astype(str) != gene].copy()


def go_table(subtype: str, gene: str) -> pd.DataFrame:
    path = gene_dir(subtype, gene) / "富集_GOBP.csv"
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    return frame if "p.adjust" in frame.columns else pd.DataFrame()


def plot_kl_bars() -> list[str]:
    stems = []
    for subtype in SUBTYPES:
        genes = [p.name for p in (ROOT / subtype / "GenKI").iterdir() if (p / "响应基因_Responsive.csv").exists()]
        usable = []
        for gene in genes:
            frame = partners(subtype, gene)
            if len(frame):
                usable.append((gene, frame.sort_values("KL", ascending=False).head(12)))
        if not usable:
            continue
        n = len(usable)
        fig, axes = plt.subplots(1, n, figsize=(3.2 * n, 4.6), squeeze=False)
        for ax, (gene, frame) in zip(axes[0], usable):
            frame = frame.iloc[::-1]
            vals = frame["KL"].clip(lower=1e-12)
            ax.barh(frame["gene"], vals, color=BAR_COLOR)
            ax.set_xscale("log")
            ax.set_xlim(float(vals.min()) / 8, float(vals.max()) * 4)
            ax.set_xlabel("KL")
            ax.set_title(f"{subtype} {gene}")
            style_ax(ax)
        fig.suptitle("Top KO-responsive genes excluding the knocked-out gene")
        fig.tight_layout()
        stems.append(save(fig, f"04_KLbar_{subtype}"))
    return stems


def plot_go_bars() -> list[str]:
    import textwrap

    stems = []
    for subtype in SUBTYPES:
        for folder in sorted((ROOT / subtype / "GenKI").iterdir()):
            frame = go_table(subtype, folder.name)
            if frame.empty:
                continue
            top = frame.sort_values("p.adjust").head(12).iloc[::-1]
            labels = ["\n".join(textwrap.wrap(str(text), 36)) for text in top["Description"]]
            fig, ax = plt.subplots(figsize=(8.6, 6.2))
            ax.barh(labels, -np.log10(top["p.adjust"].clip(lower=1e-300)), color=BAR_COLOR)
            ax.set_xlabel("-log10 adjusted P")
            ax.set_title(f"GO biological process: {subtype} {folder.name}")
            style_ax(ax)
            fig.tight_layout()
            stems.append(save(fig, f"05_GObar_{subtype}_{folder.name}"))
    return stems


def plot_search() -> list[str]:
    stems = []
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.8))
    for ax, subtype in zip(axes, SUBTYPES):
        trials = pd.read_csv(ROOT / subtype / "GenKI" / "搜索_SearchTrials.csv")
        ax.scatter(trials["trial"], trials["val_ap"], s=18, c=PEP_COLOR if subtype == "PEP" else NF1_COLOR, linewidths=0)
        best = trials.sort_values("select_score", ascending=False).iloc[0]
        ax.scatter([best["trial"]], [best["val_ap"]], s=46, c=MARK_COLOR, label="selected", zorder=3)
        ax.set_ylim(0.45, 1.02)
        ax.set_xlabel("Trial")
        ax.set_ylabel("Validation AP")
        ax.set_title(subtype)
        ax.legend(frameon=False, fontsize=8)
        style_ax(ax)
    fig.suptitle("Hyperparameter search on the wild-type graph")
    fig.tight_layout()
    stems.append(save(fig, "06_SearchValAP"))
    return stems


def plot_counts() -> list[str]:
    summary = pd.read_csv(ROOT / "对照对比_PEP_NF1_GenKI.csv")
    summary = summary[summary["role"] == "knockout"]
    genes = ["Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21"]
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    x = np.arange(len(genes))
    width = 0.36
    for offset, subtype, color in ((-0.5, "PEP", PEP_COLOR), (0.5, "NF1", NF1_COLOR)):
        part = summary[summary["subtype"] == subtype].set_index("knockout_gene")
        values = [int(part.loc[gene, "n_response_excluding_self"]) if gene in part.index else 0 for gene in genes]
        ax.bar(x + offset * width, values, width=width, color=color, label=subtype)
    ax.set_xticks(x)
    ax.set_xticklabels(genes, rotation=30, ha="right")
    ax.set_ylabel("Responsive genes excluding self")
    ax.set_title("Genes passing KL top 5% and >95% of 1000 shuffles")
    ax.legend(frameon=False)
    style_ax(ax)
    fig.tight_layout()
    return [save(fig, "07_ResponseCounts")]


def plot_overlap() -> list[str]:
    stems = []
    summary = pd.read_csv(ROOT / "对照对比_PEP_NF1_GenKI.csv")
    knockout = summary[summary["role"] == "knockout"]
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    genes = ["Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21"]
    x = np.arange(len(genes))
    for offset, subtype, color in ((-0.5, "PEP", PEP_COLOR), (0.5, "NF1", NF1_COLOR)):
        part = knockout[knockout["subtype"] == subtype].set_index("knockout_gene")
        values = [int(part.loc[gene, "n_shared_genes"]) if gene in part.index else 0 for gene in genes]
        ax.bar(x + offset * 0.36, values, width=0.36, color=color, label=subtype)
    ax.set_xticks(x)
    ax.set_xticklabels(genes, rotation=30, ha="right")
    ax.set_ylabel("Genes also found after control knockout")
    ax.set_title("Overlap with the low-correlation control")
    ax.legend(frameon=False)
    style_ax(ax)
    fig.tight_layout()
    stems.append(save(fig, "08_ControlOverlapCounts"))

    shared = partners("NF1", "Cplx2")
    shared = shared[shared["gene"].isin(["2810410L24Rik", "Calca", "Ces5a", "Kcne4", "Thbs1"])]
    if len(shared):
        shared = shared.sort_values("KL")
        fig, ax = plt.subplots(figsize=(6.2, 3.4))
        vals = shared["KL"].clip(lower=1e-12)
        ax.barh(shared["gene"], vals, color=MARK_COLOR)
        ax.set_xscale("log")
        ax.set_xlim(float(vals.min()) / 8, float(vals.max()) * 4)
        ax.set_xlabel("KL")
        ax.set_title("NF1 Cplx2 genes also recovered by Gm15551")
        style_ax(ax)
        fig.tight_layout()
        stems.append(save(fig, "08_NF1_Cplx2_SharedGenes"))
    return stems


def plot_rank_scatter() -> list[str]:
    stems = []
    for subtype, gene in (("NF1", "Cplx2"), ("NF1", "Mitf"), ("PEP", "Mitf")):
        path = gene_dir_rank(subtype, gene)
        if path is None:
            continue
        frame = pd.read_csv(path)
        fig, ax = plt.subplots(figsize=(4.6, 4.2))
        ax.scatter(frame["rank"], np.log10(frame["KL"].clip(lower=1e-12)), s=8, c=SAND_COLOR, linewidths=0)
        hit = frame[frame["hit"] > 950]
        if len(hit):
            ax.scatter(hit["rank"], np.log10(hit["KL"].clip(lower=1e-12)), s=18, c=NF1_COLOR, linewidths=0, label="hit > 950")
            ax.legend(frameon=False, fontsize=8)
        ax.set_xlabel("Rank")
        ax.set_ylabel("log10 KL")
        ax.set_title(f"{subtype} {gene}")
        style_ax(ax)
        fig.tight_layout()
        stems.append(save(fig, f"09_RankKL_{subtype}_{gene}"))
    return stems


def gene_dir_rank(subtype: str, gene: str):
    path = gene_dir(subtype, gene) / "KL排序_RankKL.csv"
    return path if path.exists() else None


def plot_r2() -> list[str]:
    try:
        import anndata
        import statsmodels.api as sm
    except Exception:
        return []
    stems = []
    rng = np.random.default_rng(8096)
    for subtype, gene in (("NF1", "Cplx2"), ("NF1", "Mitf"), ("PEP", "Mitf")):
        frame = partners(subtype, gene)
        if len(frame) < 3:
            continue
        adata = anndata.read_h5ad(ROOT / subtype / "GenKI" / f"{subtype}_hvg3000.h5ad")
        matrix = adata.layers["norm"]
        if hasattr(matrix, "toarray"):
            matrix = matrix.toarray()
        names = list(adata.var_names)
        if gene not in names:
            continue
        y = matrix[:, names.index(gene)]
        explain = [item for item in frame["gene"].astype(str) if item in names][:12]
        if len(explain) < 3:
            continue
        x = matrix[:, [names.index(item) for item in explain]]
        real = sm.OLS(y, x).fit().rsquared_adj
        nulls = []
        pool = [index for index, name in enumerate(names) if name != gene]
        for _ in range(50):
            pick = rng.choice(pool, size=len(explain), replace=False)
            nulls.append(sm.OLS(y, matrix[:, pick]).fit().rsquared_adj)
        fig, ax = plt.subplots(figsize=(4.4, 3.6))
        ax.hist(nulls, bins=12, color="#D9D9D9", edgecolor="white")
        ax.axvline(real, color=NF1_COLOR, linewidth=2, label="responsive genes")
        ax.set_xlabel("Adjusted R2")
        ax.set_ylabel("Random sets")
        ax.set_title(f"{subtype}: {gene} explained by partners")
        ax.legend(frameon=False, fontsize=8)
        style_ax(ax)
        fig.tight_layout()
        stems.append(save(fig, f"10_R2_{subtype}_{gene}"))
    return stems


def plot_more() -> list[str]:
    import anndata

    stems = []
    genes = ["Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21"]
    fig, ax = plt.subplots(figsize=(7.6, 3.2))
    for row, subtype in enumerate(SUBTYPES):
        adata = anndata.read_h5ad(ROOT / subtype / "GenKI" / f"{subtype}_hvg3000.h5ad")
        matrix = adata.layers["norm"]
        if hasattr(matrix, "toarray"):
            matrix = matrix.toarray()
        names = list(adata.var_names)
        for col, gene in enumerate(genes):
            if gene not in names:
                continue
            values = matrix[:, names.index(gene)]
            detected = values > 0
            mean = float(values[detected].mean()) if detected.any() else 0.0
            fraction = float(detected.mean())
            ax.scatter(
                col,
                row,
                s=40 + 420 * fraction,
                c=mean,
                cmap="YlGn",
                vmin=0,
                vmax=2.5,
                edgecolors="#4A4A4A",
                linewidths=0.4,
            )
    ax.set_xticks(range(len(genes)))
    ax.set_xticklabels(genes, rotation=30, ha="right")
    ax.set_yticks([0, 1])
    ax.set_yticklabels(list(SUBTYPES))
    ax.set_title("Detection fraction (size) and mean log1p in detected cells (color)")
    colorbar = fig.colorbar(
        plt.cm.ScalarMappable(norm=plt.Normalize(vmin=0, vmax=2.5), cmap="YlGn"),
        ax=ax,
        fraction=0.046,
        pad=0.04,
    )
    colorbar.set_label("Mean log1p in detected cells", fontsize=8)
    colorbar.ax.tick_params(labelsize=8, colors="#000000")
    style_ax(ax)
    fig.tight_layout()
    stems.append(save(fig, "11_Dot_KnockGenes"))

    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.6))
    for ax, subtype in zip(axes, SUBTYPES):
        trials = pd.read_csv(ROOT / subtype / "GenKI" / "搜索_SearchTrials.csv")
        ax.hist(trials["epochs_run"], bins=12, color=PEP_COLOR if subtype == "PEP" else NF1_COLOR, edgecolor="white")
        ax.set_xlabel("Epochs run before stopping")
        ax.set_ylabel("Trials")
        ax.set_title(subtype)
        style_ax(ax)
    fig.suptitle("Early stopping under the 15-epoch patience rule")
    fig.tight_layout()
    stems.append(save(fig, "12_EarlyStopEpochs"))

    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.6))
    for ax, subtype in zip(axes, SUBTYPES):
        trials = pd.read_csv(ROOT / subtype / "GenKI" / "搜索_SearchTrials.csv")
        ax.scatter(np.log10(trials["lr"]), trials["val_ap"], s=18, c=PEP_COLOR if subtype == "PEP" else NF1_COLOR, linewidths=0)
        ax.set_xlabel("log10 initial learning rate")
        ax.set_ylabel("Validation AP")
        ax.set_title(subtype)
        style_ax(ax)
    fig.suptitle("Validation AP across the searched learning rates")
    fig.tight_layout()
    stems.append(save(fig, "13_LearningRateVsAP"))

    for subtype, gene in (("NF1", "Cplx2"), ("NF1", "Gm15551"), ("NF1", "Ppp1r26")):
        frame = go_table(subtype, gene)
        if frame.empty:
            continue
        top = frame.sort_values("p.adjust").head(15)
        fig, ax = plt.subplots(figsize=(7.6, 6.4))
        sizes = top["Count"] if "Count" in top.columns else pd.Series(20, index=top.index)
        ax.scatter(
            -np.log10(top["p.adjust"].clip(lower=1e-300)),
            range(len(top)),
            s=28 + 14 * sizes,
            c=BAR_COLOR,
            edgecolors="#4A4A4A",
            linewidths=0.3,
        )
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(["\n".join(__import__("textwrap").wrap(str(text), 42)) for text in top["Description"]], fontsize=8)
        ax.invert_yaxis()
        ax.set_xlabel("-log10 adjusted P")
        ax.set_xlim(left=0)
        ax.set_title(f"GO dot plot: {subtype} {gene}")
        style_ax(ax)
        fig.tight_layout()
        stems.append(save(fig, f"14_GOdot_{subtype}_{gene}"))

    genes = partners("NF1", "Cplx2").sort_values("KL", ascending=False)["gene"].astype(str).head(12).tolist()
    if genes:
        import io
        import scipy.io

        heat_rows = []
        for subtype in SUBTYPES:
            folder = ROOT / f"输入_{subtype}"
            names = (folder / "genes.tsv").read_text(encoding="utf-8").splitlines()
            raw = (folder / "counts.mtx").read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            matrix = scipy.io.mmread(io.BytesIO(raw)).T.tocsr()
            totals = np.asarray(matrix.sum(axis=1)).ravel()
            totals[totals == 0] = 1.0
            index = {name: i for i, name in enumerate(names)}
            means = []
            for gene in genes:
                if gene not in index:
                    means.append(np.nan)
                else:
                    values = matrix[:, index[gene]].toarray().ravel()
                    means.append(float(np.log1p(values / totals * 1e4).mean()))
            heat_rows.append(means)
        heat = np.vstack(heat_rows)
        fig, ax = plt.subplots(figsize=(8.6, 2.8))
        image = ax.imshow(heat, aspect="auto", cmap="YlGn", vmin=0)
        ax.set_yticks([0, 1])
        ax.set_yticklabels(list(SUBTYPES), color="#000000")
        ax.set_xticks(range(len(genes)))
        ax.set_xticklabels(genes, rotation=40, ha="right", fontsize=8, color="#000000")
        ax.tick_params(axis="both", colors="#000000")
        ax.set_title("Mean log1p of NF1 Cplx2-responsive genes")
        colorbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
        colorbar.ax.tick_params(labelsize=8, colors="#000000")
        fig.tight_layout()
        stems.append(save(fig, "15_Heatmap_NF1_Cplx2_Genes"))

    from matplotlib.patches import FancyBboxPatch

    fig, ax = plt.subplots(figsize=(10.4, 3.2))
    ax.set_xlim(0, 10.2)
    ax.set_ylim(0, 3.2)
    ax.axis("off")
    steps = [
        (0.15, "WT counts\nPEP or NF1"),
        (2.15, "3,000 HVGs\nPC regression"),
        (4.15, "Top 15%\nedge weights"),
        (6.15, "VGAE\nzero KO edges"),
        (8.15, "KL and 1,000\npermutations"),
    ]
    colors = [PEP_COLOR, SAND_COLOR, BAR_COLOR, MARK_COLOR, NF1_COLOR]
    for (x, text), color in zip(steps, colors):
        ax.add_patch(
            FancyBboxPatch(
                (x, 1.05),
                1.75,
                1.35,
                boxstyle="round,pad=0.03,rounding_size=0.08",
                facecolor=color,
                edgecolor="#4A4A4A",
                linewidth=0.6,
            )
        )
        ax.text(x + 0.88, 1.72, text, ha="center", va="center", fontsize=8, color="#1A1A1A")
    for x in (1.92, 3.92, 5.92, 7.92):
        ax.annotate(
            "",
            xy=(x + 0.2, 1.72),
            xytext=(x, 1.72),
            arrowprops={"arrowstyle": "->", "color": "#4A4A4A", "lw": 1.1},
        )
    ax.text(
        5.1,
        0.45,
        "GO biological process uses the responsive-gene list. It does not choose the genes.",
        ha="center",
        fontsize=8,
        color="#1A1A1A",
    )
    stems.append(save(fig, "01_MethodSchematic"))
    return stems


def block(stem: str, number: str, legend: str, paragraphs: list[str]) -> str:
    path = FIG / f"{stem}.png"
    if not path.exists():
        return ""
    body = "".join(f"<p>{html.escape(text)}</p>" for text in paragraphs)
    return (
        f"<h3>{html.escape(number)}</h3>{body}"
        f"<figure><img src=\"../图片文件/{stem}.png\" alt=\"{html.escape(number)}\">"
        f"<figcaption><b>{html.escape(number)}.</b> {html.escape(legend)}</figcaption></figure>"
    )


def write_reports(stems: list[str]) -> None:
    del stems
    REPORT.mkdir(parents=True, exist_ok=True)
    sections = [
        ("01_MethodSchematic", "图 1",
         "Workflow used for each subtype. Boxes are sequential steps. GO enrichment is applied only after a gene passes the KL filter.",
         [
             "这张图把一次虚拟敲除拆成顺序，避免把富集写成筛选条件。输入只有野生型计数：PEP 或 NF1 各自一张基因乘以细胞核的矩阵。高变基因取 3000 个，主成分回归先得到边，再只保留绝对权重最高的 15%。变分图自编码器在这张网上训练。敲除时不删除细胞，只把目标基因连出的边权重置零。",
             "比较的量是每个基因在野生型和置零之后的二维潜变量，距离用 KL。稳定性来自 1000 次不放回的细胞顺序排列。过线基因才进入 GO 生物学过程。图下方那一行字是为了挡住一种常见的颠倒：先指定突触或 SNARE，再去找支持它的基因。本计划的顺序相反。",
             "同一亚群的六个靶基因和对照基因共用前面的网络和模型。改变的只有被置零的那个基因。因此亚群之间的差异可以比较，同一亚群里不同基因的差异也可以比较。",
         ]),
        ("02_UMAP_PEP_NF1", "图 2",
         "UMAP of GSE197289 Control nuclei labeled as PEP or NF1. Colors are fixed for the two subtypes.",
         [
             "这张图回答的是：按疾病标记留下的两类细胞，在转录组上是不是真的分成两群。点是 GSE197289 小鼠 Control 中作者注释为 PEP 或 NF1 的细胞核。先做总计数归一和 log1p，再取 2000 个高变基因做 PCA，邻域图和 UMAP 的随机种子是 8096。蓝绿色是 PEP，灰玫瑰色是 NF1。",
             "两类细胞核各自聚成一片，中间只有少量交错。这说明作者注释不是随意标签，PEP 和 NF1 的整体表达不同，应当分开建调控网。如果把它们合成一张网，主成分回归会把两类细胞的共变当成同一套调控，虚拟敲除的 KL 就不再对应某一种感觉神经元。",
             "图上没有疾病组和对照组的对比。这些点全部来自未造模的 Control。因此分离只说明细胞类型不同，不说明三叉神经痛改变了它们的状态。",
         ]),
        ("03_Detection_PEP_NF1", "图 2",
         "Percent of Control nuclei with a count greater than zero. PEP n = 780; NF1 n = 1765.",
         [
             "虚拟敲除之前要先看靶基因有没有被测到。柱高是表达计数大于 0 的细胞核比例。PEP 有 780 个核，NF1 有 1765 个核。Cplx2 在 PEP 为 44.0%（343 个核），在 NF1 为 50.4%（889 个核），是六个计划敲除基因里唯一广泛存在的基因。",
             "Slc28a3 在 PEP 为 10.4%，在 NF1 为 7.4%。Bace2、Ppp1r26、Mitf 都低于 8%。Sh3d21 在 PEP 只有 1 个核，在 NF1 只有 6 个核。基因被检出才进入敲除名单；检出如此稀疏时，调控网里几乎没有它的边，后续空结果首先反映的是表达太稀，而不是通路不存在。",
             "Hprt1 没有画进这张图，因为小鼠矩阵里没有这个符号。Ppia 作为定量内参也不进入敲除。",
         ]),
        ("02_Violin_KnockGenes", "图 3",
         "log1p-normalized expression of the six planned knockout genes. The width of each violin shows the density of nuclei.",
         [
             "小提琴图把检出率拆成表达高低。纵轴是每个细胞核的 log1p 标准化表达，横轴是亚群。多数基因的密度堆在 0 附近，只有一条细长的尾巴伸到高表达，表示只有少数细胞核转录了这个基因。",
             "Cplx2 是例外。PEP 和 NF1 都有可见的主体，NF1 的分布更宽，中位数仍接近低值，但高表达细胞核明显多于其他靶基因。这与检出率图一致：Cplx2 是唯一适合在这两类细胞里讨论突触相关功能的靶基因，其余基因更像稀有转录事件。",
             "Sh3d21 的小提琴几乎贴在 0 上。对它做 GenKI 仍按计划执行，因为检出细胞数不是 0；解释时必须把细胞数写在结果旁边。",
         ]),
        ("11_Dot_KnockGenes", "图 4",
         "Dot plot of the same six genes. Point size is the detection fraction. Color is the mean log1p among nuclei with a nonzero count.",
         [
             "点图同时放了两个量。点的大小是检出比例，颜色是在已检出细胞核里的平均 log1p。这样可以看出一个基因是“很多细胞少量表达”，还是“很少细胞但表达很高”。",
             "Cplx2 的点最大。在已检出细胞核里，它的平均 log1p 在 NF1 是 3.77，在 PEP 是 2.29，颜色达到色标顶端。Mitf、Bace2、Ppp1r26 的点小，检出细胞核里的平均大约在 1.5 到 2.2，并不是零。Slc28a3 的点中等。Sh3d21 的点最小：PEP 只有 1 个核，NF1 只有 6 个核；这几个核的平均并不低，只是细胞数太少。",
             "因此后续如果某个低检出基因没有响应基因，不能把它和 Cplx2 的空结果当成同一类生物学结论。前者是输入几乎为空，后者是输入存在但筛选后没有稳定的其他基因。",
         ]),
        ("06_SearchValAP", "图 5",
         "Validation average precision for 100 random hyperparameter trials. The highlighted point is the trial chosen by validation AP minus any train-validation gap.",
         [
             "每个点是一次超参数试验在验证集链接预测上的 AP。学习率、beta 和 weight decay 都在论文给出的范围内随机抽取，每个亚群 100 次。高亮点是挑选分最高的试验：验证 AP 减去训练 AP 高于验证 AP 的那一部分。",
             "两个亚群都有一批试验停在 AP 约 0.5，这是没有学到边的水平，通常对应过大的初始学习率。另一批试验集中在 0.90 以上。PEP 选中试验的验证 AP 为 0.951，训练 AP 为 0.953，差距 0.002。NF1 选中试验的验证 AP 为 0.965，训练 AP 为 0.964，差距为负，说明验证没有差于训练。",
             "挑选用的是野生型图的链接预测，不是敲除后的 KL。因此一张网、一套模型可以供该亚群的多个基因共用。基因不同，只是被置零的边不同。",
         ]),
        ("12_EarlyStopEpochs", "图 6",
         "Number of epochs completed before the 15-epoch patience rule stopped each trial.",
         [
             "早停规则是至少训练 10 轮；验证 AP 必须比当前最好高出 0.0001 才算提高；连续 15 轮没有提高才停止，并回到验证 AP 最高的那一轮。这张直方图是 100 次搜索各自实际跑了多少轮。",
             "多数试验在十几轮到几十轮停止，说明规则允许验证集波动，而不是下一轮稍差就停。也有试验跑满 100 轮，验证 AP 一直没有连续 15 轮停滞。正式模型的记录是：PEP 最好出现在第 71 轮，一共跑了 87 轮；NF1 最好出现在第 1 轮，第 17 轮停止。NF1 很早见顶，是这次数据上的结果，不是把耐心改回 1 轮。",
             "学习率还会在验证 AP 连续 5 轮不提高时乘 0.5。PEP 选中模型在最好一轮的学习率是 0.0005，结束时是 0.000125。NF1 最好一轮仍是初始学习率 0.02，结束时降到 0.005。",
         ]),
        ("13_LearningRateVsAP", "图 7",
         "Validation AP against the base-10 logarithm of the initial learning rate.",
         [
             "学习率的搜索范围是 0.0001 到 0.9。横轴取对数，是为了把几个数量级放在同一张图上。纵轴仍是验证 AP。",
             "过大的初始学习率集中在图的右侧，验证 AP 掉到 0.5 附近。中等学习率更容易到达 0.9 以上。这就是学习率和拟合的关系：步长太大时模型没有拟合到验证边；步长合适时验证 AP 升高。过拟合要看的是训练 AP 是否明显高于验证 AP，而不是学习率本身。这次选中的两次试验，训练和验证的差距都在 0.003 以内。",
             "因此没有把学习率固定成论文在别的数据集上得到的 0.0007 或 0.005。每个亚群用自己图上的搜索结果。",
         ]),
        ("07_ResponseCounts", "图 8",
         "Count of genes that passed the KL filter after excluding the knocked-out gene itself.",
         [
             "一根柱子是一个靶基因在一个亚群里的其他响应基因数。筛选是 KL 进入该次排列的 top 5%，并且在 1000 次不放回排列里出现超过 950 次。被敲除的基因自己几乎总会过线，所以已经从计数里去掉。",
             "PEP：Mitf 为 9，Bace2、Cplx2、Ppp1r26、Slc28a3、Sh3d21 都是 0。NF1：Mitf 为 27，Cplx2 为 33，Ppp1r26 为 24，Slc28a3 为 6，Bace2 为 0，Sh3d21 为 0。对照没有画在这张柱里。PEP 的对照 Abcc8 也是 0；NF1 的对照 Gm15551 是 144。",
             "PEP 的 Cplx2 没有其他响应基因，不能从这次计算里选出一条 PEP 特异通路。NF1 的数字更高，但必须先减去和对照重合的部分，否则对照自己的 144 个基因会把很多通路一起带出来。",
         ]),
        ("04_KLbar_NF1", "图 9",
         "Top responsive genes in NF1, excluding the knocked-out gene. Bar length is KL on a logarithmic scale.",
         [
             "NF1 有响应基因的敲除都放在这张多面板里。横轴是 KL 的以 10 为底的对数。Cplx2 面板的最高基因是 Calca、Cd9、Ret、Prkcb、Ntrk3，KL 比其余基因高几个数量级。这些基因名来自响应基因表，不是事后从通路名单里挑的。",
             "Mitf 和 Ppp1r26 的 KL 小于 1，Cplx2 头部基因的 KL 则高出几个数量级。对数轴把这两种幅度放在同一张图里，条形仍然都朝右。它们通过了重复出现次数的筛选，但扰动幅度远小于 Cplx2 的头部基因。读图时不能把所有过线基因都说成同等强度的候选。",
             "Gm15551 是对照，不是疾病基因。它的头部同样出现 Calca。这解释了为什么 Cplx2 与对照会共享趋化相关基因：对照敲除本身就会把 Calca 排到前面。",
         ]),
        ("04_KLbar_PEP", "图 10",
         "Top responsive genes in PEP. Only Mitf produced partners that passed the repetition filter.",
         [
             "PEP 只有 Mitf 的面板里有其他基因。表里的 9 个基因是 4930590J08Rik、A430046D13Rik、Glipr1、Gm11240、Krt10、Mblac1、Morc4、Mycbpap 和 Pcdhb18。它们没有和对照 Abcc8 重合，因为对照一个其他基因都没有过线。",
             "Cplx2、Bace2、Ppp1r26、Slc28a3 在 PEP 的响应表里只剩下基因自己，所以这张 KL 图不给它们画空面板。空结果要写在文字里：在 PEP 这张网上，这些敲除没有稳定的其他响应基因。",
             "Mitf 在 PEP 的检出率只有 1.8%。9 个响应基因可以记录，但不宜直接提升为肥大细胞或三叉神经痛通路。GenKI 用的是感觉神经元 PEP，不是肥大细胞。",
         ]),
        ("09_RankKL_NF1_Cplx2", "图 11",
         "All genes in the NF1 graph. Grey-sand points are the full ranking. Rose points were recovered in more than 950 of 1000 shuffles.",
         [
             "这张散点把 NF1、Cplx2 敲除的全部排名画出来，而不是只画前 12 个。横轴是按 KL 从高到低的名次，纵轴是 log10 KL。玫瑰色点是 hit 大于 950 的基因。",
             "曲线在最左侧陡降，随后长尾贴着低 KL。陡降的那一段才是重复筛选留下来的基因。长尾里的基因 KL 很小，而且没有在 95% 以上的排列里重复出现，不能因为名字像神经基因就补进结果。",
             "Cplx2 自己位于最左上。它的 KL 极大，是因为边被置零后它的潜变量必然远离野生型。解释通路时用的是它右侧那些其他基因。",
         ]),
        ("09_RankKL_NF1_Mitf", "图 12",
         "Rank versus log10 KL for the NF1 Mitf knockout.",
         [
             "NF1 的 Mitf 敲除同样先陡后平。玫瑰色点对应 27 个其他响应基因加上 Mitf 自己。和 Cplx2 相比，纵轴整体更低，说明过线基因的 KL 较小。",
             "这些基因与 Gm15551 的响应基因没有交集。就“是否被对照重复发现”这一条而言，Mitf 的名单比 Cplx2 更干净。它们的 KL 大约在 10 的负 4 次方，远小于 Cplx2 头部基因。这 27 个基因没有产生通过校正阈值的 GO 生物学过程，富集表是空的。名单可以保留，但目前没有一条可跟随的生物学过程。",
         ]),
        ("09_RankKL_PEP_Mitf", "图 13",
         "Rank versus log10 KL for the PEP Mitf knockout.",
         [
             "PEP 的 Mitf 是该亚群唯一有其他过线基因的敲除。散点左侧的玫瑰色点对应那 9 个基因。其余排名迅速落到很低的 KL。",
             "因为 PEP 的对照 Abcc8 没有其他响应基因，这 9 个基因目前没有被这个阴性对照重复出来。它们也没有产生通过校正的 GO 生物学过程。样本仍是正常三叉神经节的 PEP 核，不能把 Krt10 或原钙粘蛋白基因直接写成三叉神经痛的机制。",
         ]),
        ("08_ControlOverlapCounts", "图 14",
         "Number of responsive genes that were also responsive after knocking out the low-correlation control in the same subtype.",
         [
             "柱高是与对照响应基因的交集大小。PEP 的六次敲除都是 0，因为 Abcc8 没有其他响应基因。NF1 只有 Cplx2 的柱子是 5，Mitf、Ppp1r26、Slc28a3 是 0，Bace2 和 Sh3d21 自己也没有其他响应基因。",
             "交集为 0 并不自动使结果特异。NF1 的对照有 144 个响应基因，一个靶基因即使交集为 0，仍要看它的 GO 是否落在对照那 28 条术语的邻域里。本图只计基因交集，GO 交集写在总表的 shared_go 列。",
             "Cplx2 在 NF1 的基因交集是 2810410L24Rik、Calca、Ces5a、Kcne4 和 Thbs1。",
         ]),
        ("08_NF1_Cplx2_SharedGenes", "图 15",
         "KL of the five NF1 genes recovered by both Cplx2 knockout and Gm15551 knockout. The axis is logarithmic.",
         [
             "这五个基因是从 Cplx2 的响应表里取出、并且也出现在 Gm15551 响应表里的名字。Calca 的 KL 最高。它们通过了 Cplx2 的重复筛选，但同样通过了对照的重复筛选。",
             "因此 Calca 可以保留在 NF1、Cplx2 的候选列表中，同时必须注明它不是对照敲除所独有的反例。后续如果做 qPCR 或蛋白验证，Calca 需要有一个不依赖 GenKI 的理由，不能只因为它出现在虚拟敲除名单里。",
         ]),
        ("05_GObar_NF1_Cplx2", "图 16",
         "Top GO biological process terms for NF1 Cplx2-responsive genes, ordered by adjusted P. Bar length is -log10 adjusted P.",
         [
             "富集的输入是 NF1、Cplx2 敲除后过线的响应基因，没有事先限定突触囊泡、SNARE 或递质释放。横轴是校正后 P 值的负对数，只显示校正 P 最小的 12 条。",
             "排在前面的包括 response to pain、wound healing、phosphatidylinositol、myeloid leukocyte migration、chemotaxis 和 taxis。疼痛相关条目出现，是这次基因表算出来的，不是把疼痛词表塞进分析。基因数只有三十多个，一条术语往往只含两三个基因，条目容易受单个基因影响。",
             "其中 chemotaxis、taxis、leukocyte migration、myeloid leukocyte migration 和 cytosolic calcium 的正调控也出现在对照 Gm15551 的富集里。这些条不能作为 Cplx2 特异通路写进结论。response to pain 没有出现在那 8 条共有术语里，可以作为 NF1 上相对更值得跟随的候选，但仍是计算预测。",
         ]),
        ("14_GOdot_NF1_Cplx2", "图 17",
         "The same NF1 Cplx2 GO terms as a dot plot. Position is -log10 adjusted P. Point size increases with the number of genes in the term.",
         [
             "点图和前一张水平柱使用同一张富集表。横轴从 0 起算。这些术语的 -log10 校正 P 都挤在 1.6 附近，因为校正 P 都在 0.023 到 0.027，彼此几乎没有差距。点的大小是落入该术语的基因数：疼痛是 3，趋化是 5。",
             "基因数少时，校正 P 值可以很小，但稳定性差。对照一旦共享其中的基因，术语就会跟着共享。所以点图用来检查“显著是不是只靠一两个基因”，不能单独当作通路已经选定。",
         ]),
        ("05_GObar_NF1_Gm15551", "图 18",
         "GO biological process terms for the NF1 control knockout Gm15551.",
         [
             "Gm15551 与 Cplx2 的 Pearson 相关约 0.00006，按规则它是低相关对照，不是第二个疾病靶点。它自己产生 144 个其他响应基因和 28 条 GO 生物学过程。",
             "术语里有趋化、白细胞迁移、胞质钙、白细胞介素 8、巨噬细胞活化、ERK 级联和神经炎症反应。这些功能出现在一个低相关基因的敲除里，说明 NF1 这张网在虚拟敲除下容易把免疫和趋化相关基因推到前面。",
             "因此 NF1 上任何与这些术语重合的靶基因结果，都要先从特异结论里去掉。对照不是用来证明模型失效的摆设，它用来标出这张网的背景响应。",
         ]),
        ("14_GOdot_NF1_Gm15551", "图 19",
         "Dot plot of the Gm15551 GO terms.",
         [
             "对照的点图显示，若干免疫和趋化术语同时具有较小的校正 P 和较多的基因数。背景响应不是一条孤立术语。",
             "和 Cplx2 的点图对照着看：两边都有的术语，即使在 Cplx2 图上点很大，也不能单独留给 Cplx2。",
         ]),
        ("05_GObar_NF1_Ppp1r26", "图 20",
         "GO biological process terms for NF1 Ppp1r26-responsive genes.",
         [
             "Ppp1r26 在 NF1 有 24 个其他响应基因，与 Gm15551 的基因交集为 0，GO 术语交集也是 0。校正后排在前面的生物学过程是输尿管发育、上皮细胞增殖的调控、去甲肾上腺素生物合成、输尿管芽形态发生和肺发育。这些术语不是预先指定的，也不是疼痛通路。",
             "基因名单虽然不与对照重合，KL 却在 10 的负 6 次方。126 条术语来自这样弱的扰动，说明富集对小基因集很敏感，不能因为条目多就把 Ppp1r26 排到 Cplx2 前面。NF1 上更值得保留的仍是 Cplx2 中 KL 高、且不在对照交集里的基因，例如 Cd9、Ret、Prkcb 和 Ntrk3。",
         ]),
        ("14_GOdot_NF1_Ppp1r26", "图 21",
         "Dot plot for the NF1 Ppp1r26 enrichment.",
         [
             "点的大小是落入该术语的响应基因数。Ppp1r26 靠前的术语里，去甲肾上腺素生物合成只有 2 个基因，上皮细胞增殖有 5 个。点小而校正 P 不低的术语对单个基因敏感，只适合放在候选列表的后部。结合 KL 约 10 的负 6 次方，这组术语不作为优先通路。",
         ]),
        ("05_GObar_NF1_Slc28a3", "图 22",
         "GO biological process terms for NF1 Slc28a3-responsive genes.",
         [
             "Slc28a3 在 NF1 只有 6 个其他响应基因：B230312C02Rik、Ccdc125、Dvl3、Gm10687、Naip5 和 Pdgfrl。KL 大约在 0.3 到 1.2。它们都不在 Gm15551 的响应基因里。",
             "34 条 GO 生物学过程里，靠前的是 JNK 级联及其正调控，每条只有 2 个基因；嘌呤碱基转运、核苷转运和中脑多巴胺神经元分化的基因数是 1。Slc28a3 在 NF1 的检出率是 7.4%。这些术语可以留在记录里，不宜排在 Cplx2 那些高 KL 基因前面。",
         ]),
        ("08_ControlOverlapCounts", "图 14",
         "",
         []),
        ("15_Heatmap_NF1_Cplx2_Genes", "图 23",
         "Mean log1p expression, from the full count matrix, of the twelve NF1 Cplx2-responsive genes with the largest KL. Color starts at zero. Labels are black.",
         [
             "列是 NF1 里 Cplx2 虚拟敲除后 KL 最高的 12 个其他基因。颜色是全部基因计数做总计数归一和 log1p 之后的细胞平均，不限于 3000 个高变基因。色标从 0 开始，标签为黑色。",
             "Calca 在 PEP 的平均 log1p 是 4.23，检出 98.8%；在 NF1 是 2.26，检出 67.5%。Cd9 在 PEP 是 3.05（96.4%），在 NF1 是 2.41（79.0%）。Ret 和 Prkcb 在 PEP 的检出率也高于 NF1。Prelp 在两群都接近 0。",
             "因此 PEP 没有给出 Cplx2 的其他响应基因，不是因为 Calca、Cd9 或 Ret 在 PEP 里缺失。它们在 PEP 里表达更高。空结果来自 KL 和重复筛选，不来自基因没被测到。这张图也不是疾病对正常的差异分析，两行都是 Control。",
         ]),
        ("10_R2_NF1_Cplx2", "图 24",
         "Adjusted R2 when NF1 Cplx2 expression is regressed on its responsive genes, compared with 50 random gene sets of the same size.",
         [
             "这张图对应 GenKI 论文里的一个检查：敲除基因在细胞间的表达，能否被它的响应基因解释，并且好于同样个数的随机基因。这里用的是建网前的 log1p 表达，响应基因最多取 KL 最高的 12 个，随机重复 50 次，种子 8096。竖线是响应基因的调整 R2，灰色是随机基因集。",
             "NF1 的 Cplx2 竖线落在随机分布的右侧，调整 R2 约为 0.57，50 次随机大约在 0.25 到 0.50。就这张图而言，Cplx2 的表达和它的响应基因在数值上有关联，不是完全无关的名单。",
             "这仍然不是湿实验验证。回归用的是同一张野生型矩阵，响应基因也从这张矩阵的模型里来，存在循环使用同一数据的限制。它支持“名单与 Cplx2 表达有关”，不支持“三叉神经痛中 Cplx2 通过这些基因致病”。",
         ]),
        ("10_R2_NF1_Mitf", "图 24",
         "The same regression check for NF1 Mitf.",
         [
             "NF1 的 Mitf 也和随机基因集比较。读图时看竖线是否离开灰色分布。若竖线埋在灰色直方图里，这 12 个响应基因并不比随机基因更能解释 Mitf 的表达，名单的优先级应下降。",
             "Mitf 的细胞类型注释在引物表里是肥大细胞转录因子，而模型细胞是 NF1 感觉神经元。即便 R2 较高，也不能把结果解释成肥大细胞里的 Mitf 功能。",
         ]),
        ("10_R2_PEP_Mitf", "图 25",
         "The same regression check for PEP Mitf.",
         [
             "PEP 只有 Mitf 有足够的其他响应基因来做这个回归。图的读法和 NF1 相同。PEP 中 Cplx2 没有其他响应基因，因此没有 Cplx2 的 R2 图，这本身就是结果：没有一组伙伴基因可供回归。",
         ]),
    ]
    # drop the accidental duplicate key by keeping the first detailed block only
    seen = set()
    ordered = []
    for item in sections:
        if item[0] in seen:
            continue
        seen.add(item[0])
        ordered.append(item)

    def render(opening: str) -> str:
        parts = [opening]
        for index, (stem, _number, legend, paragraphs) in enumerate(ordered, start=1):
            parts.append(block(stem, f"图 {index}", legend, paragraphs))
        return "\n".join(parts)

    methods_open = """
<h2>1. 这份报告在回答什么</h2>
<p>研究计划里的虚拟敲除，是在亚群已经按疾病标记确定之后，用 GenKI 逐个敲除 Mitf、Bace2、Cplx2、Ppp1r26、Slc28a3 和 Sh3d21，再用得到的响应基因做富集，从中挑选以后可以做实验的候选通路。数据是 GSE197289 的 Control，不是慢性三叉神经痛模型。下面每一节先写这张图在计划里的位置，再给图，然后写从图上能读出的数字和不能写出的结论。</p>
<h2>2. 为什么没有做疾病对对照的差异分析</h2>
<p>差异分析需要同一组织里的疾病组和对照组。GSE197289 的非 Control 分组是硬膜炎性汤和皮质扩布性抑制，两者都是偏头痛模型。若用它们对 Naive 做差异分析，得到的是头痛模型的转录变化，不是三叉神经痛。小鼠三叉神经节的 IoN-CCI 数据 GSE316925 是 bulk，没有单细胞，不能拆成 GenKI 要的细胞矩阵，也不能在 PEP 和 NF1 里分别做差异分析。因此差异分析在现有公开数据上不成立，没有为了凑齐四种分析而做。单细胞图、虚拟敲除和富集是这份数据能够支持的三步。</p>
<h2>3. 原理</h2>
<p>GenKI 只接收野生型的基因乘以细胞矩阵。主成分回归先得到一张全连接网，再保留绝对权重最高的 15% 边。变分图自编码器把每个基因记成二维高斯。敲除时把该基因所有边的权重置零，比较每个基因在两种输入下的分布，距离是 KL。1000 次不放回排列打乱细胞顺序，不重新训练。一个基因要同时满足：该次 KL 位于 top 5%，并且在超过 950 次排列里出现。论文用这个名单做功能注释。本计划同样先有名单，再做 GO 生物学过程，不把突触囊泡或 SNARE 写进筛选条件。</p>
"""
    paper_open = """
<h2>摘要</h2>
<p>目的：在没有小鼠慢性三叉神经痛三叉神经节单细胞数据时，用正常三叉神经节中与 CGRP、NF200 对应的细胞，预测六个候选基因被虚拟敲除后的响应基因，并由此列出候选生物学过程。方法：GSE197289 Control 的 PEP（780 个核）和 NF1（1765 个核）分别建网。GenKI 搜索 100 组超参数，早停为连续 15 轮验证 AP 无明显提高，零分布为 1000 次不放回排列。每个亚群另敲一个与 Cplx2 低相关的对照基因。结果：PEP 中只有 Mitf 得到 9 个其他响应基因，Cplx2 没有。NF1 中 Cplx2 得到 33 个其他响应基因，其中 5 个和 8 条 GO 术语也出现在对照 Gm15551 中。结论：这些名单是正常三叉神经节上的计算预测，可用于挑选后续实验，不能写成三叉神经痛机制已经证实。</p>
<h2>1. 引言</h2>
<p>三叉神经痛相关的实验标记把关注点放在肽能和有髓感觉神经元上，对应公开图谱里的 PEP 和 NF1。Cplx2 在这两类细胞中检出率分别为 44.0% 和 50.4%。同一引物表里的 Mitf、Bace2、Ppp1r26、Slc28a3 和 Sh3d21 检出率低得多，但仍被列入逐个敲除，以便和 Cplx2 比较。虚拟敲除的用途是提出候选通路。疾病模型和 bulk 数据都不能替代这一步所缺的单细胞疾病矩阵，因此本文不报告三叉神经痛对对照的差异表达。</p>
<h2>2. 方法</h2>
<p>计数和作者注释来自 GSE197289 小鼠 Control。高变基因使用 Seurat vst，每群 3000 个，计划敲除且有检出的基因若不在其中则补入。边阈值是绝对权重的前 15%。初始学习率、beta 和 weight decay 的搜索范围与 Yang 等 2023 年原文一致。挑选分是验证集 AP 减去训练高于验证的差距。细胞排列不放回，种子为 0。模型种子为 8096。富集是 clusterProfiler 的 GO 生物学过程，输入为过线响应基因，去掉被敲除基因本身。对照基因在同一套基因中取与 Cplx2 绝对 Pearson 相关最小者。</p>
<h2>3. 结果</h2>
"""
    css = """<style>
body{font-family:Georgia,serif;max-width:920px;margin:36px auto;line-height:1.7;color:#222;padding:0 18px}
h1{font-size:24px;line-height:1.35} h2{font-size:20px;margin-top:32px} h3{font-size:16px;margin-top:26px}
p{margin:10px 0 12px} figure{margin:14px 0 22px} img{max-width:100%;height:auto}
figcaption{font-size:13px;color:#333;line-height:1.5;margin-top:6px}
</style>"""
    pages = (
        ("报告_原理方法与数据分析.html", "虚拟敲除的原理、方法与数据分析", methods_open),
        ("报告_论文式阐述.html", "正常小鼠三叉神经节 PEP 与 NF1 中六个候选基因的 GenKI 虚拟敲除", paper_open),
    )
    closer_methods = """
<h2>4. 从结果里能选出的候选，以及选不出的部分</h2>
<p>若按“有其他响应基因、不与对照重合、并且扰动幅度不是极小”来排，NF1 里更值得保留的是 Cplx2 的 33 个基因去掉 Calca、Thbs1、Ces5a、Kcne4 和 2810410L24Rik 之后的部分。Cd9、Ret、Prkcb、Ntrk3 的 KL 在 10 的 4 到 5 次方。Mitf 的 27 个基因不与对照重合，但 KL 约 10 的负 4 次方，而且没有通过校正的 GO 术语。Ppp1r26 的 24 个基因给出 126 条术语，排在前面的是输尿管发育和去甲肾上腺素生物合成，KL 约 10 的负 6 次方，不能因为条目多就优先。Slc28a3 的 6 个基因指向 JNK 级联，每条术语只有 1 到 2 个基因。PEP 没有给出 Cplx2 的其他响应基因。疼痛相关 GO 只作为 NF1、Cplx2 富集表里的一条候选，基因数是 3，并且要和对照的 8 条共有术语分开写。</p>
<h2>5. 没有做的分析</h2>
<p>没有做三叉神经痛对正常的差异分析，因为这份单核数据的疾病分组不是三叉神经痛。没有把 GSE316925 的 bulk 拆成单细胞。没有画 STRING 网络，因为没有检索到可引用的真实边。通路筛选就是上述富集，没有另做一套预先指定的突触基因集检验。</p>
"""
    closer_paper = """
<h2>4. 讨论</h2>
<p>虚拟敲除适合放在论文的候选通路一节，不适合放在疾病机制已经证实的一节。PEP 与 NF1 的分离、Cplx2 的高检出，以及 NF1 中一组高 KL 且不与对照重合的基因，是这一节能够写实的内容。对照 Gm15551 产生比 Cplx2 更多的响应基因，说明 NF1 网络对“去掉一个基因的边”本身就会给出大名单。特异结论必须经过对照过滤。</p>
<p>Sh3d21 几乎没有检出，Bace2 在两个亚群都没有其他响应基因。这些阴性结果应当写入论文，避免只报告有富集的基因。数据不能代表慢性三叉神经痛中的三叉神经节，也不能代表每只鼠的独立重复。</p>
"""
    for filename, title, opening in pages:
        closer = closer_methods if "原理" in title else closer_paper
        html_text = (
            f"<!DOCTYPE html><html lang='zh'><head><meta charset='utf-8'><title>{html.escape(title)}</title>{css}</head>"
            f"<body><h1>{html.escape(title)}</h1>{render(opening)}{closer}</body></html>"
        )
        (REPORT / filename).write_text(html_text, encoding="utf-8")


def main() -> None:
    stems = []
    stems += plot_kl_bars()
    stems += plot_go_bars()
    stems += plot_search()
    stems += plot_counts()
    stems += plot_overlap()
    stems += plot_rank_scatter()
    stems += plot_r2()
    stems += plot_more()
    write_reports(stems)
    print("REPORT_DONE", len(stems), flush=True)


if __name__ == "__main__":
    main()

