"""Poll HDOCK until finished, then download artifacts for both jobs."""
from __future__ import annotations

import re
import time
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parent
JOBS = {
    "ACOX1_DLD": "6aed98eb1bfd8",
    "DLD_SCD": "6aed98ee37a8c",
}
INTERVAL = 45
MAX_WAIT = 6 * 60 * 60


def fetch_html(jid: str) -> str:
    url = f"http://hdock.phys.hust.edu.cn/data/{jid}/"
    return urllib.request.urlopen(url, timeout=90).read().decode("latin-1", "replace")


def status_of(html: str) -> str:
    low = html.lower()
    if "is queued" in low:
        return "QUEUED"
    if "is running" in low or "being processed" in low:
        return "RUNNING"
    if any(x in low for x in ["top 10", "all_results", "model_1.pdb", "docking is finished", "your hdock results"]):
        # finished pages usually have model downloads and no meta refresh wait table
        if "is queued" in low or "is running" in low:
            return "RUNNING"
        return "DONE"
    if 'meta http-equiv="refresh"' in low and ("queued" in low or "running" in low):
        return "WAIT"
    return "UNKNOWN"


def download_job(name: str, jid: str, html: str) -> list[str]:
    base = f"http://hdock.phys.hust.edu.cn/data/{jid}/"
    out = ROOT / f"PPDock_{name}" / "00_服务器原始包_ServerRaw" / f"hdock_{jid}"
    out.mkdir(parents=True, exist_ok=True)
    (ROOT / f"PPDock_{name}" / "02_submit" / "hdock_results_page.html").write_text(
        html, encoding="utf-8", errors="replace"
    )
    files = re.findall(r"([\w.\-]+\.(?:pdb|out|tar\.gz|tgz|zip|txt|dat))", html, re.I)
    links = re.findall(r'href=["\']([^"\']+)["\']', html, re.I)
    candidates: list[str] = []
    for n in sorted(set(files)):
        candidates.append(urljoin(base, n))
    for href in links:
        if any(x in href.lower() for x in [".pdb", ".out", ".gz", ".zip", ".txt", ".dat", "model", "top"]):
            candidates.append(urljoin(base, href))
    # common HDOCK names even if not linked clearly
    for n in [
        "all_results.tar.gz",
        "Hdock.out",
        "model_1.pdb",
        "model_2.pdb",
        "model_3.pdb",
        "model_4.pdb",
        "model_5.pdb",
        "top1.pdb",
        "receptor.pdb",
        "ligand.pdb",
    ]:
        candidates.append(urljoin(base, n))
    seen = set()
    downloaded: list[str] = []
    for u in candidates:
        if u in seen:
            continue
        seen.add(u)
        fname = u.rstrip("/").split("/")[-1]
        if "." not in fname:
            continue
        if not any(fname.lower().endswith(ext) for ext in (".pdb", ".out", ".gz", ".tgz", ".zip", ".txt", ".dat")):
            continue
        dest = out / fname
        try:
            data = urllib.request.urlopen(u, timeout=180).read()
            if len(data) < 200 and b"404" in data[:200].lower():
                continue
            dest.write_bytes(data)
            print(f"  GET {fname} ({len(data)})")
            downloaded.append(fname)
        except Exception as e:
            print(f"  skip {fname}: {e}")
    return downloaded


def main() -> None:
    t0 = time.time()
    done = {k: False for k in JOBS}
    while time.time() - t0 < MAX_WAIT:
        all_done = True
        for name, jid in JOBS.items():
            if done[name]:
                continue
            all_done = False
            try:
                html = fetch_html(jid)
            except Exception as e:
                print(name, "fetch error", e)
                continue
            st = status_of(html)
            print(f"[{int(time.time()-t0)}s] {name} {jid} -> {st}")
            if st == "DONE" or (
                "model_1.pdb" in html
                or "all_results" in html.lower()
                or ("Hdock.out" in html and "queued" not in html.lower() and "running" not in html.lower())
            ):
                print(f"Downloading {name}...")
                files = download_job(name, jid, html)
                print(f"  downloaded {len(files)} files")
                done[name] = True
                (ROOT / f"PPDock_{name}" / "02_submit" / "FETCH_DONE.txt").write_text(
                    "\n".join(files), encoding="utf-8"
                )
        if all(done.values()):
            print("ALL DONE")
            return
        time.sleep(INTERVAL)
    print("TIMEOUT; done flags", done)


if __name__ == "__main__":
    main()
