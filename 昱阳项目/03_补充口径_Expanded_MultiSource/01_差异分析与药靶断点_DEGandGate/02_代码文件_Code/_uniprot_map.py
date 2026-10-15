"""Shared UniProt accession → gene symbol mapper (batch search)."""
from __future__ import annotations

import time
import urllib.parse
import urllib.request


def uniprot_to_gene_batch(accs: list[str], pause: float = 0.15) -> dict[str, str]:
    out: dict[str, str] = {}
    accs = sorted(set(a for a in accs if a))
    for i in range(0, len(accs), 25):
        batch = accs[i : i + 25]
        q = " OR ".join(f"accession:{a}" for a in batch)
        params = urllib.parse.urlencode(
            {
                "query": q,
                "format": "tsv",
                "fields": "accession,gene_names,organism_id",
                "size": str(len(batch)),
            }
        )
        url = f"https://rest.uniprot.org/uniprotkb/search?{params}"
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                txt = r.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print("uniprot batch fail", e, flush=True)
            time.sleep(1)
            continue
        lines = [ln for ln in txt.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        header = lines[0].split("\t")
        for ln in lines[1:]:
            cols = ln.split("\t")
            d = dict(zip(header, cols))
            acc = d.get("Entry") or cols[0]
            gene = (d.get("Gene Names") or "").strip().split()
            org = d.get("Organism (ID)") or ""
            if gene:
                # prefer human
                if acc not in out or org == "9606":
                    out[acc] = gene[0]
        print("uniprot mapped", len(out), "/", min(i + len(batch), len(accs)), flush=True)
        time.sleep(pause)
    return out
