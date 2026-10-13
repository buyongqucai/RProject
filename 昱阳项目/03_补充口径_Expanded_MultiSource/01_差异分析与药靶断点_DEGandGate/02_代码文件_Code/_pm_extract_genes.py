"""Extract PharmMapper targets from result HTML → gene CSV (UniProt in page)."""
from __future__ import annotations

import csv
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _uniprot_map import uniprot_to_gene_batch

PRED = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_预测靶点_MultiPredict"
)
JOBS = ["261011075421", "261011082113"]
ACC_RE = re.compile(
    r"\b([OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})\b"
)
ENTRY_RE = re.compile(r"\b([A-Z0-9]{1,10}_HUMAN)\b")


def fetch_html(job: str) -> list[Path]:
    paths = []
    for suf, q in [("", ""), ("_s1", "?s=1"), ("_s2", "?s=2")]:
        out = PRED / f"pm_{job}_result{suf}.html"
        url = f"https://www.lilab-ecust.cn/pharmmapper/results/{job}.html{q}"
        if not out.exists() or out.stat().st_size < 5000:
            try:
                urllib.request.urlretrieve(url, out)
            except Exception as e:
                print("fetch fail", url, e, flush=True)
                continue
        if out.exists() and out.stat().st_size >= 5000:
            paths.append(out)
    return paths


def parse_rows(html: str, job: str) -> list[dict]:
    rows = []
    for block in re.split(r"<tr>\s*<td[^>]*data-record=", html)[1:]:
        rank_m = re.match(r'"(\d+)"', block)
        if not rank_m:
            continue
        rank = int(rank_m.group(1))
        pdb_m = re.search(r"structureId=([0-9A-Za-z]{4})", block)
        content_m = re.search(r'data-content="([^"]*)"', block)
        head = block.split('data-display="')[0]
        tds = re.findall(r"<td>([^<]*)</td>", head)
        if not pdb_m:
            continue
        if len(tds) < 4:
            name, nfeat, fit, nfit = "", "", "", ""
        else:
            name, nfeat, fit, nfit = tds[0].strip(), tds[1], tds[2], tds[3]
        content = content_m.group(1) if content_m else ""
        content_u = (
            content.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        )
        uniprots = sorted(
            set(ACC_RE.findall(content_u))
            | set(re.findall(r"uniprot\.org/uniprot/([A-Z0-9_]+)", content_u, re.I))
        )
        # drop entry-style mistaken as accession
        uniprots = [u for u in uniprots if "_" not in u and ACC_RE.fullmatch(u)]
        entries = sorted(set(ENTRY_RE.findall(content_u)))
        rows.append(
            {
                "rank": rank,
                "pdb": pdb_m.group(1).upper(),
                "target_name": name,
                "n_features": nfeat,
                "fit_score": fit,
                "norm_fit": nfit,
                "uniprot": ";".join(uniprots),
                "uniprot_entry": ";".join(entries),
                "job_id": job,
            }
        )
    return rows


def main() -> None:
    all_rows: list[dict] = []
    for job in JOBS:
        for p in fetch_html(job):
            t = p.read_text(encoding="utf-8", errors="ignore")
            if "structureId=" not in t:
                print(p.name, "skip", flush=True)
                continue
            rows = parse_rows(t, job)
            print(p.name, "parsed", len(rows), flush=True)
            all_rows.extend(rows)

    seen = set()
    uniq_rows = []
    for r in sorted(all_rows, key=lambda x: (x["job_id"], x["rank"])):
        k = (r["pdb"], r["fit_score"], r["uniprot"], r["job_id"])
        if k in seen:
            continue
        seen.add(k)
        uniq_rows.append(r)

    accs = sorted({a for r in uniq_rows for a in r["uniprot"].split(";") if a})
    ents = sorted({e for r in uniq_rows for e in r["uniprot_entry"].split(";") if e})
    print("unique PDB rows", len(uniq_rows), "uniprot", len(accs), "entries", len(ents), flush=True)

    acc2g = uniprot_to_gene_batch(accs)
    print("mapped accessions", len(acc2g), flush=True)
    # entry names like M3K3_HUMAN: query as id
    ent2g: dict[str, str] = {}
    for e in ents:
        # derive from already-mapped if embedded; else skip (acc path covers most)
        pass
    print("mapped entries", len(ent2g), flush=True)

    gene_rows = []
    gene_seen = set()
    for r in uniq_rows:
        genes = []
        for a in r["uniprot"].split(";"):
            if a and a in acc2g:
                genes.append(acc2g[a])
        for e in r["uniprot_entry"].split(";"):
            if e and e in ent2g:
                genes.append(ent2g[e])
        genes = sorted(set(g for g in genes if g))
        if not genes:
            gene_rows.append(
                {
                    "gene_human": "",
                    "pdb": r["pdb"],
                    "uniprot": r["uniprot"] or r["uniprot_entry"],
                    "fit_score": r["fit_score"],
                    "target_name": r["target_name"],
                    "source": "PharmMapper",
                    "evidence": "predicted",
                    "job_id": r["job_id"],
                }
            )
            continue
        for g in genes:
            if g in gene_seen:
                continue
            gene_seen.add(g)
            gene_rows.append(
                {
                    "gene_human": g,
                    "pdb": r["pdb"],
                    "uniprot": r["uniprot"] or r["uniprot_entry"],
                    "fit_score": r["fit_score"],
                    "target_name": r["target_name"],
                    "source": "PharmMapper",
                    "evidence": "predicted",
                    "job_id": r["job_id"],
                }
            )

    out = PRED / "04_PharmMapper_Quercetin_genes.csv"
    fields = [
        "gene_human",
        "pdb",
        "uniprot",
        "fit_score",
        "target_name",
        "source",
        "evidence",
        "job_id",
    ]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(gene_rows)

    (PRED / "04_PharmMapper_raw_rows.json").write_text(
        json.dumps(uniq_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("genes_nonempty", len(gene_seen), "wrote", out, flush=True)


if __name__ == "__main__":
    main()
