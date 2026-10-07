# -*- coding: utf-8 -*-
"""SEA 批量恢复/续跑：保存 task_id，断点续传下载并映射化合物靶点。"""
from __future__ import annotations

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

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "准备文件" / "预测输入" / "代谢物预测输入_主面板.csv"
OUT = ROOT / "准备文件" / "SEA原始"
STP_DIR = ROOT / "准备文件" / "STP原始"
BASE = "https://sea.docking.org"
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": BASE + "/",
}


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(UA)
    return s


def retry_call(func, attempts=12, base_delay=2):
    last = None
    for attempt in range(attempts):
        try:
            return func()
        except Exception as exc:
            last = exc
            time.sleep(min(30, base_delay * (attempt + 1)))
    raise last


def solve_altcha(s: requests.Session) -> str:
    ch = retry_call(lambda: s.get(BASE + "/api/captcha/challenge", timeout=45).json())
    target = bytes.fromhex(ch["challenge"])
    salt = ch["salt"].encode()
    number = next((n for n in range(int(ch["maxNumber"]) + 1)
                   if hashlib.sha256(salt + str(n).encode()).digest() == target), None)
    if number is None:
        raise RuntimeError("ALTCHA PoW 未找到解")
    payload = {"algorithm": ch["algorithm"], "challenge": ch["challenge"], "number": number,
               "salt": ch["salt"], "signature": ch["signature"]}
    return base64.b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()


def task_id_from_manifest(path: Path) -> str:
    if not path.exists():
        return ""
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("task_id"):
        return str(data["task_id"])
    match = re.search(r"taskId=([a-z0-9]+)", data.get("error", ""))
    return match.group(1) if match else ""


def download_zip(s: requests.Session, task_id: str, path: Path) -> None:
    for attempt in range(15):
        try:
            with s.get(BASE + "/api/download", params={"taskId": task_id}, timeout=180, stream=True) as r:
                r.raise_for_status()
                tmp = path.with_suffix(".part")
                with tmp.open("wb") as f:
                    for chunk in r.iter_content(1024 * 256):
                        if chunk:
                            f.write(chunk)
                tmp.replace(path)
                return
        except Exception:
            time.sleep(min(30, 3 * (attempt + 1)))
    raise RuntimeError(f"下载失败: {task_id}")


def process_batch(batch_id: int, rows: list[dict], out_root: Path) -> dict:
    batch_dir = out_root / f"batch_{batch_id:03d}"
    batch_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = batch_dir / "manifest.json"
    mapping_path = batch_dir / "compound_mapping.csv"
    if (batch_dir / "compound_target_hits.tsv").exists() and (batch_dir / "sea_result.tsv").exists():
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    if not mapping_path.exists():
        mapping = []
        query_lines = []
        for i, row in enumerate(rows, 1):
            compound_id = f"m{i:04d}"
            query_lines.append(f"{row['smiles']} {compound_id}")
            mapping.append({"compound_id": compound_id, "name_en": row["name_en"], "cid": row.get("cid", ""),
                            "smiles": row["smiles"], "source": row.get("source", "")})
        pd.DataFrame(mapping).to_csv(mapping_path, index=False, encoding="utf-8-sig")
    else:
        mapping = pd.read_csv(mapping_path).to_dict("records")
        query_lines = [f"{r['smiles']} {r['compound_id']}" for r in mapping]

    s = make_session()
    task_id = task_id_from_manifest(manifest_path)
    if not task_id:
        body = {"query": "\n".join(query_lines), "fingerprint_type": "ecfp4", "reference_target": "all",
                "reference_custom_targets": "", "query_target": "subset", "query_subset_targets": "",
                "query_custom": "", "altcha": solve_altcha(s)}
        response = retry_call(lambda: s.post(BASE + "/api/submit", json=body, timeout=90), attempts=8)
        response.raise_for_status()
        task_id = response.json()["task_id"]
        (batch_dir / "submitted.json").write_text(json.dumps({"task_id": task_id, "names": [r["name_en"] for r in rows]},
                                                             ensure_ascii=False, indent=2), encoding="utf-8")

    detail = {}
    status = "PENDING"
    deadline = time.time() + 1800
    while time.time() < deadline:
        try:
            detail = s.get(BASE + "/api/result", params={"taskId": task_id}, timeout=90).json()
            status = detail.get("status", "RUNNING")
            if status in {"SUCCESS", "ERROR"}:
                break
        except Exception:
            pass
        time.sleep(5)

    manifest = {"batch_id": batch_id, "task_id": task_id, "status": status, "compound_count": len(rows),
                "names": [r["name_en"] for r in rows], "detail": detail, "access_date": "2026-10-07"}
    if status != "SUCCESS":
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return manifest

    # 下载 ZIP 在公共代理下容易 502；改用 /api/result 与 /api/best_similarity 等价重建逐化合物命中。
    target_rows = detail.get("result", []) or []
    # 仅对 STP 也命中的 UniProt 靶点调用 best_similarity，避免对 SEA 全靶点逐个请求。
    stp_accessions = set()
    for rec in mapping:
        safe = re.sub(r"[^\\w\\-]+", "_", str(rec.get("name_en", "")))
        stp_path = STP_DIR / f"{safe}_Swiss预测靶点_筛选后.csv"
        if not stp_path.exists():
            continue
        stp_frame = pd.read_csv(stp_path)
        for value in stp_frame.get("Uniprot ID", pd.Series(dtype=str)).dropna().astype(str):
            stp_accessions.update(x.strip() for x in value.replace("&", ";").split(";") if x.strip())
    target_rows = [row for row in target_rows if str(row.get("Uniprot_Accession", "")) in stp_accessions]
    pd.DataFrame(target_rows).to_csv(batch_dir / "sea_result.tsv", sep="\t", index=False, encoding="utf-8-sig")
    mapped = []
    for meta in target_rows:
        target_id = str(meta.get("Target_Chembl_ID", ""))
        if not target_id:
            continue
        best = retry_call(lambda: s.get(BASE + "/api/best_similarity",
                                        params={"taskId": task_id, "target_chembl_id": target_id},
                                        timeout=90).json(), attempts=8)
        per_compound = {}
        for row in best.get("best_similarity", []):
            name = str(row.get("Name", ""))
            try:
                tanimoto = float(row.get("Tanimoto_Score", 0))
            except (TypeError, ValueError):
                tanimoto = 0.0
            if tanimoto <= 0:
                continue
            old = per_compound.get(name)
            if old is None or tanimoto > old[0]:
                per_compound[name] = (tanimoto, row)
        for name, (tanimoto, row) in per_compound.items():
            mapped.append({
                "compound_id": name, "query_smiles": row.get("SMILES", ""),
                "target_chembl_id": target_id, "target_species": meta.get("Target_Species", ""),
                "target_name": meta.get("Target_Name", ""), "uniprot_id": meta.get("Uniprot_ID", ""),
                "uniprot_accession": meta.get("Uniprot_Accession", ""), "sea_z_score": meta.get("Z_score", ""),
                "sea_p_value": meta.get("p_value", ""), "sea_minus_log10_p": meta.get("p(P_value)", ""),
                "max_tc": meta.get("MaxTc", ""), "query_known_hit_tanimoto": tanimoto,
                "known_hit_id": row.get("Known_Hit_ID", ""), "known_hit_smiles": row.get("Known_Hit_SMILES", ""),
            })
    pd.DataFrame(mapped).to_csv(batch_dir / "compound_target_hits.tsv", sep="\t", index=False, encoding="utf-8-sig")
    manifest.update({"mapped_hit_rows": len(mapped), "sea_target_rows": len(target_rows)})
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
        futures = {pool.submit(process_batch, i + 1, b, OUT): i + 1 for i, b in enumerate(batches)}
        for future in as_completed(futures):
            batch_id = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {"batch_id": batch_id, "status": "ERROR", "error": repr(exc)}
                (OUT / f"batch_{batch_id:03d}" / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            results.append(result)
            print(json.dumps({k: result.get(k) for k in ["batch_id", "task_id", "status", "mapped_hit_rows", "error"]}, ensure_ascii=False), flush=True)
    summary = {"batches": len(batches), "compounds_with_smiles": len(records),
               "success": sum(r.get("status") == "SUCCESS" for r in results),
               "error": sum(r.get("status") != "SUCCESS" for r in results),
               "mapped_hit_rows": sum(int(r.get("mapped_hit_rows", 0)) for r in results)}
    (OUT / "SEA批量摘要.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
