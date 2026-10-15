"""Submit quercetin SMILES to TargetNet /calcnet/calc_text/ and save genes."""
from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path

PRED = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_STP_STITCH_PharmMapper_TargetNet_BATMAN_预测靶点"
)
SMILES = "C1=CC(=C(C=C1C2=C(C(=O)C3=C(C=C(C=C3O2)O)O)O)O)O"
OUT = PRED / "_targetnet_result.html"


def main() -> None:
    cmd = [
        "curl.exe",
        "-sS",
        "-m",
        "300",
        "-A",
        "Mozilla/5.0",
        "-L",
        "-F",
        f"smile={SMILES}",
        "-F",
        "param_1=AUC_score",
        "-F",
        "finger_type=BaseInfo_ecfp4",
        "-F",
        "param_2=0.7",
        "-o",
        str(OUT),
        "-w",
        "%{http_code}|%{url_effective}|%{size_download}",
        "http://targetnet.scbdd.com/calcnet/calc_text/",
    ]
    p = subprocess.run(cmd, capture_output=True)
    print("curl", p.stdout.decode(errors="ignore"), p.stderr.decode(errors="ignore")[:300])
    print("size", OUT.stat().st_size if OUT.exists() else 0)

    t = OUT.read_text(encoding="utf-8", errors="ignore") if OUT.exists() else ""
    print("title", re.search(r"<title[^>]*>(.*?)</title>", t, re.I | re.S))
    print("has table", t.count("<tr"), "uniprot", t.lower().count("uniprot"), "gene", t.lower().count("gene"))
    # dump a snippet around first table
    i = t.lower().find("<table")
    if i >= 0:
        print(t[i : i + 800])

    genes = []
    # TargetNet result tables often: Target / Gene name / UniProt / Prob
    for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", t, re.I | re.S):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", m.group(1), re.I | re.S)
        clean = [re.sub(r"<[^>]+>", " ", c) for c in cells]
        clean = [re.sub(r"\s+", " ", c).strip() for c in clean]
        if not clean:
            continue
        for c in clean:
            if re.fullmatch(r"[A-Z][A-Z0-9]{1,14}", c) and c not in {
                "HTML",
                "HTTP",
                "JSON",
                "NONE",
                "TARGET",
                "GENE",
                "NAME",
                "PROB",
            }:
                genes.append(c)
        # UniProt accession → keep note; gene often adjacent
        for c in clean:
            if re.fullmatch(
                r"[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2}",
                c,
            ):
                pass

    # also Gene Name column patterns
    genes += re.findall(
        r"(?:Gene\s*name|Gene)\s*</t[dh]>\s*<t[dh][^>]*>\s*([A-Z][A-Z0-9-]{1,14})",
        t,
        re.I,
    )

    genes = sorted(set(genes))
    print("candidate genes", len(genes), genes[:30])
    csv_path = PRED / "05_TargetNet_Quercetin_genes.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["gene_human", "source", "evidence"])
        w.writeheader()
        for g in genes:
            w.writerow({"gene_human": g, "source": "TargetNet", "evidence": "predicted"})
    print("wrote", csv_path, "n", len(genes))


if __name__ == "__main__":
    main()
