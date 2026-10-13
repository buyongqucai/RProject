"""Submit quercetin to SuperPred target_prediction.php."""
from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path

PRED = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_预测靶点_MultiPredict"
)
EMAIL = "1054034696@qq.com"
SMILES = "C1=CC(=C(C=C1C2=C(C(=O)C3=C(C=C(C=C3O2)O)O)O)O)O"
URL = "https://prediction.charite.de/subpages/target_prediction.php"


def curl(args: list[str], timeout: int = 180) -> str:
    p = subprocess.run(
        ["curl.exe", "-sS", "-k", "-m", str(timeout), "-A", "Mozilla/5.0", "-L", *args],
        capture_output=True,
    )
    return p.stdout.decode(errors="ignore")


def main() -> None:
    page = PRED / "_sp_tp.html"
    info = curl(["-o", str(page), "-w", "%{http_code}|%{size_download}", URL])
    print("GET", info, "size", page.stat().st_size if page.exists() else 0)
    t = page.read_text(encoding="utf-8", errors="ignore") if page.exists() else ""
    print("title", re.search(r"<title[^>]*>(.*?)</title>", t, re.I | re.S))
    names = re.findall(r'name=["\']([^"\']+)["\']', t, flags=re.I)
    actions = re.findall(r'action=["\']([^"\']+)["\']', t, flags=re.I)
    inputs = re.findall(r"<(?:input|textarea|select)[^>]*>", t, flags=re.I)
    print("names", names)
    print("actions", actions)
    print("inputs", len(inputs))
    # show smile neighborhood
    i = t.lower().find("smile")
    if i >= 0:
        print("snippet", t[max(0, i - 100) : i + 200])
    else:
        print("no smile token; head", t[:1500])

    # try common posts
    out = PRED / "_superpred_result.html"
    for fields in [
        ["-F", f"smiles={SMILES}", "-F", f"email={EMAIL}"],
        ["-F", f"smile={SMILES}"],
        ["-F", f"SmilesString={SMILES}", "-F", "submit=Predict"],
        ["-F", f"molecule={SMILES}"],
        ["--data-urlencode", f"smiles={SMILES}"],
    ]:
        info = curl([*fields, "-o", str(out), "-w", "%{http_code}|%{size_download}", URL])
        print("POST", fields[1][:40], info, out.stat().st_size if out.exists() else 0)
        if out.exists() and out.stat().st_size > 2000:
            html = out.read_text(encoding="utf-8", errors="ignore")
            if "target" in html.lower() and html.count("<tr") > 3:
                genes = []
                for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", html, re.I | re.S):
                    cells = [
                        re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip()
                        for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", m.group(1), re.I | re.S)
                    ]
                    for c in cells:
                        if re.fullmatch(r"[A-Z][A-Z0-9]{1,14}", c) and c not in {
                            "HTML",
                            "HTTP",
                            "TARGET",
                            "GENE",
                            "NAME",
                            "PDB",
                            "ID",
                            "ATC",
                        }:
                            genes.append(c)
                genes = sorted(set(genes))
                print("genes", len(genes), genes[:25])
                if len(genes) >= 5:
                    csv_path = PRED / "06_SuperPred_Quercetin_genes.csv"
                    with csv_path.open("w", newline="", encoding="utf-8") as f:
                        w = csv.DictWriter(
                            f, fieldnames=["gene_human", "source", "evidence"]
                        )
                        w.writeheader()
                        for g in genes:
                            w.writerow(
                                {
                                    "gene_human": g,
                                    "source": "SuperPred",
                                    "evidence": "predicted",
                                }
                            )
                    print("wrote", csv_path)
                    return
    print("SuperPred: no parseable result")


if __name__ == "__main__":
    main()
