# -*- coding: utf-8 -*-
"""Inspect ZDOCK upload response and complete job submission if needed."""
from __future__ import annotations

import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OUT = Path(__file__).resolve().parent
EMAIL = "1054034696@stu.cqut.edu.cn"
HTML = OUT / "zdock_submit_edu_CA_CA_retry.html"


def main() -> None:
    html = HTML.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    print("title:", soup.title.string if soup.title else None)
    for i, form in enumerate(soup.find_all("form")):
        print(f"FORM {i} name={form.get('name')} action={form.get('action')} method={form.get('method')}")
        for el in form.find_all(["input", "select", "textarea"]):
            name = el.get("name")
            if not name:
                continue
            typ = el.get("type", el.name)
            val = el.get("value", "")
            if el.name == "select":
                opts = [o.get("value") for o in el.find_all("option")]
                print(f"  select {name} opts={opts[:6]} selected={el.get('value')}")
            else:
                print(f"  {typ} {name}={val[:120]!r}")

    # Visible success text
    text = " ".join(soup.get_text(" ").split())
    print("TEXT:", text[:600])

    # If this is residue page after skip, look for submit to queue
    # Re-submit session using requests.Session for proper flow
    s = requests.Session()
    rec = OUT / "ACACA_6G2D_chainC_CA.pdb"
    lig = OUT / "DLD_6I4Q_chainA_CA.pdb"
    files = {
        "inputfile1": (rec.name, open(rec, "rb"), "chemical/x-pdb"),
        "inputfile2": (lig.name, open(lig, "rb"), "chemical/x-pdb"),
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
    out1 = OUT / "zdock_session_step1.html"
    out1.write_text(r1.text, encoding="utf-8", errors="replace")
    soup1 = BeautifulSoup(r1.text, "html.parser")
    print("STEP1 status", r1.status_code, "url", r1.url)
    print("STEP1 text:", " ".join(soup1.get_text(" ").split())[:500])

    # Try to find and post the confirmation / residue form
    forms = soup1.find_all("form")
    for i, form in enumerate(forms):
        action = form.get("action") or r1.url
        if action.startswith("/"):
            action = "https://zdock.wenglab.org" + action
        elif not action.startswith("http"):
            action = "https://zdock.wenglab.org/" + action.lstrip("./")
        payload = {}
        for el in form.find_all("input"):
            name = el.get("name")
            if not name:
                continue
            typ = (el.get("type") or "text").lower()
            if typ in {"submit", "button", "image"}:
                continue
            payload[name] = el.get("value") or ""
        for el in form.find_all("select"):
            name = el.get("name")
            if not name:
                continue
            selected = el.find("option", selected=True) or el.find("option")
            payload[name] = selected.get("value") if selected else ""
        # ensure email/version
        if "useremail" in payload and not payload["useremail"]:
            payload["useremail"] = EMAIL
        # Prefer submit-like buttons
        submit_name = None
        submit_val = None
        for el in form.find_all("input"):
            typ = (el.get("type") or "").lower()
            if typ == "submit":
                submit_name = el.get("name")
                submit_val = el.get("value")
                break
        if submit_name:
            payload[submit_name] = submit_val or "Submit"
        print(f"POST form {i} action={action} keys={list(payload.keys())[:20]}")
        if not payload:
            continue
        # Only post forms that look like residue / confirm / job start
        joined = " ".join(payload.keys()).lower()
        if any(k in joined for k in ["submit", "email", "zd", "file", "block", "contact", "select"]):
            r2 = s.post(action, data=payload, timeout=180)
            out2 = OUT / f"zdock_session_step2_form{i}.html"
            out2.write_text(r2.text, encoding="utf-8", errors="replace")
            soup2 = BeautifulSoup(r2.text, "html.parser")
            print("STEP2", i, r2.status_code, r2.url)
            print(" ".join(soup2.get_text(" ").split())[:700])


if __name__ == "__main__":
    main()
