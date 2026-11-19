# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import requests

OUT = Path(__file__).resolve().parent
EMAIL = "1054034696@qq.com"


def to_ca_only(src: Path, dst: Path) -> dict:
    lines = src.read_text(encoding="ascii", errors="ignore").splitlines()
    out = [L for L in lines if L.startswith(("HEADER", "TITLE", "EXPDTA", "REMARK   1"))]
    out.append("REMARK   1 CA-ONLY MODEL FOR WEB-SERVER SIZE LIMIT")
    n = 0
    for L in lines:
        if L.startswith("ATOM") and L[12:16].strip() == "CA":
            out.append(L.rstrip())
            n += 1
    out.append("END")
    dst.write_text("\n".join(out) + "\n", encoding="ascii")
    return {"file": dst.name, "CA": n, "KB": dst.stat().st_size / 1024}


def submit_zdock(rec: Path, lig: Path, tag: str) -> Path:
    files = {
        "inputfile1": (rec.name, rec.open("rb"), "chemical/x-pdb"),
        "inputfile2": (lig.name, lig.open("rb"), "chemical/x-pdb"),
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
    r = requests.post("https://zdock.wenglab.org/", data=data, files=files, timeout=180)
    html = OUT / f"zdock_submit_{tag}.html"
    html.write_text(r.text, encoding="utf-8", errors="replace")
    text = " ".join(re.sub(r"<[^>]+>", " ", r.text).split())
    print(f"[ZDOCK {tag}] status={r.status_code}")
    print(text[:900])
    return html


def main() -> None:
    full_acaca = OUT / "ACACA_6G2D_chainC_clean.pdb"
    full_dld = OUT / "DLD_6I4Q_chainA_clean.pdb"
    ca_acaca = OUT / "ACACA_6G2D_chainC_CA.pdb"
    ca_dld = OUT / "DLD_6I4Q_chainA_CA.pdb"
    print(to_ca_only(full_acaca, ca_acaca))
    print(to_ca_only(full_dld, ca_dld))
    # Prefer CA receptor + full-atom ligand if ligand under limit; else CA+CA
    if full_dld.stat().st_size < 1.2 * 1024 * 1024:
        submit_zdock(ca_acaca, full_dld, "CArec_fulllig")
    submit_zdock(ca_acaca, ca_dld, "CA_CA")


if __name__ == "__main__":
    main()
