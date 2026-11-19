"""Submit two HDOCK jobs (PDB-ID mode), same pattern as ACACA–DLD test."""
from __future__ import annotations

import json
import re
from pathlib import Path

import requests

URL = "http://hdock.phys.hust.edu.cn/runhdock.php"
EMAIL = "1054034696@qq.com"
ROOT = Path(__file__).resolve().parent

JOBS = [
    {
        "key": "ACOX1_DLD",
        "out": ROOT / "PPDock_ACOX1_DLD" / "02_submit",
        "pdbid1": "7Q84:AB",
        "pdbid2": "6I4Q:AB",
        "jobname": "ACOX1_DLD",
    },
    {
        "key": "DLD_SCD",
        "out": ROOT / "PPDock_DLD_SCD" / "02_submit",
        "pdbid1": "6I4Q:AB",
        "pdbid2": "4ZYO:A",
        "jobname": "DLD_SCD",
    },
]


def empty_files():
    return {
        "pdbfile1": ("", b""),
        "fastafile1": ("", b""),
        "pdbfile2": ("", b""),
        "fastafile2": ("", b""),
        "saxsfile": ("", b""),
        "sitefile1": ("", b""),
        "sitefile2": ("", b""),
        "restrfile": ("", b""),
    }


def submit_one(job: dict) -> dict:
    out: Path = job["out"]
    out.mkdir(parents=True, exist_ok=True)
    data = {
        "pdbid1": job["pdbid1"],
        "fastaseq1": "",
        "pdbid2": job["pdbid2"],
        "ligtyp": "Protein",
        "fastaseq2": "",
        "pdbsite": "no",
        "symmetry": "",
        "sitenum1": "",
        "sitenum2": "",
        "restrnum": "",
        "email": EMAIL,
        "jobname": job["jobname"],
        "upload": "Submit",
    }
    r = requests.post(URL, data=data, files=empty_files(), timeout=180)
    html_path = out / "hdock_submit_response.html"
    html_path.write_text(r.text, encoding="utf-8", errors="replace")
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.text))
    data_paths = re.findall(r"/data/([A-Za-z0-9_\-]+)/?", r.text)
    links = re.findall(r"https?://hdock[^\"'\s<>]+", r.text, re.I)
    summary = {
        "key": job["key"],
        "status_code": r.status_code,
        "url": r.url,
        "jobname": job["jobname"],
        "pdbid1": job["pdbid1"],
        "pdbid2": job["pdbid2"],
        "data_ids": data_paths,
        "links": links[:10],
        "text_snip": text[:800],
        "html": str(html_path),
    }
    (out / "hdock_submit_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary


def main() -> None:
    results = []
    for job in JOBS:
        print("=== submitting", job["key"], job["pdbid1"], "x", job["pdbid2"], "===")
        s = submit_one(job)
        results.append(s)
        print("status", s["status_code"], "data_ids", s["data_ids"], "links", s["links"][:3])
        print(s["text_snip"][:400])
        print()
    (ROOT / "hdock_submit_batch.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
