"""Apply plan/literature-backed PharmMapper filters → genes CSV.

Adopted (main analysis) — 加宽版:
  - Species: Mus musculus (10090) OR Homo sapiens (9606)
  - Normalized Fit Score ≥ 0.6

Stricter audit (not auto-merged):
  - Same species ∩ Normalized Fit Score ≥ 0.8
"""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

PRED = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_预测靶点_MultiPredict"
)
AUDIT = PRED / "_audit"
JOB = "261011075421"
MAIN_CSV = PRED / "04_PharmMapper_Quercetin_genes.csv"
UNFILTERED = AUDIT / "04_PharmMapper_Quercetin_genes_unfiltered.csv"
STRICT08 = AUDIT / "04_PharmMapper_Quercetin_genes_studySpecies_normFit0.8.csv"
META = AUDIT / "04_PharmMapper_filter_meta.json"
ORG_MAP = PRED / "_pm_uniprot_org.json"

STUDY_ORG_IDS = {"10090", "9606"}
ORG_LABEL = {"10090": "Mus_musculus", "9606": "Homo_sapiens"}
PRIMARY_TH = 0.6
STRICT_TH = 0.8


def rows_at(raw: list[dict], org: dict, gene: dict, th: float) -> list[dict]:
    out = []
    seen = set()
    for r in sorted(raw, key=lambda x: -float(x.get("norm_fit") or 0)):
        try:
            nf = float(r.get("norm_fit") or 0)
        except ValueError:
            continue
        if nf < th:
            continue
        for a in (r.get("uniprot") or "").split(";"):
            oid = org.get(a, "")
            if not a or oid not in STUDY_ORG_IDS:
                continue
            g = gene.get(a, "")
            if not g or g in seen:
                continue
            seen.add(g)
            out.append(
                {
                    "gene_human": g,
                    "pdb": r.get("pdb", ""),
                    "uniprot": a,
                    "organism_id": oid,
                    "organism": ORG_LABEL.get(oid, oid),
                    "fit_score": r.get("fit_score", ""),
                    "norm_fit": r.get("norm_fit", ""),
                    "target_name": r.get("target_name", ""),
                    "source": "PharmMapper",
                    "evidence": "predicted",
                    "job_id": r.get("job_id", JOB),
                    "filter": f"studySpecies_mouseORhuman_AND_normFit>={th}",
                }
            )
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = [
        "gene_human",
        "pdb",
        "uniprot",
        "organism_id",
        "organism",
        "fit_score",
        "norm_fit",
        "target_name",
        "source",
        "evidence",
        "job_id",
        "filter",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    raw_all = json.loads((PRED / "04_PharmMapper_raw_rows.json").read_text(encoding="utf-8"))
    raw = [r for r in raw_all if r.get("job_id") == JOB]
    maps = json.loads(ORG_MAP.read_text(encoding="utf-8"))
    org, gene = maps["org"], maps["gene"]

    legacy = PRED / "04_PharmMapper_Quercetin_genes_unfiltered.csv"
    if legacy.exists() and not UNFILTERED.exists():
        shutil.move(str(legacy), str(UNFILTERED))

    primary = rows_at(raw, org, gene, PRIMARY_TH)
    strict = rows_at(raw, org, gene, STRICT_TH)
    write_csv(MAIN_CSV, primary)
    write_csv(STRICT08, strict)

    def n_sp(rows, oid):
        return sum(1 for r in rows if r["organism_id"] == oid)

    meta = {
        "job_id": JOB,
        "adopted": "widened_normFit_0.6",
        "primary_filter": {
            "species_policy": "Mus musculus (10090) OR Homo sapiens (9606)",
            "normalized_fit_score_min": PRIMARY_TH,
            "n_genes": len(primary),
            "n_mouse": n_sp(primary, "10090"),
            "n_human": n_sp(primary, "9606"),
            "genes": [r["gene_human"] for r in primary],
            "note": "User-adopted widened cut; literature often cites ≥0.8 (kept as strict audit)",
        },
        "strict_audit": {
            "normalized_fit_score_min": STRICT_TH,
            "n_genes": len(strict),
            "genes": [r["gene_human"] for r in strict],
            "file": STRICT08.name,
            "literature": "Norm Fit ≥ 0.8 commonly used in network-pharmacology PharmMapper papers",
        },
        "unfiltered_backup": UNFILTERED.name if UNFILTERED.exists() else None,
    }
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        "PRIMARY(adopted) n=",
        len(primary),
        "mouse",
        n_sp(primary, "10090"),
        "human",
        n_sp(primary, "9606"),
        [r["gene_human"] for r in primary],
    )
    print("strict0.8 n=", len(strict), [r["gene_human"] for r in strict])
    print("wrote", MAIN_CSV)


if __name__ == "__main__":
    main()
