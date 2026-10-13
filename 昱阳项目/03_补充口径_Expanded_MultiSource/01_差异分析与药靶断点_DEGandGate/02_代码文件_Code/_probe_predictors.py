"""Probe TargetNet / SuperPred / SEA forms and attempt submit+parse."""
from __future__ import annotations

import csv
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


def curl(*args: str, timeout: int = 180) -> tuple[int, bytes]:
    cmd = ["curl.exe", "-sS", "-m", str(timeout), "-A", "Mozilla/5.0", *args]
    p = subprocess.run(cmd, capture_output=True)
    return p.returncode, p.stdout


def summarize_html(path: Path, tag: str) -> dict:
    info = {"tag": tag, "path": str(path), "size": path.stat().st_size if path.exists() else 0}
    if not path.exists() or path.stat().st_size < 50:
        info["status"] = "empty"
        return info
    t = path.read_text(encoding="utf-8", errors="ignore")
    info["title"] = (re.search(r"<title[^>]*>(.*?)</title>", t, re.I | re.S) or [None, ""])[1]
    if isinstance(info["title"], str):
        info["title"] = re.sub(r"\s+", " ", info["title"]).strip()[:120]
    info["actions"] = re.findall(r'action=["\']([^"\']+)["\']', t, flags=re.I)[:20]
    info["input_names"] = re.findall(r'<input[^>]+name=["\']([^"\']+)["\']', t, flags=re.I)[:40]
    info["textarea_names"] = re.findall(
        r'<textarea[^>]+name=["\']([^"\']+)["\']', t, flags=re.I
    )
    info["select_names"] = re.findall(r'<select[^>]+name=["\']([^"\']+)["\']', t, flags=re.I)
    return info


def save_genes(name: str, genes: list[str], extra: dict | None = None) -> Path:
    csv_path = PRED / f"{name}_Quercetin_genes.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["gene_human", "source", "evidence", "note"])
        w.writeheader()
        for g in sorted(set(genes)):
            if not re.fullmatch(r"[A-Z][A-Z0-9]{1,14}", g):
                continue
            if g in {"HTML", "HTTP", "JSON", "POST", "GET", "NONE", "PDB", "CSV", "API"}:
                continue
            row = {"gene_human": g, "source": name, "evidence": "predicted", "note": ""}
            if extra:
                row["note"] = json.dumps(extra, ensure_ascii=False)[:200]
            w.writerow(row)
    return csv_path


def try_targetnet() -> dict:
    idx = PRED / "_targetnet_index.html"
    curl("-o", str(idx), "http://targetnet.scbdd.com/calcnet/index/")
    info = summarize_html(idx, "targetnet_index")
    print("TargetNet index", json.dumps(info, ensure_ascii=False)[:800])

    # common field names from TargetNet docs / page
    attempts = []
    for url, fields in [
        (
            "http://targetnet.scbdd.com/calcnet/index/",
            [
                "-F",
                f"smiles={SMILES}",
                "-F",
                "fingerprint=ECFP2",
                "-F",
                "threshold=0.9",
            ],
        ),
        (
            "http://targetnet.scbdd.com/calcnet/index/",
            ["-F", f"Smiles={SMILES}", "-F", "Fingerprint=ECFP4"],
        ),
        (
            "http://targetnet.scbdd.com/calcnet/predict_result/",
            ["-F", f"smiles={SMILES}"],
        ),
        (
            "http://targetnet.scbdd.com/calcnet/calc_prediction/",
            ["-F", f"smiles={SMILES}", "-F", "fp=ecfp4"],
        ),
    ]:
        out = PRED / f"_targetnet_post_{abs(hash(url + str(fields))) % 10**8}.html"
        curl(*fields, "-L", "-o", str(out), url)
        s = summarize_html(out, url)
        attempts.append(s)
        if out.exists() and out.stat().st_size > 2000:
            t = out.read_text(encoding="utf-8", errors="ignore")
            # TargetNet often shows tables with Gene Name / UniProt
            genes = re.findall(
                r"(?:Gene(?:\s*Name)?|Target)[^<]{0,40}</t[dh]>\s*<t[dh][^>]*>\s*([A-Z][A-Z0-9]{1,14})",
                t,
                re.I,
            )
            genes2 = re.findall(r"<td[^>]*>\s*([A-Z][A-Z0-9]{2,14})\s*</td>", t)
            # filter noise
            cand = [g for g in genes + genes2 if len(g) >= 2]
            if len(set(cand)) >= 8:
                path = save_genes("05_TargetNet", cand[:500])
                return {"status": "ok", "csv": str(path), "n": len(set(cand)), "attempts": attempts}
    # parse index for JS endpoints
    t = idx.read_text(encoding="utf-8", errors="ignore") if idx.exists() else ""
    urls = re.findall(r'["\'](/calcnet/[^"\']+)["\']', t)
    info["js_urls"] = sorted(set(urls))[:30]
    info["status"] = "no_parseable_result"
    info["attempts"] = attempts
    return info


def try_superpred() -> dict:
    idx = PRED / "_superpred_index.html"
    # cert often expired
    curl("-k", "-L", "-o", str(idx), "https://prediction.charite.de/subpages/target_prediction.php")
    info = summarize_html(idx, "superpred")
    print("SuperPred index", json.dumps(info, ensure_ascii=False)[:800])
    if info.get("size", 0) < 200:
        curl("-k", "-L", "-o", str(idx), "https://prediction.charite.de/")
        info = summarize_html(idx, "superpred_home")
    # try POST
    out = PRED / "_superpred_post.html"
    for fields in [
        ["-k", "-L", "-F", f"smiles={SMILES}", "-F", f"email={EMAIL}", "-o", str(out),
         "https://prediction.charite.de/subpages/target_prediction.php"],
        ["-k", "-L", "-F", f"smile={SMILES}", "-F", "start=Start", "-o", str(out),
         "https://prediction.charite.de/subpages/target_prediction.php"],
        ["-k", "-L", "-F", f"SmilesString={SMILES}", "-o", str(out),
         "https://prediction.charite.de/index.php?site=5"],
    ]:
        curl(*fields)
        if out.exists() and out.stat().st_size > 1000:
            t = out.read_text(encoding="utf-8", errors="ignore")
            genes = re.findall(r"\b([A-Z][A-Z0-9]{2,14})\b", t)
            # too noisy; look for table
            if "target" in t.lower() and t.count("<tr") > 5:
                info["status"] = "html_returned"
                info["post_size"] = out.stat().st_size
                return info
    info["status"] = "tls_or_form_blocked"
    return info


def try_sea() -> dict:
    idx = PRED / "_sea_index.html"
    curl("-k", "-L", "-o", str(idx), "https://sea.bkslab.org/")
    info = summarize_html(idx, "sea")
    print("SEA index", json.dumps(info, ensure_ascii=False)[:500])
    out = PRED / "_sea_post.html"
    for args in [
        ["-k", "-L", "-X", "POST", "-F", f"query={SMILES}", "-o", str(out), "https://sea.bkslab.org/search"],
        ["-k", "-L", "-G", "--data-urlencode", f"query={SMILES}", "-o", str(out), "https://sea.bkslab.org/search/"],
        ["-k", "-L", "-o", str(out), f"https://sea.bkslab.org/search/?query={SMILES}"],
    ]:
        curl(*args)
        if out.exists():
            info["last_size"] = out.stat().st_size
            t = out.read_text(encoding="utf-8", errors="ignore")
            if "target" in t.lower() and out.stat().st_size > 2000:
                info["status"] = "html_has_target"
                return info
    info["status"] = "blocked_or_no_api"
    return info


def pm_status(job: str) -> str:
    out = PRED / f"_pm_poll_{job}.html"
    curl("-F", f"mid={job}", "-o", str(out), "https://www.lilab-ecust.cn/pharmmapper/check.html")
    if not out.exists():
        return "curl_fail"
    t = out.read_text(encoding="utf-8", errors="ignore")
    m = re.search(
        r"Status</strong></label><label[^>]*><strong><span[^>]*>([^<]+)", t
    )
    return m.group(1).strip() if m else "unknown"


def main() -> None:
    meta = {}
    if META.exists():
        meta = json.loads(META.read_text(encoding="utf-8"))
    meta["email"] = EMAIL
    meta["jobs"] = meta.get("jobs") or {}
    for job in ["261011082113", "261011075421"]:
        st = pm_status(job)
        print("PM", job, st)
        meta["jobs"][job] = {
            "id": job,
            "email": EMAIL,
            "status": st,
        }
        if st.lower() == "completed":
            # download result pages
            for suf, q in [("", ""), ("_s1", "?s=1"), ("_s2", "?s=2")]:
                out = PRED / f"pm_{job}_result{suf}.html"
                curl(
                    "-L",
                    "-o",
                    str(out),
                    f"https://www.lilab-ecust.cn/pharmmapper/results/{job}.html{q}",
                )
    meta["other"] = {
        "targetnet": try_targetnet(),
        "superpred": try_superpred(),
        "sea": try_sea(),
    }
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", META)


if __name__ == "__main__":
    main()
