# -*- coding: utf-8 -*-
"""
Ulcerative Colitis × 12味药：网络药理学后续处理（交集 + 出图）
输入：D:/网络药理学文件/准备文件（及 CTD 已有 AUTO）
输出：E:/RProject/努力学习项目/网络药理学/结果/
"""
from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns
from matplotlib_venn import venn2, venn3

# ---------------- paths ----------------
PREP = Path(r"D:/网络药理学文件/准备文件")
DRUG_XLSX = Path(r"D:/网络药理学文件/药物中文名称.xlsx")
CTD = Path(r"E:/RProject/努力学习项目/网络药理学/数据文件/上游_疾病/疾病靶点_CTD_DiseaseGenes.csv")
# 计算中间表；正式出图请用 01_run_uc_skill_plots.R → 结果文件/图片文件
OUT = Path(r"E:/RProject/努力学习项目/网络药理学/代码文件/结果文件")
DATA = OUT / "数据文件" / "_compute_scratch"
FIG = OUT / "图片文件" / "_compute_scratch"
REP = OUT / "报告文件"
for d in (DATA, FIG, REP):
    d.mkdir(parents=True, exist_ok=True)

DISEASE = "Ulcerative Colitis"
GC_REL = 40.0
STRING_SCORE = 400  # 0.4 * 1000

sns.set_theme(style="whitegrid")
plt.rcParams["axes.unicode_minus"] = False
from matplotlib import font_manager

_zh = None
for _fp in (
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
):
    if Path(_fp).exists():
        font_manager.fontManager.addfont(_fp)
        _zh = font_manager.FontProperties(fname=_fp).get_name()
        break
if _zh:
    plt.rcParams["font.sans-serif"] = [_zh, "DejaVu Sans"]
else:
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]


def norm_gene(x) -> str | None:
    if pd.isna(x):
        return None
    s = str(x).strip()
    if not s or s.lower() in {"nan", "none", "null", "gene", "symbol", "value", "key"}:
        return None
    # strip isoforms like Gene(xxx)
    s = re.sub(r"\s+", "", s)
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9\-_@\.]*$", s):
        return None
    return s.upper() if s.isupper() or re.match(r"^[A-Za-z]", s) else s


def uniq_genes(series) -> set[str]:
    out = set()
    for v in series:
        g = norm_gene(v)
        if g:
            # expand A;B
            for part in re.split(r"[;/,|]", g):
                gg = norm_gene(part)
                if gg:
                    out.add(gg)
    return out


# ---------------- disease ----------------
def load_disease() -> dict[str, set[str]]:
    db: dict[str, set[str]] = {}

    gc = pd.read_csv(PREP / "GeneCards Results.csv", encoding="utf-8-sig")
    db["GeneCards_full"] = uniq_genes(gc["Symbol"])
    db["GeneCards"] = uniq_genes(gc.loc[gc["Relevance Score"] >= GC_REL, "Symbol"])

    ttd = pd.read_csv(PREP / "TTD靶点数据.csv", encoding="utf-8-sig", header=None)
    db["TTD"] = uniq_genes(ttd.iloc[:, 0])

    dbank = pd.read_csv(PREP / "Drugbank靶点数据.csv", encoding="utf-8-sig")
    col = "Gene" if "Gene" in dbank.columns else dbank.columns[-1]
    db["DrugBank"] = uniq_genes(dbank[col])

    omim = pd.read_csv(PREP / "OMIM靶点数据.csv", encoding="utf-8-sig", header=None)
    db["OMIM"] = uniq_genes(omim.iloc[:, 0])

    if CTD.exists():
        ctd = pd.read_csv(CTD, encoding="utf-8-sig")
        gcol = "gene" if "gene" in ctd.columns else ctd.columns[0]
        db["CTD"] = uniq_genes(ctd[gcol])
    else:
        db["CTD"] = set()

    # DisGeNET not found in prep
    db["DisGeNET"] = set()
    return db


# ---------------- drugs ----------------
HERBS = [
    "半夏",
    "茯苓",
    "木香",
    "黄连",
    "干姜",
    "淫羊藿",
    "黄芩",
    "肉桂",
    "人参",
    "白术",
    "香附",
    "棕榈炭",
]


def genes_from_baishu_like(xlsx: Path) -> set[str]:
    df = pd.read_excel(xlsx, header=None)
    # gene in col 4 (0-based), skip header row
    if df.shape[1] < 5:
        return set()
    return uniq_genes(df.iloc[1:, 4])


def genes_from_xiangfu(xlsx: Path) -> set[str]:
    df = pd.read_excel(xlsx, header=None)
    return uniq_genes(df.iloc[1:, 1])


def genes_from_zonglvtan() -> set[str]:
    xlsx = PREP / "棕榈炭" / "棕榈炭靶点基因.xlsx"
    integ = pd.read_excel(xlsx, sheet_name="整合靶点")
    gcol = "Gene Names (primary)" if "Gene Names (primary)" in integ.columns else integ.columns[-1]
    genes = uniq_genes(integ[gcol])
    # also HERB targets
    herb = PREP / "棕榈炭" / "HERB_棕榈炭_靶点明细.csv"
    if herb.exists():
        h = pd.read_csv(herb, encoding="utf-8-sig")
        genes |= uniq_genes(h["gene"])
    return genes


def load_herb_genes() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for h in HERBS:
        if h == "棕榈炭":
            out[h] = genes_from_zonglvtan()
        elif h == "香附":
            out[h] = genes_from_xiangfu(PREP / "香附靶点基因.xlsx")
        else:
            p = PREP / f"{h}靶点基因.xlsx"
            if not p.exists():
                out[h] = set()
                continue
            out[h] = genes_from_baishu_like(p)
    return out


# ---------------- plots ----------------
def save_fig(name: str):
    for ext in ("png", "svg", "pdf"):
        plt.savefig(FIG / f"{name}.{ext}", dpi=600 if ext == "png" else None, bbox_inches="tight")
    plt.close()


def plot_disease_counts(db: dict[str, set[str]]):
    keys = ["GeneCards", "TTD", "DrugBank", "OMIM", "CTD", "DisGeNET"]
    vals = [len(db.get(k, set())) for k in keys]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(keys, vals, color="#4C78A8")
    ax.set_ylabel("Gene count")
    ax.set_title(f"Disease targets by database ({DISEASE})")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), str(v), ha="center", va="bottom", fontsize=9)
    save_fig("01_疾病各库靶点数_Bar")


def plot_disease_venn_main(db: dict[str, set[str]]):
    # Top3 non-empty for classic venn3
    ranked = sorted(
        [(k, db[k]) for k in ["GeneCards", "TTD", "DrugBank", "OMIM", "CTD"] if db.get(k)],
        key=lambda x: -len(x[1]),
    )[:3]
    if len(ranked) < 2:
        return
    fig, ax = plt.subplots(figsize=(7, 6))
    if len(ranked) == 2:
        venn2([ranked[0][1], ranked[1][1]], set_labels=(ranked[0][0], ranked[1][0]), ax=ax)
    else:
        venn3(
            [ranked[0][1], ranked[1][1], ranked[2][1]],
            set_labels=(ranked[0][0], ranked[1][0], ranked[2][0]),
            ax=ax,
        )
    ax.set_title(f"Disease gene Venn (top databases) — {DISEASE}")
    save_fig("02_疾病多库韦恩_TopDB")


def plot_herb_bars(herb_genes: dict[str, set[str]], disease: set[str]):
    herbs = list(herb_genes.keys())
    n_t = [len(herb_genes[h]) for h in herbs]
    n_o = [len(herb_genes[h] & disease) for h in herbs]
    x = np.arange(len(herbs))
    w = 0.38
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(x - w / 2, n_t, w, label="Herb targets", color="#72B7B2")
    ax.bar(x + w / 2, n_o, w, label="∩ Disease", color="#E45756")
    ax.set_xticks(x)
    ax.set_xticklabels(herbs, rotation=45, ha="right")
    ax.set_ylabel("Gene count")
    ax.set_title("Per-herb targets and disease overlap (UC)")
    ax.legend()
    for i, (a, b) in enumerate(zip(n_t, n_o)):
        ax.text(i - w / 2, a, str(a), ha="center", va="bottom", fontsize=7)
        ax.text(i + w / 2, b, str(b), ha="center", va="bottom", fontsize=7)
    save_fig("03_单药靶点与疾病交集_Bar")


def plot_drug_disease_venn(drug_u: set[str], disease: set[str]):
    fig, ax = plt.subplots(figsize=(6.5, 6))
    venn2([drug_u, disease], set_labels=("Drug targets", "Disease genes"), ax=ax)
    ax.set_title(f"Drug ∪ vs Disease — {DISEASE}")
    save_fig("04_药物疾病韦恩_DrugDisease")


def plot_overlap_heatmap(herb_genes: dict[str, set[str]], disease: set[str]):
    herbs = list(herb_genes.keys())
    mat = np.zeros((len(herbs), len(herbs)))
    overlaps = {h: herb_genes[h] & disease for h in herbs}
    for i, a in enumerate(herbs):
        for j, b in enumerate(herbs):
            mat[i, j] = len(overlaps[a] & overlaps[b])
    fig, ax = plt.subplots(figsize=(8.5, 7))
    sns.heatmap(mat, annot=True, fmt=".0f", cmap="YlOrRd", xticklabels=herbs, yticklabels=herbs, ax=ax)
    ax.set_title("Shared disease-overlap genes between herbs")
    save_fig("05_单药疾病交集基因_两两热图")


# ---------------- enrichment ----------------
def run_enrichment(genes: list[str], prefix: str):
    if len(genes) < 5:
        return None
    try:
        import gseapy as gp
    except Exception as e:
        (REP / "enrichment_skip.txt").write_text(f"gseapy unavailable: {e}", encoding="utf-8")
        return None

    results = {}
    for lib, tag in [
        ("GO_Biological_Process_2023", "GO_BP"),
        ("KEGG_2021_Human", "KEGG"),
    ]:
        try:
            enr = gp.enrichr(gene_list=genes, gene_sets=lib, organism="human", outdir=None, cutoff=0.5)
            df = enr.results
            if df is None or df.empty:
                continue
            df = df.sort_values("Adjusted P-value").head(20)
            df.to_csv(DATA / f"{prefix}_{tag}.csv", index=False, encoding="utf-8-sig")
            results[tag] = df
            # barplot
            top = df.head(15).copy()
            top["-log10(padj)"] = -np.log10(top["Adjusted P-value"].clip(lower=1e-300))
            top["Term_short"] = top["Term"].astype(str).str.slice(0, 60)
            fig, ax = plt.subplots(figsize=(9, 6))
            ax.barh(top["Term_short"][::-1], top["-log10(padj)"][::-1], color="#F58518")
            ax.set_xlabel("-log10(Adjusted P-value)")
            ax.set_title(f"{prefix} {tag} top terms")
            save_fig(f"{prefix}_{tag}_Bar")
        except Exception as e:
            (REP / f"{prefix}_{tag}_error.txt").write_text(str(e), encoding="utf-8")
    return results


# ---------------- STRING PPI ----------------
def fetch_string_ppi(genes: list[str]) -> pd.DataFrame | None:
    if len(genes) < 2:
        return None
    genes = genes[:200]
    try:
        r = requests.post(
            "https://string-db.org/api/json/network",
            data={
                "identifiers": "\r".join(genes),
                "species": 9606,
                "required_score": STRING_SCORE,
                "caller_identity": "RProject_UC_netpharm",
            },
            timeout=120,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        (REP / "STRING_error.txt").write_text(str(e), encoding="utf-8")
        return None
    if not data:
        return None
    df = pd.DataFrame(data)
    df.to_csv(DATA / "19_PPI互作_StringInteractions.tsv", sep="\t", index=False, encoding="utf-8-sig")
    return df


def plot_ppi_degree(ppi: pd.DataFrame):
    # preferredName_A/B or stringId
    a = "preferredName_A" if "preferredName_A" in ppi.columns else None
    b = "preferredName_B" if "preferredName_B" in ppi.columns else None
    if not a:
        return
    deg = defaultdict(int)
    for _, row in ppi.iterrows():
        deg[row[a]] += 1
        deg[row[b]] += 1
    s = pd.Series(deg).sort_values(ascending=False).head(30)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(s.index[::-1], s.values[::-1], color="#54A24B")
    ax.set_xlabel("Degree")
    ax.set_title("STRING PPI hub genes (overlap set)")
    save_fig("06_PPI_Degree_Bar")
    pd.DataFrame({"gene": s.index, "degree": s.values}).to_csv(
        DATA / "19_PPI_DegreeTop.csv", index=False, encoding="utf-8-sig"
    )


# ---------------- main ----------------
def main():
    status = {
        "disease": DISEASE,
        "data_provenance": "REAL",
        "status": "PARTIAL",
        "notes": [],
    }

    db = load_disease()
    # downstream disease set: GeneCards>=40 ∪ others (exclude GeneCards_full duplicate)
    disease_parts = {k: v for k, v in db.items() if k not in {"GeneCards_full", "DisGeNET"} or (k == "DisGeNET" and v)}
    # primary union for overlap: GeneCards filtered + TTD + DrugBank + OMIM + CTD
    D = set()
    for k in ["GeneCards", "TTD", "DrugBank", "OMIM", "CTD"]:
        D |= db.get(k, set())
    if not db["DisGeNET"]:
        status["notes"].append("DisGeNET missing in 准备文件 → excluded")

    herb_genes = load_herb_genes()
    if len(herb_genes.get("肉桂", set())) == 0:
        status["notes"].append(
            "肉桂：TCMSP有效成分靶点表为空且靶点基因.xlsx无成分-基因侧列 → BLOCKED_EXTERNAL，交集为0"
        )

    # >=2 DB co-occurrence
    membership = defaultdict(int)
    for k in ["GeneCards", "TTD", "DrugBank", "OMIM", "CTD"]:
        for g in db.get(k, set()):
            membership[g] += 1
    D_strict = {g for g, n in membership.items() if n >= 2}

    # save disease tables
    rows = []
    for k in ["GeneCards", "GeneCards_full", "TTD", "DrugBank", "OMIM", "CTD", "DisGeNET"]:
        for g in sorted(db.get(k, set())):
            rows.append({"database": k, "gene": g})
    pd.DataFrame(rows).to_csv(DATA / "11_疾病靶点按库_DiseaseGenesByDB.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame({"gene": sorted(D)}).to_csv(DATA / "疾病靶点合并_DiseaseGenesUnion.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame({"gene": sorted(D_strict)}).to_csv(
        DATA / "疾病靶点_≥2库_DiseaseGenesStrict.csv", index=False, encoding="utf-8-sig"
    )

    herb_rows = []
    for h, gs in herb_genes.items():
        for g in sorted(gs):
            herb_rows.append({"herb": h, "gene": g})
    pd.DataFrame(herb_rows).to_csv(DATA / "药物靶点_按药_HerbTargets.csv", index=False, encoding="utf-8-sig")

    T_db = set().union(*herb_genes.values()) if herb_genes else set()
    pd.DataFrame({"gene": sorted(T_db)}).to_csv(DATA / "药物去重基因_DrugGenesUnion.csv", index=False, encoding="utf-8-sig")

    I_A = T_db & D
    I_A_strict = T_db & D_strict
    pd.DataFrame({"gene": sorted(I_A), "disease": DISEASE}).to_csv(
        DATA / "02_药物疾病交集_DrugDiseaseOverlap.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame({"gene": sorted(I_A_strict), "disease": DISEASE}).to_csv(
        DATA / "02_药物疾病交集_Strict2DB.csv", index=False, encoding="utf-8-sig"
    )

    per_rows = []
    for h, gs in herb_genes.items():
        ov = sorted(gs & D)
        pd.DataFrame({"gene": ov, "herb": h, "disease": DISEASE}).to_csv(
            DATA / f"药物_{h}_疾病交集_HerbDiseaseOverlap.csv", index=False, encoding="utf-8-sig"
        )
        per_rows.append(
            {
                "herb": h,
                "n_targets": len(gs),
                "n_overlap_D": len(ov),
                "n_overlap_Dstrict": len(gs & D_strict),
            }
        )
    summary = pd.DataFrame(per_rows)
    summary.to_csv(DATA / "03_单药疾病交集汇总.csv", index=False, encoding="utf-8-sig")

    # plots
    plot_disease_counts(db)
    plot_disease_venn_main(db)
    plot_herb_bars(herb_genes, D)
    plot_drug_disease_venn(T_db, D)
    plot_overlap_heatmap(herb_genes, D)

    # enrichment on I_A
    enr = run_enrichment(sorted(I_A), "07_药物疾病交集")
    # STRING
    ppi = fetch_string_ppi(sorted(I_A))
    if ppi is not None and len(ppi):
        plot_ppi_degree(ppi)
        status["notes"].append(f"STRING edges={len(ppi)}")
    else:
        status["notes"].append("STRING PPI empty or failed")

    # counts report
    counts = {
        "disease_union_D": len(D),
        "disease_strict_2DB": len(D_strict),
        "drug_union_Tdb": len(T_db),
        "overlap_IA": len(I_A),
        "overlap_IA_strict": len(I_A_strict),
        "per_herb": summary.to_dict(orient="records"),
        "disease_db_sizes": {k: len(v) for k, v in db.items()},
        "herb_sizes": {k: len(v) for k, v in herb_genes.items()},
    }
    (REP / "STATUS.json").write_text(json.dumps({**status, **counts}, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        f"# UC 网络药理学结果摘要",
        f"",
        f"- 疾病：{DISEASE}",
        f"- 疾病并集 D：{len(D)}（GeneCards≥{int(GC_REL)} ∪ TTD ∪ DrugBank ∪ OMIM ∪ CTD）",
        f"- ≥2 库：{len(D_strict)}",
        f"- 12 药靶点并集：{len(T_db)}",
        f"- 药交病 I_A：{len(I_A)}；严格：{len(I_A_strict)}",
        f"- DisGeNET：{'缺失' if not db['DisGeNET'] else len(db['DisGeNET'])}",
        f"",
        f"## 单药交集",
        summary.to_string(index=False),
        f"",
        f"图片目录：`{FIG}`",
        f"数据目录：`{DATA}`",
    ]
    (REP / "结果摘要.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
