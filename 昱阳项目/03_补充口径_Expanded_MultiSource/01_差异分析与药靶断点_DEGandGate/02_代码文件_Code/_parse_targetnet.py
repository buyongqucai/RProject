"""Parse TargetNet result HTML → gene CSV (prefer Gene / Target columns)."""
from __future__ import annotations

import csv
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

PRED = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_预测靶点_MultiPredict"
)
HTML = PRED / "_targetnet_result.html"
ACC_RE = re.compile(
    r"^(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})$"
)


def uniprot_to_gene_batch(accs: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    # UniProt retrieve by query OR — batch of 20
    for i in range(0, len(accs), 20):
        batch = accs[i : i + 20]
        q = " OR ".join(f"accession:{a}" for a in batch)
        params = urllib.parse.urlencode(
            {
                "query": q,
                "format": "tsv",
                "fields": "accession,gene_names",
                "size": str(len(batch)),
            }
        )
        url = f"https://rest.uniprot.org/uniprotkb/search?{params}"
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                txt = r.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print("batch fail", e, flush=True)
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
            if gene:
                out[acc] = gene[0]
        print("mapped", len(out), "/", i + len(batch), flush=True)
        time.sleep(0.2)
    return out


def main() -> None:
    t = HTML.read_text(encoding="utf-8", errors="ignore")
    # find header
    thead = re.search(r"<thead>(.*?)</thead>", t, re.I | re.S)
    headers = []
    if thead:
        headers = [
            re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).strip()
            for h in re.findall(r"<th[^>]*>(.*?)</th>", thead.group(1), re.I | re.S)
        ]
    print("headers", headers)

    rows = []
    # data rows in tbody
    tbody = re.search(r"<tbody>(.*?)</tbody>", t, re.I | re.S)
    body = tbody.group(1) if tbody else t
    for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", body, re.I | re.S):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", m.group(1), re.I | re.S)
        clean = [re.sub(r"<[^>]+>", " ", c) for c in cells]
        clean = [re.sub(r"\s+", " ", c).strip() for c in clean]
        if len(clean) < 2:
            continue
        row = {"raw": clean}
        if headers and len(headers) == len(clean):
            row.update(dict(zip(headers, clean)))
        rows.append(row)

    print("nrows", len(rows), "sample", rows[:2])

    # identify gene / uniprot columns
    gene_keys = [h for h in headers if re.search(r"gene", h, re.I)]
    uni_keys = [h for h in headers if re.search(r"uniprot", h, re.I)]
    prob_keys = [h for h in headers if re.search(r"prob|score|auc", h, re.I)]
    print("gene_keys", gene_keys, "uni_keys", uni_keys, "prob_keys", prob_keys)

    pairs = []  # (uniprot, prob)
    for r in rows:
        u = ""
        for k in uni_keys:
            v = r.get(k, "")
            if ACC_RE.match(v):
                u = v
                break
        if not u:
            continue
        try:
            prob = float(r.get("Prob") or "0")
        except ValueError:
            prob = 0.0
        if prob <= 0:
            continue
        pairs.append((u, prob))

    accs = sorted({u for u, _ in pairs})
    print("accs Prob>0", len(accs), "of rows", len(pairs))
    acc2g = uniprot_to_gene_batch(accs) if accs else {}

    csv_path = PRED / "05_TargetNet_Quercetin_genes.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["gene_human", "uniprot", "prob", "source", "evidence"],
        )
        w.writeheader()
        seen = set()
        n = 0
        for u, prob in sorted(pairs, key=lambda x: -x[1]):
            g = acc2g.get(u, "")
            if not g or g in seen:
                continue
            seen.add(g)
            w.writerow(
                {
                    "gene_human": g,
                    "uniprot": u,
                    "prob": prob,
                    "source": "TargetNet",
                    "evidence": "predicted",
                }
            )
            n += 1
    print("wrote", csv_path, "n", n)
    (PRED / "05_TargetNet_parse_meta.json").write_text(
        json.dumps(
            {
                "headers": headers,
                "nrows": len(rows),
                "n_prob_gt0": len(accs),
                "n_genes": n,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
