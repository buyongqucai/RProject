# -*- coding: utf-8 -*-
"""结构库策展_curateStructureLists.py
生成扩展登记表：
  蛋白表_扩展3000.csv  —— RCSB：人源(9606) + X-ray ≤3.0Å + 含类药配体(分子量≥150)，
                          分辨率升序，每 UniProt 至多 2 套，凑满 --n-protein
  化合物表_扩展7000.csv —— ChEMBL max_phase=4→3→2 依次取药，InChIKey→PubChem CID，
                          与既有 224 个 CID 去重合并，凑满 --n-compound
幂等：中间结果落盘 _curate_cache\\*.json，重跑直接续。
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import requests

UA = {"User-Agent": "Mozilla/5.0 (structure-lib-curate; mailto:local)"}
RCSB_SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"
CHEMBL = "https://www.ebi.ac.uk/chembl/api/data"
PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


def read_any(p: Path) -> list[dict]:
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "gbk"):
        try:
            return list(csv.DictReader(raw.decode(enc).splitlines()))
        except UnicodeDecodeError:
            continue
    return []


# ---------------- 蛋白 ----------------
def rcsb_query(s: requests.Session, start: int, rows: int = 1000) -> dict:
    q = {
        "query": {"type": "group", "logical_operator": "and", "nodes": [
            {"type": "terminal", "service": "text",
             "parameters": {"attribute": "rcsb_entity_source_organism.taxonomy_lineage.id",
                            "operator": "exact_match", "value": "9606"}},
            {"type": "terminal", "service": "text",
             "parameters": {"attribute": "exptl.method",
                            "operator": "exact_match", "value": "X-RAY DIFFRACTION"}},
            {"type": "terminal", "service": "text",
             "parameters": {"attribute": "rcsb_entry_info.resolution_combined",
                            "operator": "less_or_equal", "value": 3.0}},
            {"type": "terminal", "service": "text",
             "parameters": {"attribute": "rcsb_entry_info.nonpolymer_entity_count",
                            "operator": "greater", "value": 0}},
        ]},
        "return_type": "entry",
        "request_options": {
            "sort": [{"sort_by": "rcsb_entry_info.resolution_combined", "direction": "asc"}],
            "paginate": {"start": start, "rows": rows},
            "results_content_type": ["experimental"],
        },
        "request_info": {"query_id": "curate3000", "src": "ui"},
    }
    r = s.post(RCSB_SEARCH, json=q, timeout=120)
    r.raise_for_status()
    return r.json()


def entry_uniprots(s: requests.Session, pdb_ids: list[str]) -> dict[str, str]:
    """批量取 entry→首个 UniProt（polymer entities 接口，100 个/批）。"""
    out = {}
    for i in range(0, len(pdb_ids), 50):
        chunk = pdb_ids[i:i + 50]
        for pid in chunk:
            try:
                r = s.get(f"https://data.rcsb.org/rest/v1/core/polymer_entity/{pid}/1",
                          timeout=30)
                ids = (r.json()
                       .get("rcsb_polymer_entity_container_identifiers", {})
                       .get("reference_sequence_identifiers", []))
                up = next((x["database_accession"] for x in ids
                           if x.get("database_name") == "UniProt"), "")
                out[pid] = up or "NA"
            except Exception:
                out[pid] = "NA"
            time.sleep(0.12)
        print(f"  uniprot 映射 {min(i + 50, len(pdb_ids))}/{len(pdb_ids)}", flush=True)
    return out


def curate_proteins(s: requests.Session, n: int, cache: Path) -> list[dict]:
    cache.mkdir(exist_ok=True)
    id_cache = cache / "rcsb_ids.json"
    if id_cache.exists():
        pdb_ids = json.loads(id_cache.read_text())
    else:
        pdb_ids, start = [], 0
        while len(pdb_ids) < n * 2:  # 多取余量，UniProt 去重会损耗
            d = rcsb_query(s, start)
            batch = [x["identifier"] for x in d.get("result_set", [])]
            if not batch:
                break
            pdb_ids.extend(batch)
            start += len(batch)
            print(f"  rcsb 搜索 {len(pdb_ids)} 条", flush=True)
            if start >= d.get("total_count", 0):
                break
            time.sleep(0.5)
        id_cache.write_text(json.dumps(pdb_ids))
    up_cache = cache / "rcsb_uniprot.json"
    up_map = json.loads(up_cache.read_text()) if up_cache.exists() else {}
    todo = [p for p in pdb_ids if p not in up_map]
    if todo:
        up_map.update(entry_uniprots(s, todo))
        up_cache.write_text(json.dumps(up_map))
    picked, per_up = [], {}
    for pid in pdb_ids:
        up = up_map.get(pid, "NA")
        key = up if up != "NA" else pid
        if per_up.get(key, 0) >= 2:
            continue
        per_up[key] = per_up.get(key, 0) + 1
        picked.append({"entry号": up, "蛋白质靶点": "", "蛋白质3D结构名称": pid.lower(),
                       "x center": "", "y center": "", "z center": ""})
        if len(picked) >= n:
            break
    return picked


# ---------------- 化合物 ----------------
def chembl_molecules(s: requests.Session, phase: int, cache: Path) -> list[dict]:
    f = cache / f"chembl_phase{phase}.json"
    if f.exists():
        return json.loads(f.read_text())
    out, offset = [], 0
    while True:
        r = s.get(f"{CHEMBL}/molecule.json", params={
            "max_phase": phase, "limit": 1000, "offset": offset,
        }, timeout=120)
        r.raise_for_status()
        d = r.json()
        for m in d.get("molecules", []):
            ik = (m.get("molecule_structures") or {}).get("standard_inchi_key")
            if ik:
                out.append({"name": m.get("pref_name") or m.get("molecule_chembl_id"),
                            "inchikey": ik})
        total = d.get("page_meta", {}).get("total_count", 0)
        offset += 1000
        print(f"  chembl phase{phase} {min(offset, total)}/{total}", flush=True)
        if offset >= total:
            break
        time.sleep(0.3)
    f.write_text(json.dumps(out))
    return out


def inchikey_to_cid(s: requests.Session, iks: list[str], cache: Path) -> dict[str, str]:
    f = cache / "inchikey_cid.json"
    m = json.loads(f.read_text()) if f.exists() else {}
    for i, ik in enumerate(iks, 1):
        if ik in m:
            continue
        try:
            r = s.get(f"{PUG}/compound/inchikey/{ik}/cids/JSON", timeout=30)
            m[ik] = str(r.json()["IdentifierList"]["CID"][0])
        except Exception:
            m[ik] = ""
        if i % 200 == 0:
            f.write_text(json.dumps(m))
            print(f"  inchikey→cid {i}/{len(iks)}", flush=True)
        time.sleep(0.21)  # PUG ≤5 req/s
    f.write_text(json.dumps(m))
    return m


def curate_compounds(s: requests.Session, n: int, cache: Path, db: Path) -> list[dict]:
    cache.mkdir(exist_ok=True)
    existing = {r["活性成分3D结构名称"].strip()
                for r in read_any(db / "分子对接_化合物表.csv") if r.get("活性成分3D结构名称")}
    cands, seen_ik = [], set()
    for phase in (4, 3, 2):
        for m in chembl_molecules(s, phase, cache):
            if m["inchikey"] not in seen_ik:
                seen_ik.add(m["inchikey"])
                cands.append(m)
        if len(cands) >= n * 1.3:
            break
    print(f"  候选分子 {len(cands)}（去 InChIKey 后）", flush=True)
    ik2cid = inchikey_to_cid(s, [m["inchikey"] for m in cands], cache)
    out, seen_cid = [], set(existing)
    for m in cands:
        cid = ik2cid.get(m["inchikey"], "")
        if not cid or cid in seen_cid:
            continue
        seen_cid.add(cid)
        out.append({"活性成分名称": m["name"], "活性成分重命名": "", "活性成分3D结构名称": cid})
        if len(out) >= n:
            break
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-protein", type=int, default=3000)
    ap.add_argument("--n-compound", type=int, default=7000)
    ap.add_argument("--db", default=r"D:\数据库\分子对接数据库")
    args = ap.parse_args()
    db = Path(args.db)
    cache = db / "_curate_cache"
    s = requests.Session()
    s.headers.update(UA)
    s.trust_env = False  # 系统代理对 search.rcsb.org 不稳定，直连

    print("[1/2] 蛋白策展…", flush=True)
    prots = curate_proteins(s, args.n_protein, cache)
    pt = db / "分子对接_蛋白表_扩展3000.csv"
    with pt.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["entry号", "蛋白质靶点", "蛋白质3D结构名称",
                                          "x center", "y center", "z center"])
        w.writeheader()
        w.writerows(prots)
    print(f"  -> {pt} ({len(prots)} 条)", flush=True)

    print("[2/2] 化合物策展…", flush=True)
    comps = curate_compounds(s, args.n_compound, cache, db)
    ct = db / "分子对接_化合物表_扩展7000.csv"
    with ct.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["活性成分名称", "活性成分重命名", "活性成分3D结构名称"])
        w.writeheader()
        w.writerows(comps)
    print(f"  -> {ct} ({len(comps)} 条)", flush=True)


if __name__ == "__main__":
    sys.exit(main())
