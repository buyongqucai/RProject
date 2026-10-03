"""KEGG official pathway maps for GenKI results.

Selection is the enrichKEGG table, not a pre-chosen pathway list.
A map is downloaded only when at least two response genes sit on that pathway.
Download follows the network-pharmacology function: KEGG REST /get/{id}/image.
"""

from __future__ import annotations

import html
import math
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(r"C:\Users\10540\Desktop\琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO\GenKI_GenKI\结果文件")
FIG = ROOT / "图片文件"
MAP_DIR = FIG / "KEGG官方通路图"
REPORT = ROOT / "报告文件"
BAR = "#6B8F71"
TIMEOUT = 180
RETRIES = 4
MIN_GENES_ON_MAP = 2


def safe_name(text: str) -> str:
    cleaned = re.sub(r"[^\w\-]+", "_", str(text))
    return cleaned.strip("_")[:50] or "pathway"


def is_good_png(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 1000:
        return False
    return path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def fetch_png(url: str) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "RProject-GenKI/1.0 (academic)"})
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                data = response.read()
            if data.startswith(b"\x89PNG") and len(data) > 1000:
                return data
            raise RuntimeError(f"unexpected payload bytes={len(data)}")
        except (TimeoutError, urllib.error.URLError, RuntimeError, OSError) as error:
            last_error = error
            wait = 2.0 * attempt
            print(f"RETRY {attempt}/{RETRIES} {error!r} sleep {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"failed {url}: {last_error}")


def control_genes(subtype: str) -> set[str]:
    control = {"PEP": "Abcc8", "NF1": "Gm15551"}[subtype]
    path = ROOT / subtype / "GenKI" / control / "响应基因_Responsive.csv"
    if not path.exists():
        return set()
    frame = pd.read_csv(path)
    return set(frame.loc[frame["gene"].astype(str) != control, "gene"].astype(str))


def style_ax(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=8)


def plot_bars(table: pd.DataFrame) -> list[str]:
    stems = []
    FIG.mkdir(parents=True, exist_ok=True)
    for (subtype, gene), part in table.groupby(["subtype", "knockout_gene"], sort=False):
        part = part.sort_values("p.adjust", ascending=False)
        labels = ["\n".join(__import__("textwrap").wrap(str(text), 42)) for text in part["Description"]]
        fig, ax = plt.subplots(figsize=(8.8, max(3.2, 0.48 * len(part) + 1.2)))
        ax.barh(labels, [-math.log10(max(float(value), 1e-300)) for value in part["p.adjust"]], color=BAR)
        ax.set_xlabel("-log10 adjusted P")
        ax.set_title(f"KEGG: {subtype} {gene}")
        style_ax(ax)
        fig.tight_layout()
        stem = f"16_KEGGbar_{subtype}_{gene}"
        fig.savefig(FIG / f"{stem}.png", dpi=600, bbox_inches="tight", facecolor="white")
        fig.savefig(FIG / f"{stem}.svg", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        stems.append(stem)
    return stems


def download_maps(table: pd.DataFrame) -> pd.DataFrame:
    chosen = table[table["Count"] >= MIN_GENES_ON_MAP].copy()
    chosen = chosen.sort_values(["subtype", "knockout_gene", "p.adjust"])
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for rank, (_, row) in enumerate(chosen.iterrows(), start=1):
        pathway_id = str(row["ID"])
        url = f"https://rest.kegg.jp/get/{pathway_id}/image"
        fname = f"{rank:02d}_{row['subtype']}_{row['knockout_gene']}_{pathway_id}_{safe_name(row['Description'])}.png"
        dest = MAP_DIR / fname
        if is_good_png(dest):
            print("HAVE", fname, flush=True)
        else:
            print("GET", url, flush=True)
            dest.write_bytes(fetch_png(url))
            time.sleep(0.7)
        symbols = [item for item in str(row["gene_symbol"]).split("/") if item and item != "nan"]
        shared = sorted(set(symbols) & control_genes(row["subtype"]))
        rows.append(
            {
                "rank": rank,
                "subtype": row["subtype"],
                "knockout_gene": row["knockout_gene"],
                "pathway_id": pathway_id,
                "description": row["Description"],
                "p.adjust": row["p.adjust"],
                "count": int(row["Count"]),
                "genes": "/".join(symbols),
                "genes_also_in_control": "/".join(shared),
                "file": fname,
                "url": url,
            }
        )
    manifest = pd.DataFrame(rows)
    manifest.to_csv(MAP_DIR / "00_通路图清单.csv", index=False, encoding="utf-8-sig")
    (MAP_DIR / "README.txt").write_text(
        "KEGG 官方通路图，下载方式与网络药理学脚本 24_download_kegg_pathway_maps.py 相同：\n"
        "https://rest.kegg.jp/get/{pathway_id}/image\n"
        "入选规则：enrichKEGG 通过 BH、p=0.05、q=0.2，并且至少 2 个响应基因落在该通路。\n"
        "只有 1 个基因的通路留在富集表里，不下载通路图。\n"
        "仅学术用途。KEGG 条款：https://www.kegg.jp/kegg/legal.html\n"
        "引用：Kanehisa M, Goto S. KEGG: Kyoto Encyclopedia of Genes and Genomes. Nucleic Acids Res. 2000.\n",
        encoding="utf-8",
    )
    return manifest


def append_reports(manifest: pd.DataFrame, bar_stems: list[str]) -> None:
    blocks = []
    blocks.append("<h2>6. KEGG 通路是怎么选的，以及通路图</h2>")
    blocks.append(
        "<p>GO 和 KEGG 用的是同一条规则，都不是事先指定通路。基因集是该次虚拟敲除里通过 KL 筛选的响应基因，去掉被敲除基因自己。少于 5 个基因不做检验。GO 用 enrichGO 的生物学过程，小鼠 SYMBOL，BH 校正，p 值阈值 0.05，q 值阈值 0.2。之前图上的 12 条是校正 P 最小的那些，不是第二次挑选。突触囊泡、递质释放这几个 GO 号只写在记录里，没有用来过滤。KEGG 这一步之前没有做。现在用 enrichKEGG，物种 mmu，基因先从符号转到 Entrez，阈值与 GO 相同。</p>"
    )
    blocks.append(
        "<p>通过 KEGG 阈值的结果是：NF1 的 Cplx2 有 6 条，Ppp1r26 有 3 条，Slc28a3 有 12 条；PEP 的 Mitf 有 4 条。对照基因 NF1 的 Gm15551 和 PEP 的 Abcc8 没有通过阈值的 KEGG 通路，所以没有通路层面的对照重合。Slc28a3 的 12 条每条只有 1 个基因，Dvl3 或 Naip5。一个基因撑起的通路留在表里，不画成通路图。通路图只下载至少含有 2 个响应基因的通路，顺序按校正 P。下载函数与网络药理学的官方通路图相同，地址是 rest.kegg.jp/get/{通路号}/image。图是 KEGG 官方位图，不是本课题重绘的拓扑，也不能把癌症通路的名字写成 Cplx2 导致肿瘤。</p>"
    )
    for stem in bar_stems:
        blocks.append(
            f"<figure><img src=\"../图片文件/{stem}.png\" alt=\"{html.escape(stem)}\">"
            f"<figcaption>{html.escape(stem)}. KEGG terms that passed BH p = 0.05 and q = 0.2. "
            "Bar length is -log10 adjusted P. Terms with one gene are shown here and are not drawn as maps.</figcaption></figure>"
        )
    for _, row in manifest.iterrows():
        shared = row["genes_also_in_control"] or "none"
        blocks.append(
            f"<figure><img src=\"../图片文件/KEGG官方通路图/{html.escape(str(row['file']))}\" alt=\"{html.escape(str(row['pathway_id']))}\">"
            f"<figcaption>{html.escape(str(row['subtype']))} {html.escape(str(row['knockout_gene']))}, {html.escape(str(row['pathway_id']))} "
            f"{html.escape(str(row['description']))}. Adjusted P = {float(row['p.adjust']):.4g}. "
            f"Response genes on this map: {html.escape(str(row['genes']))}. "
            f"Also recovered by the control knockout: {html.escape(str(shared))}. "
            "Official KEGG image, academic use.</figcaption></figure>"
        )
    blocks.append(
        "<p>NF1、Cplx2 的 6 条里，钙信号和 MAPK 各有 4 个响应基因：Ret、Prkcb、Ntrk3、Fgfr1，MAPK 里是 Ret、Prkcb、Fgfr1、Fos。蛋白聚糖那条含有 Thbs1，而 Thbs1 也出现在对照 Gm15551 的响应基因里；通路本身没有在对照的 KEGG 检验里过线。中央碳代谢、蛋白聚糖和乳腺癌这三条用了 KEGG 的癌症地图，落在上面的是受体酪氨酸激酶和 Fos，不是肿瘤表型。Ppp1r26 的神经活性配体–受体相互作用有 Chrm3、Npy1r、Lypd6、Gabra3，但这组基因的 KL 约在 10 的负 6 次方，统计过线不等于扰动强。PEP 的 Mitf 只有钙粘蛋白信号含有 2 个基因，Pcdhb18 和 Krt10。</p>"
    )
    section = "\n".join(blocks)
    for name in ("报告_原理方法与数据分析.html", "报告_论文式阐述.html"):
        path = REPORT / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"<h2>6\. KEGG.*?</body>", "</body>", text, count=1, flags=re.S)
        text = text.replace("</body>", section + "\n</body>", 1)
        path.write_text(text, encoding="utf-8")


def main() -> None:
    table = pd.read_csv(ROOT / "富集_KEGG_全部.csv")
    stems = plot_bars(table)
    manifest = download_maps(table)
    append_reports(manifest, stems)
    print("MAPS_DONE", len(manifest), "bars", len(stems), flush=True)


if __name__ == "__main__":
    main()
