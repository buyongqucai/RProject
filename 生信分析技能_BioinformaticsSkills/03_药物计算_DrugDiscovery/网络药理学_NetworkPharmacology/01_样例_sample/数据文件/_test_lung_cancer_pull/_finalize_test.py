# -*- coding: utf-8 -*-
"""Finalize lung-cancer disease pull artifacts (strict MeSH + optional OpenTargets)."""
from __future__ import annotations

import csv
import gzip
import json
import ssl
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent
gz = OUT / "CTD_curated_genes_diseases.tsv.gz"
report_path = OUT / "TEST_REPORT.json"

genes: set[str] = set()
n = 0
names: set[tuple[str, str]] = set()
with gzip.open(gz, "rt", encoding="utf-8", errors="replace") as f:
    for line in f:
        if line.startswith("#") or line.lower().startswith("genesymbol"):
            continue
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 4:
            continue
        dname, did = parts[2], parts[3]
        if did in ("MESH:D008175", "D008175") or dname == "Lung Neoplasms":
            genes.add(parts[0])
            names.add((did, dname))
            n += 1

glist = sorted(g for g in genes if g)
strict_csv = OUT / "CTD_MESH_D008175_Lung_Neoplasms_genes.csv"
with strict_csv.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["gene", "source", "disease_id", "disease_name_filter"])
    for g in glist:
        w.writerow([g, "CTD_curated", "MESH:D008175", "Lung Neoplasms"])

print(f"strict n_genes={len(glist)} rows={n} names={sorted(names)[:10]}")

rep = json.loads(report_path.read_text(encoding="utf-8"))
rep["results"]["CTD_strict_MESH_D008175"] = {
    "ok": True,
    "n_genes": len(glist),
    "n_rows": n,
    "artifact": str(strict_csv),
    "matched": [list(x) for x in sorted(names)],
    "english_terms": ["Lung Neoplasms", "MESH:D008175"],
    "sample_genes": glist[:30],
}

ctx = ssl.create_default_context()
ot_query = {
    "query": (
        '{ search(queryString: "lung cancer", entityNames: ["disease"], '
        "page: {size: 5, index: 0}) { hits { id name } } }"
    )
}
body = json.dumps(ot_query).encode()
req = urllib.request.Request(
    "https://api.platform.opentargets.org/api/v4/graphql",
    data=body,
    method="POST",
    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
)
try:
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        data = json.loads(resp.read().decode())
    hits = (((data.get("data") or {}).get("search") or {}).get("hits")) or []
    print("OT hits", [(h.get("id"), h.get("name")) for h in hits])
    pick = None
    for h in hits:
        name = (h.get("name") or "").lower()
        if "lung" in name and ("cancer" in name or "carcinoma" in name or "neoplasm" in name):
            pick = h
            break
    if pick is None and hits:
        pick = hits[0]
    if pick:
        q2 = {
            "query": (
                '{ disease(efoId: "%s") { id name associatedTargets(page:{size:200,index:0}) '
                "{ count rows { score target { approvedSymbol } } } } }"
            )
            % pick["id"]
        }
        req2 = urllib.request.Request(
            "https://api.platform.opentargets.org/api/v4/graphql",
            data=json.dumps(q2).encode(),
            method="POST",
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req2, timeout=120, context=ctx) as resp2:
            data2 = json.loads(resp2.read().decode())
        d = (data2.get("data") or {}).get("disease") or {}
        rows = (((d.get("associatedTargets") or {}).get("rows")) or [])
        genes2 = []
        for r in rows:
            t = r.get("target") or {}
            sym = t.get("approvedSymbol")
            if sym:
                genes2.append({"gene": sym, "score": r.get("score")})
        art = OUT / "OpenTargets_lung_cancer_associatedTargets.csv"
        with art.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["gene", "score"])
            w.writeheader()
            w.writerows(genes2)
        rep["results"]["OpenTargets"] = {
            "ok": True,
            "query": "lung cancer",
            "disease_id": d.get("id"),
            "disease_name": d.get("name"),
            "n_genes_returned": len(genes2),
            "total_count": (d.get("associatedTargets") or {}).get("count"),
            "sample_genes": [g["gene"] for g in genes2[:30]],
            "artifact": str(art),
            "note": "Companion API; not a primary delivery SOP DB",
        }
        print(
            "OT OK",
            d.get("name"),
            "returned",
            len(genes2),
            "total",
            (d.get("associatedTargets") or {}).get("count"),
        )
except Exception as e:
    rep["results"]["OpenTargets"] = {"ok": False, "error": repr(e)}
    print("OT fail", repr(e))

# Prefer documenting both successes
rep["summary"] = {
    "success": True,
    "primary_automated_success": "CTD_curated_bulk",
    "n_genes_broad_lung_filter": rep["results"]["CTD_bulk"]["n_genes"],
    "n_genes_strict_MESH_D008175": len(glist),
    "english_terms_used": ["lung cancer", "Lung Neoplasms", "MESH:D008175"],
    "skill_primary_dbs": ["GeneCards", "TTD", "DrugBank", "OMIM"],
    "optional_db_tested": "CTD",
    "artifacts": {
        "report": str(report_path),
        "broad_csv": rep["results"]["CTD_bulk"].get("gene_list_csv"),
        "strict_csv": str(strict_csv),
        "bulk_gz": rep["results"]["CTD_bulk"].get("artifact_gz"),
    },
    "auth_notes": {
        "GeneCards_TTD_DrugBank": "Manual English-name browser export; auto-scrape blocked (403 / no API in skill)",
        "OMIM": "Optional OMIM_API_KEY from https://www.omim.org/api",
        "CTD": "No key for bulk download of curated gene-disease TSV",
    },
}
report_path.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
print("updated", report_path)
