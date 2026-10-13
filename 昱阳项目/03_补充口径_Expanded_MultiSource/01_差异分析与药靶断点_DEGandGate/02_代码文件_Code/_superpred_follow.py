"""Follow SuperPred homepage links to find target prediction form and submit."""
from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urljoin

PRED = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_预测靶点_MultiPredict"
)
EMAIL = "1054034696@qq.com"
SMILES = "C1=CC(=C(C=C1C2=C(C(=O)C3=C(C=C(C=C3O2)O)O)O)O)O"
BASE = "https://prediction.charite.de/"


def curl(*args: str, timeout: int = 180) -> str:
    p = subprocess.run(
        ["curl.exe", "-sS", "-k", "-m", str(timeout), "-A", "Mozilla/5.0", "-L", *args],
        capture_output=True,
    )
    return p.stdout.decode(errors="ignore")


def main() -> None:
    home = PRED / "_superpred_home.html"
    curl("-o", str(home), BASE)
    t = home.read_text(encoding="utf-8", errors="ignore")
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', t, flags=re.I)
    print("hrefs", hrefs[:40])
    cand = [
        h
        for h in hrefs
        if re.search(r"target|predict|ligand| fore", h, re.I)
        or "site=" in h
        or "subpage" in h
    ]
    print("cand", cand)
    pages = []
    for h in sorted(set(cand + hrefs))[:40]:
        if h.startswith("#") or h.startswith("javascript"):
            continue
        url = urljoin(BASE, h)
        if "charite.de" not in url and not h.startswith("/"):
            continue
        if not any(x in url for x in ["charite.de", "prediction"]):
            if h.startswith("/"):
                url = urljoin(BASE, h)
            else:
                continue
        out = PRED / f"_sp_page_{abs(hash(url)) % 10**8}.html"
        curl("-o", str(out), url)
        if not out.exists() or out.stat().st_size < 400:
            continue
        html = out.read_text(encoding="utf-8", errors="ignore")
        names = re.findall(r'name=["\']([^"\']+)["\']', html, flags=re.I)
        actions = re.findall(r'action=["\']([^"\']+)["\']', html, flags=re.I)
        if any(re.search(r"smile", n, re.I) for n in names) or "smiles" in html.lower():
            pages.append({"url": url, "names": names, "actions": actions, "size": out.stat().st_size})
            print("FORM", url, names[:20], actions[:10])

    if not pages:
        # dump title snippets
        for h in hrefs[:25]:
            print("link", h)
        (PRED / "_superpred_follow.json").write_text(
            json.dumps({"hrefs": hrefs, "pages": pages}, indent=2), encoding="utf-8"
        )
        print("no form found")
        return

    page = pages[0]
    action = page["actions"][0] if page["actions"] else page["url"]
    post_url = urljoin(page["url"], action)
    field = next((n for n in page["names"] if re.search(r"smile", n, re.I)), "smiles")
    out = PRED / "_superpred_result.html"
    curl(
        "-F",
        f"{field}={SMILES}",
        "-F",
        f"email={EMAIL}",
        "-o",
        str(out),
        post_url,
    )
    print("posted", post_url, "size", out.stat().st_size if out.exists() else 0)
    if out.exists() and out.stat().st_size > 1000:
        html = out.read_text(encoding="utf-8", errors="ignore")
        genes = re.findall(
            r"<t[dh][^>]*>\s*([A-Z][A-Z0-9]{1,14})\s*</t[dh]>", html
        )
        genes = sorted(
            {
                g
                for g in genes
                if g
                not in {
                    "HTML",
                    "HTTP",
                    "JSON",
                    "NONE",
                    "TARGET",
                    "GENE",
                    "NAME",
                    "PDB",
                    "ID",
                }
            }
        )
        print("genes cand", len(genes), genes[:20])
        if len(genes) >= 5:
            csv_path = PRED / "06_SuperPred_Quercetin_genes.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["gene_human", "source", "evidence"])
                w.writeheader()
                for g in genes:
                    w.writerow(
                        {"gene_human": g, "source": "SuperPred", "evidence": "predicted"}
                    )
            print("wrote", csv_path)

    (PRED / "_superpred_follow.json").write_text(
        json.dumps({"pages": pages, "posted": post_url}, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
