"""Fetch HDOCK result page and download pose/model files."""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

JOB = "http://hdock.phys.hust.edu.cn/data/6ae693419a01b/"
ROOT = Path(r"E:\RProject\_scratch_ppdock_ACACA_DLD\PPDock_ACACA_DLD")
OUT = ROOT / "03_poses" / "hdock_6ae693419a01b"
SUBMIT = ROOT / "02_submit"


def main() -> None:
    html = urllib.request.urlopen(JOB, timeout=90).read().decode("latin-1", "replace")
    (SUBMIT / "hdock_results_page.html").write_text(html, encoding="utf-8", errors="replace")
    print("len", len(html))
    print("RUNNING", "RUNNING" in html)
    print("finished markers", any(x in html.lower() for x in ["finished", "completed", "top 10", "model"]))
    links = re.findall(r'href=["\']([^"\']+)["\']', html, re.I)
    interesting = [
        l
        for l in links
        if any(
            x in l.lower()
            for x in [".pdb", ".out", ".tar", ".gz", ".zip", "model", "top", "download", ".txt"]
        )
    ]
    print("interesting", interesting[:50])
    # also bare filenames in page
    files = re.findall(
        r"([\w.\-]+\.(?:pdb|out|tar\.gz|tgz|zip|txt|dat))",
        html,
        re.I,
    )
    print("filenames", sorted(set(files))[:80])
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
    print("text snippet:", text[:2000])

    OUT.mkdir(parents=True, exist_ok=True)
    # Prefer common HDOCK artifacts
    candidates = []
    for name in sorted(set(files)):
        candidates.append(urljoin(JOB, name))
    for href in interesting:
        candidates.append(urljoin(JOB, href))
    # dedupe
    seen = set()
    uniq = []
    for u in candidates:
        if u not in seen:
            seen.add(u)
            uniq.append(u)

    downloaded = []
    for u in uniq:
        name = u.rstrip("/").split("/")[-1]
        if not name or "." not in name:
            continue
        if not any(name.lower().endswith(ext) for ext in (".pdb", ".out", ".gz", ".tgz", ".zip", ".txt", ".dat")):
            continue
        dest = OUT / name
        try:
            print("GET", u)
            data = urllib.request.urlopen(u, timeout=120).read()
            dest.write_bytes(data)
            print("  ->", dest, len(data))
            downloaded.append(dest.name)
        except Exception as e:
            print("  FAIL", e)
    print("downloaded", downloaded)


if __name__ == "__main__":
    main()
