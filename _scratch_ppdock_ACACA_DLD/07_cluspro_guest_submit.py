# -*- coding: utf-8 -*-
"""Submit ACACA/DLD to ClusPro as guest (or with PHPSESSID if provided)."""
from __future__ import annotations

from pathlib import Path

import requests

OUT = Path(__file__).resolve().parent
BASE = "https://cluspro.bu.edu"
REC = OUT / "ACACA_6G2D_chainC_CA.pdb"
LIG = OUT / "DLD_6I4Q_chainA_CA.pdb"
# Full-atom DLD is fine size-wise for ClusPro; ACACA full is large — use CA receptor.
# Prefer full DLD ligand for better docking if server accepts.
LIG_FULL = OUT / "DLD_6I4Q_chainA_clean.pdb"


def main() -> None:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
    )
    # Establish guest session: follow the "use without account" link if present
    r0 = s.get(f"{BASE}/login.php", timeout=60)
    print("login", r0.status_code, r0.url, "cookies", s.cookies.get_dict())
    # common guest endpoints
    for path in ["/nologin.php", "/login.php?guest=1", "/guest.php", "/home.php"]:
        try:
            r = s.get(f"{BASE}{path}", timeout=60, allow_redirects=True)
            print("GET", path, r.status_code, r.url, "sign out" in r.text.lower(), "jobname" in r.text)
            if "jobname" in r.text and "name=\"rec\"" in r.text:
                break
        except Exception as e:
            print("GET fail", path, e)

    lig = LIG_FULL if LIG_FULL.stat().st_size < 8_000_000 else LIG
    print("using", REC.name, REC.stat().st_size, lig.name, lig.stat().st_size)

    files = {
        "rec": (REC.name, REC.open("rb"), "chemical/x-pdb"),
        "lig": (lig.name, lig.open("rb"), "chemical/x-pdb"),
    }
    data = {
        "advanced": "0",
        "useattrep": "0",
        "usedssp": "0",
        "usedimer": "0",
        "useperrot": "0",
        "useantibody": "0",
        "useothers": "0",
        "useheparin": "0",
        "usebindingsite": "0",
        "usesaxs": "0",
        "userrot": "0",
        "usepatches": "0",
        "usecoeff": "0",
        "userots": "0",
        "userestraints": "0",
        "userecpdbid": "0",
        "useligpdbid": "0",
        "userecrepfile": "0",
        "useligrepfile": "0",
        "jobname": "ACACA_DLD_CA_guest",
        "recpdb": "",
        "recchains": "",
        "ligpdb": "",
        "ligchains": "",
        "multimers": "",
        "noncommercial": "on",
        "action": "Dock",
        # server select may be named differently
        "server": "scc2",
    }
    r = s.post(f"{BASE}/home.php", data=data, files=files, timeout=300, allow_redirects=True)
    out = OUT / "cluspro_guest_submit.html"
    out.write_text(r.text, encoding="utf-8", errors="replace")
    print("POST", r.status_code, r.url, "len", len(r.text))
    text = " ".join(r.text.split())
    print(text[:1000])
    # also try queue page
    rq = s.get(f"{BASE}/queue.php", timeout=60)
    (OUT / "cluspro_queue.html").write_text(rq.text, encoding="utf-8", errors="replace")
    print("queue", rq.status_code, rq.url, "len", len(rq.text))
    print(" ".join(rq.text.split())[:600])


if __name__ == "__main__":
    main()
