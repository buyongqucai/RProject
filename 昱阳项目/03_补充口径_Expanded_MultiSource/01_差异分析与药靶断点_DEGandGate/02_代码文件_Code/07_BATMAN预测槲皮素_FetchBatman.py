"""BATMAN-TCM 2.0: queryTarget for quercetin PubChem CID 5280343."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PRED = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_STP_STITCH_PharmMapper_TargetNet_BATMAN_预测靶点"
)
CID = "5280343"
SCORE = 20
PVAL = 0.05
JOB = f"batman-yuyang-quercetin-{int(time.time())}"

POST_URLS = [
    "http://batman2api.cloudna.cn/queryTarget",
    "http://bionet.ncpsb.org.cn/api/queryTarget",
    "http://batman2.cloudna.cn/api/queryTarget",
]
RESULT_BASES = [
    "http://bionet.ncpsb.org.cn/api/queryTargetResult",
    "http://batman2api.cloudna.cn/queryTargetResult",
    "http://batman2.cloudna.cn/api/queryTargetResult",
]


def http_json(url: str, body: dict | None = None, method: str = "GET") -> tuple[int, object]:
    data = None
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
        method = "POST"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = r.read()
            try:
                return r.status, json.loads(raw.decode("utf-8", errors="replace"))
            except Exception:
                return r.status, raw[:500]
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:500]


body = {
    "jobId": JOB,
    "content": [
        {
            "type": "compound",
            "clusterName": "quercetin",
            "list": [CID],
        }
    ],
    "userInScore": SCORE,
    "pvalue": PVAL,
    "homo": 0,
}

ok_post = None
for url in POST_URLS:
    code, resp = http_json(url, body)
    print("POST", url, code, str(resp)[:200])
    if code == 200 and isinstance(resp, dict) and resp.get("status") in (200, "200", 0, "0"):
        ok_post = url
        (PRED / "06_BATMAN_queryTarget_submit.json").write_text(
            json.dumps({"url": url, "body": body, "resp": resp}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        break
    # some APIs return 200 with status field only after accept
    if code == 200 and isinstance(resp, dict):
        ok_post = url
        (PRED / "06_BATMAN_queryTarget_submit.json").write_text(
            json.dumps({"url": url, "body": body, "resp": resp}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        break

if not ok_post:
    raise SystemExit("BATMAN queryTarget submit failed")

# poll result
genes = []
final = None
for i in range(40):
    time.sleep(3 if i else 1)
    for base in RESULT_BASES:
        q = urllib.parse.urlencode(
            {
                "tab": "tab1",
                "userInScore": SCORE,
                "pvalue": PVAL,
                "jobId": JOB,
                "top_20": 0,
                "drug_score": 0,
            }
        )
        url = f"{base}?{q}"
        code, resp = http_json(url)
        print("GET", i, base, code, str(resp)[:180])
        if code != 200 or not isinstance(resp, dict):
            continue
        st = resp.get("status")
        if st == 300:
            continue
        if st == 200 and resp.get("result"):
            final = resp
            break
    if final:
        break

if not final:
    raise SystemExit("BATMAN result not ready / failed")

(PRED / "06_BATMAN_queryTarget_result_raw.json").write_text(
    json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8"
)

# parse genes from nested tables (frontend path)
result = final.get("result", {})
tables = result.get("table") or []
rows_out = []
for block in tables:
    cluster = block.get("clusterName")
    for row in block.get("table") or []:
        # row structure from frontend: [..., cid, geneKnown pairs, ...]
        # fallback: walk nested lists for [geneid, name, score]
        if not isinstance(row, (list, tuple)) or len(row) < 3:
            continue
        cid = row[1] if len(row) > 1 else CID
        gene_pairs = row[2] if len(row) > 2 else []
        if isinstance(gene_pairs, list):
            for g in gene_pairs:
                if isinstance(g, (list, tuple)) and len(g) >= 2:
                    rows_out.append(
                        {
                            "gene_human": g[1],
                            "gene_id": g[0],
                            "score": g[2] if len(g) > 2 else "",
                            "cid": cid,
                            "clusterName": cluster,
                            "source": "BATMAN-TCM2_queryTarget",
                            "evidence": "predicted",
                        }
                    )

# also flatten any gene/name keys
if not rows_out:
    text = json.dumps(final)


def walk(o):
    if isinstance(o, dict):
        if "name" in o and ("gene" in o or "geneid" in o or "geneId" in o):
            rows_out.append(
                {
                    "gene_human": o.get("name") or o.get("gene"),
                    "gene_id": o.get("geneid") or o.get("geneId") or o.get("gene"),
                    "score": o.get("score", ""),
                    "cid": o.get("cid", CID),
                    "clusterName": o.get("clusterName", "quercetin"),
                    "source": "BATMAN-TCM2_queryTarget",
                    "evidence": "predicted",
                }
            )
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)


if not rows_out:
    walk(final)

# unique by gene
seen = set()
uniq = []
for r in rows_out:
    g = str(r.get("gene_human") or "").strip()
    if not g or g in seen:
        continue
    seen.add(g)
    uniq.append(r)

out_csv = PRED / "06_BATMAN_Quercetin_genes.csv"
import csv

with out_csv.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(
        f,
        fieldnames=["gene_human", "gene_id", "score", "cid", "clusterName", "source", "evidence"],
    )
    w.writeheader()
    w.writerows(uniq)

print("genes", len(uniq), "->", out_csv)
print("jobId", JOB)
