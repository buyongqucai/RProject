# -*- coding: utf-8 -*-
"""Collect key NetPharm delivery stats as JSON for the HTML report."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"E:/RProject/清风项目")
D = ROOT / "交付文件" / "数据"
OUT = ROOT / "交付文件" / "报告" / "_stats.json"


def main() -> dict:
    db_full = pd.read_csv(D / "疾病/疾病靶点按库.csv", encoding="utf-8-sig")
    by_db_full = db_full.groupby("source")["gene"].nunique().sort_values(ascending=False).to_dict()
    db_down = D / "疾病/疾病靶点按库_下游.csv"
    if db_down.exists():
        db2 = pd.read_csv(db_down, encoding="utf-8-sig")
        by_db_down = db2.groupby("source")["gene"].nunique().sort_values(ascending=False).to_dict()
    else:
        by_db_down = {}
    disease_union = pd.read_csv(D / "疾病/疾病靶点合并.csv", encoding="utf-8-sig")
    # gene col
    gcol = "gene" if "gene" in disease_union.columns else disease_union.columns[0]
    n_disease = int(disease_union[gcol].nunique())

    drug_u = pd.read_csv(D / "药物/药物靶点合并.csv", encoding="utf-8-sig")
    dg = "gene" if "gene" in drug_u.columns else drug_u.columns[0]
    n_drug = int(drug_u[dg].nunique())

    ov = pd.read_csv(D / "药物/药物疾病交集.csv", encoding="utf-8-sig")
    og = "gene" if "gene" in ov.columns else ov.columns[0]
    n_overlap = int(ov[og].nunique())

    ph = pd.read_csv(D / "药物/单药疾病交集汇总.csv", encoding="utf-8-sig")
    per_herb = ph.sort_values("n_overlap_genes", ascending=False).to_dict(orient="records")

    rename = pd.read_csv(D / "药物/成分重命名.csv", encoding="utf-8-sig")
    n_compounds = int(rename["compound_id"].nunique()) if "compound_id" in rename.columns else len(rename)
    n_herbs_with_comp = int(rename["herb_zh"].nunique()) if "herb_zh" in rename.columns else None

    edges = pd.read_csv(D / "药物/草药成分边.csv", encoding="utf-8-sig")
    n_herb_comp_edges = len(edges)

    kegg = pd.read_csv(D / "富集分析/KEGG.csv", encoding="utf-8-sig")
    if "pvalue" in kegg.columns:
        kegg = kegg.sort_values("pvalue")
    top_kegg = []
    for _, r in kegg.head(10).iterrows():
        top_kegg.append(
            {
                "id": str(r.get("ID", "")),
                "desc": str(r.get("Description", r.get("term", ""))),
                "pvalue": float(r["pvalue"]) if "pvalue" in r and pd.notna(r["pvalue"]) else None,
                "padj": float(r["p.adjust"]) if "p.adjust" in r and pd.notna(r["p.adjust"]) else (
                    float(r["padj"]) if "padj" in r and pd.notna(r["padj"]) else None
                ),
                "count": int(r["Count"]) if "Count" in r and pd.notna(r["Count"]) else (
                    int(r["count"]) if "count" in r and pd.notna(r["count"]) else None
                ),
            }
        )
    n_kegg_sig = int((kegg["p.adjust"] < 0.05).sum()) if "p.adjust" in kegg.columns else len(kegg)

    go = pd.read_csv(D / "富集分析/BPCCMF.csv", encoding="utf-8-sig")
    go_n = {}
    if "ONTOLOGY" in go.columns:
        go_n = go.groupby("ONTOLOGY").size().to_dict()
    elif "one_type" in go.columns:
        go_n = go.groupby("one_type").size().to_dict()
    n_go = len(go)

    typ = pd.read_csv(D / "网络图/type.csv", encoding="utf-8-sig")
    type_counts = typ["type"].value_counts().to_dict()
    net = pd.read_csv(D / "网络图/network.csv", encoding="utf-8-sig")
    n_edges = len(net)

    ppi = pd.read_csv(D / "PPI/string_interactions_short.tsv", sep="\t", encoding="utf-8-sig")
    n_ppi = len(ppi)
    # unique proteins
    cols = ppi.columns.tolist()
    a = cols[0]
    b = cols[1]
    n_ppi_prot = len(set(ppi[a].astype(str)) | set(ppi[b].astype(str)))

    stats = {
        "n_disease_union": n_disease,
        "disease_by_db_venn_full": {str(k): int(v) for k, v in by_db_full.items()},
        "disease_by_db_downstream": {str(k): int(v) for k, v in by_db_down.items()},
        "genecards_full": int(by_db_full.get("GeneCards", 0)),
        "genecards_filtered_ge40": int(by_db_down.get("GeneCards", 0)),
        "genecards_relevance_cutoff": 40.0,
        # backward-compatible alias used by older HTML: venn-full counts
        "disease_by_db": {str(k): int(v) for k, v in by_db_full.items()},
        "n_drug_targets": n_drug,
        "n_overlap": n_overlap,
        "overlap_pct_of_drug": round(100.0 * n_overlap / max(n_drug, 1), 1),
        "overlap_pct_of_disease": round(100.0 * n_overlap / max(n_disease, 1), 1),
        "n_herbs_nominal": 9,
        "n_herbs_with_targets": sum(1 for r in per_herb if int(r.get("n_overlap_genes", 0) or 0) > 0 or int(r.get("n_targets", 0) or 0) > 0),
        "per_herb": [
            {
                "herb_zh": str(r.get("herb_zh", "")),
                "n_overlap": int(r.get("n_overlap_genes", 0) or 0),
                "n_targets": int(r.get("n_targets", 0) or 0),
            }
            for r in per_herb
        ],
        "n_compounds": n_compounds,
        "n_herbs_with_comp": n_herbs_with_comp,
        "n_herb_comp_edges": n_herb_comp_edges,
        "n_kegg_terms": len(kegg),
        "n_kegg_padj05": n_kegg_sig,
        "top_kegg": top_kegg,
        "n_go": n_go,
        "go_by_ont": {str(k): int(v) for k, v in go_n.items()},
        "network_type_counts": {str(k): int(v) for k, v in type_counts.items()},
        "n_network_edges": n_edges,
        "n_ppi_edges": n_ppi,
        "n_ppi_proteins": n_ppi_prot,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return stats


if __name__ == "__main__":
    main()
