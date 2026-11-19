# -*- coding: utf-8 -*-
"""Submit cleaned ACACA vs DLD to ZDOCK web server."""
from __future__ import annotations

from pathlib import Path

import requests

OUT = Path(__file__).resolve().parent
URL = "https://zdock.wenglab.org/"
EMAIL = "1054034696@qq.com"
REC = OUT / "ACACA_6G2D_chainC_clean.pdb"
LIG = OUT / "DLD_6I4Q_chainA_clean.pdb"


def main() -> None:
    assert REC.is_file() and LIG.is_file()
    print("receptor", REC.name, REC.stat().st_size)
    print("ligand  ", LIG.name, LIG.stat().st_size)
    files = {
        "inputfile1": (REC.name, REC.open("rb"), "chemical/x-pdb"),
        "inputfile2": (LIG.name, LIG.open("rb"), "chemical/x-pdb"),
    }
    data = {
        "pdb1select": "file",
        "pdb2select": "file",
        "pdbid1": "",
        "pdbid2": "",
        "useremail": EMAIL,
        "zdversion": "ZD3.0.2",
        "skipselect": "Skip",
        "upload": "Submit",
    }
    r = requests.post(URL, data=data, files=files, timeout=180, allow_redirects=True)
    print("status", r.status_code, "url", r.url)
    print("len", len(r.text))
    out_html = OUT / "zdock_submit_response.html"
    out_html.write_text(r.text, encoding="utf-8", errors="replace")
    # extract useful bits
    low = r.text.lower()
    for key in ["error", "job", "queue", "thank", "success", "too large", "residue", "atom", "limit"]:
        if key in low:
            print("contains:", key)
    # print title-ish
    import re

    m = re.search(r"<title>(.*?)</title>", r.text, re.I | re.S)
    if m:
        print("title:", " ".join(m.group(1).split()))
    # save snippet around body
    print("--- body snippet ---")
    body = re.sub(r"<script[\s\S]*?</script>", "", r.text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", body)
    text = " ".join(text.split())
    print(text[:1200])


if __name__ == "__main__":
    main()
