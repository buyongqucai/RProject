# -*- coding: utf-8 -*-
"""批量运行 SEA16（ChEMBL 27）作为新 SEA 公共代理 502 时的可审计回退。"""
from __future__ import annotations

import csv
import json
import re
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "数据文件" / "预测输入" / "代谢物预测输入_全库与主面板并集.csv"
OUT = ROOT / "数据文件" / "SEA16原始"
BASE = "https://sea16.docking.org"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/140 Safari/537.36"}


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update(UA)
    s.trust_env = False
    return s


def submit(s: requests.Session, query: str) -> str:
    page = s.get(BASE + "/search", timeout=45)
    page.raise_for_status()
    token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page.text).group(1)
    form = {
        "query_custom_fp_type": "rdkit_ecfp", "ref_type": "library",
        "ref_library_targets_paste": "", "query_type": "custom",
        "query_custom_targets_paste": query, "csrf_token": token,
    }
    response = s.post(BASE + "/search", data=form, timeout=90, allow_redirects=True)
    response.raise_for_status()
    if "/jobs/" not in response.url:
        raise RuntimeError(f"未返回 job URL: {response.url}")
    return response.url


def process_batch(batch_id: int, rows: list[dict], out_root: Path) -> dict:
    batch_dir = out_root / f"batch_{batch_id:03d}"
    batch_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = batch_dir / "manifest.json"
    if (batch_dir / "compound_target_hits.tsv").exists():
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    mapping = []
    query_lines = []
    for i, row in enumerate(rows, 1):
        compound_id = f"m{i:04d}"
        query_lines.append(f"{row['smiles']} {compound_id}")
        mapping.append({"compound_id": compound_id, "name_en": row["name_en"], "cid": row.get("cid", ""),
                        "smiles": row["smiles"], "source": row.get("source", "")})
    pd.DataFrame(mapping).to_csv(batch_dir / "compound_mapping.csv", index=False, encoding="utf-8-sig")

    s = session()
    s = session()
    job_url = ""
    if manifest_path.exists():
        old_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        job_url = old_manifest.get("job_url", "")
        if not job_url:
            match = re.search(r"https://sea16\.docking\.org/jobs/(search_[a-z0-9-]+)", old_manifest.get("error", ""))
            if match:
                job_url = match.group(0)
    if not job_url:
        job_url = submit(s, "\n".join(query_lines))
    job_id = job_url.rstrip("/").split("/")[-1]
    status_code = 202
    deadline = time.time() + 1800
    while time.time() < deadline:
        response = s.get(job_url, timeout=60)
        status_code = response.status_code
        if status_code == 200:
            break
        time.sleep(5)
    if status_code != 200:
        manifest = {"batch_id": batch_id, "job_id": job_id, "job_url": job_url, "status": "TIMEOUT",
                    "http_status": status_code, "compound_count": len(rows)}
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return manifest

    zip_path = batch_dir / "sea16_download.zip"
    with s.get(job_url + ".zip", timeout=180, stream=True) as response:
        response.raise_for_status()
        with zip_path.open("wb") as f:
            for chunk in response.iter_content(1024 * 256):
                if chunk:
                    f.write(chunk)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(batch_dir / "extracted")

    result_path = batch_dir / "extracted" / "sea-results.xls"
    mapped = []
    if result_path.exists():
        with result_path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                target_id = row.get("Target ID", "")
                species = "Homo" if target_id.upper().endswith("_HUMAN") else "Other"
                mapped.append({
                    "compound_id": row.get("Query ID", ""), "query_smiles": row.get("Query Smiles", ""),
                    "target_chembl_id": "", "target_species": species,
                    "target_gene": row.get("Name", ""), "target_name": row.get("Description", ""),
                    "uniprot_id": target_id, "uniprot_accession": "",
                    "sea_z_score": row.get("Z-Score", ""), "sea_p_value": row.get("P-Value", ""),
                    "sea_minus_log10_p": "", "max_tc": row.get("Max Tc", ""),
                    "query_known_hit_tanimoto": row.get("Max Tc", ""), "known_hit_id": "",
                    "known_hit_smiles": "", "sea_version": "SEA16_ChEMBL27_rdkit_ecfp4",
                })
    pd.DataFrame(mapped).to_csv(batch_dir / "compound_target_hits.tsv", sep="\t", index=False, encoding="utf-8-sig")
    manifest = {"batch_id": batch_id, "job_id": job_id, "job_url": job_url, "status": "SUCCESS",
                "compound_count": len(rows), "mapped_hit_rows": len(mapped),
                "sea_version": "SEA16_ChEMBL27_rdkit_ecfp4", "access_date": "2026-10-07"}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    df = pd.read_csv(INPUT)
    df = df[df["smiles"].fillna("").astype(str).str.strip().ne("")]
    records = df.to_dict("records")
    batches = [records[i:i + 10] for i in range(0, len(records), 10)]
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    with ThreadPoolExecutor(max_workers=1) as pool:
        futures = {pool.submit(process_batch, i + 1, batch, OUT): i + 1 for i, batch in enumerate(batches)}
        for future in as_completed(futures):
            batch_id = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {"batch_id": batch_id, "status": "ERROR", "error": repr(exc)}
                (OUT / f"batch_{batch_id:03d}" / "manifest.json").write_text(
                    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            results.append(result)
            print(json.dumps({k: result.get(k) for k in ["batch_id", "job_id", "status", "mapped_hit_rows", "error"]},
                             ensure_ascii=False), flush=True)
    summary = {"batches": len(batches), "compounds_with_smiles": len(records),
               "success": sum(r.get("status") == "SUCCESS" for r in results),
               "error": sum(r.get("status") != "SUCCESS" for r in results),
               "mapped_hit_rows": sum(int(r.get("mapped_hit_rows", 0)) for r in results),
               "sea_version": "SEA16_ChEMBL27_rdkit_ecfp4"}
    (OUT / "SEA16批量摘要.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
