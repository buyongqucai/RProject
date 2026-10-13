"""Poll PharmMapper jobs; when Completed, download HTML + extract genes. Also refresh TargetNet CSV if needed."""
from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path

PRED = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_预测靶点_MultiPredict"
)
CODE = Path(__file__).resolve().parent
EMAIL = "1054034696@qq.com"
META = PRED / "00_预测站任务监听_JobMonitor.json"
JOBS = ["261011082113", "261011075421"]


def curl(*args: str, timeout: int = 180) -> int:
    p = subprocess.run(
        ["curl.exe", "-sS", "-m", str(timeout), "-A", "Mozilla/5.0", *args],
        capture_output=True,
    )
    return p.returncode


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


def download_results(job: str) -> None:
    for suf, q in [("", ""), ("_s1", "?s=1"), ("_s2", "?s=2")]:
        out = PRED / f"pm_{job}_result{suf}.html"
        curl(
            "-L",
            "-o",
            str(out),
            f"https://www.lilab-ecust.cn/pharmmapper/results/{job}.html{q}",
        )


def main() -> None:
    meta = {}
    if META.exists():
        meta = json.loads(META.read_text(encoding="utf-8"))
    meta["email"] = EMAIL
    meta.setdefault("jobs", {})
    deadline = time.time() + 50 * 60
    round_i = 0
    extracted = set()
    while time.time() < deadline:
        round_i += 1
        all_done = True
        for job in JOBS:
            st = pm_status(job)
            print(f"[poll#{round_i}] PM {job} -> {st}", flush=True)
            meta["jobs"][job] = {
                "id": job,
                "email": EMAIL,
                "status": st,
                "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            if st.lower() in {"completed", "finished", "done"}:
                if job not in extracted:
                    download_results(job)
                    extracted.add(job)
            elif st.lower() not in {"failed", "error"}:
                all_done = False
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        if all_done:
            break
        time.sleep(90)

    # extract genes once at least one completed
    if extracted or (PRED / "pm_261011075421_result_s2.html").exists():
        print("running extract...", flush=True)
        subprocess.run(
            ["python", "-u", str(CODE / "_pm_extract_genes.py")], check=False
        )
    print("monitor done ->", META, flush=True)


if __name__ == "__main__":
    main()
