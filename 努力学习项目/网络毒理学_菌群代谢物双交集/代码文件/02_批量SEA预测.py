# -*- coding: utf-8 -*-
"""批量提交 SEA（ChEMBL 36）并保存可审计结果。"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import re
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "数据文件" / "预测输入" / "代谢物预测输入_全库与主面板并集.csv"
OUT = ROOT / "数据文件" / "SEA原始"
BASE = "https://sea.bkslab.org"
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": BASE + "/",
}


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update(UA)
    retry = Retry(
        total=8, connect=8, read=8, backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    return s


def solve_altcha(s: requests.Session) -> str:
    ch = s.get(BASE + "/api/captcha/challenge", timeout=45).json()
    target = bytes.fromhex(ch["challenge"])
    salt = ch["salt"].encode()
    number = None
    for n in range(int(ch["maxNumber"]) + 1):
        if hashlib.sha256(salt + str(n).encode()).digest() == target:
            number = n
            break
    if number is None:
        raise RuntimeError("ALTCHA PoW 未找到解")
    payload = {
        "algorithm": ch["algorithm"], "challenge": ch["challenge"],
        "number": number, "salt": ch["salt"], "signature": ch["signature"],
    }
    return base64.b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()


def submit_batch(batch_id: int, rows: list[dict], out_root: Path) -> dict:
    batch_dir = out_root / f"batch_{batch_id:03d}"
    batch_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = batch_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("status") == "SUCCESS" and (batch_dir / "sea_result.tsv").exists():
            return manifest

    mapping = []
    query_lines = []
    for i, row in enumerate(rows, 1):
        compound_id = f"m{i:04d}"
        query_lines.append(f"{row['smiles']} {compound_id}")
        mapping.append({
            "compound_id": compound_id, "name_en": row["name_en"],
            "cid": row.get("cid", ""), "smiles": row["smiles"], "source": row.get("source", ""),
        })
    pd.DataFrame(mapping).to_csv(batch_dir / "compound_mapping.csv", index=False, encoding="utf-8-sig")

    s = session()
    altcha = solve_altcha(s)
    body = {
        "query": "\n".join(query_lines), "fingerprint_type": "ecfp4",
        "reference_target": "all", "reference_custom_targets": "",
        "query_target": "subset", "query_subset_targets": "", "query_custom": "",
        "altcha": altcha,
    }
    response = s.post(BASE + "/api/submit", json=body, timeout=90)
    response.raise_for_status()
    task_id = response.json()["task_id"]

    status = "PENDING"
    detail = {}
    deadline = time.time() + 1800
    while time.time() < deadline:
        try:
            detail = s.get(BASE + "/api/result", params={"taskId": task_id}, timeout=90).json()
            status = detail.get("status", "RUNNING")
            if status in {"SUCCESS", "ERROR"}:
                break
        except Exception:
            time.sleep(5)
        time.sleep(5)
    manifest = {
        "batch_id": batch_id, "task_id": task_id, "status": status,
        "compound_count": len(rows), "names": [r["name_en"] for r in rows],
        "detail": detail, "access_date": "2026-10-07",
    }
    if status != "SUCCESS":
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return manifest

    zip_path = batch_dir / "sea_download.zip"
    with s.get(BASE + "/api/download", params={"taskId": task_id}, timeout=180, stream=True) as r:
        r.raise_for_status()
        with zip_path.open("wb") as f:
            for chunk in r.iter_content(1024 * 256):
                if chunk:
                    f.write(chunk)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(batch_dir / "extracted")

    extracted = batch_dir / "extracted"
    sea_result = extracted / "sea_result.tsv"
    if sea_result.exists():
        sea_result.replace(batch_dir / "sea_result.tsv")
    sea_all = extracted / "sea_result_all.tsv"
    if sea_all.exists():
        sea_all.replace(batch_dir / "sea_result_all.tsv")

    target_rows = []
    if (batch_dir / "sea_result.tsv").exists():
        target_rows = list(csv.DictReader((batch_dir / "sea_result.tsv").open(encoding="utf-8-sig"), delimiter="\t"))
    valid_targets = {r["Target_Chembl_ID"] for r in target_rows}
    mapped = []
    for top10 in extracted.glob("top10_*.tsv"):
        target_id = top10.stem.replace("top10_", "")
        if target_id not in valid_targets:
            continue
        meta = next((r for r in target_rows if r["Target_Chembl_ID"] == target_id), {})
        with top10.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                try:
                    tanimoto = float(row.get("Tanimoto_Score", "0"))
                except ValueError:
                    tanimoto = 0.0
                if tanimoto <= 0:
                    continue
                mapped.append({
                    "compound_id": row.get("Name", ""), "query_smiles": row.get("SMILES", ""),
                    "target_chembl_id": target_id, "target_species": meta.get("Target_Species", ""),
                    "target_name": meta.get("Target_Name", ""), "uniprot_id": meta.get("Uniprot_ID", ""),
                    "uniprot_accession": meta.get("Uniprot_Accession", ""),
                    "sea_z_score": meta.get("Z_score", ""), "sea_p_value": meta.get("p_value", ""),
                    "sea_minus_log10_p": meta.get("p(P_value)", ""), "max_tc": meta.get("MaxTc", ""),
                    "query_known_hit_tanimoto": row.get("Tanimoto_Score", ""),
                    "known_hit_id": row.get("Known_Hit_ID", ""), "known_hit_smiles": row.get("Known_Hit_SMILES", ""),
                })
    pd.DataFrame(mapped).to_csv(batch_dir / "compound_target_hits.tsv", sep="\t", index=False, encoding="utf-8-sig")
    manifest["mapped_hit_rows"] = len(mapped)
    manifest["sea_target_rows"] = len(target_rows)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=10)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    df = df[df["smiles"].fillna("").astype(str).str.strip().ne("")].copy()
    records = df.to_dict("records")
    batches = [records[i:i + args.batch_size] for i in range(0, len(records), args.batch_size)]

    manifests = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(submit_batch, i + 1, batch, OUT): i + 1 for i, batch in enumerate(batches)}
        for future in as_completed(futures):
            batch_id = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {"batch_id": batch_id, "status": "ERROR", "error": repr(exc)}
                (OUT / f"batch_{batch_id:03d}").mkdir(parents=True, exist_ok=True)
                (OUT / f"batch_{batch_id:03d}" / "manifest.json").write_text(
                    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            manifests.append(result)
            print(json.dumps({k: result.get(k) for k in ["batch_id", "task_id", "status", "compound_count", "mapped_hit_rows", "error"]}, ensure_ascii=False), flush=True)

    summary = {
        "batches": len(batches), "compounds_with_smiles": len(records),
        "success": sum(x.get("status") == "SUCCESS" for x in manifests),
        "error": sum(x.get("status") != "SUCCESS" for x in manifests),
        "mapped_hit_rows": sum(int(x.get("mapped_hit_rows", 0)) for x in manifests),
    }
    (OUT / "SEA批量摘要.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
