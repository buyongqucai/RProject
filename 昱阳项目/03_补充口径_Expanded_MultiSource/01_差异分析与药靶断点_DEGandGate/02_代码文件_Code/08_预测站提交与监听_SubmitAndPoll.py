#!/usr/bin/env python3
"""Submit PharmMapper (+ try other predictors) and poll until results ready."""
from __future__ import annotations

import csv
import json
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PRED = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_预测靶点_MultiPredict"
)
EMAIL = "1054034696@qq.com"
MOL2 = PRED / "quercetin.mol2"
SDF = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"04_分子对接_Docking/01_数据文件_Data/01_初始数据_RawInitial/quercetin_PubChem3D.sdf"
)
SMILES = "C1=CC(=C(C=C1C2=C(C(=O)C3=C(C=C(C=C3O2)O)O)O)O)O"
META = PRED / "00_预测站任务监听_JobMonitor.json"


def curl(*args: str, timeout: int = 180) -> tuple[int, bytes]:
    cmd = ["curl.exe", "-sS", "-m", str(timeout), "-A", "Mozilla/5.0", *args]
    p = subprocess.run(cmd, capture_output=True)
    return p.returncode, p.stdout


def pm_status(job: str) -> str:
    out = PRED / f"_pm_poll_{job}.html"
    code, _ = curl(
        "-F",
        f"mid={job}",
        "-o",
        str(out),
        "https://www.lilab-ecust.cn/pharmmapper/check.html",
    )
    if code != 0 or not out.exists():
        return "curl_fail"
    t = out.read_text(encoding="utf-8", errors="ignore")
    m = re.search(
        r"Status</strong></label><label[^>]*><strong><span[^>]*>([^<]+)", t
    )
    return m.group(1).strip() if m else "unknown"


def pm_getres_html(job: str) -> Path:
    out = PRED / f"_pm_getres_{job}.html"
    curl(
        "-F",
        f"mid={job}",
        "-o",
        str(out),
        "https://www.lilab-ecust.cn/pharmmapper/getres.html",
    )
    return out


def pm_extract_links(html: str) -> list[str]:
    hrefs = re.findall(r'href="([^"]+)"', html)
    keep = []
    for h in hrefs:
        hl = h.lower()
        if any(k in hl for k in ["result", "download", "job", "file", ".txt", ".csv", ".zip", "xlsx"]):
            if h.startswith("/"):
                h = "https://www.lilab-ecust.cn" + h
            elif h.startswith("http"):
                pass
            else:
                h = "https://www.lilab-ecust.cn/pharmmapper/" + h
            keep.append(h)
    return sorted(set(keep))


def pm_try_download_tables(job: str) -> Path | None:
    """Try known PharmMapper result endpoints after Completed."""
    candidates = [
        f"https://www.lilab-ecust.cn/pharmmapper/help.html",  # noop warm
        f"https://www.lilab-ecust.cn/pharmmapper/result.html?job={job}",
        f"https://www.lilab-ecust.cn/pharmmapper/result.html?mid={job}",
        f"https://www.lilab-ecust.cn/pharmmapper/getres.html?mid={job}",
    ]
    html_path = pm_getres_html(job)
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    links = pm_extract_links(html)
    print("PM links", job, links[:20])
    # also scrape any /pharmmapper/ path with job id
    for m in re.finditer(rf"[\"']([^\"']*{job}[^\"']*)[\"']", html):
        u = m.group(1)
        if u.startswith("/"):
            u = "https://www.lilab-ecust.cn" + u
        links.append(u)
    # JS may load JSON
    for jsname in ["getres.js", "result.js", "check.js"]:
        code, body = curl(
            "-o",
            str(PRED / f"_pm_{jsname}"),
            f"https://www.lilab-ecust.cn/pharmmapper/js/{jsname}",
        )
        if code == 0 and body:
            txt = body.decode("utf-8", errors="ignore")
            for m in re.finditer(r"[\"']([^\"']*(?:result|download|getfile|jobfile)[^\"']*)[\"']", txt):
                u = m.group(1)
                if u.startswith("/"):
                    u = "https://www.lilab-ecust.cn" + u
                elif not u.startswith("http"):
                    u = "https://www.lilab-ecust.cn/pharmmapper/" + u
                links.append(u.replace("$JOB", job).replace("{job}", job).replace("+mid+", job))

    # probe constructed endpoints
    for u in [
        f"https://www.lilab-ecust.cn/pharmmapper/jobfile/{job}/",
        f"https://www.lilab-ecust.cn/pharmmapper/jobs/{job}/",
        f"https://www.lilab-ecust.cn/pharmmapper/tmp/{job}/",
        f"https://www.lilab-ecust.cn/pharmmapper/data/{job}/",
        f"https://www.lilab-ecust.cn/pharmmapper/download.html?mid={job}",
        f"https://www.lilab-ecust.cn/pharmmapper/download.html?job={job}",
    ]:
        links.append(u)

    saved = []
    for u in sorted(set(links)):
        if "help.html" in u:
            continue
        out = PRED / f"_pm_dl_{job}_{abs(hash(u)) % 10**8}.bin"
        code, body = curl("-L", "-o", str(out), "-w", "%{http_code}|%{content_type}", u)
        # curl -w appends to stdout not file when -o used; re-fetch status
        st, info = curl("-L", "-o", str(out), "-w", "%{http_code}|%{size_download}|%{content_type}", u)
        print("DL", info.decode(), u[:120])
        if out.exists() and out.stat().st_size > 500:
            head = out.read_bytes()[:200]
            if b"<!DOCTYPE" in head or b"<html" in head.lower():
                # parse for more links / tables
                t = out.read_text(encoding="utf-8", errors="ignore")
                if "FitScore" in t or "PDB" in t:
                    saved.append(out)
            else:
                saved.append(out)

    # parse getres HTML tables if present
    genes = parse_pm_html_genes(html)
    if genes:
        csv_path = PRED / "04_PharmMapper_Quercetin_genes.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["gene_human", "pdb", "fit_score", "source", "evidence", "job_id"],
            )
            w.writeheader()
            w.writerows(genes)
        print("PM genes", len(genes), csv_path)
        return csv_path
    return saved[0] if saved else None


def parse_pm_html_genes(html: str) -> list[dict]:
    rows = []
    # typical columns: Rank PDB FitScore Target Name ...
    for m in re.finditer(
        r"<tr[^>]*>\s*<td[^>]*>\s*(\d+)\s*</td>\s*<td[^>]*>\s*([A-Za-z0-9]{4})\s*</td>[\s\S]*?FitScore[\s\S]*?<td[^>]*>\s*([0-9.]+)",
        html,
        re.I,
    ):
        rows.append(
            {
                "gene_human": "",
                "pdb": m.group(2),
                "fit_score": m.group(3),
                "source": "PharmMapper",
                "evidence": "predicted",
                "job_id": "",
            }
        )
    # UniProt / gene symbol patterns near PDB
    for m in re.finditer(
        r"([A-Z0-9]{4}).{0,120}?(?:Gene|gene|GENE)[:\s]*([A-Za-z0-9-]{2,20})",
        html,
    ):
        rows.append(
            {
                "gene_human": m.group(2),
                "pdb": m.group(1),
                "fit_score": "",
                "source": "PharmMapper",
                "evidence": "predicted",
                "job_id": "",
            }
        )
    # Target name with human gene-like
    for m in re.finditer(r">\s*([A-Z][A-Z0-9]{1,14})\s*<", html):
        g = m.group(1)
        if g in {"PDB", "HTML", "HTTP", "JSON", "POST", "JOB", "ID"}:
            continue
    return rows


def submit_pharmmapper() -> str:
    cookie = PRED / "_pm_monitor_cookies.txt"
    if cookie.exists():
        cookie.unlink()
    step1 = PRED / "_pm_monitor_step1.html"
    curl(
        "-L",
        "-c",
        str(cookie),
        "-b",
        str(cookie),
        "-F",
        f"file=@{MOL2};filename=quercetin.mol2",
        "-F",
        f"email={EMAIL}",
        "-F",
        "describe=yuyang_quercetin_monitor",
        "-F",
        "submit=Submit",
        "-o",
        str(step1),
        "https://www.lilab-ecust.cn/pharmmapper/submitjob.html",
    )
    outj = PRED / "_pm_monitor_job.json"
    curl(
        "-c",
        str(cookie),
        "-b",
        str(cookie),
        "-H",
        "X-Requested-With: XMLHttpRequest",
        "-F",
        "d0=Y",
        "-F",
        "d1=300",
        "-F",
        "d2=4",
        "-F",
        "d3=500",
        "-F",
        "d4=1",
        "-F",
        "d5=500",
        "-F",
        "d6=N",
        "-F",
        "d7=MMFF94",
        "-F",
        "d8=2",
        "-F",
        "d9=300",
        "-F",
        "d10=N",
        "-F",
        "d11=Y",
        "-F",
        "d12=2.0",
        "-F",
        "d13=90",
        "-F",
        "d14=1.0",
        "-F",
        "d15=1.0",
        "-F",
        "d16=1.0",
        "-F",
        "d17=1.0",
        "-F",
        "d18=1.0",
        "-F",
        "d19=1.0",
        "-F",
        "d20=0",
        "-F",
        "d21=0",
        "-F",
        "d22=0",
        "-F",
        "d23=0",
        "-F",
        "d24=0",
        "-F",
        "d25=0",
        "-o",
        str(outj),
        "https://www.lilab-ecust.cn/pharmmapper/submitdb.html",
    )
    data = json.loads(outj.read_text(encoding="utf-8"))
    job = str(data.get("response", ""))
    (PRED / "04_PharmMapper_job_id.txt").write_text(job + "\n", encoding="utf-8")
    (PRED / "04_PharmMapper_submit_meta.txt").write_text(
        f"email={EMAIL}\njob={job}\n", encoding="utf-8"
    )
    return job


def try_targetnet() -> dict:
    """TargetNet: probe upload/predict endpoints with SMILES."""
    info = {"status": "unknown", "detail": ""}
    # save index
    idx = PRED / "_targetnet_index.html"
    curl("-o", str(idx), "http://targetnet.scbdd.com/calcnet/index/")
    html = idx.read_text(encoding="utf-8", errors="ignore") if idx.exists() else ""
    actions = re.findall(r'action=["\']([^"\']+)["\']', html, flags=re.I)
    info["actions"] = actions
    # common predict endpoints
    for url, fields in [
        (
            "http://targetnet.scbdd.com/calcnet/index/",
            [
                "-F",
                f"smiles={SMILES}",
                "-F",
                "fingerprint=ECFP4",
                "-F",
                "email=" + EMAIL,
            ],
        ),
        (
            "http://targetnet.scbdd.com/calcnet/predict/",
            ["-F", f"smiles={SMILES}", "-F", f"email={EMAIL}"],
        ),
        (
            "http://targetnet.scbdd.com/calcnet/calc/",
            ["-F", f"Smiles={SMILES}", "-F", f"email={EMAIL}"],
        ),
    ]:
        out = PRED / f"_targetnet_try_{abs(hash(url)) % 10**6}.html"
        code, body = curl(*fields, "-o", str(out), "-w", "%{http_code}", url)
        # stdout has http code when -w used with -o? depends; read file
        info["detail"] += f"| tried {url} size={out.stat().st_size if out.exists() else 0}"
        if out.exists():
            t = out.read_text(encoding="utf-8", errors="ignore")
            if "gene" in t.lower() or "target" in t.lower() and "error" not in t.lower()[:200]:
                # extract gene-like tokens later
                genes = sorted(set(re.findall(r"\b([A-Z][A-Z0-9]{1,10})\b", t)))
                genes = [g for g in genes if g not in {"HTML", "HTTP", "POST", "GET", "JSON"}]
                if len(genes) > 5:
                    csv_path = PRED / "05_TargetNet_Quercetin_genes.csv"
                    with csv_path.open("w", newline="", encoding="utf-8") as f:
                        w = csv.DictWriter(f, fieldnames=["gene_human", "source", "evidence"])
                        w.writeheader()
                        for g in genes[:500]:
                            w.writerow(
                                {
                                    "gene_human": g,
                                    "source": "TargetNet",
                                    "evidence": "predicted",
                                }
                            )
                    info["status"] = "saved_csv"
                    info["csv"] = str(csv_path)
                    return info
    info["status"] = "no_parseable_result"
    return info


def try_sea() -> dict:
    info = {"status": "unknown"}
    # SEA often uses library search page; try GET/POST smiles
    out = PRED / "_sea_try.html"
    for args in [
        ["-G", "--data-urlencode", f"query={SMILES}", "-o", str(out), "https://sea.bkslab.org/search"],
        ["-X", "POST", "--data-urlencode", f"query={SMILES}", "-o", str(out), "https://sea.bkslab.org/search"],
        ["-X", "POST", "-F", f"smiles={SMILES}", "-o", str(out), "https://sea.bkslab.org/search"],
    ]:
        curl(*args)
        if out.exists() and out.stat().st_size > 200:
            t = out.read_text(encoding="utf-8", errors="ignore")
            info["size"] = out.stat().st_size
            if "405" in t or "Method Not Allowed" in t:
                info["status"] = "method_not_allowed"
                continue
            # look for job id / targets
            m = re.search(r"job[_ ]?id[\"':\s]+([A-Za-z0-9_-]+)", t, re.I)
            if m:
                info["status"] = "job"
                info["job"] = m.group(1)
                return info
            if "target" in t.lower():
                info["status"] = "html_has_target"
                return info
    info["status"] = "blocked_or_no_api"
    return info


def try_superpred() -> dict:
    info = {"status": "unknown"}
    out = PRED / "_superpred_try.html"
    code, _ = curl("-o", str(out), "https://prediction.charite.de/")
    if not out.exists() or out.stat().st_size < 100:
        info["status"] = "tls_or_unreachable"
        return info
    # try predict endpoints
    for url in [
        "https://prediction.charite.de/subpages/target_prediction.php",
        "https://prediction.charite.de/index.php?site=5",
    ]:
        curl(
            "-F",
            f"smiles={SMILES}",
            "-F",
            f"email={EMAIL}",
            "-o",
            str(PRED / "_superpred_post.html"),
            url,
        )
    info["status"] = "page_reached_post_attempted"
    return info


def load_meta() -> dict:
    if META.exists():
        return json.loads(META.read_text(encoding="utf-8"))
    return {"jobs": {}, "email": EMAIL}


def save_meta(meta: dict) -> None:
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    meta = load_meta()
    meta["email"] = EMAIL

    # ensure mol2
    if not MOL2.exists() and SDF.exists():
        subprocess.run(["obabel", str(SDF), "-omol2", "-O", str(MOL2)], check=False)

    # PharmMapper jobs to watch: new + previous completed
    jobs = []
    # always (re)submit with user email as requested
    try:
        job = submit_pharmmapper()
        print("PM submitted", job, EMAIL)
        jobs.append(job)
        meta["jobs"]["pharmmapper_latest"] = {
            "id": job,
            "email": EMAIL,
            "status": "submitted",
        }
    except Exception as e:
        print("PM submit error", e)

    for extra in ["261011082113", "261011075421"]:
        if extra not in jobs:
            jobs.append(extra)

    meta["other"] = {
        "targetnet": try_targetnet(),
        "sea": try_sea(),
        "superpred": try_superpred(),
    }
    save_meta(meta)

    # poll PharmMapper up to ~45 min
    deadline = time.time() + 45 * 60
    round_i = 0
    while time.time() < deadline:
        round_i += 1
        all_done = True
        for job in jobs:
            st = pm_status(job)
            print(f"[PM poll#{round_i}] {job} -> {st}")
            meta.setdefault("jobs", {})[job] = {
                "id": job,
                "email": EMAIL,
                "status": st,
                "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            if st.lower() in {"completed", "finished", "done"}:
                path = pm_try_download_tables(job)
                meta["jobs"][job]["result"] = str(path) if path else None
            elif st.lower() in {"failed", "error"}:
                pass
            else:
                all_done = False
        save_meta(meta)
        if all_done:
            break
        time.sleep(90)

    print("monitor meta ->", META)


if __name__ == "__main__":
    main()
