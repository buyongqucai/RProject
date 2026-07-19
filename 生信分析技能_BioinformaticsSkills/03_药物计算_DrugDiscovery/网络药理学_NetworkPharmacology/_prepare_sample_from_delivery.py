# -*- coding: utf-8 -*-
"""从用户网药交付物按单药/分库组装样例中间表（去标识契约 CSV）。"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

DELIVERY = Path(r"D:\网络药理学文件\网络药理学交付文件20260710(1)\交付文件")
OUT = Path(__file__).resolve().parent / "01_样例_sample" / "数据文件"

HERBS = [
    ("三七", "Sanqi", "SQ"),
    ("丹参", "Danshen", "DS"),
    ("人参", "Renshen", "RS"),
    ("葛根", "Gegen", "GG"),
    ("黄芪", "Huangqi", "HQ"),
    ("黄连", "Huanglian", "HL"),
]

DISEASE_EN = "Atherosclerosis"


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def load_herb_genes(herb_zh: str) -> pd.DataFrame:
    xlsx = DELIVERY / "数据" / "药物" / f"{herb_zh}靶点基因.xlsx"
    df = pd.read_excel(xlsx)
    gene_col = "Gene" if "Gene" in df.columns else "Gene Names (primary)"
    genes = (
        df[gene_col]
        .dropna()
        .astype(str)
        .str.strip()
        .str.split(r"[;\s]+")
        .explode()
        .str.strip()
    )
    genes = sorted({g for g in genes if g and g.lower() != "nan"})
    return pd.DataFrame({"herb_zh": herb_zh, "gene": genes})


def load_genecards(min_score: float | None = 40.0) -> pd.DataFrame:
    """按英文病名导出的 GeneCards Results。
    min_score=None → 完整导出（疾病多库韦恩用）；默认 >=40 供下游交集/富集。
    """
    p = DELIVERY / "数据" / "疾病" / "GeneCards Results.csv"
    df = pd.read_csv(p, encoding="utf-8")
    df["Relevance Score"] = pd.to_numeric(df["Relevance Score"], errors="coerce")
    if min_score is not None:
        df = df[df["Relevance Score"] >= min_score].copy()
    out = pd.DataFrame(
        {
            "gene": df["Symbol"].astype(str).str.strip(),
            "name": df.get("Name", pd.Series([""] * len(df))).astype(str),
            "score": df["Relevance Score"],
            "source": "GeneCards",
        }
    )
    return out.dropna(subset=["gene"]).drop_duplicates("gene")


def _assemble_disease_by_db(gc: pd.DataFrame, ttd, omim, db) -> pd.DataFrame:
    disease_parts = [gc[["gene", "source"]], ttd, omim]
    if len(db) and db["gene"].notna().any() and len(db["gene"].dropna()):
        disease_parts.append(db[["gene", "source"]])
    else:
        old = OUT / "疾病靶点_DrugBank.csv"
        if old.exists():
            old_df = pd.read_csv(old, encoding="utf-8-sig")
            if "gene" in old_df.columns:
                disease_parts.append(
                    pd.DataFrame({"gene": old_df["gene"].astype(str), "source": "DrugBank"})
                )
    dis_by = pd.concat(disease_parts, ignore_index=True)
    dis_by = dis_by.dropna(subset=["gene"])
    dis_by["gene"] = dis_by["gene"].astype(str).str.strip()
    dis_by = dis_by[dis_by["gene"] != ""]
    return dis_by.drop_duplicates(["gene", "source"])


def load_ttd() -> pd.DataFrame:
    p = DELIVERY / "数据" / "疾病" / "TTD疾病靶点数据.csv"
    raw = pd.read_csv(p, encoding="utf-8", header=None)
    genes = []
    for val in raw.iloc[:, 0].astype(str):
        m = re.findall(r"\(([A-Z0-9\-]+)\)", val)
        if m:
            genes.extend(m)
        else:
            # fallback: last token
            tok = val.strip().split()[-1] if val.strip() else ""
            if re.fullmatch(r"[A-Z0-9\-]+", tok):
                genes.append(tok)
    genes = sorted(set(genes))
    return pd.DataFrame({"gene": genes, "source": "TTD"})


def load_omim() -> pd.DataFrame:
    """OMIM Gene Map Search export for disease English name; use Approved Symbol column."""
    p = DELIVERY / "数据" / "疾病" / "OMIM疾病靶点数据.csv"
    raw = pd.read_csv(p, encoding="utf-8", header=None)
    # find header row containing 'Approved Symbol'
    header_idx = None
    for i, row in raw.iterrows():
        vals = [str(x) for x in row.tolist()]
        if any("Approved Symbol" == v for v in vals):
            header_idx = i
            break
    genes: list[str] = []
    if header_idx is not None:
        header = [str(x) for x in raw.iloc[header_idx].tolist()]
        body = raw.iloc[header_idx + 1 :].copy()
        body.columns = header
        col = "Approved Symbol"
        if col in body.columns:
            for v in body[col].dropna().astype(str):
                v = v.strip()
                if re.fullmatch(r"[A-Z][A-Z0-9\-]*", v):
                    genes.append(v)
        # also Gene/Locus symbols like 'ATHS, ALP'
        if "Gene/Locus" in body.columns:
            for v in body["Gene/Locus"].dropna().astype(str):
                for tok in re.split(r"[,;/]+", v):
                    tok = tok.strip()
                    if re.fullmatch(r"[A-Z][A-Z0-9\-]*", tok) and len(tok) >= 3:
                        genes.append(tok)
    genes = sorted(set(genes))
    return pd.DataFrame({"gene": genes, "source": "OMIM"})


def load_drugbank() -> pd.DataFrame:
    p = DELIVERY / "数据" / "疾病" / "Drugbank疾病靶点数据.csv"
    df = pd.read_csv(p, encoding="utf-8", header=None)
    # protein names only in col0 — keep as name; gene unknown → skip unless existing cleaned
    names = df.iloc[:, 0].astype(str).str.strip().tolist()
    # Prefer cleaned sample if present later; here emit empty gene with note via PROVENANCE
    # Try map common names from UniProt-style: use Drugbank靶点数据.csv if richer
    p2 = DELIVERY / "数据" / "疾病" / "Drugbank靶点数据.csv"
    genes = []
    if p2.exists():
        d2 = pd.read_csv(p2, encoding="utf-8", header=None)
        for val in d2.iloc[:, 0].astype(str):
            m = re.findall(r"\(([A-Z0-9\-]+)\)", val)
            genes.extend(m if m else [])
            if re.fullmatch(r"[A-Z][A-Z0-9\-]+", val.strip()):
                genes.append(val.strip())
    # If still empty, leave minimal placeholder genes from names that look like symbols
    for n in names:
        if re.fullmatch(r"[A-Z][A-Z0-9\-]+", n):
            genes.append(n)
    genes = sorted(set(genes))
    return pd.DataFrame({"gene": genes, "source": "DrugBank", "note": "from delivery DrugBank disease export"})


def load_overlap_union() -> pd.DataFrame:
    p = DELIVERY / "数据" / "网络图" / "药物疾病交集靶点.csv"
    df = pd.read_csv(p, encoding="utf-8")
    # first column genes often
    col = df.columns[0]
    genes = df[col].dropna().astype(str).str.strip()
    genes = sorted({g for g in genes if g and g.lower() != "nan"})
    return pd.DataFrame({"gene": genes})


def load_drug_union() -> pd.DataFrame:
    p = DELIVERY / "数据" / "药物" / "药物去重基因.xlsx"
    df = pd.read_excel(p)
    # find gene-like column
    gene_col = None
    for c in df.columns:
        if str(c).lower() in {"gene", "genes", "symbol"} or "gene" in str(c).lower():
            gene_col = c
            break
    if gene_col is None:
        gene_col = df.columns[0]
    genes = df[gene_col].dropna().astype(str).str.strip()
    genes = sorted({g for g in genes if g and g.lower() != "nan"})
    return pd.DataFrame({"gene": genes})


def load_per_herb_overlap(herb_zh: str, herb_en: str) -> pd.DataFrame:
    p = DELIVERY / "数据" / "网络图" / f"{herb_zh}与疾病基因交集去重.xlsx"
    if not p.exists():
        p = DELIVERY / "数据" / "网络图" / f"{herb_zh}与疾病基因交集.xlsx"
    df = pd.read_excel(p)
    # prefer Gene column
    gene_col = None
    for c in ["Gene", "gene", "Gene Names (primary)", "symbol", "Symbol"]:
        if c in df.columns:
            gene_col = c
            break
    if gene_col is None:
        # last column often Gene in these workbooks
        gene_col = df.columns[-1]
    genes = (
        df[gene_col]
        .dropna()
        .astype(str)
        .str.strip()
        .str.split(r"[;\s]+")
        .explode()
        .str.strip()
    )
    genes = sorted({g for g in genes if g and g.lower() != "nan" and re.match(r"^[A-Za-z]", g)})
    return pd.DataFrame({"herb_zh": herb_zh, "herb_en": herb_en, "gene": genes})


def main() -> None:
    if not DELIVERY.exists():
        raise SystemExit(f"Delivery not found: {DELIVERY}")
    OUT.mkdir(parents=True, exist_ok=True)

    herb_frames = []
    overlap_frames = []
    for zh, en, _abbr in HERBS:
        hg = load_herb_genes(zh)
        hg["herb_en"] = en
        _write_csv(
            hg[["herb_zh", "herb_en", "gene"]],
            OUT / f"药物_{en}_靶点基因_HerbTargets.csv",
        )
        herb_frames.append(hg)
        ov = load_per_herb_overlap(zh, en)
        _write_csv(ov, OUT / f"药物_{en}_疾病交集_HerbDiseaseOverlap.csv")
        overlap_frames.append(ov)
        print(f"{zh}/{en}: targets={len(hg)} overlap={len(ov)}")

    all_herb = pd.concat(herb_frames, ignore_index=True)
    _write_csv(all_herb, OUT / "药物_全部单药靶点_AllHerbTargets.csv")

    drug_union = load_drug_union()
    if drug_union.empty:
        drug_union = pd.DataFrame({"gene": sorted(set(all_herb["gene"]))})
    _write_csv(drug_union, OUT / "药物去重基因_DrugGenesUnion.csv")

    gc = load_genecards(min_score=40.0)
    gc_full = load_genecards(min_score=None)
    ttd = load_ttd()
    omim = load_omim()
    db = load_drugbank()

    dis_by = _assemble_disease_by_db(gc, ttd, omim, db)
    _write_csv(dis_by, OUT / "疾病靶点按库_DiseaseGenesByDB.csv")

    dis_by_venn = _assemble_disease_by_db(gc_full, ttd, omim, db)
    _write_csv(dis_by_venn, OUT / "疾病靶点按库_VennFull_DiseaseGenesByDB.csv")

    for src, sub in dis_by.groupby("source"):
        _write_csv(
            sub[["gene"]].drop_duplicates(),
            OUT / f"疾病靶点_{src}_DiseaseGenes.csv",
        )

    # also write GeneCards with scores for reference (filtered + full)
    _write_csv(gc, OUT / "疾病靶点_GeneCards.csv")
    _write_csv(gc_full, OUT / "疾病靶点_GeneCards_Full_ForVenn.csv")

    dis_union = pd.DataFrame({"gene": sorted(set(dis_by["gene"]))})
    _write_csv(dis_union, OUT / "疾病靶点合并_DiseaseGenesUnion.csv")

    overlap = load_overlap_union()
    if overlap.empty:
        overlap = pd.DataFrame(
            {
                "gene": sorted(
                    set(drug_union["gene"]).intersection(set(dis_union["gene"]))
                )
            }
        )
    _write_csv(overlap, OUT / "药物疾病交集_DrugDiseaseOverlap.csv")

    # derived compound-target edge table from TCMSP compound tables (optional summary)
    # Keep a derived multi-herb edge cache marked in PROVENANCE
    derived_edges = []
    for zh, en, abbr in HERBS:
        p = DELIVERY / "数据" / "药物" / f"TCMSP{zh}有效成分靶点表格.xlsx"
        if not p.exists():
            continue
        t = pd.read_excel(p)
        # heuristic columns
        cols = {c: str(c).lower() for c in t.columns}
        mol = None
        gene = None
        for c, low in cols.items():
            if mol is None and ("mol" in low or "成分" in str(c) or "compound" in low or "name" in low):
                mol = c
            if gene is None and ("gene" in low or "target" in low or "靶" in str(c)):
                gene = c
        if gene is None:
            gene = t.columns[-1]
        if mol is None:
            mol = t.columns[0]
        for i, row in t.iterrows():
            g = str(row[gene]).strip() if pd.notna(row[gene]) else ""
            m = str(row[mol]).strip() if pd.notna(row[mol]) else f"{abbr}{i}"
            if g and re.match(r"^[A-Za-z]", g):
                derived_edges.append(
                    {"herb": en, "herb_zh": zh, "compound_id": m, "target_gene": g.split()[0]}
                )
    if derived_edges:
        dedge = pd.DataFrame(derived_edges).drop_duplicates()
        _write_csv(dedge, OUT / "派生_成分靶点边_DerivedCompoundTargets.csv")

    # network / type from delivery
    net_src = DELIVERY / "数据" / "网络图" / "network.csv"
    type_src = DELIVERY / "数据" / "网络图" / "type.csv"
    if net_src.exists():
        pd.read_csv(net_src, encoding="utf-8").to_csv(
            OUT / "网络边_network.csv", index=False, encoding="utf-8-sig"
        )
    if type_src.exists():
        pd.read_csv(type_src, encoding="utf-8").to_csv(
            OUT / "网络节点类型_type.csv", index=False, encoding="utf-8-sig"
        )

    # PPI / enrichment: copy if present in old sample or delivery
    ppi_src = DELIVERY / "数据" / "PPI" / "string_interactions_short.tsv"
    if ppi_src.exists():
        text = ppi_src.read_bytes()
        (OUT / "PPI互作_StringInteractions.tsv").write_bytes(text)

    # keep existing enrichment CSVs if already in OUT
    # write per-herb overlap summary
    summary = (
        pd.concat(overlap_frames, ignore_index=True)
        .groupby(["herb_zh", "herb_en"], as_index=False)["gene"]
        .nunique()
        .rename(columns={"gene": "n_overlap_genes"})
    )
    _write_csv(summary, OUT / "单药疾病交集汇总_PerHerbOverlapSummary.csv")

    prov = {
        "data_provenance": "REAL",
        "source": "user_delivery_query_backed_export",
        "not_live_scrape": True,
        "delivery_path": str(DELIVERY),
        "disease_english_name": DISEASE_EN,
        "genecards_min_relevance_score": 40.0,
        "venn_uses_full_genecards": True,
        "disease_query_note": (
            "Each disease DB file was queried with the English disease name "
            "(see 网药数据解读.docx). Disease multi-DB Venn uses FULL GeneCards export "
            "(疾病靶点按库_VennFull_DiseaseGenesByDB.csv). Downstream overlap/enrichment "
            "uses GeneCards filtered at Relevance Score>=40."
        ),
        "herbs": [{"zh": z, "en": e} for z, e, _ in HERBS],
        "databases": {
            "drug": ["TCMSP"],
            "disease": ["GeneCards", "TTD", "DrugBank", "OMIM"],
            "ppi": ["STRING"],
        },
        "urls": {
            "GeneCards": "https://www.genecards.org/",
            "TTD": "https://db.idrblab.net/ttd/",
            "DrugBank": "https://go.drugbank.com/",
            "OMIM": "https://www.omim.org/",
            "TCMSP": "https://tcmsp-e.com/",
            "STRING": "https://string-db.org/",
        },
        "derived_files": [
            "派生_成分靶点边_DerivedCompoundTargets.csv",
            "疾病靶点按库_DiseaseGenesByDB.csv",
            "疾病靶点按库_VennFull_DiseaseGenesByDB.csv",
            "疾病靶点合并_DiseaseGenesUnion.csv",
        ],
        "counts": {
            "n_herbs": len(HERBS),
            "drug_union": int(len(drug_union)),
            "disease_union_filtered": int(len(dis_union)),
            "disease_by_db_rows_filtered": int(len(dis_by)),
            "disease_by_db_rows_venn_full": int(len(dis_by_venn)),
            "genecards_full": int(gc_full["gene"].nunique()),
            "genecards_filtered": int(gc["gene"].nunique()),
            "drug_disease_overlap": int(len(overlap)),
        },
        "note": "REAL query-backed intermediates from user delivery; not fabricated with rnorm. Do not treat as clinical advice. Cytoscape figures remain BLOCKED_EXTERNAL.",
    }
    (OUT / "PROVENANCE.json").write_text(
        json.dumps(prov, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    ds = f"""# 数据来源

- **data_provenance: REAL**（query-backed export；**非**本机自动爬取 TCMSP/GeneCards）
- **disease_english_name: {DISEASE_EN}**
- **单药**: 三七 / 丹参 / 人参 / 葛根 / 黄芪 / 黄连（各有独立 `药物_*_靶点基因_HerbTargets.csv` 与疾病交集表）
- **疾病库**: GeneCards / TTD / DrugBank / OMIM（按英文病名导出后入库）
- **韦恩图**: 使用完整 GeneCards（`疾病靶点按库_VennFull_DiseaseGenesByDB.csv`）
- **下游交集/富集**: GeneCards Relevance≥40（`疾病靶点按库_DiseaseGenesByDB.csv`）
- **交付路径**: `{DELIVERY}`
- **规范**: DeliveryStandards + VizStandards + DataAuthenticity
- **说明**: 详见 `PROVENANCE.json`。Cytoscape 网络图 / PPI 渐变图 / KEGG 官方通路图见技能说明断点 SOP，样例 STATUS=PARTIAL。
"""
    (OUT / "DATA_SOURCE.md").write_text(ds, encoding="utf-8")
    print("DONE ->", OUT)
    print(json.dumps(prov["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
