# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parent
EMAIL = "1054034696@stu.cqut.edu.cn"


def html_to_text(html: str) -> str:
    noscript = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    return " ".join(re.sub(r"<[^>]+>", " ", noscript).split())


def parse_file(path: Path) -> None:
    t = path.read_text(encoding="utf-8", errors="replace")
    text = html_to_text(t)
    print("====", path.name, "len", len(t))
    for m in re.finditer(
        r".{0,100}(not allowed|academic|error|thank|submitted|queue|email|Select residues|Job|blocked).{0,160}",
        text,
        re.I,
    ):
        print(">", m.group(0)[:280])
    if "getSelection" in t or "residue" in text.lower():
        print("HAS residue-selection markers")
    emails = re.findall(r'useremail[^>]*value="([^"]*)"', t, flags=re.I)
    print("email fields", emails[:5])


def submit(rec: Path, lig: Path, tag: str) -> Path:
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
    html = OUT / f"zdock_submit_edu_{tag}.html"
    html.write_text(r.text, encoding="utf-8", errors="replace")
    print(f"[submit {tag}] status={r.status_code}")
    print(html_to_text(r.text)[:900])
    return html


def main() -> None:
    for f in sorted(OUT.glob("zdock_submit_edu_*.html")):
        parse_file(f)
    # if previous looked like front page, try CA+CA again and dump more carefully
    rec = OUT / "ACACA_6G2D_chainC_CA.pdb"
    lig = OUT / "DLD_6I4Q_chainA_CA.pdb"
    html = submit(rec, lig, "CA_CA_retry")
    parse_file(html)


if __name__ == "__main__":
    main()
