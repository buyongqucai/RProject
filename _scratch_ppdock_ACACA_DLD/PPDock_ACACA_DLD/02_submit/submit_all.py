# -*- coding: utf-8 -*-
"""Submit ST/PT to ZDOCK; probe HDOCK; ClusPro handled via browser session separately."""
from __future__ import annotations

import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "01_clean"
SUB = ROOT / "02_submit"
EMAIL = "1054034696@stu.cqut.edu.cn"
ST_CA = CLEAN / "ST_ACACA_6G2D_chainC_CA.pdb"
PT_CA = CLEAN / "PT_DLD_6I4Q_AB_CA.pdb"
ST_FULL = CLEAN / "ST_ACACA_6G2D_chainC_clean.pdb"
PT_FULL = CLEAN / "PT_DLD_6I4Q_AB_clean.pdb"


def submit_zdock() -> str:
    s = requests.Session()
    files = {
        "inputfile1": (ST_CA.name, ST_CA.open("rb"), "chemical/x-pdb"),
        "inputfile2": (PT_CA.name, PT_CA.open("rb"), "chemical/x-pdb"),
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
    r1 = s.post("https://zdock.wenglab.org/", data=data, files=files, timeout=180)
    (SUB / "zdock_step1.html").write_text(r1.text, encoding="utf-8", errors="replace")
    soup = BeautifulSoup(r1.text, "html.parser")
    form = soup.find("form")
    if not form:
        return "FAIL no form: " + " ".join(soup.get_text(" ").split())[:400]
    payload = {}
    for el in form.find_all("input"):
        name = el.get("name")
        if not name:
            continue
        if (el.get("type") or "").lower() in {"submit", "button", "image"}:
            continue
        payload[name] = el.get("value") or ""
    if not payload.get("email"):
        payload["email"] = EMAIL
    action = form.get("action") or "db_insert.php"
    if action.startswith("/"):
        action = "https://zdock.wenglab.org" + action
    elif not action.startswith("http"):
        action = "https://zdock.wenglab.org/" + action.lstrip("./")
    r2 = s.post(action, data=payload, timeout=180)
    (SUB / "zdock_step2.html").write_text(r2.text, encoding="utf-8", errors="replace")
    text = " ".join(BeautifulSoup(r2.text, "html.parser").get_text(" ").split())
    return text[:800]


def probe_hdock() -> str:
    urls = [
        "http://hdock.phys.hust.edu.cn/",
        "https://hdock.phys.hust.edu.cn/",
    ]
    notes = []
    for u in urls:
        try:
            r = requests.get(u, timeout=30)
            notes.append(f"{u} -> {r.status_code} len={len(r.text)}")
            (SUB / "hdock_home.html").write_text(r.text, encoding="utf-8", errors="replace")
            if r.ok:
                return "OK " + notes[-1]
        except Exception as e:
            notes.append(f"{u} -> {type(e).__name__}: {e}")
    return "FAIL " + " | ".join(notes)


def main() -> None:
    print("sizes MB", ST_CA.stat().st_size / 1e6, PT_CA.stat().st_size / 1e6, ST_FULL.stat().st_size / 1e6, PT_FULL.stat().st_size / 1e6)
    print("=== ZDOCK ===")
    print(submit_zdock())
    print("=== HDOCK probe ===")
    print(probe_hdock())


if __name__ == "__main__":
    main()
