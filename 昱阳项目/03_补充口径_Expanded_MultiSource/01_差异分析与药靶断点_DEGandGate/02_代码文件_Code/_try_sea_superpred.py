"""Attempt SEA / SuperPred uploads; record status in JobMonitor."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

PRED = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_STP_STITCH_PharmMapper_TargetNet_BATMAN_预测靶点"
)
EMAIL = "1054034696@qq.com"
SMILES = "C1=CC(=C(C=C1C2=C(C(=O)C3=C(C=C(C=C3O2)O)O)O)O)O"
META = PRED / "00_预测站任务监听_JobMonitor.json"


def curl(*args: str, timeout: int = 120) -> tuple[int, str]:
    p = subprocess.run(
        ["curl.exe", "-sS", "-m", str(timeout), "-A", "Mozilla/5.0", *args],
        capture_output=True,
    )
    return p.returncode, p.stdout.decode(errors="ignore")


def main() -> None:
    meta = json.loads(META.read_text(encoding="utf-8")) if META.exists() else {}
    meta["email"] = EMAIL
    other = meta.get("other") or {}

    # SuperPred: try several known paths with -k
    sp = {"status": "unknown", "tries": []}
    for url in [
        "https://prediction.charite.de/",
        "https://prediction.charite.de/index.php",
        "https://prediction.charite.de/subpages/target_prediction.php",
        "https://prediction.charite.de/subpages/target_prediction.html",
        "http://prediction.charite.de/subpages/target_prediction.php",
    ]:
        out = PRED / f"_sp_{abs(hash(url)) % 10**8}.html"
        code, info = curl("-k", "-L", "-o", str(out), "-w", "%{http_code}|%{size_download}", url)
        size = out.stat().st_size if out.exists() else 0
        sp["tries"].append({"url": url, "curl": code, "info": info, "size": size})
        if size > 1000:
            t = out.read_text(encoding="utf-8", errors="ignore")
            actions = re.findall(r'action=["\']([^"\']+)["\']', t, flags=re.I)
            names = re.findall(r'name=["\']([^"\']+)["\']', t, flags=re.I)
            sp["actions"] = actions[:20]
            sp["names"] = names[:40]
            # try post if smiles-like field present
            for field in ["smiles", "smile", "SmilesString", "molecule", "query"]:
                if field in names or field.lower() in [n.lower() for n in names]:
                    pout = PRED / "_superpred_post.html"
                    curl(
                        "-k",
                        "-L",
                        "-F",
                        f"{field}={SMILES}",
                        "-F",
                        f"email={EMAIL}",
                        "-o",
                        str(pout),
                        url if url.endswith(".php") or "index" in url else actions[0]
                        if actions
                        else url,
                    )
                    sp["post_size"] = pout.stat().st_size if pout.exists() else 0
                    sp["status"] = "posted" if sp["post_size"] > 500 else "form_found_post_small"
                    break
            if sp["status"] == "unknown":
                sp["status"] = "page_ok_no_smiles_field"
            break
    if sp["status"] == "unknown":
        sp["status"] = "unreachable_or_404"

    # SEA
    sea = {"status": "unknown", "tries": []}
    for args in [
        ["-k", "-L", "-o", str(PRED / "_sea_home.html"), "-w", "%{http_code}|%{size_download}", "https://sea.bkslab.org/"],
        ["-k", "-L", "-o", str(PRED / "_sea_search.html"), "-w", "%{http_code}|%{size_download}", "https://sea.bkslab.org/search"],
        [
            "-k",
            "-L",
            "-X",
            "POST",
            "-H",
            "Content-Type: application/json",
            "-d",
            json.dumps({"query": SMILES}),
            "-o",
            str(PRED / "_sea_api.json"),
            "-w",
            "%{http_code}|%{size_download}",
            "https://sea.bkslab.org/api/search",
        ],
        [
            "-k",
            "-L",
            "-F",
            f"query={SMILES}",
            "-o",
            str(PRED / "_sea_post.html"),
            "-w",
            "%{http_code}|%{size_download}",
            "https://sea.bkslab.org/search/",
        ],
    ]:
        code, info = curl(*args)
        sea["tries"].append({"args0": args[-1], "curl": code, "info": info})
    # inspect largest
    for name in ["_sea_home.html", "_sea_search.html", "_sea_post.html", "_sea_api.json"]:
        p = PRED / name
        if p.exists() and p.stat().st_size > 1000:
            t = p.read_text(encoding="utf-8", errors="ignore")
            if "target" in t.lower() or "gene" in t.lower():
                sea["status"] = f"content_in_{name}"
                sea["size"] = p.stat().st_size
                break
    if sea["status"] == "unknown":
        sea["status"] = "blocked_or_spa_only"

    other["superpred"] = sp
    other["sea"] = sea
    other["targetnet"] = {
        "status": "ok",
        "csv": str(PRED / "05_TargetNet_Quercetin_genes.csv"),
        "filter": "Prob>0",
    }
    other["pharmmapper"] = {
        "status": "ok_extracted",
        "csv": str(PRED / "04_PharmMapper_Quercetin_genes.csv"),
        "jobs": ["261011075421", "261011082113"],
        "email": EMAIL,
    }
    meta["other"] = other
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"superpred": sp["status"], "sea": sea["status"]}, indent=2))
    print("tries_sp", sp["tries"][:5])
    print("tries_sea", sea["tries"][:5])


if __name__ == "__main__":
    main()
