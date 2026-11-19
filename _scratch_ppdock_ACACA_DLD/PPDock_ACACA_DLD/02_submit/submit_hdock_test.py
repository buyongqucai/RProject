"""Submit HDOCK: receptor 6G2D:C, ligand 6I4Q:AB, email qq, jobname test."""
from __future__ import annotations

import re
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parent
URL = "http://hdock.phys.hust.edu.cn/runhdock.php"

files = {
    "pdbfile1": ("", b""),
    "fastafile1": ("", b""),
    "pdbfile2": ("", b""),
    "fastafile2": ("", b""),
    "saxsfile": ("", b""),
    "sitefile1": ("", b""),
    "sitefile2": ("", b""),
    "restrfile": ("", b""),
}
data = {
    "pdbid1": "6G2D:C",
    "fastaseq1": "",
    "pdbid2": "6I4Q:AB",
    "ligtyp": "Protein",
    "fastaseq2": "",
    "pdbsite": "no",
    "symmetry": "",
    "sitenum1": "",
    "sitenum2": "",
    "restrnum": "",
    "email": "1054034696@qq.com",
    "jobname": "test",
    "upload": "Submit",
}


def main() -> None:
    r = requests.post(URL, data=data, files=files, timeout=180)
    html_path = OUT / "hdock_submit_response.html"
    html_path.write_text(r.text, encoding="utf-8", errors="replace")
    print("status", r.status_code, "len", len(r.text), "url", r.url)
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.text))
    print(text[:1500])
    links = re.findall(r"https?://hdock[^\"'\s<>]+", r.text, re.I)
    print("links", links[:10])
    job = re.findall(r"jobid[=\"'/: ]+([A-Za-z0-9_\-]+)", r.text, re.I)
    print("jobid-like", job[:10])
    # common HDOCK result path /data/xxx/
    data_paths = re.findall(r"/data/[A-Za-z0-9_\-]+/?", r.text)
    print("data_paths", data_paths[:10])


if __name__ == "__main__":
    main()
